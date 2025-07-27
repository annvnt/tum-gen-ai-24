"""
ChatFileManager - Enhanced file management for chat-based financial analysis
Provides smart file selection, context management, and PDF generation
"""

import json
import uuid
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
import logging

from .document_storage import GCSMetadataManager
from .unified_vector_service import VectorService
from ..storage.database_manager import db_manager
from ..security.input_validator import InputValidator
from ..security.sql_sanitizer import SQLSanitizer


logger = logging.getLogger(__name__)


class ChatFileManager:
    """Enhanced file management service for chat-based financial analysis"""
    
    def __init__(self):
        """Initialize the chat file manager"""
        self.gcs_manager = GCSMetadataManager()
        self.vector_service = VectorService()
        
    def get_available_files(self, 
                          limit: Optional[int] = None,
                          file_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all available files with enhanced metadata
        
        Args:
            limit: Maximum number of files to return
            file_type: Filter by file type (excel, pdf, json, etc.)
            
        Returns:
            List of file metadata with chat-specific information
        """
        try:
            # Get files from database
            files = db_manager.list_uploaded_files()
            
            # Enhance with vector processing status
            enhanced_files = []
            for file_info in files[:limit] if limit else files:
                # Get vector processing status
                vector_status = db_manager.get_vector_metadata(file_info['id'])
                
                enhanced_file = {
                    **file_info,
                    'vector_processed': bool(vector_status),
                    'vector_status': vector_status.get('status') if vector_status else 'not_processed',
                    'processed_at': vector_status.get('processed_at') if vector_status else None,
                    'file_type': self._get_file_type(file_info['filename']),
                    'size_category': self._categorize_file_size(file_info.get('file_size', 0))
                }
                enhanced_files.append(enhanced_file)
                
            return enhanced_files
            
        except Exception as e:
            logger.error(f"Error getting available files: {e}")
            return []
    
    def search_files(self, 
                    query: str,
                    search_type: str = "semantic",
                    limit: int = 10,
                    filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Search files using semantic search or filename matching
        
        Args:
            query: Search query
            search_type: "semantic" for vector search, "filename" for name matching
            limit: Maximum results
            filters: Additional filters (date_range, file_type, etc.)
            
        Returns:
            List of matching files with relevance scores
        """
        try:
            if search_type == "semantic":
                return self._semantic_search(query, limit, filters)
            else:
                return self._filename_search(query, limit, filters)
                
        except Exception as e:
            logger.error(f"Error searching files: {e}")
            return []
    
    def _semantic_search(self, 
                        query: str,
                        limit: int,
                        filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Perform semantic search using vector embeddings"""
        try:
            # Use vector service for semantic search
            results = self.vector_service.search_similar_documents(
                query_vector=self._get_query_embedding(query),
                limit=limit,
                score_threshold=filters.get('min_score', 0.7) if filters else 0.7
            )
            
            # Enhance results with file metadata
            enhanced_results = []
            for result in results:
                doc_id = result.get('doc_id')
                if doc_id:
                    file_info = db_manager.get_uploaded_file(doc_id)
                    if file_info:
                        enhanced_results.append({
                            **file_info,
                            'relevance_score': result.get('score', 0),
                            'content_preview': result.get('qdrant_payload', {}).get('content_preview', ''),
                            'search_type': 'semantic'
                        })
            
            return enhanced_results
            
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return []
    
    def _filename_search(self, 
                        query: str,
                        limit: int,
                        filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Perform filename-based search"""
        try:
            # Use database search
            files = db_manager.search_documents_by_filename(query)
            
            # Apply additional filters
            if filters:
                if 'file_type' in filters:
                    files = [f for f in files if self._get_file_type(f['filename']) == filters['file_type']]
                if 'date_range' in filters:
                    files = self._filter_by_date_range(files, filters['date_range'])
            
            # Limit results
            files = files[:limit]
            
            # Add search metadata
            enhanced_files = []
            for file_info in files:
                enhanced_files.append({
                    **file_info,
                    'relevance_score': self._calculate_filename_relevance(query, file_info['filename']),
                    'search_type': 'filename'
                })
            
            return enhanced_files
            
        except Exception as e:
            logger.error(f"Error in filename search: {e}")
            return []
    
    def get_file_context(self, file_id: str) -> Dict[str, Any]:
        """
        Get comprehensive file context for chat analysis
        
        Args:
            file_id: File ID to get context for
            
        Returns:
            Complete file context including metadata, analysis history, and content preview
        """
        try:
            # Get file info
            file_info = db_manager.get_uploaded_file(file_id)
            if not file_info:
                return {}
            
            # Get vector processing status
            vector_status = db_manager.get_vector_metadata(file_id)
            
            # Get analysis history
            reports = db_manager.get_reports_for_file(file_id)
            
            # Get related chat history
            chat_history = self._get_file_chat_history(file_id)
            
            context = {
                'file_info': file_info,
                'vector_status': vector_status,
                'analysis_history': reports,
                'chat_history': chat_history,
                'file_type': self._get_file_type(file_info['filename']),
                'estimated_processing_time': self._estimate_processing_time(file_info.get('file_size', 0)),
                'content_preview': self._get_content_preview(file_id)
            }
            
            return context
            
        except Exception as e:
            logger.error(f"Error getting file context: {e}")
            return {}
    
    def auto_select_files(self, 
                         context: str,
                         max_files: int = 5,
                         criteria: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Auto-select relevant files based on chat context
        
        Args:
            context: Current chat context or user query
            max_files: Maximum files to select
            criteria: Selection criteria (date_range, file_types, etc.)
            
        Returns:
            List of auto-selected files with relevance scores
        """
        try:
            # Use semantic search to find relevant files
            candidates = self.search_files(
                query=context,
                search_type="semantic",
                limit=max_files * 2,  # Get more candidates for filtering
                filters=criteria
            )
            
            # Apply additional selection logic
            selected = self._apply_selection_criteria(candidates, criteria, max_files)
            
            return selected
            
        except Exception as e:
            logger.error(f"Error in auto-selection: {e}")
            return []
    
    def _get_file_type(self, filename: str) -> str:
        """Determine file type from filename"""
        extension = Path(filename).suffix.lower()
        type_map = {
            '.xlsx': 'excel',
            '.xls': 'excel',
            '.csv': 'csv',
            '.pdf': 'pdf',
            '.json': 'json',
            '.txt': 'text'
        }
        return type_map.get(extension, 'unknown')
    
    def _categorize_file_size(self, size_bytes: int) -> str:
        """Categorize file size"""
        if size_bytes < 1024 * 1024:  # < 1MB
            return "small"
        elif size_bytes < 10 * 1024 * 1024:  # < 10MB
            return "medium"
        else:
            return "large"
    
    def _estimate_processing_time(self, size_bytes: int) -> str:
        """Estimate processing time based on file size"""
        if size_bytes < 1024 * 1024:
            return "< 30 seconds"
        elif size_bytes < 10 * 1024 * 1024:
            return "1-2 minutes"
        else:
            return "2-5 minutes"
    
    def _get_content_preview(self, file_id: str) -> str:
        """Get content preview for a file"""
        try:
            # This would need to be implemented based on file type
            # For now, return a placeholder
            return "Content preview available after processing"
        except Exception:
            return "Preview not available"
    
    def _get_query_embedding(self, query: str) -> List[float]:
        """Get vector embedding for search query"""
        # This would use the embedding service
        # For now, return a dummy vector
        return [0.1] * 768  # Jina embeddings are 768-dimensional
    
    def _calculate_filename_relevance(self, query: str, filename: str) -> float:
        """Calculate filename-based relevance score"""
        query_lower = query.lower()
        filename_lower = filename.lower()
        
        score = 0.0
        if query_lower in filename_lower:
            score += 0.8
        
        # Bonus for exact word matches
        query_words = query_lower.split()
        filename_words = filename_lower.replace('_', ' ').replace('-', ' ').split()
        matches = sum(1 for qw in query_words if qw in filename_words)
        score += (matches / len(query_words)) * 0.2
        
        return min(score, 1.0)
    
    def _filter_by_date_range(self, files: List[Dict], date_range: Dict[str, str]) -> List[Dict]:
        """Filter files by date range"""
        try:
            from datetime import datetime
            start_date = datetime.fromisoformat(date_range['start'])
            end_date = datetime.fromisoformat(date_range['end'])
            
            return [
                f for f in files
                if start_date <= datetime.fromisoformat(f['uploaded_at']) <= end_date
            ]
        except Exception:
            return files
    
    def _apply_selection_criteria(self, 
                                candidates: List[Dict],
                                criteria: Optional[Dict],
                                max_files: int) -> List[Dict]:
        """Apply selection criteria to candidates"""
        if not criteria:
            return candidates[:max_files]
        
        # Score candidates based on criteria
        scored = []
        for candidate in candidates:
            score = candidate.get('relevance_score', 0.5)
            
            # Boost recent files
            if criteria.get('prefer_recent'):
                from datetime import datetime
                upload_date = datetime.fromisoformat(candidate['uploaded_at'])
                days_old = (datetime.now() - upload_date).days
                recency_boost = max(0, 1 - (days_old / 30)) * 0.3
                score += recency_boost
            
            # Boost vector-processed files
            if criteria.get('prefer_processed') and candidate.get('vector_processed'):
                score += 0.2
            
            scored.append({**candidate, 'selection_score': score})
        
        # Sort by selection score and return top files
        scored.sort(key=lambda x: x['selection_score'], reverse=True)
        return scored[:max_files]
    
    def _get_file_chat_history(self, file_id: str) -> List[Dict[str, Any]]:
        """Get chat history related to a specific file"""
        try:
            # This would query the chat history for mentions of this file
            # For now, return empty list
            return []
        except Exception:
            return []