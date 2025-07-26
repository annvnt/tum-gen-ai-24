"""
VectorService - Unified service for GCS+Qdrant vector database architecture
Coordinates between Qdrant vectors and GCS document storage
"""

import json
import os
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path

from .vector_database import QrantManager
from .document_storage import GCSMetadataManager


class VectorService:
    """Unified service for vector operations with GCS+Qdrant architecture"""
    
    def __init__(self, 
                 qdrant_config: Dict[str, Any] = None,
                 gcs_config: Dict[str, Any] = None):
        """
        Initialize vector service with Qdrant and GCS
        
        Args:
            qdrant_config: Configuration for QdrantManager
            gcs_config: Configuration for GCSMetadataManager
        """
        self.qdrant_manager = QdrantManager(**(qdrant_config or {}))
        self.gcs_manager = GCSMetadataManager(**(gcs_config or {}))
    
    def store_document(self, 
                      document_data: Dict[str, Any],
                      vector_embedding: List[float],
                      doc_id: Optional[str] = None,
                      metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Store a complete document with vector embedding
        
        Args:
            document_data: The document content
            vector_embedding: The vector embedding
            doc_id: Optional document ID
            metadata: Optional additional metadata
            
        Returns:
            Document ID used
        """
        # Store document in GCS
        doc_id = self.gcs_manager.store_document(
            document_data=document_data,
            doc_id=doc_id,
            metadata=metadata
        )
        
        # Prepare payload for Qdrant (minimal metadata)
        qdrant_payload = {
            "title": document_data.get("title", "Untitled"),
            "author": document_data.get("author", "Unknown"),
            "content_preview": document_data.get("content", "")[:100] + "...",
            "doc_length": len(document_data.get("content", ""))
        }
        
        # Store vector in Qdrant
        self.qdrant_manager.add_vectors(
            vectors=[vector_embedding],
            payloads=[qdrant_payload],
            doc_ids=[doc_id]
        )
        
        return doc_id
    
    def search_similar_documents(self, 
                                query_vector: List[float],
                                limit: int = 5,
                                score_threshold: float = 0.0) -> List[Dict[str, Any]]:
        """
        Search for similar documents
        
        Args:
            query_vector: The query vector
            limit: Maximum number of results
            score_threshold: Minimum similarity score
            
        Returns:
            List of documents with similarity scores
        """
        # Search vectors in Qdrant
        qdrant_results = self.qdrant_manager.search_vectors(
            query_vector=query_vector,
            limit=limit,
            score_threshold=score_threshold
        )
        
        # Fetch full documents from GCS
        results = []
        for result in qdrant_results:
            doc_id = result.get("doc_id")
            if doc_id:
                document = self.gcs_manager.get_document(doc_id)
                if document:
                    results.append({
                        "document": document,
                        "score": result.get("score", 0.0),
                        "doc_id": doc_id,
                        "qdrant_payload": result.get("payload", {})
                    })
        
        return results
    
    def get_document_with_vector(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a document along with its vector metadata
        
        Args:
            doc_id: Document ID
            
        Returns:
            Document with vector metadata or None
        """
        document = self.gcs_manager.get_document(doc_id)
        if not document:
            return None
        
        # Get additional metadata
        metadata = self.gcs_manager.get_document_metadata(doc_id)
        
        return {
            "document": document,
            "metadata": metadata,
            "doc_id": doc_id
        }
    
    def delete_document(self, doc_id: str) -> bool:
        """
        Delete a document and its vector
        
        Args:
            doc_id: Document ID to delete
            
        Returns:
            True if deleted successfully
        """
        # Delete from GCS
        gcs_deleted = self.gcs_manager.delete_document(doc_id)
        
        # Delete vectors from Qdrant
        qdrant_deleted = self.qdrant_manager.delete_vectors([doc_id])
        
        return gcs_deleted and qdrant_deleted > 0
    
    def list_all_documents(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        List all documents with their metadata
        
        Args:
            limit: Maximum number of documents to return
            
        Returns:
            List of documents with metadata
        """
        return self.gcs_manager.list_documents(limit=limit)
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector collection"""
        return {
            "qdrant": self.qdrant_manager.get_collection_info(),
            "gcs": {
                "bucket": self.gcs_manager.bucket_name,
                "documents_count": len(self.gcs_manager.list_documents())
            }
        }