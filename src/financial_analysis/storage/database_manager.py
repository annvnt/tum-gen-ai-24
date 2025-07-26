"""
Database models and operations for Financial Report API
Handles document persistence and retrieval
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from sqlalchemy import create_engine, Column, String, DateTime, Text, JSON, Integer, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON
import uuid
from pathlib import Path

# Database configuration
DATABASE_URL = "sqlite:///./data/financial_reports.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class UploadedDocument(Base):
    __tablename__ = "uploaded_documents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_size = Column(Integer, nullable=True)
    content_type = Column(String, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="uploaded")

    # Store extracted data as JSON
    extracted_data = Column(SQLiteJSON, nullable=True)
    file_metadata = Column(SQLiteJSON, nullable=True)  # Renamed from metadata

class GeneratedReport(Base):
    __tablename__ = "generated_reports"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String, nullable=False)  # Foreign key to uploaded_documents
    report_type = Column(String, nullable=False)
    generated_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="generated")

    # Report content
    summary = Column(Text, nullable=True)
    tables = Column(SQLiteJSON, nullable=True)
    analysis_results = Column(SQLiteJSON, nullable=True)

    # Generation parameters
    generation_params = Column(SQLiteJSON, nullable=True)
    model_used = Column(String, nullable=True)

class ChatHistory(Base):
    __tablename__ = "chat_history"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, nullable=False)
    document_id = Column(String, nullable=True)  # Can be null for general queries
    user_message = Column(Text, nullable=False)
    bot_response = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Context and metadata
    context_documents = Column(SQLiteJSON, nullable=True)  # List of document IDs used
    chat_metadata = Column(SQLiteJSON, nullable=True)  # Renamed from metadata to avoid conflict

class VectorMetadata(Base):
    __tablename__ = "vector_metadata"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    file_id = Column(String, nullable=False)  # Foreign key to uploaded_documents
    filename = Column(String, nullable=False)
    processing_date = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="processing")  # processing, completed, failed
    
    # Vector information
    vector_count = Column(Integer, default=0)
    vector_ids = Column(SQLiteJSON, nullable=True)  # List of Qdrant vector IDs
    
    # Processing metadata
    processing_method = Column(String, nullable=True)
    vector_size = Column(Integer, nullable=True)
    collection_name = Column(String, nullable=True)
    processing_metadata = Column(SQLiteJSON, nullable=True)
    
    # Error information
    error_message = Column(Text, nullable=True)

class ProcessingLog(Base):
    __tablename__ = "processing_log"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    file_id = Column(String, nullable=False)
    operation = Column(String, nullable=False)  # upload, process, search, delete
    status = Column(String, nullable=False)  # success, failed
    timestamp = Column(DateTime, default=datetime.utcnow)
    details = Column(SQLiteJSON, nullable=True)
    error_message = Column(Text, nullable=True)

# Database operations
class DatabaseManager:
    def __init__(self):
        self.engine = engine
        self.SessionLocal = SessionLocal
        self.ensure_data_directory()
        self.create_tables()

    def ensure_data_directory(self):
        """Ensure the data directory exists"""
        data_dir = Path("./data")
        data_dir.mkdir(exist_ok=True)

    def create_tables(self):
        """Create all database tables"""
        Base.metadata.create_all(bind=self.engine)

    def get_session(self) -> Session:
        """Get database session"""
        return self.SessionLocal()

    # Document operations
    def save_uploaded_document(self,
                             filename: str,
                             original_filename: str,
                             file_path: str,
                             file_size: int = None,
                             content_type: str = None,
                             extracted_data: Dict = None,
                             metadata: Dict = None) -> str:
        """Save uploaded document to database"""
        with self.get_session() as session:
            doc = UploadedDocument(
                filename=filename,
                original_filename=original_filename,
                file_path=file_path,
                file_size=file_size,
                content_type=content_type,
                extracted_data=extracted_data,
                file_metadata=metadata  # Updated to use new column name
            )
            session.add(doc)
            session.commit()
            session.refresh(doc)
            return doc.id

    def get_uploaded_document(self, document_id: str) -> Optional[UploadedDocument]:
        """Get uploaded document by ID"""
        with self.get_session() as session:
            return session.query(UploadedDocument).filter(UploadedDocument.id == document_id).first()

    def get_all_uploaded_documents(self) -> List[UploadedDocument]:
        """Get all uploaded documents"""
        with self.get_session() as session:
            return session.query(UploadedDocument).order_by(UploadedDocument.uploaded_at.desc()).all()

    def update_document_extracted_data(self, document_id: str, extracted_data: Dict):
        """Update extracted data for a document"""
        with self.get_session() as session:
            doc = session.query(UploadedDocument).filter(UploadedDocument.id == document_id).first()
            if doc:
                doc.extracted_data = extracted_data
                session.commit()

    # Report operations
    def save_generated_report(self,
                            document_id: str,
                            report_type: str,
                            summary: str = None,
                            tables: Dict = None,
                            analysis_results: Dict = None,
                            generation_params: Dict = None,
                            model_used: str = None) -> str:
        """Save generated report to database"""
        with self.get_session() as session:
            report = GeneratedReport(
                document_id=document_id,
                report_type=report_type,
                summary=summary,
                tables=tables,
                analysis_results=analysis_results,
                generation_params=generation_params,
                model_used=model_used
            )
            session.add(report)
            session.commit()
            session.refresh(report)
            return report.id

    def get_generated_report(self, report_id: str) -> Optional[GeneratedReport]:
        """Get generated report by ID"""
        with self.get_session() as session:
            return session.query(GeneratedReport).filter(GeneratedReport.id == report_id).first()

    def get_reports_for_document(self, document_id: str) -> List[GeneratedReport]:
        """Get all reports for a specific document"""
        with self.get_session() as session:
            return session.query(GeneratedReport).filter(GeneratedReport.document_id == document_id).all()

    def get_all_generated_reports(self) -> List[GeneratedReport]:
        """Get all generated reports"""
        with self.get_session() as session:
            return session.query(GeneratedReport).order_by(GeneratedReport.generated_at.desc()).all()

    # Chat history operations
    def save_chat_message(self,
                         session_id: str,
                         user_message: str,
                         bot_response: str,
                         document_id: str = None,
                         context_documents: List[str] = None,
                         metadata: Dict = None) -> str:
        """Save chat message to database"""
        with self.get_session() as session:
            chat = ChatHistory(
                session_id=session_id,
                document_id=document_id,
                user_message=user_message,
                bot_response=bot_response,
                context_documents=context_documents,
                chat_metadata=metadata  # Updated to use new column name
            )
            session.add(chat)
            session.commit()
            session.refresh(chat)
            return chat.id

    def get_chat_history(self, session_id: str) -> List[ChatHistory]:
        """Get chat history for a session"""
        with self.get_session() as session:
            return session.query(ChatHistory).filter(
                ChatHistory.session_id == session_id
            ).order_by(ChatHistory.timestamp.asc()).all()

    def get_document_related_chats(self, document_id: str) -> List[ChatHistory]:
        """Get all chats related to a specific document"""
        with self.get_session() as session:
            return session.query(ChatHistory).filter(
                ChatHistory.document_id == document_id
            ).order_by(ChatHistory.timestamp.desc()).all()

    # Search and query operations
    def search_documents_by_filename(self, filename_pattern: str) -> List[UploadedDocument]:
        """Search documents by filename pattern"""
        with self.get_session() as session:
            return session.query(UploadedDocument).filter(
                UploadedDocument.original_filename.like(f"%{filename_pattern}%")
            ).all()

    def get_documents_with_extracted_data(self) -> List[UploadedDocument]:
        """Get all documents that have extracted data"""
        with self.get_session() as session:
            return session.query(UploadedDocument).filter(
                UploadedDocument.extracted_data.isnot(None)
            ).all()

    # Vector metadata operations
    def store_vector_processing_metadata(self, file_id: str, metadata: Dict[str, Any]) -> str:
        """Store vector processing metadata"""
        with self.get_session() as session:
            vector_meta = VectorMetadata(
                file_id=file_id,
                filename=metadata.get("filename", ""),
                vector_count=metadata.get("vector_count", 0),
                vector_ids=metadata.get("vector_ids", []),
                processing_method=metadata.get("processing_method"),
                vector_size=metadata.get("vector_size"),
                collection_name=metadata.get("collection_name"),
                processing_metadata=metadata.get("additional_metadata"),
                status="completed"
            )
            session.add(vector_meta)
            session.commit()
            session.refresh(vector_meta)
            return vector_meta.id

    def get_vector_metadata(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Get vector metadata for a file"""
        with self.get_session() as session:
            metadata = session.query(VectorMetadata).filter(
                VectorMetadata.file_id == file_id
            ).order_by(VectorMetadata.processing_date.desc()).first()
            
            if metadata:
                return {
                    "id": metadata.id,
                    "file_id": metadata.file_id,
                    "filename": metadata.filename,
                    "processing_date": metadata.processing_date,
                    "status": metadata.status,
                    "vector_count": metadata.vector_count,
                    "vector_ids": metadata.vector_ids,
                    "processing_method": metadata.processing_method,
                    "vector_size": metadata.vector_size,
                    "collection_name": metadata.collection_name,
                    "processing_metadata": metadata.processing_metadata,
                    "error_message": metadata.error_message
                }
            return None

    def get_all_vector_metadata(self) -> List[Dict[str, Any]]:
        """Get all vector metadata records"""
        with self.get_session() as session:
            metadata_list = session.query(VectorMetadata).order_by(
                VectorMetadata.processing_date.desc()
            ).all()
            
            return [
                {
                    "id": meta.id,
                    "file_id": meta.file_id,
                    "filename": meta.filename,
                    "processing_date": meta.processing_date,
                    "status": meta.status,
                    "vector_count": meta.vector_count,
                    "vector_ids": meta.vector_ids,
                    "processing_method": meta.processing_method,
                    "vector_size": meta.vector_size,
                    "collection_name": meta.collection_name
                }
                for meta in metadata_list
            ]

    def update_document_status(self, file_id: str, status: str, metadata: Dict[str, Any] = None):
        """Update document processing status and metadata"""
        with self.get_session() as session:
            doc = session.query(UploadedDocument).filter(UploadedDocument.id == file_id).first()
            if doc:
                doc.status = status
                if metadata:
                    doc.file_metadata = {**(doc.file_metadata or {}), **metadata}
                session.commit()

    def delete_vector_metadata(self, file_id: str) -> bool:
        """Delete vector metadata for a file"""
        with self.get_session() as session:
            metadata = session.query(VectorMetadata).filter(
                VectorMetadata.file_id == file_id
            ).all()
            
            for meta in metadata:
                session.delete(meta)
            session.commit()
            return len(metadata) > 0

    # Processing log operations
    def log_processing_operation(self, 
                               file_id: str, 
                               operation: str, 
                               status: str, 
                               details: Dict[str, Any] = None, 
                               error_message: str = None) -> str:
        """Log a processing operation"""
        with self.get_session() as session:
            log_entry = ProcessingLog(
                file_id=file_id,
                operation=operation,
                status=status,
                details=details,
                error_message=error_message
            )
            session.add(log_entry)
            session.commit()
            session.refresh(log_entry)
            return log_entry.id

    def get_processing_logs(self, file_id: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get processing logs, optionally filtered by file_id"""
        with self.get_session() as session:
            query = session.query(ProcessingLog)
            
            if file_id:
                query = query.filter(ProcessingLog.file_id == file_id)
            
            logs = query.order_by(ProcessingLog.timestamp.desc()).limit(limit).all()
            
            return [
                {
                    "id": log.id,
                    "file_id": log.file_id,
                    "operation": log.operation,
                    "status": log.status,
                    "timestamp": log.timestamp,
                    "details": log.details,
                    "error_message": log.error_message
                }
                for log in logs
            ]

    def get_vector_processing_stats(self) -> Dict[str, Any]:
        """Get vector processing statistics"""
        with self.get_session() as session:
            total_files = session.query(VectorMetadata).count()
            completed_files = session.query(VectorMetadata).filter(
                VectorMetadata.status == "completed"
            ).count()
            failed_files = session.query(VectorMetadata).filter(
                VectorMetadata.status == "failed"
            ).count()
            
            total_vectors = session.query(VectorMetadata).with_entities(
                func.sum(VectorMetadata.vector_count)
            ).scalar() or 0
            
            recent_processing = session.query(VectorMetadata).order_by(
                VectorMetadata.processing_date.desc()
            ).limit(5).all()
            
            return {
                "total_files": total_files,
                "completed_files": completed_files,
                "failed_files": failed_files,
                "total_vectors": total_vectors,
                "recent_processing": [
                    {
                        "filename": meta.filename,
                        "processing_date": meta.processing_date,
                        "vector_count": meta.vector_count,
                        "status": meta.status
                    }
                    for meta in recent_processing
                ]
            }

    def cleanup_old_files(self, days_old: int = 30):
        """Clean up old documents and reports (utility function)"""
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)

        with self.get_session() as session:
            # Clean up old documents
            old_docs = session.query(UploadedDocument).filter(
                UploadedDocument.uploaded_at < cutoff_date
            ).all()

            for doc in old_docs:
                # Remove physical file if it exists
                if os.path.exists(doc.file_path):
                    os.remove(doc.file_path)

                # Remove from database
                session.delete(doc)

            # Clean up old reports
            old_reports = session.query(GeneratedReport).filter(
                GeneratedReport.generated_at < cutoff_date
            ).all()

            for report in old_reports:
                session.delete(report)

            session.commit()

    # Convenience methods for API compatibility
    def store_uploaded_file(self, file_id: str, filename: str, file_path: str):
        """Store uploaded file (compatibility method)"""
        # Get file size
        file_size = os.path.getsize(file_path) if os.path.exists(file_path) else None

        # Create document record
        with self.get_session() as session:
            doc = UploadedDocument(
                id=file_id,
                filename=filename,
                original_filename=filename,
                file_path=file_path,
                file_size=file_size,
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            session.add(doc)
            session.commit()

    def get_uploaded_file(self, file_id: str) -> Optional[Dict]:
        """Get uploaded file info (compatibility method)"""
        doc = self.get_uploaded_document(file_id)
        if doc:
            return {
                "file_id": doc.id,
                "filename": doc.filename,
                "file_path": doc.file_path,
                "uploaded_at": doc.uploaded_at,
                "status": doc.status,
                "file_size": doc.file_size
            }
        return None

    def store_generated_report(self, report_id: str, file_id: str, summary: str, tables: Dict, custom_params: Dict = None):
        """Store generated report (compatibility method)"""
        return self.save_generated_report(
            document_id=file_id,
            report_type="financial_analysis",
            summary=summary,
            tables=tables,
            generation_params=custom_params
        )

    def get_generated_report_dict(self, report_id: str) -> Optional[Dict]:
        """Get generated report (compatibility method)"""
        report = self.get_generated_report(report_id)
        if report:
            return {
                "report_id": report.id,
                "file_id": report.document_id,
                "generated_at": report.generated_at,
                "summary": report.summary,
                "tables": report.tables,
                "status": report.status
            }
        return None

    def list_uploaded_files(self) -> List[Dict]:
        """List all uploaded files (compatibility method)"""
        docs = self.get_all_uploaded_documents()
        return [
            {
                "file_id": doc.id,
                "filename": doc.original_filename,
                "uploaded_at": doc.uploaded_at.isoformat(),
                "status": doc.status,
                "file_size": doc.file_size
            }
            for doc in docs
        ]

    def list_generated_reports(self) -> List[Dict]:
        """List all generated reports (compatibility method)"""
        reports = self.get_all_generated_reports()
        return [
            {
                "report_id": report.id,
                "file_id": report.document_id,
                "generated_at": report.generated_at.isoformat(),
                "status": report.status,
                "report_type": report.report_type
            }
            for report in reports
        ]

    def delete_uploaded_file(self, file_id: str):
        """Delete uploaded file (compatibility method)"""
        with self.get_session() as session:
            doc = session.query(UploadedDocument).filter(UploadedDocument.id == file_id).first()
            if doc:
                session.delete(doc)
                session.commit()
                return True
        return False

# Global database manager instance
db_manager = DatabaseManager()
