"""
Session management with Redis for financial platform
Provides secure session handling with Redis backend
"""

import redis
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, List
import logging

logger = logging.getLogger(__name__)


class SessionManager:
    """Redis-based session management"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379", db: int = 0):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.from_url(redis_url, decode_responses=True, db=db)
            self.redis_client.ping()
            logger.info("Redis session manager initialized")
        except redis.ConnectionError:
            logger.warning("Redis connection failed, using in-memory fallback")
            self.redis_client = None
            self._memory_store = {}
    
    def create_session(self, user_id: str, session_data: Dict[str, Any] = None, 
                      expires_in: int = 3600) -> str:
        """Create new session"""
        session_id = str(uuid.uuid4())
        session_data = session_data or {}
        
        session_info = {
            "user_id": user_id,
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(seconds=expires_in)).isoformat(),
            "data": session_data
        }
        
        if self.redis_client:
            try:
                self.redis_client.setex(
                    f"session:{session_id}",
                    expires_in,
                    json.dumps(session_info)
                )
            except redis.RedisError as e:
                logger.error(f"Redis error creating session: {e}")
                self._set_memory_session(session_id, session_info, expires_in)
        else:
            self._set_memory_session(session_id, session_info, expires_in)
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data"""
        if not session_id:
            return None
        
        try:
            if self.redis_client:
                data = self.redis_client.get(f"session:{session_id}")
                if data:
                    return json.loads(data)
            else:
                return self._get_memory_session(session_id)
        except (json.JSONDecodeError, redis.RedisError) as e:
            logger.error(f"Error getting session: {e}")
        
        return None
    
    def update_session(self, session_id: str, session_data: Dict[str, Any]) -> bool:
        """Update session data"""
        existing_session = self.get_session(session_id)
        if not existing_session:
            return False
        
        existing_session["data"] = session_data
        existing_session["updated_at"] = datetime.utcnow().isoformat()
        
        if self.redis_client:
            try:
                ttl = self.redis_client.ttl(f"session:{session_id}")
                if ttl > 0:
                    self.redis_client.setex(
                        f"session:{session_id}",
                        ttl,
                        json.dumps(existing_session)
                    )
                    return True
            except redis.RedisError as e:
                logger.error(f"Redis error updating session: {e}")
        
        return self._update_memory_session(session_id, existing_session)
    
    def delete_session(self, session_id: str) -> bool:
        """Delete session"""
        if not session_id:
            return False
        
        try:
            if self.redis_client:
                result = self.redis_client.delete(f"session:{session_id}")
                return result > 0
            else:
                return self._delete_memory_session(session_id)
        except redis.RedisError as e:
            logger.error(f"Error deleting session: {e}")
        
        return False
    
    def extend_session(self, session_id: str, expires_in: int = 3600) -> bool:
        """Extend session expiration"""
        if not session_id:
            return False
        
        try:
            if self.redis_client:
                result = self.redis_client.expire(f"session:{session_id}", expires_in)
                return bool(result)
            else:
                return self._extend_memory_session(session_id, expires_in)
        except redis.RedisError as e:
            logger.error(f"Error extending session: {e}")
        
        return False
    
    def is_session_valid(self, session_id: str) -> bool:
        """Check if session is valid and not expired"""
        session_data = self.get_session(session_id)
        if not session_data:
            return False
        
        try:
            expires_at = datetime.fromisoformat(session_data["expires_at"])
            return datetime.utcnow() < expires_at
        except (ValueError, KeyError):
            return False
    
    def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all sessions for a user"""
        sessions = []
        
        try:
            if self.redis_client:
                # Scan for user sessions (Redis pattern matching)
                pattern = f"session:*"
                for key in self.redis_client.scan_iter(match=pattern, count=100):
                    session_data = self.redis_client.get(key)
                    if session_data:
                        data = json.loads(session_data)
                        if data.get("user_id") == user_id:
                            sessions.append({
                                "session_id": key.replace("session:", ""),
                                **data
                            })
            else:
                # Memory store fallback
                for session_id, data in self._memory_store.items():
                    if isinstance(data, dict) and data.get("user_id") == user_id:
                        sessions.append({
                            "session_id": session_id,
                            **data
                        })
        except (json.JSONDecodeError, redis.RedisError) as e:
            logger.error(f"Error getting user sessions: {e}")
        
        return sessions
    
    def invalidate_user_sessions(self, user_id: str) -> int:
        """Invalidate all sessions for a user"""
        sessions = self.get_user_sessions(user_id)
        deleted_count = 0
        
        for session in sessions:
            if self.delete_session(session["session_id"]):
                deleted_count += 1
        
        return deleted_count
    
    def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions"""
        cleaned_count = 0
        
        try:
            if self.redis_client:
                # Redis automatically handles expiration
                return 0
            else:
                # Manual cleanup for memory store
                expired_sessions = []
                now = datetime.utcnow()
                
                for session_id, data in self._memory_store.items():
                    if isinstance(data, dict):
                        try:
                            expires_at = datetime.fromisoformat(data.get("expires_at", ""))
                            if now >= expires_at:
                                expired_sessions.append(session_id)
                        except (ValueError, TypeError):
                            expired_sessions.append(session_id)
                
                for session_id in expired_sessions:
                    self._delete_memory_session(session_id)
                    cleaned_count += 1
        except Exception as e:
            logger.error(f"Error cleaning up sessions: {e}")
        
        return cleaned_count
    
    def get_session_count(self) -> int:
        """Get total active session count"""
        try:
            if self.redis_client:
                pattern = f"session:*"
                return len(list(self.redis_client.scan_iter(match=pattern, count=100)))
            else:
                return len([
                    k for k, v in self._memory_store.items()
                    if isinstance(v, dict) and self.is_session_valid(k)
                ])
        except redis.RedisError as e:
            logger.error(f"Error getting session count: {e}")
            return 0
    
    def _set_memory_session(self, session_id: str, session_info: Dict, expires_in: int):
        """Set session in memory store"""
        self._memory_store[session_id] = session_info
        # Schedule cleanup
        import threading
        timer = threading.Timer(expires_in, self._delete_memory_session, [session_id])
        timer.daemon = True
        timer.start()
    
    def _get_memory_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session from memory store"""
        data = self._memory_store.get(session_id)
        if data and self._is_memory_session_valid(session_id):
            return data
        return None
    
    def _update_memory_session(self, session_id: str, session_info: Dict) -> bool:
        """Update session in memory store"""
        if session_id in self._memory_store:
            self._memory_store[session_id] = session_info
            return True
        return False
    
    def _delete_memory_session(self, session_id: str) -> bool:
        """Delete session from memory store"""
        if session_id in self._memory_store:
            del self._memory_store[session_id]
            return True
        return False
    
    def _extend_memory_session(self, session_id: str, expires_in: int) -> bool:
        """Extend memory session expiration"""
        if session_id in self._memory_store:
            # In memory store, we just update the expires_at
            data = self._memory_store[session_id]
            data["expires_at"] = (datetime.utcnow() + timedelta(seconds=expires_in)).isoformat()
            return True
        return False
    
    def _is_memory_session_valid(self, session_id: str) -> bool:
        """Check if memory session is valid"""
        data = self._memory_store.get(session_id)
        if not data:
            return False
        
        try:
            expires_at = datetime.fromisoformat(data.get("expires_at", ""))
            return datetime.utcnow() < expires_at
        except (ValueError, TypeError):
            return False


# Global session manager instance
session_manager = SessionManager()