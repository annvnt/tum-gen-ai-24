"""
Input validation utilities for financial platform
Provides comprehensive input validation and sanitization
"""

import re
import uuid
from typing import Any, Dict, List, Optional, Union
from decimal import Decimal, InvalidOperation
from datetime import datetime
import logging
import mimetypes
from pathlib import Path

logger = logging.getLogger(__name__)


class InputValidator:
    """Comprehensive input validation and sanitization class"""
    
    # Allowed file extensions for uploads
    ALLOWED_FILE_EXTENSIONS = {
        'excel': ['.xlsx', '.xls', '.csv'],
        'pdf': ['.pdf'],
        'json': ['.json'],
        'text': ['.txt']
    }
    
    # Maximum file size (100MB)
    MAX_FILE_SIZE = 100 * 1024 * 1024
    
    # UUID regex pattern
    UUID_PATTERN = re.compile(
        r'^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$',
        re.IGNORECASE
    )
    
    # SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r'(?i)(union|select|insert|update|delete|drop|create|alter|exec|execute)',
        r'(?i)(script|javascript|vbscript|onload|onerror|onclick)',
        r'(?i)(<|>|&lt;|&gt;|%3C|%3E)',
        r'(?i)(\.\./|\.\.\\|%2e%2e%2f|%2e%2e%5c)',
        r'(?i)(/etc/passwd|/windows/system32|/proc/)',
    ]
    
    @classmethod
    def validate_uuid(cls, uuid_str: str) -> bool:
        """Validate UUID format"""
        try:
            uuid.UUID(uuid_str)
            return bool(cls.UUID_PATTERN.match(uuid_str))
        except (ValueError, TypeError):
            return False
    
    @classmethod
    def validate_file_extension(cls, filename: str, allowed_types: List[str] = None) -> bool:
        """Validate file extension against allowed types"""
        if not filename:
            return False
            
        file_extension = Path(filename).suffix.lower()
        
        if allowed_types is None:
            # Allow all configured types
            allowed_extensions = []
            for extensions in cls.ALLOWED_FILE_EXTENSIONS.values():
                allowed_extensions.extend(extensions)
        else:
            allowed_extensions = []
            for file_type in allowed_types:
                if file_type in cls.ALLOWED_FILE_EXTENSIONS:
                    allowed_extensions.extend(cls.ALLOWED_FILE_EXTENSIONS[file_type])
        
        return file_extension in allowed_extensions
    
    @classmethod
    def validate_file_size(cls, file_size: int) -> bool:
        """Validate file size"""
        return isinstance(file_size, int) and 0 < file_size <= cls.MAX_FILE_SIZE
    
    @classmethod
    def validate_filename(cls, filename: str) -> bool:
        """Validate filename for malicious patterns"""
        if not filename or not isinstance(filename, str):
            return False
            
        # Check for path traversal
        if '..' in filename or '/' in filename or '\\' in filename:
            return False
            
        # Check for null bytes
        if '\x00' in filename:
            return False
            
        # Check for SQL injection patterns
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, filename):
                return False
                
        return True
    
    @classmethod
    def sanitize_string(cls, input_str: str, max_length: int = 255) -> str:
        """Sanitize string input"""
        if not isinstance(input_str, str):
            return ""
            
        # Remove null bytes
        sanitized = input_str.replace('\x00', '')
        
        # Remove control characters
        sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', sanitized)
        
        # Limit length
        sanitized = sanitized[:max_length]
        
        # Strip whitespace
        sanitized = sanitized.strip()
        
        return sanitized
    
    @classmethod
    def sanitize_filename(cls, filename: str) -> str:
        """Sanitize filename"""
        if not isinstance(filename, str):
            return ""
            
        # Remove path separators
        sanitized = re.sub(r'[<>:\\|?*]', '_', filename)
        
        # Remove control characters
        sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', sanitized)
        
        # Limit length
        sanitized = sanitized[:100]
        
        return sanitized.strip()
    
    @classmethod
    def validate_monetary_amount(cls, amount: Any) -> bool:
        """Validate monetary amount"""
        try:
            if isinstance(amount, str):
                amount = amount.replace(',', '').strip()
            
            decimal_amount = Decimal(str(amount))
            return decimal_amount >= 0
        except (InvalidOperation, ValueError, TypeError):
            return False
    
    @classmethod
    def validate_currency_code(cls, currency_code: str) -> bool:
        """Validate ISO 4217 currency code"""
        valid_codes = {
            'USD', 'EUR', 'GBP', 'JPY', 'AUD', 'CAD', 'CHF', 'CNY', 'SEK', 'NZD',
            'MXN', 'SGD', 'HKD', 'NOK', 'KRW', 'TRY', 'RUB', 'INR', 'BRL', 'ZAR'
        }
        return currency_code.upper() in valid_codes
    
    @classmethod
    def validate_email(cls, email: str) -> bool:
        """Validate email format"""
        if not email or not isinstance(email, str):
            return False
            
        pattern = re.compile(
            r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        )
        return bool(pattern.match(email.strip()))
    
    @classmethod
    def validate_date_string(cls, date_str: str) -> bool:
        """Validate date string format"""
        try:
            datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return True
        except (ValueError, TypeError):
            return False
    
    @classmethod
    def validate_dict_structure(cls, data: Dict[str, Any], required_fields: List[str], 
                              field_types: Dict[str, type] = None) -> bool:
        """Validate dictionary structure and types"""
        if not isinstance(data, dict):
            return False
            
        # Check required fields
        for field in required_fields:
            if field not in data:
                return False
                
        # Check field types
        if field_types:
            for field, expected_type in field_types.items():
                if field in data and not isinstance(data[field], expected_type):
                    return False
                    
        return True
    
    @classmethod
    def detect_sql_injection(cls, input_str: str) -> bool:
        """Detect potential SQL injection patterns"""
        if not isinstance(input_str, str):
            return False
            
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, input_str, re.IGNORECASE):
                return True
                
        return False
    
    @classmethod
    def validate_mime_type(cls, file_path: str) -> bool:
        """Validate MIME type of file"""
        try:
            mime_type, _ = mimetypes.guess_type(file_path)
            allowed_mimes = {
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',  # .xlsx
                'application/vnd.ms-excel',  # .xls
                'text/csv',
                'application/pdf',
                'application/json',
                'text/plain'
            }
            return mime_type in allowed_mimes
        except Exception:
            return False
    
    @classmethod
    def sanitize_dict_values(cls, data: Dict[str, Any], max_depth: int = 3) -> Dict[str, Any]:
        """Recursively sanitize dictionary values"""
        if max_depth <= 0:
            return {}
            
        sanitized = {}
        for key, value in data.items():
            safe_key = cls.sanitize_string(str(key), 50)
            
            if isinstance(value, str):
                sanitized[safe_key] = cls.sanitize_string(value)
            elif isinstance(value, dict):
                sanitized[safe_key] = cls.sanitize_dict_values(value, max_depth - 1)
            elif isinstance(value, list):
                sanitized[safe_key] = [
                    cls.sanitize_string(item) if isinstance(item, str) else item
                    for item in value
                ]
            else:
                sanitized[safe_key] = value
                
        return sanitized