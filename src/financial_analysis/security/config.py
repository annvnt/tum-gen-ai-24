"""
Security configuration for financial platform
Centralized security settings and configurations
"""

import os
from typing import Dict, List, Any


class SecurityConfig:
    """Security configuration class"""
    
    # File upload settings
    MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", "100")) * 1024 * 1024  # 100MB default
    ALLOWED_FILE_EXTENSIONS = {
        'excel': ['.xlsx', '.xls', '.csv'],
        'pdf': ['.pdf'],
        'json': ['.json'],
        'text': ['.txt']
    }
    
    # Rate limiting settings
    RATE_LIMITS = {
        'default': {'requests': 100, 'window': 60},  # 100 requests per minute
        'upload': {'requests': 10, 'window': 3600},  # 10 uploads per hour
        'auth': {'requests': 5, 'window': 300},      # 5 auth attempts per 5 minutes
        'api': {'requests': 1000, 'window': 60},     # 1000 API calls per minute
    }
    
    # Authentication settings
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
    JWT_ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    
    # Session settings
    SESSION_TIMEOUT = int(os.getenv("SESSION_TIMEOUT", "3600"))  # 1 hour
    MAX_SESSIONS_PER_USER = int(os.getenv("MAX_SESSIONS_PER_USER", "5"))
    
    # Redis settings
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    REDIS_SESSION_DB = int(os.getenv("REDIS_SESSION_DB", "0"))
    REDIS_RATE_LIMIT_DB = int(os.getenv("REDIS_RATE_LIMIT_DB", "1"))
    
    # Security headers
    SECURITY_HEADERS = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
        "Referrer-Policy": "strict-origin-when-cross-origin",
    }
    
    # CORS settings
    CORS_ALLOWED_ORIGINS = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://localhost:3000",
        "https://127.0.0.1:3000",
    ]
    
    # GCS settings
    GCS_ALLOWED_BUCKETS = [
        "financial-reports-data",
        "financial-uploads-data",
    ]
    
    # Path restrictions
    ALLOWED_TEMP_DIRS = [
        "/tmp",
        "/var/tmp",
        "/app/data/temp",
    ]
    
    # SQL injection prevention
    SQL_INJECTION_DETECTION = True
    MAX_QUERY_LENGTH = 1000
    
    # Logging settings
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_SENSITIVE_DATA = os.getenv("LOG_SENSITIVE_DATA", "false").lower() == "true"
    
    # Monitoring settings
    ENABLE_SECURITY_MONITORING = os.getenv("ENABLE_SECURITY_MONITORING", "true").lower() == "true"
    SECURITY_ALERT_EMAIL = os.getenv("SECURITY_ALERT_EMAIL", "security@company.com")
    
    @classmethod
    def get_allowed_file_extensions(cls, file_type: str = None) -> List[str]:
        """Get allowed file extensions for specific type or all types"""
        if file_type and file_type in cls.ALLOWED_FILE_EXTENSIONS:
            return cls.ALLOWED_FILE_EXTENSIONS[file_type]
        
        # Return all extensions
        all_extensions = []
        for extensions in cls.ALLOWED_FILE_EXTENSIONS.values():
            all_extensions.extend(extensions)
        return all_extensions
    
    @classmethod
    def is_file_allowed(cls, filename: str, file_type: str = None) -> bool:
        """Check if file is allowed"""
        from pathlib import Path
        
        extension = Path(filename).suffix.lower()
        allowed_extensions = cls.get_allowed_file_extensions(file_type)
        
        return extension in allowed_extensions
    
    @classmethod
    def get_rate_limit_config(cls, endpoint_type: str) -> Dict[str, int]:
        """Get rate limit configuration for endpoint type"""
        return cls.RATE_LIMITS.get(endpoint_type, cls.RATE_LIMITS['default'])
    
    @classmethod
    def validate_environment(cls) -> List[str]:
        """Validate security configuration"""
        warnings = []
        
        # Check JWT secret key
        if cls.JWT_SECRET_KEY == "your-secret-key-change-in-production":
            warnings.append("JWT_SECRET_KEY is using default value. Please change in production.")
        
        # Check Redis URL
        if cls.REDIS_URL == "redis://localhost:6379":
            warnings.append("Using default Redis URL. Consider using secure Redis in production.")
        
        # Check CORS origins
        localhost_origins = [origin for origin in cls.CORS_ALLOWED_ORIGINS if 'localhost' in origin]
        if localhost_origins:
            warnings.append("CORS configuration includes localhost origins. Review for production.")
        
        return warnings


# Global security configuration instance
security_config = SecurityConfig()