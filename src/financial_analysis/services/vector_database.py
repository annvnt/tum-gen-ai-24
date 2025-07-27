"""
QdrantManager - Vector Database Operations for GCS+Qdrant Architecture
Handles all vector operations with Qdrant while storing full documents in GCS
"""

import os
import uuid
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams, PointStruct, Filter


class QdrantManager:
    """Manages vector operations with Qdrant database"""
    
    def __init__(self, 
                 host: str = None, 
                 port: int = 6333,
                 collection_name: str = "documents",
                 vector_size: int = 1024):
        # Use environment variable for host, fallback to localhost
        if host is None:
            host = os.getenv("QDRANT_HOST", "localhost")
        """
        Initialize Qdrant client
        
        Args:
            host: Qdrant server host
            port: Qdrant server port
            collection_name: Name of the collection
            vector_size: Dimension of vectors (1024 for Jina v3)
        """
        self.host = host
        self.port = port
        self.collection_name = collection_name
        self.vector_size = vector_size
        
        # Initialize Qdrant client
        self.client = QdrantClient(host=host, port=port)
        
        # Ensure collection exists
        self._ensure_collection()
    
    def _ensure_collection(self):
        """Create collection if it doesn't exist"""
        try:
            collections = self.client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            if self.collection_name not in collection_names:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_size,
                        distance=Distance.COSINE
                    )
                )
                print(f"✅ Created Qdrant collection: {self.collection_name}")
            else:
                print(f"✅ Qdrant collection {self.collection_name} already exists")
                
        except Exception as e:
            print(f"❌ Error creating Qdrant collection: {e}")
            raise
    
    def add_vectors(self, 
                   vectors: List[List[float]], 
                   payloads: List[Dict[str, Any]], 
                   doc_ids: Optional[List[str]] = None) -> List[str]:
        """
        Add vectors and associated metadata to Qdrant
        
        Args:
            vectors: List of vector embeddings
            payloads: List of metadata payloads
            doc_ids: Optional list of document IDs (auto-generated if None)
            
        Returns:
            List of document IDs used
        """
        if len(vectors) != len(payloads):
            raise ValueError("Vectors and payloads must have same length")
        
        if doc_ids is None:
            doc_ids = [str(uuid.uuid4()) for _ in vectors]
        elif len(doc_ids) != len(vectors):
            raise ValueError("doc_ids must match vectors length")
        
        points = []
        for idx, (vector, payload, doc_id) in enumerate(zip(vectors, payloads, doc_ids)):
            point = PointStruct(
                id=idx + 1,  # Qdrant uses integer IDs
                vector=vector,
                payload={
                    "doc_id": doc_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    **payload
                }
            )
            points.append(point)
        
        try:
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            print(f"✅ Added {len(points)} vectors to Qdrant")
            return doc_ids
            
        except Exception as e:
            print(f"❌ Error adding vectors to Qdrant: {e}")
            raise
    
    def search_vectors(self, 
                      query_vector: List[float], 
                      limit: int = 5,
                      score_threshold: float = 0.0) -> List[Dict[str, Any]]:
        """
        Search for similar vectors
        
        Args:
            query_vector: The vector to search against
            limit: Maximum number of results
            score_threshold: Minimum similarity score
            
        Returns:
            List of search results with scores and metadata
        """
        try:
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=limit,
                score_threshold=score_threshold
            )
            
            results = []
            for hit in search_result:
                results.append({
                    "doc_id": hit.payload.get("doc_id"),
                    "score": hit.score,
                    "payload": hit.payload
                })
            
            return results
            
        except Exception as e:
            print(f"❌ Error searching vectors: {e}")
            raise
    
    def delete_vectors(self, doc_ids: List[str]) -> int:
        """
        Delete vectors by document IDs
        
        Args:
            doc_ids: List of document IDs to delete
            
        Returns:
            Number of vectors deleted
        """
        try:
            # Create filter for doc_ids
            filter_condition = Filter(
                must=[
                    models.FieldCondition(
                        key="doc_id",
                        match=models.MatchAny(any=doc_ids)
                    )
                ]
            )
            
            # Get points to delete
            scroll_result = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=filter_condition,
                limit=1000
            )
            
            if scroll_result[0]:
                point_ids = [point.id for point in scroll_result[0]]
                self.client.delete(
                    collection_name=self.collection_name,
                    points_selector=models.PointIdsList(points=point_ids)
                )
                print(f"✅ Deleted {len(point_ids)} vectors from Qdrant")
                return len(point_ids)
            
            return 0
            
        except Exception as e:
            print(f"❌ Error deleting vectors: {e}")
            raise
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the collection"""
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                "name": info.config.params.vectors.size,
                "vector_size": info.config.params.vectors.size,
                "distance": str(info.config.params.vectors.distance),
                "points_count": info.points_count
            }
        except Exception as e:
            print(f"❌ Error getting collection info: {e}")
            raise
    
    def clear_collection(self):
        """Clear all vectors from the collection"""
        try:
            self.client.delete_collection(self.collection_name)
            self._ensure_collection()
            print(f"✅ Cleared Qdrant collection: {self.collection_name}")
        except Exception as e:
            print(f"❌ Error clearing collection: {e}")
            raise

    def get_vectors_by_file_id(self, file_id: str) -> List[Dict[str, Any]]:
        """Get all vectors for a specific file_id"""
        try:
            # Create filter for file_id
            filter_condition = Filter(
                must=[
                    models.FieldCondition(
                        key="file_id",
                        match=models.MatchValue(value=file_id)
                    )
                ]
            )
            
            # Get all vectors for this file
            scroll_result = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=filter_condition,
                limit=1000
            )
            
            vectors = []
            for point in scroll_result[0]:
                vectors.append({
                    "id": point.id,
                    "payload": point.payload,
                    "vector": point.vector
                })
            
            return vectors
            
        except Exception as e:
            print(f"❌ Error getting vectors by file_id: {e}")
            raise

    def search_by_metadata(self, 
                          metadata_filter: Dict[str, Any],
                          limit: int = 10) -> List[Dict[str, Any]]:
        """Search vectors by metadata filter"""
        try:
            # Build filter conditions
            conditions = []
            for key, value in metadata_filter.items():
                if isinstance(value, list):
                    conditions.append(
                        models.FieldCondition(
                            key=key,
                            match=models.MatchAny(any=value)
                        )
                    )
                else:
                    conditions.append(
                        models.FieldCondition(
                            key=key,
                            match=models.MatchValue(value=value)
                        )
                    )
            
            filter_condition = Filter(must=conditions)
            
            search_result = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=filter_condition,
                limit=limit
            )
            
            results = []
            for point in search_result[0]:
                results.append({
                    "id": point.id,
                    "payload": point.payload,
                    "vector": point.vector
                })
            
            return results
            
        except Exception as e:
            print(f"❌ Error searching by metadata: {e}")
            raise