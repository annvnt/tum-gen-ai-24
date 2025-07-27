#!/usr/bin/env python3
"""
FastAPI Backend for Financial Report Analysis
Provides endpoints for uploading Excel files, analyzing financial data,
and generating reports using OpenAI GPT.
"""

import os
import uuid
import tempfile
import shutil
import io
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
from contextlib import asynccontextmanager
import json

import pandas as pd
from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# Import core financial analysis functionality
from ..core.financial_analyzer import (
    setup_environment,
    load_financial_data,
    load_financial_indicators,
    generate_financial_report,
    extract_simple_table,
    extract_structured_tables
)
# Import the financial agent
from ..services.financial_agent import FinancialReportAgent
from ..services.vector_processing import get_vector_processing_service

# Import database manager
from ..storage.database_manager import db_manager

# Custom JSON encoder for datetime objects
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

# Global variables
openai_client = None
financial_agent = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager
    Handles startup and shutdown events
    """
    # Startup
    global openai_client, financial_agent
    try:
        openai_client = setup_environment()
        financial_agent = FinancialReportAgent()
        print("✅ OpenAI client initialized successfully")
        print("✅ Financial Agent initialized successfully")
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize services: {str(e)}")
        raise

    yield

    # Shutdown
    print("🔄 Shutting down Financial Report API...")

# Initialize FastAPI app with lifespan
app = FastAPI(
    title="Financial Report API",
    description="API for financial data analysis and report generation",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware - simplified for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # Local development only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data models
class FinancialIndicators(BaseModel):
    balance_sheet: List[str]
    income_statement: List[str]
    cash_flow: List[str]

class AnalysisRequest(BaseModel):
    file_id: str
    custom_params: Optional[Dict[str, Any]] = None

class AnalysisResponse(BaseModel):
    report_id: str
    summary: str
    tables: Optional[Dict[str, Any]] = None
    status: str

class ReportResponse(BaseModel):
    report_id: str
    file_id: str
    generated_at: datetime
    summary: str
    tables: Optional[Dict[str, Any]] = None
    status: str

class UploadResponse(BaseModel):
    file_id: str
    filename: str
    uploaded_at: datetime
    status: str

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Financial Report API is running", "status": "healthy"}

@app.post("/api/financial/upload", response_model=UploadResponse)
async def upload_excel_file(file: UploadFile = File(...)):
    """
    Upload an Excel file for financial analysis
    Returns a file ID for later use
    """
    try:
        # Validate file type and size (simple validation for local dev)
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="Only Excel files (.xlsx, .xls) are supported")
        
        # Simple file size check (100MB limit for local development)
        file_content = await file.read()
        if len(file_content) > 100 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File too large (max 100MB)")
        
        # Reset file pointer
        file.file.seek(0)

        # Generate unique file ID
        file_id = str(uuid.uuid4())

        # Import GCS client and path utilities
        from ..storage.gcs_client import get_gcs_client
        from ..storage.gcs_path_utils import GCSPathManager
        
        # Upload file to Google Cloud Storage
        gcs_client = get_gcs_client()
        
        # Create standardized GCS blob name using path utilities
        blob_name = GCSPathManager.get_upload_blob_name(file.filename, file_id)
        
        # Upload file content to GCS
        gcs_client.upload_file(
            io.BytesIO(file_content), 
            blob_name, 
            content_type=file.content_type or "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        # Store only the relative blob name (not full URL) for consistent access
        file_url = blob_name
        
        # Store file information in the database with GCS URL
        db_manager.store_uploaded_file(file_id, file.filename, file_url)

        return UploadResponse(
            file_id=file_id,
            filename=file.filename,
            uploaded_at=datetime.now(),
            status="uploaded"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")

@app.get("/api/financial/indicators", response_model=FinancialIndicators)
async def get_financial_indicators():
    """
    Get list of available financial indicators
    Returns indicators for Balance Sheet, Income Statement, and Cash Flow
    """
    try:
        # Load financial indicators from the reference file
        balance_str, income_str, cf_str = load_financial_indicators()

        # Parse the strings back to lists
        balance_items = [item.strip("- ") for item in balance_str.split("\n") if item.strip()]
        income_items = [item.strip("- ") for item in income_str.split("\n") if item.strip()]
        cf_items = [item.strip("- ") for item in cf_str.split("\n") if item.strip()]

        return FinancialIndicators(
            balance_sheet=balance_items,
            income_statement=income_items,
            cash_flow=cf_items
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading financial indicators: {str(e)}")

@app.post("/api/financial/analyze", response_model=AnalysisResponse)
async def analyze_financial_data(request: AnalysisRequest, background_tasks: BackgroundTasks):
    """
    Analyze financial data and generate report
    Takes a file ID and optional custom parameters
    """
    try:
        # Validate file exists
        file_info = db_manager.get_uploaded_file(request.file_id)
        if not file_info:
            raise HTTPException(status_code=404, detail="File not found")

        file_url = file_info["file_path"]
        
        # Download file from GCS to temporary location for processing
        from ..storage.gcs_client import get_gcs_client
        from ..storage.gcs_path_utils import GCSPathManager
        gcs_client = get_gcs_client()
        
        # Extract clean blob name using centralized path utilities
        blob_name = GCSPathManager.extract_blob_name_from_url(file_url)
        
        file_content = gcs_client.download_file(blob_name)
        
        # Save to temporary file for processing
        temp_file = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
        temp_file.write(file_content)
        temp_file.close()
        
        try:
            # Load financial data from temporary file
            df = load_financial_data(temp_file.name)
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)

        # Load financial indicators
        balance_str, income_str, cf_str = load_financial_indicators()

        # Generate report ID
        report_id = str(uuid.uuid4())

        # Generate financial report using OpenAI
        report_text = generate_financial_report(openai_client, df, balance_str, income_str, cf_str)

        # Extract tables from the report
        simple_table = extract_simple_table(report_text)
        structured_tables = extract_structured_tables(report_text)

        # Prepare tables data for response
        tables_data = {}
        if simple_table is not None:
            tables_data["summary"] = simple_table.to_dict(orient="records")
        if structured_tables:
            for table_name, table_df in structured_tables.items():
                tables_data[table_name.lower().replace(" ", "_")] = table_df.to_dict(orient="records")

        # Store generated report in the database
        db_manager.store_generated_report(report_id, request.file_id, report_text, tables_data, request.custom_params)

        return AnalysisResponse(
            report_id=report_id,
            summary=report_text,
            tables=tables_data,
            status="completed"
        )

    except HTTPException:
        # Re-raise HTTP exceptions (like 404) without modification
        raise
    except Exception as e:
        # Only catch unexpected errors as 500
        raise HTTPException(status_code=500, detail=f"Error analyzing financial data: {str(e)}")

@app.get("/api/financial/report/{report_id}", response_model=ReportResponse)
async def get_financial_report(report_id: str):
    """
    Get a previously generated financial report
    """
    try:
        report_data = db_manager.get_generated_report_dict(report_id)
        if not report_data:
            raise HTTPException(status_code=404, detail="Report not found")

        # Ensure datetime is properly serialized
        generated_at = report_data["generated_at"]
        if isinstance(generated_at, str):
            generated_at = datetime.fromisoformat(generated_at.replace('Z', '+00:00'))

        return {
            "report_id": report_data["report_id"],
            "file_id": report_data["file_id"],
            "generated_at": generated_at.isoformat(),
            "summary": report_data["summary"],
            "tables": report_data["tables"],
            "status": report_data["status"]
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving report: {str(e)}")

@app.post("/api/financial/export/{report_id}")
async def export_report_to_excel(report_id: str):
    """
    Export a generated report to Excel format
    Returns a downloadable Excel file
    """
    try:
        report_data = db_manager.get_generated_report_dict(report_id)
        if not report_data:
            raise HTTPException(status_code=404, detail="Report not found")

        # Create temporary Excel file
        temp_dir = tempfile.gettempdir()
        excel_file = os.path.join(temp_dir, f"financial_report_{report_id}.xlsx")

        # Create Excel file with multiple sheets
        with pd.ExcelWriter(excel_file, engine="xlsxwriter") as writer:
            # Write summary sheet
            if "summary" in report_data["tables"]:
                summary_df = pd.DataFrame(report_data["tables"]["summary"])
                summary_df.to_excel(writer, sheet_name="Summary", index=False)

            # Write structured tables
            for table_name, table_data in report_data["tables"].items():
                if table_name != "summary":
                    table_df = pd.DataFrame(table_data)
                    sheet_name = table_name.replace("_", " ").title()[:31]  # Excel sheet name limit
                    table_df.to_excel(writer, sheet_name=sheet_name, index=False)

        return FileResponse(
            excel_file,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=f"financial_report_{report_id}.xlsx"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting report: {str(e)}")

# Additional utility endpoints
@app.get("/api/financial/files")
async def list_uploaded_files():
    """List all uploaded files"""
    try:
        files_list = db_manager.list_uploaded_files()

        return {"files": files_list}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing files: {str(e)}")

@app.get("/api/financial/reports")
async def list_generated_reports():
    """List all generated reports"""
    try:
        reports_list = db_manager.list_generated_reports()

        return {"reports": reports_list}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing reports: {str(e)}")

@app.delete("/api/financial/file/{file_id}")
async def delete_uploaded_file(file_id: str):
    """Delete an uploaded file"""
    if not db_manager.get_uploaded_file(file_id):
        raise HTTPException(status_code=404, detail="File not found")

    try:
        file_info = db_manager.get_uploaded_file(file_id)
        file_url = file_info["file_path"]
        
        # Remove file from GCS
        from ..storage.gcs_client import get_gcs_client
        from ..storage.gcs_path_utils import GCSPathManager
        gcs_client = get_gcs_client()
        
        # Extract clean blob name using centralized path utilities
        blob_name = GCSPathManager.extract_blob_name_from_url(file_url)
        
        try:
            gcs_client.delete_file(blob_name)
        except Exception as e:
            # Log the error but continue with database deletion
            print(f"Warning: Could not delete file from GCS: {str(e)}")

        # Remove from database
        db_manager.delete_uploaded_file(file_id)

        return {"message": "File deleted successfully", "file_id": file_id}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting file: {str(e)}")

# Enhanced agent endpoints with database integration
class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    timestamp: str
    session_id: str
    context_documents: Optional[List[str]] = None

class DocumentAnalysisRequest(BaseModel):
    file_id: str

class VectorProcessingRequest(BaseModel):
    file_id: str
    metadata: Optional[Dict[str, Any]] = None

class VectorSearchRequest(BaseModel):
    query: str
    limit: int = 10
    score_threshold: float = 0.7

class VectorProcessingResponse(BaseModel):
    status: str
    file_id: str
    vectors_stored: int
    processing_timestamp: str
    vector_ids: List[str]

class VectorSearchResponse(BaseModel):
    results: List[Dict[str, Any]]
    query: str
    total_results: int

class VectorStatsResponse(BaseModel):
    total_files: int
    total_vectors: int
    collection_info: Dict[str, Any]
    processing_stats: Dict[str, Any]

@app.post("/api/agent/chat", response_model=ChatResponse)
async def chat_with_agent(chat_message: ChatMessage):
    """
    Chat with the financial report agent with persistent conversation history
    """
    try:
        if not financial_agent:
            raise HTTPException(status_code=500, detail="Agent not initialized")

        # Set session ID if provided
        if chat_message.session_id:
            financial_agent.current_session_id = chat_message.session_id

        response = await financial_agent.process_message(chat_message.message)

        # Get context documents used in this response
        context_docs = financial_agent.get_document_context(chat_message.message)

        return ChatResponse(
            response=response,
            timestamp=datetime.now().isoformat(),
            session_id=financial_agent.current_session_id,
            context_documents=context_docs
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")

@app.get("/api/agent/conversation/{session_id}")
async def get_conversation_history(session_id: str):
    """
    Get the conversation history for a specific session from database
    """
    try:
        if not financial_agent:
            raise HTTPException(status_code=500, detail="Agent not initialized")

        history = financial_agent.get_database_chat_history(session_id)

        return {
            "session_id": session_id,
            "conversation": history,
            "message_count": len(history)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving conversation: {str(e)}")

@app.get("/api/agent/conversation")
async def get_current_conversation_history():
    """
    Get the conversation history for the current session
    """
    try:
        if not financial_agent:
            raise HTTPException(status_code=500, detail="Agent not initialized")

        # Get both in-memory and database history
        memory_history = financial_agent.get_conversation_history()
        db_history = financial_agent.get_database_chat_history()

        return {
            "session_id": financial_agent.current_session_id,
            "memory_conversation": memory_history,
            "database_conversation": db_history,
            "message_count": len(db_history)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving conversation: {str(e)}")

@app.post("/api/agent/analyze-document")
async def analyze_document_with_agent(request: DocumentAnalysisRequest):
    """
    Analyze a specific document using the financial agent
    """
    try:
        if not financial_agent:
            raise HTTPException(status_code=500, detail="Agent not initialized")

        result = await financial_agent.analyze_document(request.file_id)

        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing document: {str(e)}")

@app.get("/api/agent/documents")
async def get_available_documents():
    """
    Get list of available documents for analysis
    """
    try:
        if not financial_agent:
            raise HTTPException(status_code=500, detail="Agent not initialized")

        return financial_agent.get_available_documents()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving documents: {str(e)}")

@app.post("/api/agent/clear/{session_id}")
async def clear_conversation_session(session_id: str):
    """
    Clear the conversation history for a specific session
    """
    try:
        if not financial_agent:
            raise HTTPException(status_code=500, detail="Agent not initialized")

        # Clear from current agent if it's the same session
        if financial_agent.current_session_id == session_id:
            financial_agent.clear_conversation()

        return {"message": f"Conversation history cleared for session {session_id}"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing conversation: {str(e)}")

@app.post("/api/agent/clear")
async def clear_conversation():
    """
    Clear the conversation history for current session
    """
    try:
        if not financial_agent:
            raise HTTPException(status_code=500, detail="Agent not initialized")

        old_session = financial_agent.current_session_id
        financial_agent.clear_conversation()

        return {
            "message": "Conversation history cleared",
            "old_session_id": old_session,
            "new_session_id": financial_agent.current_session_id
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing conversation: {str(e)}")

@app.get("/api/agent/files")
async def list_agent_files():
    """
    List available files for the agent
    """
    try:
        if not financial_agent:
            raise HTTPException(status_code=500, detail="Agent not initialized")

        financial_agent.scan_available_files()

        return {
            "files": financial_agent.available_files,
            "session_id": financial_agent.current_session_id
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing files: {str(e)}")

# Vector processing endpoints
@app.post("/api/vector/process", response_model=VectorProcessingResponse)
async def process_document_vectors(request: VectorProcessingRequest, background_tasks: BackgroundTasks):
    """
    Process a document for vector storage using Jina embeddings and Qdrant
    """
    try:
        # Validate file exists
        file_info = db_manager.get_uploaded_file(request.file_id)
        if not file_info:
            raise HTTPException(status_code=404, detail="File not found")

        # Get vector processing service
        vector_service = get_vector_processing_service()
        
        # Start processing in background
        background_tasks.add_task(
            vector_service.process_excel_file,
            file_info["file_path"],
            request.file_id,
            file_info["filename"],
            request.metadata
        )
        
        return VectorProcessingResponse(
            status="processing_started",
            file_id=request.file_id,
            vectors_stored=0,
            processing_timestamp=datetime.now().isoformat(),
            vector_ids=[]
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting vector processing: {str(e)}")

@app.get("/api/vector/status/{file_id}")
async def get_vector_processing_status(file_id: str):
    """
    Get the vector processing status for a document
    """
    try:
        metadata = db_manager.get_vector_metadata(file_id)
        if not metadata:
            return {"status": "not_processed", "file_id": file_id}
        
        return metadata
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting processing status: {str(e)}")

@app.post("/api/vector/search", response_model=VectorSearchResponse)
async def search_similar_documents(request: VectorSearchRequest):
    """
    Search for similar documents using vector similarity
    """
    try:
        vector_service = get_vector_processing_service()
        
        results = await vector_service.search_similar_documents(
            query_text=request.query,
            limit=request.limit,
            score_threshold=request.score_threshold
        )
        
        return VectorSearchResponse(
            results=results,
            query=request.query,
            total_results=len(results)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching documents: {str(e)}")

@app.get("/api/vector/vectors/{file_id}")
async def get_document_vectors(file_id: str):
    """
    Get all vectors for a specific document
    """
    try:
        vector_service = get_vector_processing_service()
        vectors = await vector_service.get_document_vectors(file_id)
        
        return {"file_id": file_id, "vectors": vectors}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving vectors: {str(e)}")

@app.delete("/api/vector/vectors/{file_id}")
async def delete_document_vectors(file_id: str):
    """
    Delete all vectors for a specific document
    """
    try:
        vector_service = get_vector_processing_service()
        deleted_count = await vector_service.delete_document_vectors(file_id)
        
        return {
            "file_id": file_id,
            "deleted_vectors": deleted_count,
            "message": f"Deleted {deleted_count} vectors for document {file_id}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting vectors: {str(e)}")

@app.get("/api/vector/stats", response_model=VectorStatsResponse)
async def get_vector_processing_stats():
    """
    Get vector processing statistics
    """
    try:
        vector_service = get_vector_processing_service()
        stats = await vector_service.get_processing_stats()
        
        return VectorStatsResponse(**stats)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting statistics: {str(e)}")

# Enhanced Chat Endpoints
from ..services.enhanced_chat_agent import EnhancedChatAgent
from ..services.chat_file_manager import ChatFileManager
from ..services.pdf_generator import FinancialPDFGenerator

# Initialize enhanced services
enhanced_chat_agent = EnhancedChatAgent()
chat_file_manager = ChatFileManager()
pdf_generator = FinancialPDFGenerator()

class EnhancedChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

class EnhancedChatResponse(BaseModel):
    response: str
    session_id: str
    status: str
    report_id: Optional[str] = None
    download_url: Optional[str] = None
    files_included: Optional[List[str]] = None
    analysis_results: Optional[List[Dict[str, Any]]] = None
    search_results: Optional[List[Dict[str, Any]]] = None

class FileSearchRequest(BaseModel):
    query: str
    search_type: str = "semantic"  # "semantic" or "filename"
    limit: int = 10
    filters: Optional[Dict[str, Any]] = None

class FileContextRequest(BaseModel):
    file_id: str

class ReportGenerationRequest(BaseModel):
    file_ids: List[str]
    template: str = "comprehensive"
    custom_config: Optional[Dict[str, Any]] = None

class SessionRequest(BaseModel):
    session_id: str

@app.post("/api/enhanced/chat", response_model=EnhancedChatResponse)
async def enhanced_chat_endpoint(request: EnhancedChatMessage):
    """
    Enhanced chat endpoint with file context and knowledge base integration
    """
    try:
        response = await enhanced_chat_agent.process_message(
            message=request.message,
            session_id=request.session_id or str(uuid.uuid4()),
            context=request.context
        )
        return EnhancedChatResponse(**response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in enhanced chat: {str(e)}")

@app.get("/api/enhanced/chat/session/{session_id}")
async def get_chat_session_summary(session_id: str):
    """
    Get summary of chat session activity
    """
    try:
        return await enhanced_chat_agent.get_session_summary(session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting session summary: {str(e)}")

@app.delete("/api/enhanced/chat/session/{session_id}")
async def clear_chat_session(session_id: str):
    """
    Clear chat session history
    """
    try:
        return await enhanced_chat_agent.clear_session(session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing session: {str(e)}")

@app.post("/api/enhanced/files/search")
async def search_files_endpoint(request: FileSearchRequest):
    """
    Search files using semantic or filename-based search
    """
    try:
        results = chat_file_manager.search_files(
            query=request.query,
            search_type=request.search_type,
            limit=request.limit,
            filters=request.filters
        )
        return {"results": results, "query": request.query, "total": len(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching files: {str(e)}")

@app.get("/api/enhanced/files/available")
async def get_available_files(limit: int = 20, file_type: Optional[str] = None):
    """
    Get all available files with enhanced metadata
    """
    try:
        files = chat_file_manager.get_available_files(
            limit=limit,
            file_type=file_type
        )
        return {"files": files, "total": len(files)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting files: {str(e)}")

@app.get("/api/enhanced/files/{file_id}/context")
async def get_file_context(file_id: str):
    """
    Get comprehensive file context for chat analysis
    """
    try:
        context = chat_file_manager.get_file_context(file_id)
        if not context:
            raise HTTPException(status_code=404, detail="File not found")
        return context
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting file context: {str(e)}")

@app.post("/api/enhanced/files/auto-select")
async def auto_select_files(request: Dict[str, Any]):
    """
    Auto-select relevant files based on context
    """
    try:
        selected = chat_file_manager.auto_select_files(
            context=request.get('context', ''),
            max_files=request.get('max_files', 5),
            criteria=request.get('criteria', {})
        )
        return {"selected_files": selected, "context": request.get('context', '')}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error auto-selecting files: {str(e)}")

@app.post("/api/enhanced/reports/generate")
async def generate_enhanced_report(request: ReportGenerationRequest, background_tasks: BackgroundTasks):
    """
    Generate enhanced PDF report from selected files
    """
    try:
        report_id = str(uuid.uuid4())
        
        # Start report generation in background
        background_tasks.add_task(
            pdf_generator.generate_custom_report,
            report_config={
                'template': request.template,
                **request.custom_config
            },
            file_ids=request.file_ids
        )
        
        return {
            "report_id": report_id,
            "status": "generating",
            "message": "Report generation started"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting report generation: {str(e)}")

@app.get("/api/enhanced/reports/templates")
async def get_report_templates():
    """
    Get available report templates
    """
    try:
        templates = pdf_generator.get_report_template_options()
        return {"templates": templates}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting templates: {str(e)}")

# Database management endpoints
@app.get("/api/database/stats")
async def get_database_stats():
    """
    Get statistics about the database contents
    """
    try:
        uploaded_files = db_manager.get_all_uploaded_documents()
        generated_reports = db_manager.get_all_generated_reports()

        # Get chat statistics
        with db_manager.get_session() as session:
            from database import ChatHistory
            total_chats = session.query(ChatHistory).count()
            unique_sessions = session.query(ChatHistory.session_id).distinct().count()

        return {
            "uploaded_documents": len(uploaded_files),
            "generated_reports": len(generated_reports),
            "total_chat_messages": total_chats,
            "unique_chat_sessions": unique_sessions,
            "recent_uploads": [
                {
                    "filename": doc.original_filename,
                    "uploaded_at": doc.uploaded_at.isoformat(),
                    "file_size": doc.file_size
                }
                for doc in uploaded_files[:5]
            ]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting database stats: {str(e)}")

@app.get("/api/database/search")
async def search_documents(filename: str = None):
    """
    Search for documents by filename
    """
    try:
        if filename:
            documents = db_manager.search_documents_by_filename(filename)
        else:
            documents = db_manager.get_all_uploaded_documents()

        return {
            "documents": [
                {
                    "file_id": doc.id,
                    "filename": doc.original_filename,
                    "uploaded_at": doc.uploaded_at.isoformat(),
                    "status": doc.status,
                    "file_size": doc.file_size
                }
                for doc in documents
            ],
            "count": len(documents)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching documents: {str(e)}")

# Add server info endpoint
@app.get("/api/server/info")
async def get_server_info():
    """
    Get server information and status
    """
    return {
        "service": "Financial Report API",
        "version": "1.0.0",
        "database": "SQLite",
        "database_file": "financial_reports.db",
        "features": [
            "Document upload and storage",
            "Financial report generation",
            "Persistent chat history",
            "Document analysis",
            "Report export",
            "Vector processing with Jina embeddings",
            "Vector similarity search",
            "Qdrant vector database integration"
        ],
        "endpoints": {
            "upload": "/api/financial/upload",
            "chat": "/api/agent/chat",
            "analyze": "/api/financial/analyze",
            "export": "/api/financial/export/{report_id}",
            "vector_process": "/api/vector/process",
            "vector_search": "/api/vector/search",
            "vector_status": "/api/vector/status/{file_id}"
        }
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
