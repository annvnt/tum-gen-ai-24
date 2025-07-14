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

# Import our existing financial report functions
from financial_report_llm_demo import (
    setup_environment,
    load_financial_data,
    load_financial_indicators,
    generate_financial_report,
    extract_simple_table,
    extract_structured_tables
)
# Import the financial agent
from financial_agent import FinancialReportAgent

# Custom JSON encoder for datetime objects
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

# Global variables for storage (in production, use a proper database)
uploaded_files: Dict[str, Dict] = {}
generated_reports: Dict[str, Dict] = {}
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
    except Exception as e:
        print(f"❌ Failed to initialize OpenAI client: {str(e)}")
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

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure as needed for production
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
        # Validate file type
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="Only Excel files (.xlsx, .xls) are supported")

        # Generate unique file ID
        file_id = str(uuid.uuid4())

        # Create temporary file path
        temp_dir = tempfile.gettempdir()
        file_path = os.path.join(temp_dir, f"{file_id}_{file.filename}")

        # Save uploaded file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Store file information
        uploaded_files[file_id] = {
            "filename": file.filename,
            "file_path": file_path,
            "uploaded_at": datetime.now(),
            "status": "uploaded"
        }

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
        if request.file_id not in uploaded_files:
            raise HTTPException(status_code=404, detail="File not found")

        file_info = uploaded_files[request.file_id]

        # Load financial data
        df = load_financial_data(file_info["file_path"])

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

        # Store generated report
        generated_reports[report_id] = {
            "report_id": report_id,
            "file_id": request.file_id,
            "generated_at": datetime.now(),
            "summary": report_text,
            "tables": tables_data,
            "status": "completed",
            "custom_params": request.custom_params
        }

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
        if report_id not in generated_reports:
            raise HTTPException(status_code=404, detail="Report not found")

        report_data = generated_reports[report_id]

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
        if report_id not in generated_reports:
            raise HTTPException(status_code=404, detail="Report not found")

        report_data = generated_reports[report_id]

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
        files_list = []
        for file_id, info in uploaded_files.items():
            uploaded_at = info["uploaded_at"]
            if isinstance(uploaded_at, datetime):
                uploaded_at = uploaded_at.isoformat()

            files_list.append({
                "file_id": file_id,
                "filename": info["filename"],
                "uploaded_at": uploaded_at,
                "status": info["status"]
            })

        return {"files": files_list}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing files: {str(e)}")

@app.get("/api/financial/reports")
async def list_generated_reports():
    """List all generated reports"""
    try:
        reports_list = []
        for report_id, info in generated_reports.items():
            generated_at = info["generated_at"]
            if isinstance(generated_at, datetime):
                generated_at = generated_at.isoformat()

            reports_list.append({
                "report_id": report_id,
                "file_id": info["file_id"],
                "generated_at": generated_at,
                "status": info["status"]
            })

        return {"reports": reports_list}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing reports: {str(e)}")

@app.delete("/api/financial/file/{file_id}")
async def delete_uploaded_file(file_id: str):
    """Delete an uploaded file"""
    if file_id not in uploaded_files:
        raise HTTPException(status_code=404, detail="File not found")

    try:
        file_info = uploaded_files[file_id]
        # Remove file from disk
        if os.path.exists(file_info["file_path"]):
            os.remove(file_info["file_path"])

        # Remove from memory
        del uploaded_files[file_id]

        return {"message": "File deleted successfully", "file_id": file_id}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting file: {str(e)}")

# New agent endpoints
class ChatMessage(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    timestamp: str

@app.post("/api/agent/chat", response_model=ChatResponse)
async def chat_with_agent(chat_message: ChatMessage):
    """
    Chat with the financial report agent
    """
    try:
        if not financial_agent:
            raise HTTPException(status_code=500, detail="Agent not initialized")

        response = await financial_agent.process_message(chat_message.message)

        return ChatResponse(
            response=response,
            timestamp=datetime.now().isoformat()
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")

@app.get("/api/agent/conversation")
async def get_conversation_history():
    """
    Get the conversation history with the agent
    """
    try:
        if not financial_agent:
            raise HTTPException(status_code=500, detail="Agent not initialized")

        return {
            "conversation": financial_agent.get_conversation_history()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving conversation: {str(e)}")

@app.post("/api/agent/clear")
async def clear_conversation():
    """
    Clear the conversation history
    """
    try:
        if not financial_agent:
            raise HTTPException(status_code=500, detail="Agent not initialized")

        financial_agent.clear_conversation()

        return {"message": "Conversation history cleared"}

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
            "count": len(financial_agent.available_files)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing files: {str(e)}")
