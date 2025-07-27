"""
Security middleware for FastAPI
Provides request validation, sanitization, and security headers
"""

import uuid
from typing import Dict, Any, Optional
from fastapi import Request, Response
from fastapi.responses import JSONResponse
import logging
from datetime import datetime

from .input_validator import InputValidator
from .rate_limiter import rate_limiter
from .error_handler import error_handler, SecurityError

logger = logging.getLogger(__name__)


class SecurityMiddleware:
    """Security middleware for request validation and protection"""
    
    def __init__(self):
        self.request_id_header = "X-Request-ID"
        self.security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
            "Referrer-Policy": "strict-origin-when-cross-origin",
        }
    
    async def __call__(self, request: Request, call_next):
        """Process request and response"""
        start_time = datetime.utcnow()
        
        # Generate request ID
        request_id = str(uuid.uuid4())
        
        # Add request ID to request state
        request.state.request_id = request_id
        
        try:
            # Validate request
            validation_result = await self.validate_request(request)
            if not validation_result["valid"]:
                return JSONResponse(
                    status_code=400,
                    content={"error": validation_result["error"]}
                )
            
            # Process request
            response = await call_next(request)
            
            # Add security headers
            response = self.add_security_headers(response, request_id)
            
            # Log request
            self.log_request(request, response, start_time)
            
            return response
            
        except Exception as e:
            logger.error(f"Security middleware error: {e}")
            return error_handler.handle_exception(e, request)
    
    async def validate_request(self, request: Request) -> Dict[str, Any]:
        """Validate incoming request"""
        validation_result = {"valid": True, "error": None}
        
        try:
            # Validate request path
            path = str(request.url.path)
            if not InputValidator.validate_path_traversal(path):
                validation_result.update({
                    "valid": False,
                    "error": "Invalid request path"
                })
                return validation_result
            
            # Validate query parameters
            for key, value in request.query_params.items():
                if not self.validate_query_param(key, value):
                    validation_result.update({
                        "valid": False,
                        "error": f"Invalid query parameter: {key}"
                    })
                    return validation_result
            
            # Validate headers
            for key, value in request.headers.items():
                if not self.validate_header(key, value):
                    validation_result.update({
                        "valid": False,
                        "error": f"Invalid header: {key}"
                    })
                    return validation_result
            
            # Check content length for large requests
            content_length = request.headers.get("content-length")
            if content_length:
                try:
                    length = int(content_length)
                    if length > 100 * 1024 * 1024:  # 100MB limit
                        validation_result.update({
                            "valid": False,
                            "error": "Request too large"
                        })
                        return validation_result
                except ValueError:
                    validation_result.update({
                        "valid": False,
                        "error": "Invalid content length"
                    })
                    return validation_result
            
        except Exception as e:
            logger.error(f"Request validation error: {e}")
            validation_result.update({
                "valid": False,
                "error": "Request validation failed"
            })
        
        return validation_result
    
    def validate_query_param(self, key: str, value: str) -> bool:
        """Validate query parameter"""
        if not key or not isinstance(key, str):
            return False
        
        # Sanitize key and value
        key = InputValidator.sanitize_string(key, 100)
        value = InputValidator.sanitize_string(str(value), 1000)
        
        # Check for SQL injection
        if InputValidator.detect_sql_injection(key) or InputValidator.detect_sql_injection(value):
            return False
        
        return True
    
    def validate_header(self, key: str, value: str) -> bool:
        """Validate HTTP header"""
        if not key or not isinstance(key, str):
            return False
        
        # Sanitize key and value
        key = InputValidator.sanitize_string(key, 100)
        value = InputValidator.sanitize_string(str(value), 1000)
        
        # Check for injection patterns
        if "\r\n" in key or "\r\n" in value:
            return False
        
        return True
    
    def add_security_headers(self, response: Response, request_id: str) -> Response:
        """Add security headers to response"""
        
        # Add request ID
        response.headers[self.request_id_header] = request_id
        
        # Add security headers
        for header, value in self.security_headers.items():
            response.headers[header] = value
        
        return response
    
    def log_request(self, request: Request, response: Response, start_time: datetime):
        """Log request details"""
        duration = (datetime.utcnow() - start_time).total_seconds()
        
        log_data = {
            "request_id": request.state.request_id,
            "method": request.method,
            "url": str(request.url),
            "status_code": response.status_code,
            "duration": duration,
            "client_ip": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent", "unknown")
        }
        
        # Log at appropriate level
        if response.status_code >= 400:
            logger.warning(f"Request completed with error: {log_data}")
        else:
            logger.info(f"Request completed: {log_data}")


class CORSMiddleware:
    """Enhanced CORS middleware"""
    
    def __init__(self, allowed_origins: list = None):
        self.allowed_origins = allowed_origins or [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "https://localhost:3000",
            "https://127.0.0.1:3000",
        ]
    
    async def __call__(self, request: Request, call_next):
        """Process CORS headers"""
        
        # Get origin
        origin = request.headers.get("origin")
        
        # Process request
        response = await call_next(request)
        
        # Add CORS headers
        if origin and origin in self.allowed_origins:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "*"
        
        return response


class RequestLoggingMiddleware:
    """Request logging middleware"""
    
    async def __call__(self, request: Request, call_next):
        """Log all requests"""
        start_time = datetime.utcnow()
        
        # Get request ID
        request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
        
        # Log request
        logger.info(f"[{request_id}] {request.method} {request.url} - Started")
        
        try:
            response = await call_next(request)
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            logger.info(f"[{request_id}] {request.method} {request.url} - {response.status_code} - {duration:.2f}s")
            
            return response
            
        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            logger.error(f"[{request_id}] {request.method} {request.url} - ERROR - {duration:.2f}s - {e}")
            raise


# Global middleware instances
security_middleware = SecurityMiddleware()
cors_middleware = CORSMiddleware()
logging_middleware = RequestLoggingMiddleware()