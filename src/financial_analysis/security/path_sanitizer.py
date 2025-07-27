"""
Path traversal protection and file path sanitization utilities
"""

import os
import re
from pathlib import Path
from typing import Optional, Union
import logging

logger = logging.getLogger(__name__)


class PathSanitizer:
    """Path traversal protection and sanitization utilities"""
    
    # Blocked path patterns
    BLOCKED_PATTERNS = [
        r'\.\./',  # Parent directory traversal
        r'\.\.\\',  # Windows parent directory traversal
        r'%2e%2e%2f',  # URL encoded parent directory
        r'%2e%2e%5c',  # URL encoded Windows parent directory
        r'/etc/passwd',
        r'/etc/shadow',
        r'/proc/',
        r'/sys/',
        r'/windows/system32',
        r'\\windows\\system32',
        r'\x00',  # Null bytes
        r'[<>\|"\*\?]',  # Invalid filename characters
    ]
    
    # Allowed base directories
    ALLOWED_BASE_DIRS = [
        '/tmp',
        '/var/tmp',
        '/app/data',
        '/app/uploads',
        '/app/reports',
        'C:\\temp',
        'C:\\Users\\Public\\AppData\\Local\\Temp',
    ]
    
    @classmethod
    def sanitize_filename(cls, filename: str) -> str:
        """Sanitize filename to prevent path traversal"""
        if not filename:
            return ""
            
        # Remove null bytes
        filename = filename.replace('\x00', '')
        
        # Remove path separators
        filename = re.sub(r'[\\/]+', '_', filename)
        
        # Remove dangerous characters
        filename = re.sub(r'[<>:"|?*]', '_', filename)
        
        # Remove control characters
        filename = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', filename)
        
        # Ensure filename is not empty
        filename = filename.strip()
        if not filename:
            filename = "unnamed_file"
            
        # Limit length
        filename = filename[:100]
        
        return filename
    
    @classmethod
    def validate_path(cls, path: Union[str, Path]) -> bool:
        """Validate path for malicious patterns"""
        if not path:
            return False
            
        path_str = str(path)
        
        # Check for blocked patterns
        for pattern in cls.BLOCKED_PATTERNS:
            if re.search(pattern, path_str, re.IGNORECASE):
                logger.warning(f"Blocked path pattern detected: {pattern} in {path_str}")
                return False
                
        # Check for null bytes
        if '\x00' in path_str:
            return False
            
        return True
    
    @classmethod
    def resolve_path(cls, base_dir: str, filename: str) -> Optional[Path]:
        """Resolve path safely within base directory"""
        try:
            # Validate base directory
            base_path = Path(base_dir).resolve()
            
            # Sanitize filename
            safe_filename = cls.sanitize_filename(filename)
            if not safe_filename:
                return None
                
            # Construct full path
            full_path = base_path / safe_filename
            resolved_path = full_path.resolve()
            
            # Ensure path stays within base directory
            try:
                resolved_path.relative_to(base_path)
            except ValueError:
                logger.warning(f"Path traversal attempt detected: {resolved_path}")
                return None
                
            return resolved_path
            
        except (OSError, ValueError) as e:
            logger.error(f"Error resolving path: {e}")
            return None
    
    @classmethod
    def get_safe_filepath(cls, base_dir: str, filename: str, create_dirs: bool = True) -> Optional[str]:
        """Get safe file path with validation"""
        resolved_path = cls.resolve_path(base_dir, filename)
        if not resolved_path:
            return None
            
        # Validate the resolved path
        if not cls.validate_path(resolved_path):
            return None
            
        # Create directories if needed
        if create_dirs:
            try:
                resolved_path.parent.mkdir(parents=True, exist_ok=True)
            except OSError:
                return None
                
        return str(resolved_path)
    
    @classmethod
    def is_safe_path(cls, path: str, allowed_base_dirs: list = None) -> bool:
        """Check if path is within allowed directories"""
        if not path:
            return False
            
        try:
            resolved_path = Path(path).resolve()
            
            # Check against allowed base directories
            check_dirs = allowed_base_dirs or cls.ALLOWED_BASE_DIRS
            
            for allowed_dir in check_dirs:
                try:
                    resolved_path.relative_to(Path(allowed_dir).resolve())
                    return True
                except ValueError:
                    continue
                    
            return False
            
        except (OSError, ValueError):
            return False
    
    @classmethod
    def get_temp_filepath(cls, filename: str) -> Optional[str]:
        """Get safe temporary file path"""
        import tempfile
        
        # Get system temp directory
        temp_dir = tempfile.gettempdir()
        
        # Ensure temp directory is in allowed base dirs
        temp_path = Path(temp_dir).resolve()
        allowed_paths = [Path(d).resolve() for d in cls.ALLOWED_BASE_DIRS]
        
        is_allowed = any(
            str(temp_path).startswith(str(allowed_path))
            for allowed_path in allowed_paths
        )
        
        if not is_allowed:
            # Use /tmp as fallback
            temp_dir = '/tmp'
            
        return cls.get_safe_filepath(temp_dir, filename)
    
    @classmethod
    def validate_gcs_path(cls, gcs_path: str) -> bool:
        """Validate Google Cloud Storage path"""
        if not gcs_path or not isinstance(gcs_path, str):
            return False
            
        # GCS path format: bucket/path/to/object
        if gcs_path.startswith('gs://'):
            gcs_path = gcs_path[5:]
            
        # Split into bucket and object
        parts = gcs_path.split('/', 1)
        if len(parts) < 2:
            return False
            
        bucket_name, object_path = parts
        
        # Validate bucket name
        if not re.match(r'^[a-z0-9][a-z0-9\-_]{1,61}[a-z0-9]$', bucket_name):
            return False
            
        # Validate object path
        if not object_path or object_path.endswith('/'):
            return False
            
        # Check for blocked patterns in object path
        if not cls.validate_path(object_path):
            return False
            
        return True
    
    @classmethod
    def sanitize_gcs_object_name(cls, object_name: str) -> str:
        """Sanitize GCS object name"""
        if not object_name:
            return ""
            
        # Remove leading slashes
        object_name = object_name.lstrip('/')
        
        # Replace unsafe characters
        object_name = re.sub(r'[^a-zA-Z0-9\-_./]', '_', object_name)
        
        # Remove consecutive slashes
        object_name = re.sub(r'/+', '/', object_name)
        
        # Ensure no path traversal
        object_name = object_name.replace('..', '_')
        
        return object_name
    
    @classmethod
    def get_safe_report_path(cls, report_id: str, extension: str = '.pdf') -> Optional[str]:
        """Get safe report file path"""
        if not report_id or not cls.validate_uuid(report_id):
            return None
            
        # Sanitize extension
        extension = extension.lstrip('.')
        if extension not in ['pdf', 'xlsx', 'json']:
            extension = 'pdf'
            
        filename = f"financial_report_{report_id}.{extension}"
        return cls.get_temp_filepath(filename)


class PathValidator:
    """Additional path validation utilities"""
    
    @staticmethod
    def is_path_within_directory(path: str, directory: str) -> bool:
        """Check if path is within specified directory"""
        try:
            # Resolve both paths to absolute paths
            abs_path = os.path.abspath(path)
            abs_directory = os.path.abspath(directory)
            
            # Check if the path starts with the directory
            return abs_path.startswith(abs_directory)
            
        except (OSError, ValueError):
            return False
    
    @staticmethod
    def get_safe_directory_path(base_dir: str, sub_dir: str = None) -> Optional[str]:
        """Get safe directory path"""
        try:
            base_path = Path(base_dir).resolve()
            
            if sub_dir:
                # Sanitize subdirectory
                safe_sub_dir = PathSanitizer.sanitize_filename(sub_dir)
                full_path = base_path / safe_sub_dir
            else:
                full_path = base_path
                
            resolved_path = full_path.resolve()
            
            # Ensure it stays within base directory
            try:
                resolved_path.relative_to(base_path)
                return str(resolved_path)
            except ValueError:
                return None
                
        except (OSError, ValueError):
            return None