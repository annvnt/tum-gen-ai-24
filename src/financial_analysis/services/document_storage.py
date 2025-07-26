"""
GCSMetadataManager - Document Storage for GCS+Qdrant Architecture
Handles full document storage in Google Cloud Storage while Qdrant handles vectors
"""

import json
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path

from ..storage.gcs_client import GCSClient


class GCSMetadataManager:
    """Manages document storage in Google Cloud Storage"""
    
    def __init__(self, 
                 bucket_name: str = None,
                 credentials_path: str = "gcs-credentials.json"):
        """
        Initialize GCS metadata manager
        
        Args:
            bucket_name: GCS bucket name (uses env var if None)
            credentials_path: Path to GCS credentials file
        """
        self.gcs_client = GCSClient(credentials_path=credentials_path, bucket_name=bucket_name)
        self.bucket_name = self.gcs_client.bucket_name
        
        # Define GCS paths
        self.documents_prefix = "documents/"
        self.metadata_prefix = "metadata/"
    
    def store_document(self, 
                      document_data: Dict[str, Any], 
                      doc_id: Optional[str] = None,
                      metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Store a document in GCS
        
        Args:
            document_data: The document content to store
            doc_id: Optional document ID (auto-generated if None)
            metadata: Optional additional metadata
            
        Returns:
            Document ID used
        """
        if doc_id is None:
            doc_id = str(uuid.uuid4())
        
        # Prepare full document with metadata
        full_document = {
            **document_data,
            "_metadata": {
                "doc_id": doc_id,
                "stored_at": datetime.utcnow().isoformat(),
                "bucket": self.bucket_name,
                **(metadata or {})
            }
        }
        
        # Store document
        try:
            doc_blob_name = f"{self.documents_prefix}{doc_id}.json"
            doc_content = json.dumps(full_document, indent=2, ensure_ascii=False)
            
            doc_url = self.gcs_client.upload_file_from_path(
                file_path=None,  # We'll use file content instead
                destination_blob_name=doc_blob_name,
                content_type="application/json"
            )
            
            # Upload file content directly
            from io import BytesIO
            file_data = BytesIO(doc_content.encode('utf-8'))
            doc_url = self.gcs_client.upload_file(
                file_data=file_data,
                destination_blob_name=doc_blob_name,
                content_type="application/json"
            )
            
            # Store separate metadata file
            if metadata:
                metadata_blob_name = f"{self.metadata_prefix}{doc_id}_meta.json"
                metadata_content = json.dumps({
                    "doc_id": doc_id,
                    "document_url": doc_url,
                    "metadata": metadata,
                    "stored_at": datetime.utcnow().isoformat()
                }, indent=2)
                
                metadata_data = BytesIO(metadata_content.encode('utf-8'))
                self.gcs_client.upload_file(
                    file_data=metadata_data,
                    destination_blob_name=metadata_blob_name,
                    content_type="application/json"
                )
            
            print(f"✅ Document stored in GCS: {doc_url}")
            return doc_id
            
        except Exception as e:
            print(f"❌ Error storing document in GCS: {e}")
            raise
    
    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a document from GCS
        
        Args:
            doc_id: Document ID to retrieve
            
        Returns:
            Document data or None if not found
        """
        try:
            doc_blob_name = f"{self.documents_prefix}{doc_id}.json"
            
            # Download document content
            file_content = self.gcs_client.download_file(doc_blob_name)
            document_data = json.loads(file_content.decode('utf-8'))
            
            return document_data
            
        except Exception as e:
            if "404" in str(e):
                print(f"⚠️ Document {doc_id} not found in GCS")
                return None
            else:
                print(f"❌ Error retrieving document from GCS: {e}")
                raise
    
    def get_document_metadata(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve document metadata from GCS
        
        Args:
            doc_id: Document ID to retrieve metadata for
            
        Returns:
            Metadata dictionary or None if not found
        """
        try:
            metadata_blob_name = f"{self.metadata_prefix}{doc_id}_meta.json"
            
            file_content = self.gcs_client.download_file(metadata_blob_name)
            metadata = json.loads(file_content.decode('utf-8'))
            
            return metadata
            
        except Exception as e:
            if "404" in str(e):
                print(f"⚠️ Metadata for {doc_id} not found in GCS")
                return None
            else:
                print(f"❌ Error retrieving metadata from GCS: {e}")
                raise
    
    def list_documents(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        List all documents in GCS
        
        Args:
            limit: Maximum number of documents to return
            
        Returns:
            List of document metadata
        """
        try:
            # List all documents in the documents prefix
            blobs = self.gcs_client.bucket.list_blobs(prefix=self.documents_prefix)
            
            documents = []
            for blob in blobs:
                if blob.name.endswith('.json'):
                    # Extract doc_id from filename
                    filename = Path(blob.name).stem
                    if filename != "":
                        doc_id = filename
                        doc_data = self.get_document_metadata(doc_id)
                        if doc_data:
                            documents.append(doc_data)
                        
                        if limit and len(documents) >= limit:
                            break
            
            return documents
            
        except Exception as e:
            print(f"❌ Error listing documents: {e}")
            raise
    
    def delete_document(self, doc_id: str) -> bool:
        """
        Delete a document and its metadata from GCS
        
        Args:
            doc_id: Document ID to delete
            
        Returns:
            True if deleted successfully, False if not found
        """
        try:
            doc_blob_name = f"{self.documents_prefix}{doc_id}.json"
            metadata_blob_name = f"{self.metadata_prefix}{doc_id}_meta.json"
            
            # Delete document
            self.gcs_client.delete_file(doc_blob_name)
            
            # Delete metadata if it exists
            try:
                self.gcs_client.delete_file(metadata_blob_name)
            except:
                pass  # Metadata might not exist
            
            print(f"✅ Document {doc_id} deleted from GCS")
            return True
            
        except Exception as e:
            if "404" in str(e):
                print(f"⚠️ Document {doc_id} not found in GCS")
                return False
            else:
                print(f"❌ Error deleting document from GCS: {e}")
                raise
    
    def document_exists(self, doc_id: str) -> bool:
        """
        Check if a document exists in GCS
        
        Args:
            doc_id: Document ID to check
            
        Returns:
            True if document exists, False otherwise
        """
        try:
            doc_blob_name = f"{self.documents_prefix}{doc_id}.json"
            from google.cloud import storage
            
            blob = self.gcs_client.bucket.blob(doc_blob_name)
            return blob.exists()
            
        except Exception as e:
            print(f"❌ Error checking document existence: {e}")
            raise