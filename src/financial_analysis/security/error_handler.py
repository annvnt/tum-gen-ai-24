"""
Enhanced error handling and sanitization for financial platform
Provides secure error responses and logging
"""

import logging
import traceback
from typing import Dict, Any, Optional, List
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class SecurityError(Exception):
    """Base security error"""
    pass


class ValidationError(SecurityError):
    """Input validation error"""
    pass


class PathTraversalError(SecurityError):
    """Path traversal attempt detected"""
    pass


class SQLInjectionError(SecurityError):
    """SQL injection attempt detected"""
    pass


class RateLimitError(SecurityError):
    """Rate limit exceeded"""
    pass


class SecurityErrorHandler:
    """Centralized error handling with security considerations"""
    
    # Sensitive patterns to mask in error messages
    SENSITIVE_PATTERNS = [
        'password',
        'token',
        'secret',
        'key',
        'auth',
        'credential',
        'private',
        'passwd',
        'pwd',
        'api_key',
        'access_token',
        'refresh_token',
    ]
    
    @classmethod
    def sanitize_error_message(cls, message: str) -> str:
        """Sanitize error message to remove sensitive information"""
        if not message:
            return "An error occurred"
        
        message_lower = message.lower()
        
        # Mask sensitive information
        for pattern in cls.SENSITIVE_PATTERNS:
            if pattern in message_lower:
                return "Invalid input or authentication error"
        
        # Remove file paths
        import re
        message = re.sub(r'(\/[^\/\s]+)+', '[REDACTED_PATH]', message)
        message = re.sub(r'([A-Za-z]:\\[^\\\s]+)+', '[REDACTED_PATH]', message)
        
        # Remove email addresses
        message = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[REDACTED_EMAIL]', message)
        
        # Remove UUIDs
        message = re.sub(r'\b[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\b', '[REDACTED_ID]', message)
        
        return message
    
    @classmethod
    def create_secure_response(cls, error: Exception, status_code: int = 500, 
                             include_details: bool = False) -> Dict[str, Any]:
        """Create secure error response"""
        
        # Map exception types to appropriate status codes
        exception_map = {
            ValidationError: 400,
            PathTraversalError: 403,
            SQLInjectionError: 400,
            RateLimitError: 429,
            SecurityError: 403,
            ValueError: 400,
            TypeError: 400,
            FileNotFoundError: 404,
            PermissionError: 403,
        }
        
        error_type = type(error)
        status_code = exception_map.get(error_type, status_code)
        
        # Create secure error response
        response = {
            "error": {
                "message": cls.sanitize_error_message(str(error)),
                "code": error_type.__name__,
                "timestamp": datetime.utcnow().isoformat(),
                "status_code": status_code
            }
        }
        
        # Add generic error details for debugging (safely)
        if include_details and status_code < 500:
            response["error"]["details"] = {
                "type": error_type.__name__,
                "help": "Please check your input and try again"
            }
        
        return response
    
    @classmethod
    def log_security_event(cls, error: Exception, request: Optional[Request] = None, 
                          context: Dict[str, Any] = None) -> None:
        """Log security events with context"""
        log_entry = {
            "event_type": "security_error",
            "error_type": type(error).__name__,
            "timestamp": datetime.utcnow().isoformat(),
            "message": str(error),
            "context": context or {}
        }
        
        if request:
            log_entry["request"] = {
                "method": request.method,
                "url": str(request.url),
                "client_ip": request.client.host if request.client else "unknown",
                "user_agent": request.headers.get("user-agent", "unknown"),
                "referer": request.headers.get("referer", "unknown")
            }
        
        # Log at appropriate level
        if isinstance(error, (PathTraversalError, SQLInjectionError)):
            logger.warning(f"Security incident: {json.dumps(log_entry)}")
        elif isinstance(error, RateLimitError):
            logger.info(f"Rate limit exceeded: {json.dumps(log_entry)}")
        else:
            logger.error(f"Application error: {json.dumps(log_entry)}")
    
    @classmethod
    def handle_exception(cls, error: Exception, request: Optional[Request] = None) -> JSONResponse:
        """Handle exception and return secure response"""
        
        # Log the error
        cls.log_security_event(error, request)
        
        # Create secure response
        response_data = cls.create_secure_response(error)
        
        # Return JSON response
        return JSONResponse(
            status_code=response_data["error"]["status_code"],
            content=response_data
        )
    
    @classmethod
    def validate_and_handle(cls, func):
        """Decorator for automatic error handling"""
        from functools import wraps
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                # Get request from arguments
                request = None
                for arg in args:
                    if hasattr(arg, 'method'):  # FastAPI Request
                        request = arg
                        break
                
                return cls.handle_exception(e, request)
        
        return wrapper


# Global error handler
error_handler = SecurityErrorHandler()


# FastAPI exception handlers
def register_exception_handlers(app):
    """Register exception handlers with FastAPI app"""
    
    @app.exception_handler(SecurityError)
    async def security_error_handler(request: Request, exc: SecurityError):
        return error_handler.handle_exception(exc, request)
    
    @app.exception_handler(ValidationError)
    async def validation_error_handler(request: Request, exc: ValidationError):
        return error_handler.handle_exception(exc, request)
    
    @app.exception_handler(PathTraversalError)
    async def path_traversal_handler(request: Request, exc: PathTraversalError):
        return error_handler.handle_exception(exc, request)
    
    @app.exception_handler(SQLInjectionError)
    async def sql_injection_handler(request: Request, exc: SQLInjectionError):
        return error_handler.handle_exception(exc, request)
    
    @app.exception_handler(RateLimitError)
    async def rate_limit_handler(request: Request, exc: RateLimitError):
        response = error_handler.handle_exception(exc, request)
        response.headers["Retry-After"] = "60"  # Standard HTTP header
        return response
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        # Log unexpected errors
        logger.error(f"Unexpected error: {exc}\n{traceback.format_exc()}")
        
        # Return generic error response
        response = error_handler.create_secure_response(exc, 500)
        return JSONResponse(
            status_code=500,
            content=response
        )


# Convenience functions
def sanitize_error_response(error: Exception, status_code: int = 500) -> Dict[str, Any]:
    """Quick sanitize error response"""
    return SecurityErrorHandler.create_secure_response(error, status_code)


def log_security_event(error: Exception, request: Optional[Request] = None) -> None:
    """Quick log security event"""
    SecurityErrorHandler.log_security_event(error, request)