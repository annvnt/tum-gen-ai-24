import os
import shutil
from pathlib import Path
from typing import Optional, BinaryIO
import tempfile

class LocalStorageClient:
    """Local file storage client for development/testing when GCS is not available."""
    
    def __init__(self, base_path: str = None):
        """Initialize local storage client."""
        if base_path is None:
            base_path = os.getenv("LOCAL_STORAGE_PATH", "./local_storage")
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)
    
    def upload_file(self, file_data: BinaryIO, destination_blob_name: str, content_type: str = None) -> str:
        """Upload a file to local storage."""
        try:
            file_path = self.base_path / destination_blob_name
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'wb') as f:
                f.write(file_data.read())
            
            return str(destination_blob_name)
        except Exception as e:
            raise Exception(f"Failed to upload file to local storage: {str(e)}")
    
    def download_file(self, blob_name: str) -> bytes:
        """Download a file from local storage."""
        try:
            file_path = self.base_path / blob_name
            if not file_path.exists():
                raise FileNotFoundError(f"File {blob_name} not found in local storage")
            
            with open(file_path, 'rb') as f:
                return f.read()
        except Exception as e:
            raise Exception(f"Failed to download file from local storage: {str(e)}")
    
    def delete_file(self, blob_name: str):
        """Delete a file from local storage."""
        try:
            file_path = self.base_path / blob_name
            if file_path.exists():
                file_path.unlink()
        except Exception as e:
            raise Exception(f"Failed to delete file from local storage: {str(e)}")
    
    def file_exists(self, blob_name: str) -> bool:
        """Check if a file exists in local storage."""
        try:
            file_path = self.base_path / blob_name
            return file_path.exists()
        except Exception as e:
            raise Exception(f"Failed to check file existence in local storage: {str(e)}")

# Singleton instance
local_storage_client = None

def get_local_storage_client():
    """Get the singleton local storage client instance."""
    global local_storage_client
    if local_storage_client is None:
        local_storage_client = LocalStorageClient()
    return local_storage_client
