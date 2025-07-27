"""
Vector Processing Service - Orchestrates complete workflow from Excel upload to vector storage
Coordinates Excel analysis, Jina embeddings, GCS metadata storage, and Qdrant vector storage
"""

import asyncio
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
import pandas as pd
import logging

from .embedding_service import JinaEmbeddingService, EmbeddingResult
from .vector_database import QdrantManager
from ..storage.gcs_client import GCSClient
from ..storage.database_manager import DatabaseManager

logger = logging.getLogger(__name__)

class VectorProcessingService:
    """Orchestrates the complete vector processing workflow"""
    
    def __init__(self, 
                 jina_api_key: str = None,
                 qdrant_host: str = "localhost", 
                 qdrant_port: int = 6333,
                 collection_name: str = "financial_documents"):
        """
        Initialize the vector processing service
        
        Args:
            jina_api_key: Jina API key for embeddings
            qdrant_host: Qdrant server host
            qdrant_port: Qdrant server port
            collection_name: Name for Qdrant collection
        """
        self.embedding_service = JinaEmbeddingService(api_key=jina_api_key)
        self.qdrant_manager = QdrantManager(
            host=qdrant_host,
            port=qdrant_port,
            collection_name=collection_name,
            vector_size=1024  # Jina v3 embedding size
        )
        self.gcs_client = GCSClient()
        self.db_manager = DatabaseManager()
        
    async def process_excel_file(self, 
                               gcs_url: str, 
                               file_id: str, 
                               filename: str,
                               metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Complete processing workflow for Excel files
        
        Args:
            gcs_url: GCS URL of the uploaded file
            file_id: Unique file identifier
            filename: Original filename
            metadata: Additional metadata for processing
            
        Returns:
            Processing results including vector IDs and metadata
        """
        try:
            logger.info(f"Starting vector processing for file: {filename} (ID: {file_id})")
            
            # Step 1: Download and load Excel file from GCS
            df = await self._load_excel_from_gcs(gcs_url)
            logger.info(f"Loaded Excel file with {len(df)} rows and {len(df.columns)} columns")
            
            # Step 2: Generate embeddings for Excel content
            embeddings = await self._generate_excel_embeddings(df, filename, file_id)
            logger.info(f"Generated {len(embeddings)} embeddings")
            
            # Step 3: Store vectors in Qdrant
            vector_ids = await self._store_vectors_in_qdrant(embeddings, file_id)
            logger.info(f"Stored {len(vector_ids)} vectors in Qdrant")
            
            # Step 4: Store metadata in database
            metadata_record = await self._store_vector_metadata(file_id, filename, metadata, vector_ids)
            logger.info(f"Stored metadata for file processing")
            
            # Step 5: Update document status
            await self._update_document_status(file_id, "processed", metadata_record)
            
            return {
                "status": "success",
                "file_id": file_id,
                "filename": filename,
                "vectors_stored": len(vector_ids),
                "vector_ids": vector_ids,
                "processing_timestamp": datetime.utcnow().isoformat(),
                "metadata_record": metadata_record
            }
            
        except Exception as e:
            logger.error(f"Error processing Excel file {filename}: {str(e)}")
            await self._update_document_status(file_id, "failed", {"error": str(e)})
            raise
    
    async def _load_excel_from_gcs(self, gcs_url: str) -> pd.DataFrame:
        """Download and load Excel file from GCS"""
        try:
            # Import path utilities for consistent URL handling
            from ..storage.gcs_path_utils import GCSPathManager
            
            # Extract clean blob name using centralized path utilities
            blob_name = GCSPathManager.extract_blob_name_from_url(gcs_url)
            
            # Download file content
            file_content = self.gcs_client.download_file(blob_name)
            
            # Load into pandas DataFrame
            df = pd.read_excel(file_content)
            
            # Basic data cleaning
            df = df.dropna(how='all')  # Remove empty rows
            df = df.fillna('')  # Fill NaN values with empty strings
            
            return df
            
        except Exception as e:
            logger.error(f"Error loading Excel from GCS: {str(e)}")
            raise Exception(f"Failed to load Excel file: {str(e)}")
    
    async def _generate_excel_embeddings(self, df: pd.DataFrame, filename: str, file_id: str) -> List[EmbeddingResult]:
        """Generate embeddings for Excel content"""
        try:
            # Generate embeddings for each row
            row_embeddings = self.embedding_service.generate_excel_embeddings(df, filename, file_id)
            
            # Generate summary embedding for the entire file
            summary_embedding = self.embedding_service.generate_file_summary_embedding(df, filename, file_id)
            
            # Combine all embeddings
            all_embeddings = row_embeddings + [summary_embedding]
            
            return all_embeddings
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            raise Exception(f"Failed to generate embeddings: {str(e)}")
    
    async def _store_vectors_in_qdrant(self, embeddings: List[EmbeddingResult], file_id: str) -> List[str]:
        """Store vectors in Qdrant database"""
        try:
            vectors = [emb.embedding for emb in embeddings]
            payloads = [emb.metadata for emb in embeddings]
            
            # Generate vector IDs
            vector_ids = [str(uuid.uuid4()) for _ in embeddings]
            
            # Store in Qdrant
            stored_ids = self.qdrant_manager.add_vectors(
                vectors=vectors,
                payloads=payloads,
                doc_ids=vector_ids
            )
            
            return stored_ids
            
        except Exception as e:
            logger.error(f"Error storing vectors in Qdrant: {str(e)}")
            raise Exception(f"Failed to store vectors: {str(e)}")
    
    async def _store_vector_metadata(self, 
                                   file_id: str, 
                                   filename: str, 
                                   metadata: Optional[Dict], 
                                   vector_ids: List[str]) -> Dict[str, Any]:
        """Store vector processing metadata in database"""
        try:
            metadata_record = {
                "file_id": file_id,
                "filename": filename,
                "processing_date": datetime.utcnow().isoformat(),
                "vector_count": len(vector_ids),
                "vector_ids": vector_ids,
                "processing_method": "jina_embeddings_v3",
                "vector_size": 1024,
                "collection_name": self.qdrant_manager.collection_name,
                "additional_metadata": metadata or {}
            }
            
            # Store metadata in database
            self.db_manager.store_vector_processing_metadata(file_id, metadata_record)
            
            return metadata_record
            
        except Exception as e:
            logger.error(f"Error storing vector metadata: {str(e)}")
            raise Exception(f"Failed to store vector metadata: {str(e)}")
    
    async def _update_document_status(self, file_id: str, status: str, metadata: Dict[str, Any]):
        """Update document processing status"""
        try:
            self.db_manager.update_document_status(file_id, status, metadata)
        except Exception as e:
            logger.error(f"Error updating document status: {str(e)}")
    
    async def search_similar_documents(self, 
                                     query_text: str, 
                                     limit: int = 10,
                                     score_threshold: float = 0.7) -> List[Dict[str, Any]]:
        """
        Search for similar documents using vector similarity
        
        Args:
            query_text: Text to search for
            limit: Maximum number of results
            score_threshold: Minimum similarity score
            
        Returns:
            List of similar documents with scores
        """
        try:
            # Generate query embedding
            query_embedding = self.embedding_service.generate_single_embedding(
                query_text, 
                task="retrieval.query"
            )
            
            # Search in Qdrant
            search_results = self.qdrant_manager.search_vectors(
                query_vector=query_embedding.embedding,
                limit=limit,
                score_threshold=score_threshold
            )
            
            # Enrich results with file information
            enriched_results = []
            for result in search_results:
                file_id = result["payload"].get("file_id")
                if file_id:
                    file_info = self.db_manager.get_uploaded_file(file_id)
                    if file_info:
                        result["file_info"] = file_info
                enriched_results.append(result)
            
            return enriched_results
            
        except Exception as e:
            logger.error(f"Error searching similar documents: {str(e)}")
            raise Exception(f"Failed to search documents: {str(e)}")
    
    async def get_document_vectors(self, file_id: str) -> List[Dict[str, Any]]:
        """Get all vectors for a specific document"""
        try:
            # Search for vectors with specific file_id
            vectors = self.qdrant_manager.get_vectors_by_file_id(file_id)
            return vectors
            
        except Exception as e:
            logger.error(f"Error retrieving document vectors: {str(e)}")
            raise Exception(f"Failed to retrieve document vectors: {str(e)}")
    
    async def delete_document_vectors(self, file_id: str) -> int:
        """Delete all vectors for a specific document"""
        try:
            # Get vector metadata to find vector IDs
            metadata = self.db_manager.get_vector_metadata(file_id)
            if metadata and "vector_ids" in metadata:
                vector_ids = metadata["vector_ids"]
                deleted_count = self.qdrant_manager.delete_vectors(vector_ids)
                
                # Update database
                self.db_manager.update_document_status(file_id, "deleted", {"vectors_deleted": deleted_count})
                
                return deleted_count
            return 0
            
        except Exception as e:
            logger.error(f"Error deleting document vectors: {str(e)}")
            raise Exception(f"Failed to delete document vectors: {str(e)}")
    
    async def get_processing_stats(self) -> Dict[str, Any]:
        """Get vector processing statistics"""
        try:
            # Get collection info from Qdrant
            collection_info = self.qdrant_manager.get_collection_info()
            
            # Get processing stats from database
            stats = self.db_manager.get_vector_processing_stats()
            
            return {
                "collection_info": collection_info,
                "processing_stats": stats,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting processing stats: {str(e)}")
            raise Exception(f"Failed to get processing statistics: {str(e)}")

# Global service instance
vector_processing_service = None

def get_vector_processing_service() -> VectorProcessingService:
    """Get the singleton vector processing service instance"""
    global vector_processing_service
    if vector_processing_service is None:
        vector_processing_service = VectorProcessingService()
    return vector_processing_service