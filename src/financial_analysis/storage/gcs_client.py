import os
from google.cloud import storage
from google.oauth2 import service_account
from typing import Optional, BinaryIO
import io
from pathlib import Path

class GCSClient:
    def __init__(self, credentials_path: str = None, bucket_name: str = None):
        # Always use Docker path since we're container-only
        if credentials_path is None:
            credentials_path = "/app/gcs-credentials.json"
        self.credentials_path = credentials_path
        self.bucket_name = bucket_name or os.getenv("GCS_BUCKET_NAME", "tum-gen-ai-storage")
        self.client = None
        self.bucket = None
        self._initialize_client()
    
    def _initialize_client(self):
        try:
            credentials = service_account.Credentials.from_service_account_file(
                self.credentials_path
            )
            self.client = storage.Client(credentials=credentials)
            self.bucket = self.client.bucket(self.bucket_name)
        except Exception as e:
            raise Exception(f"Failed to initialize GCS client: {str(e)}")
    
    def upload_file(self, file_data: BinaryIO, destination_blob_name: str, content_type: str = None) -> str:
        """Upload a file to GCS and return the blob name."""
        try:
            # Normalize blob name to prevent duplication
            from .gcs_path_utils import GCSPathManager
            clean_blob_name = GCSPathManager.normalize_blob_name(destination_blob_name)
            
            blob = self.bucket.blob(clean_blob_name)
            blob.upload_from_file(file_data, content_type=content_type)
            return clean_blob_name
        except Exception as e:
            raise Exception(f"Failed to upload file to GCS: {str(e)}")
    
    def upload_file_from_path(self, file_path: str, destination_blob_name: str, content_type: str = None) -> str:
        """Upload a file from local path to GCS and return the blob name."""
        try:
            # Normalize blob name to prevent duplication
            from .gcs_path_utils import GCSPathManager
            clean_blob_name = GCSPathManager.normalize_blob_name(destination_blob_name)
            
            blob = self.bucket.blob(clean_blob_name)
            blob.upload_from_filename(file_path, content_type=content_type)
            return clean_blob_name
        except Exception as e:
            raise Exception(f"Failed to upload file from path to GCS: {str(e)}")
    
    def download_file(self, blob_name: str) -> bytes:
        """Download a file from GCS and return its contents as bytes."""
        try:
            # Normalize blob name to prevent duplication
            from .gcs_path_utils import GCSPathManager
            clean_blob_name = GCSPathManager.normalize_blob_name(blob_name)
            
            blob = self.bucket.blob(clean_blob_name)
            return blob.download_as_bytes()
        except Exception as e:
            raise Exception(f"Failed to download file from GCS: {str(e)}")
    
    def download_file_to_path(self, blob_name: str, destination_path: str):
        """Download a file from GCS to a local path."""
        try:
            # Normalize blob name to prevent duplication
            from .gcs_path_utils import GCSPathManager
            clean_blob_name = GCSPathManager.normalize_blob_name(blob_name)
            
            blob = self.bucket.blob(clean_blob_name)
            blob.download_to_filename(destination_path)
        except Exception as e:
            raise Exception(f"Failed to download file from GCS to path: {str(e)}")
    
    def delete_file(self, blob_name: str):
        """Delete a file from GCS."""
        try:
            # Normalize blob name to prevent duplication
            from .gcs_path_utils import GCSPathManager
            clean_blob_name = GCSPathManager.normalize_blob_name(blob_name)
            
            blob = self.bucket.blob(clean_blob_name)
            blob.delete()
        except Exception as e:
            raise Exception(f"Failed to delete file from GCS: {str(e)}")
    
    def list_files(self, prefix: str = None) -> list:
        """List files in the bucket, optionally filtered by prefix."""
        try:
            # Normalize prefix if provided
            from .gcs_path_utils import GCSPathManager
            if prefix:
                prefix = GCSPathManager.normalize_blob_name(prefix)
                blobs = self.bucket.list_blobs(prefix=prefix)
            else:
                blobs = self.bucket.list_blobs()
            return [blob.name for blob in blobs]
        except Exception as e:
            raise Exception(f"Failed to list files in GCS: {str(e)}")
    
    def file_exists(self, blob_name: str) -> bool:
        """Check if a file exists in GCS."""
        try:
            # Normalize blob name to prevent duplication
            from .gcs_path_utils import GCSPathManager
            clean_blob_name = GCSPathManager.normalize_blob_name(blob_name)
            
            blob = self.bucket.blob(clean_blob_name)
            return blob.exists()
        except Exception as e:
            raise Exception(f"Failed to check file existence in GCS: {str(e)}")
    
    def get_file_url(self, blob_name: str) -> str:
        """Get the blob name for a file in GCS."""
        try:
            # Normalize blob name to prevent duplication
            from .gcs_path_utils import GCSPathManager
            clean_blob_name = GCSPathManager.normalize_blob_name(blob_name)
            
            blob = self.bucket.blob(clean_blob_name)
            if not blob.exists():
                raise Exception(f"File {clean_blob_name} does not exist")
            return clean_blob_name
        except Exception as e:
            raise Exception(f"Failed to get file URL from GCS: {str(e)}")
    
    def get_file_size(self, blob_name: str) -> int:
        """Get the size of a file in GCS."""
        try:
            # Normalize blob name to prevent duplication
            from .gcs_path_utils import GCSPathManager
            clean_blob_name = GCSPathManager.normalize_blob_name(blob_name)
            
            blob = self.bucket.blob(clean_blob_name)
            blob.reload()
            return blob.size
        except Exception as e:
            raise Exception(f"Failed to get file size from GCS: {str(e)}")

# Singleton instance
gcs_client = None

def get_gcs_client() -> GCSClient:
    """Get the singleton GCS client instance."""
    global gcs_client
    if gcs_client is None:
        gcs_client = GCSClient()
    return gcs_client