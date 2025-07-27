import os
from google.cloud import storage
from google.oauth2 import service_account
from typing import Optional, BinaryIO
import io
from pathlib import Path

class GCSClient:
    def __init__(self, credentials_path: str = None, bucket_name: str = None):
        # Allow flexible credentials path
        if credentials_path is None:
            credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "/app/gcs-credentials.json")
        
        self.credentials_path = credentials_path
        self.bucket_name = bucket_name or os.getenv("GCS_BUCKET_NAME", "tum-gen-ai-storage")
        self.client = None
        self.bucket = None
        self.use_local = False
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize GCS client with fallback to local storage."""
        try:
            # Try to initialize GCS client
            if not os.path.exists(self.credentials_path):
                raise FileNotFoundError(f"GCS credentials not found: {self.credentials_path}")
            
            credentials = service_account.Credentials.from_service_account_file(
                self.credentials_path
            )
            self.client = storage.Client(credentials=credentials)
            self.bucket = self.client.bucket(self.bucket_name)
            print(f"✅ GCS client initialized successfully for bucket: {self.bucket_name}")
        except Exception as e:
            print(f"⚠️ GCS initialization failed, using local storage: {str(e)}")
            # Import local storage client
            from .local_storage_client import get_local_storage_client
            self.use_local = True
            self.local_client = get_local_storage_client()
    
    def upload_file(self, file_data: BinaryIO, destination_blob_name: str, content_type: str = None) -> str:
        """Upload a file to GCS or local storage."""
        if self.use_local:
            return self.local_client.upload_file(file_data, destination_blob_name, content_type)
        
        try:
            from .gcs_path_utils import GCSPathManager
            clean_blob_name = GCSPathManager.normalize_blob_name(destination_blob_name)
            
            blob = self.bucket.blob(clean_blob_name)
            blob.upload_from_file(file_data, content_type=content_type)
            return clean_blob_name
        except Exception as e:
            raise Exception(f"Failed to upload file to GCS: {str(e)}")
    
    def download_file(self, blob_name: str) -> bytes:
        """Download a file from GCS or local storage."""
        if self.use_local:
            return self.local_client.download_file(blob_name)
        
        try:
            from .gcs_path_utils import GCSPathManager
            clean_blob_name = GCSPathManager.normalize_blob_name(blob_name)
            
            blob = self.bucket.blob(clean_blob_name)
            return blob.download_as_bytes()
        except Exception as e:
            raise Exception(f"Failed to download file from GCS: {str(e)}")
    
    def delete_file(self, blob_name: str):
        """Delete a file from GCS or local storage."""
        if self.use_local:
            return self.local_client.delete_file(blob_name)
        
        try:
            from .gcs_path_utils import GCSPathManager
            clean_blob_name = GCSPathManager.normalize_blob_name(blob_name)
            
            blob = self.bucket.blob(clean_blob_name)
            blob.delete()
        except Exception as e:
            raise Exception(f"Failed to delete file from GCS: {str(e)}")
    
    def file_exists(self, blob_name: str) -> bool:
        """Check if a file exists in GCS or local storage."""
        if self.use_local:
            return self.local_client.file_exists(blob_name)
        
        try:
            from .gcs_path_utils import GCSPathManager
            clean_blob_name = GCSPathManager.normalize_blob_name(blob_name)
            
            blob = self.bucket.blob(clean_blob_name)
            return blob.exists()
        except Exception as e:
            raise Exception(f"Failed to check file existence in GCS: {str(e)}")

# Singleton instance
gcs_client = None

def get_gcs_client() -> GCSClient:
    """Get the singleton GCS client instance."""
    global gcs_client
    if gcs_client is None:
        gcs_client = GCSClient()
    return gcs_client
