"""
Authentication and authorization management for financial platform
Provides JWT-based authentication and role-based access control
"""

import jwt
import bcrypt
import secrets
import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any
from pydantic import BaseModel, Field
import logging
from functools import wraps
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import text

from ..storage.database_manager import db_manager
from .session_manager import SessionManager
logger = logging.getLogger(__name__)

# Security configuration
SECRET_KEY = secrets.token_urlsafe(32)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

security = HTTPBearer()


class UserCredentials(BaseModel):
    """User credentials model"""
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_\-@.]+$")
    password: str = Field(..., min_length=8, max_length=128)
    email: Optional[str] = Field(None, pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


class TokenData(BaseModel):
    """JWT token data"""
    username: Optional[str] = None
    user_id: Optional[str] = None
    roles: List[str] = Field(default_factory=list)
    permissions: List[str] = Field(default_factory=list)


class UserCreate(BaseModel):
    """User creation model"""
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    password: str = Field(..., min_length=8, max_length=128)
    full_name: Optional[str] = Field(None, max_length=100)
    roles: List[str] = Field(default_factory=lambda: ["user"])


class User(BaseModel):
    """User model"""
    id: str
    username: str
    email: str
    full_name: Optional[str]
    roles: List[str]
    is_active: bool = True
    created_at: datetime
    last_login: Optional[datetime]


class AuthManager:
    """Authentication and authorization manager"""
    
    def __init__(self):
        self.session_manager = SessionManager()
        self._init_database()
    
    def _init_database(self):
        """Initialize authentication database tables"""
        try:
            with db_manager.get_session() as session:
                # Create users table if not exists
                session.execute(text("""
                    CREATE TABLE IF NOT EXISTS users (
                        id VARCHAR(36) PRIMARY KEY,
                        username VARCHAR(50) UNIQUE NOT NULL,
                        email VARCHAR(255) UNIQUE NOT NULL,
                        password_hash VARCHAR(255) NOT NULL,
                        full_name VARCHAR(100),
                        roles JSON DEFAULT '["user"]',
                        is_active BOOLEAN DEFAULT TRUE,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        last_login DATETIME,
                        failed_login_attempts INTEGER DEFAULT 0,
                        locked_until DATETIME
                    )
                """))
                
                # Create sessions table if not exists
                session.execute(text("""
                    CREATE TABLE IF NOT EXISTS user_sessions (
                        id VARCHAR(36) PRIMARY KEY,
                        user_id VARCHAR(36) NOT NULL,
                        refresh_token VARCHAR(255) UNIQUE NOT NULL,
                        expires_at DATETIME NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        ip_address VARCHAR(45),
                        user_agent TEXT,
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                    )
                """))
                
                # Create default admin user if not exists
                admin_exists = session.execute(
                    text("SELECT COUNT(*) FROM users WHERE username = 'admin'")
                ).scalar()
                
                if not admin_exists:
                    admin_hash = self._hash_password("admin123")
                    session.execute(
                        text("""
                            INSERT INTO users (id, username, email, password_hash, roles)
                            VALUES (:id, :username, :email, :password_hash, :roles)
                        """),
                        {
                            "id": str(uuid.uuid4()),
                            "username": "admin",
                            "email": "admin@financialapp.com",
                            "password_hash": admin_hash,
                            "roles": '["admin", "user"]'
                        }
                    )
                
                session.commit()
                logger.info("Authentication database initialized")
                
        except Exception as e:
            logger.error(f"Error initializing auth database: {e}")
            raise
    
    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        try:
            return bcrypt.checkpw(
                plain_password.encode('utf-8'),
                hashed_password.encode('utf-8')
            )
        except Exception:
            return False
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: timedelta = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    def create_refresh_token(self, user_id: str) -> str:
        """Create refresh token"""
        expires_delta = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        refresh_token = secrets.token_urlsafe(32)
        
        # Store refresh token in database
        with db_manager.get_session() as session:
            session.execute(
                text("""
                    INSERT INTO user_sessions (id, user_id, refresh_token, expires_at)
                    VALUES (:id, :user_id, :refresh_token, :expires_at)
                """),
                {
                    "id": str(uuid.uuid4()),
                    "user_id": user_id,
                    "refresh_token": refresh_token,
                    "expires_at": datetime.utcnow() + expires_delta
                }
            )
            session.commit()
        
        return refresh_token
    
    def register_user(self, user_data: UserCreate) -> Dict[str, Any]:
        """Register new user"""
        try:
            with db_manager.get_session() as session:
                # Check if username exists
                existing = session.execute(
                    text("SELECT COUNT(*) FROM users WHERE username = :username"),
                    {"username": user_data.username}
                ).scalar()
                
                if existing:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Username already exists"
                    )
                
                # Check if email exists
                existing = session.execute(
                    text("SELECT COUNT(*) FROM users WHERE email = :email"),
                    {"email": user_data.email}
                ).scalar()
                
                if existing:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Email already exists"
                    )
                
                # Create user
                user_id = str(uuid.uuid4())
                password_hash = self._hash_password(user_data.password)
                
                session.execute(
                    text("""
                        INSERT INTO users (id, username, email, password_hash, full_name, roles)
                        VALUES (:id, :username, :email, :password_hash, :full_name, :roles)
                    """),
                    {
                        "id": user_id,
                        "username": user_data.username,
                        "email": user_data.email,
                        "password_hash": password_hash,
                        "full_name": user_data.full_name,
                        "roles": json.dumps(user_data.roles)
                    }
                )
                session.commit()
                
                return {
                    "user_id": user_id,
                    "username": user_data.username,
                    "email": user_data.email,
                    "message": "User registered successfully"
                }
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error registering user: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error registering user"
            )
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user"""
        try:
            with db_manager.get_session() as session:
                # Get user
                result = session.execute(
                    text("""
                        SELECT id, username, email, password_hash, full_name, roles, 
                               is_active, created_at, last_login, locked_until
                        FROM users WHERE username = :username
                    """),
                    {"username": username}
                ).fetchone()
                
                if not result:
                    return None
                
                # Check if account is locked
                if result.locked_until and result.locked_until > datetime.utcnow():
                    raise HTTPException(
                        status_code=status.HTTP_423_LOCKED,
                        detail="Account is locked due to too many failed login attempts"
                    )
                
                # Check if account is active
                if not result.is_active:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Account is deactivated"
                    )
                
                # Verify password
                if not self._verify_password(password, result.password_hash):
                    # Increment failed login attempts
                    session.execute(
                        text("""
                            UPDATE users SET failed_login_attempts = failed_login_attempts + 1
                            WHERE username = :username
                        """),
                        {"username": username}
                    )
                    
                    # Lock account after 5 failed attempts
                    if result.failed_login_attempts + 1 >= 5:
                        session.execute(
                            text("""
                                UPDATE users SET locked_until = :locked_until
                                WHERE username = :username
                            """),
                            {
                                "username": username,
                                "locked_until": datetime.utcnow() + timedelta(minutes=30)
                            }
                        )
                    
                    session.commit()
                    return None
                
                # Reset failed attempts and update last login
                session.execute(
                    text("""
                        UPDATE users SET 
                            failed_login_attempts = 0,
                            locked_until = NULL,
                            last_login = :last_login
                        WHERE username = :username
                    """),
                    {
                        "username": username,
                        "last_login": datetime.utcnow()
                    }
                )
                session.commit()
                
                return User(
                    id=result.id,
                    username=result.username,
                    email=result.email,
                    full_name=result.full_name,
                    roles=json.loads(result.roles),
                    is_active=result.is_active,
                    created_at=result.created_at,
                    last_login=result.last_login
                )
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error authenticating user: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication error"
            )
    
    def verify_token(self, token: str) -> Optional[TokenData]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
            user_id: str = payload.get("user_id")
            roles: List[str] = payload.get("roles", [])
            permissions: List[str] = payload.get("permissions", [])
            
            if username is None or user_id is None:
                return None
            
            return TokenData(
                username=username,
                user_id=user_id,
                roles=roles,
                permissions=permissions
            )
            
        except jwt.PyJWTError:
            return None
    
    def get_current_user(self, credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
        """Get current authenticated user"""
        token = credentials.credentials
        token_data = self.verify_token(token)
        
        if token_data is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get user from database
        with db_manager.get_session() as session:
            result = session.execute(
                text("""
                    SELECT id, username, email, full_name, roles, is_active, created_at, last_login
                    FROM users WHERE id = :user_id AND is_active = 1
                """),
                {"user_id": token_data.user_id}
            ).fetchone()
            
            if not result:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            return User(
                id=result.id,
                username=result.username,
                email=result.email,
                full_name=result.full_name,
                roles=json.loads(result.roles),
                is_active=result.is_active,
                created_at=result.created_at,
                last_login=result.last_login
            )
    
    def require_role(self, required_role: str):
        """Role-based access control decorator"""
        def role_checker(user: User = Depends(self.get_current_user)):
            if required_role not in user.roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions"
                )
            return user
        return role_checker
    
    def require_any_role(self, required_roles: List[str]):
        """Require any of the specified roles"""
        def role_checker(user: User = Depends(self.get_current_user)):
            if not any(role in user.roles for role in required_roles):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions"
                )
            return user
        return role_checker
    
    def logout_user(self, user_id: str) -> bool:
        """Logout user by invalidating tokens"""
        try:
            with db_manager.get_session() as session:
                # Remove all sessions for the user
                session.execute(
                    text("DELETE FROM user_sessions WHERE user_id = :user_id"),
                    {"user_id": user_id}
                )
                session.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error logging out user: {e}")
            return False
    
    def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        """Refresh access token using refresh token"""
        try:
            with db_manager.get_session() as session:
                # Validate refresh token
                result = session.execute(
                    text("""
                        SELECT us.user_id, u.username, u.roles
                        FROM user_sessions us
                        JOIN users u ON us.user_id = u.id
                        WHERE us.refresh_token = :refresh_token
                        AND us.expires_at > :now
                    """),
                    {
                        "refresh_token": refresh_token,
                        "now": datetime.utcnow()
                    }
                ).fetchone()
                
                if not result:
                    return None
                
                # Create new access token
                access_token = self.create_access_token({
                    "sub": result.username,
                    "user_id": result.user_id,
                    "roles": json.loads(result.roles)
                })
                
                return access_token
                
        except Exception as e:
            logger.error(f"Error refreshing token: {e}")
            return None


# Global auth manager instance
auth_manager = AuthManager()