"""
Centralized GCS Path Utilities
Handles consistent path construction and extraction for Google Cloud Storage
"""

import re
from typing import Optional, Tuple
from urllib.parse import urlparse


class GCSPathManager:
    """Centralized manager for GCS path operations"""
    
    # Standard prefixes for different content types
    UPLOAD_PREFIX = "uploads/"
    DOCUMENT_PREFIX = "documents/"
    METADATA_PREFIX = "metadata/"
    REPORT_PREFIX = "reports/"
    
    # GCS URL patterns
    GCS_URL_PATTERN = re.compile(r'https://storage\.googleapis\.com/([^/]+)/(.+)')
    GCS_BUCKET_URL_PATTERN = re.compile(r'https://([^\.]+)\.storage\.googleapis\.com/(.+)')
    
    @staticmethod
    def normalize_blob_name(blob_name: str) -> str:
        """
        Normalize blob name to prevent duplication and ensure consistency
        
        Args:
            blob_name: Raw blob name or path
            
        Returns:
            Normalized blob name without bucket prefix
        """
        if not blob_name:
            return ""
            
        # Remove leading slashes
        blob_name = blob_name.lstrip('/')
        
        # Remove bucket name if present at start
        parts = blob_name.split('/', 1)
        if len(parts) > 1 and parts[0] in ['tum-gen-ai-24-uploads', 'tum-gen-ai-storage']:
            blob_name = parts[1]
            
        return blob_name
    
    @staticmethod
    def extract_blob_name_from_url(url: str) -> str:
        """
        Extract the actual blob name from various GCS URL formats
        
        Args:
            url: GCS URL (can be full URL, gs:// path, or blob name)
            
        Returns:
            Clean blob name without bucket prefix
            
        Examples:
            >>> extract_blob_name_from_url("https://storage.googleapis.com/bucket/uploads/file.xlsx")
            "uploads/file.xlsx"
            >>> extract_blob_name_from_url("gs://bucket/uploads/file.xlsx")
            "uploads/file.xlsx"
            >>> extract_blob_name_from_url("uploads/file.xlsx")
            "uploads/file.xlsx"
        """
        if not url:
            return ""
            
        # Handle gs:// URLs
        if url.startswith('gs://'):
            parts = url[5:].split('/', 1)  # Remove 'gs://' and split
            if len(parts) > 1:
                return parts[1]  # Return path after bucket name
            return ""
            
        # Handle HTTP(S) URLs
        if url.startswith('http'):
            # Try different URL patterns
            
            # Pattern 1: https://storage.googleapis.com/bucket/path
            match = GCSPathManager.GCS_URL_PATTERN.match(url)
            if match:
                return match.group(2)  # Return the path part
                
            # Pattern 2: https://bucket.storage.googleapis.com/path
            match = GCSPathManager.GCS_BUCKET_URL_PATTERN.match(url)
            if match:
                return match.group(2)  # Return the path part
                
            # Pattern 3: Generic URL parsing
            parsed = urlparse(url)
            if parsed.netloc.endswith('storage.googleapis.com'):
                # Remove leading slash from path
                path = parsed.path.lstrip('/')
                # Remove bucket name if it's at the start
                parts = path.split('/', 1)
                if len(parts) > 1:
                    return parts[1]
                return path
                
        # Handle direct blob names or relative paths
        return GCSPathManager.normalize_blob_name(url)
    
    @staticmethod
    def construct_blob_name(prefix: str, filename: str, file_id: str = None) -> str:
        """
        Construct a consistent blob name with proper prefix
        
        Args:
            prefix: Directory prefix (uploads/, documents/, etc.)
            filename: Original filename
            file_id: Optional file ID for uniqueness
            
        Returns:
            Properly formatted blob name
        """
        # Ensure prefix ends with slash
        if not prefix.endswith('/'):
            prefix += '/'
            
        # Clean filename
        clean_filename = filename.replace('/', '_').replace('\\', '_')
        
        # Construct blob name
        if file_id:
            blob_name = f"{prefix}{file_id}_{clean_filename}"
        else:
            blob_name = f"{prefix}{clean_filename}"
            
        return blob_name
    
    @staticmethod
    def get_upload_blob_name(filename: str, file_id: str) -> str:
        """Get standardized upload blob name"""
        return GCSPathManager.construct_blob_name(
            GCSPathManager.UPLOAD_PREFIX, filename, file_id
        )
    
    @staticmethod
    def get_document_blob_name(filename: str, doc_id: str) -> str:
        """Get standardized document blob name"""
        return GCSPathManager.construct_blob_name(
            GCSPathManager.DOCUMENT_PREFIX, filename, doc_id
        )
    
    @staticmethod
    def get_metadata_blob_name(doc_id: str) -> str:
        """Get standardized metadata blob name"""
        return f"{GCSPathManager.METADATA_PREFIX}{doc_id}_meta.json"
    
    @staticmethod
    def is_valid_blob_name(blob_name: str) -> bool:
        """Validate blob name format"""
        if not blob_name:
            return False
            
        # Check for empty or invalid characters
        invalid_chars = ['\\', '..', '//']
        for char in invalid_chars:
            if char in blob_name:
                return False
                
        # Check length limits (GCS limit is 1024)
        if len(blob_name) > 1024:
            return False
            
        return True
    
    @staticmethod
    def get_bucket_and_blob_from_url(url: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract both bucket name and blob name from GCS URL
        
        Returns:
            Tuple of (bucket_name, blob_name)
        """
        if not url:
            return None, None
            
        # Handle gs:// URLs
        if url.startswith('gs://'):
            parts = url[5:].split('/', 1)  # Remove 'gs://'
            if len(parts) >= 2:
                return parts[0], parts[1]
            return parts[0], None
            
        # Handle HTTP(S) URLs
        if url.startswith('http'):
            # Pattern 1: https://storage.googleapis.com/bucket/path
            match = GCSPathManager.GCS_URL_PATTERN.match(url)
            if match:
                return match.group(1), match.group(2)
                
            # Pattern 2: https://bucket.storage.googleapis.com/path
            match = GCSPathManager.GCS_BUCKET_URL_PATTERN.match(url)
            if match:
                return match.group(1), match.group(2)
                
        return None, None
    
    @staticmethod
    def create_gcs_url(bucket_name: str, blob_name: str) -> str:
        """
        Create a proper GCS URL from bucket and blob names
        
        Args:
            bucket_name: GCS bucket name
            blob_name: Blob name/path
            
        Returns:
            Full GCS HTTPS URL
        """
        clean_blob_name = GCSPathManager.normalize_blob_name(blob_name)
        return f"https://storage.googleapis.com/{bucket_name}/{clean_blob_name}"


# Global instance for convenience
path_manager = GCSPathManager()