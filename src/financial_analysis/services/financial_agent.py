#!/usr/bin/env python3
"""
Financial Report Agent
This agent handles chat interactions and can generate financial reports
by utilizing the financial_report_llm_demo.py functionality.
"""

import os
import json
import asyncio
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
import pandas as pd

from ..core.financial_analyzer import (
    setup_environment,
    load_financial_data,
    load_financial_indicators,
    generate_financial_report,
    extract_simple_table,
    extract_structured_tables
)

# Import database manager
from ..storage.database_manager import db_manager

class FinancialReportAgent:
    """
    Agent that can chat with users and generate financial reports
    """

    def __init__(self):
        self.client = None
        self.conversation_history = []
        self.available_files = []
        self.current_session_id = str(uuid.uuid4())
        self.initialize_agent()

    def initialize_agent(self):
        """Initialize the agent with OpenAI client"""
        try:
            self.client = setup_environment()
            self.scan_available_files()
            print("✅ Financial Report Agent initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize agent: {str(e)}")
            raise

    def scan_available_files(self):
        """Scan for available Excel files in the input directory and database"""
        # Scan input directory
        input_dir = Path("input")
        local_files = []
        if input_dir.exists():
            excel_files = list(input_dir.glob("*.xlsx")) + list(input_dir.glob("*.xls"))
            local_files = [f.name for f in excel_files]

        # Get uploaded files from database
        uploaded_files = db_manager.list_uploaded_files()

        # Combine both sources
        self.available_files = {
            "local_files": local_files,
            "uploaded_files": uploaded_files
        }

    def get_document_context(self, user_message: str) -> List[str]:
        """
        Analyze user message to determine which documents might be relevant
        Returns list of document IDs that should be used as context
        """
        # Simple keyword matching for now - could be enhanced with embeddings
        relevant_docs = []

        # Check if user mentions specific filenames
        uploaded_files = db_manager.list_uploaded_files()
        for file_info in uploaded_files:
            filename = file_info["filename"].lower()
            if filename.replace(".xlsx", "").replace(".xls", "") in user_message.lower():
                relevant_docs.append(file_info["file_id"])

        # If no specific files mentioned, use the most recent ones
        if not relevant_docs and uploaded_files:
            # Use the 3 most recent files as context
            relevant_docs = [f["file_id"] for f in uploaded_files[:3]]

        return relevant_docs

    async def process_message(self, user_message: str) -> str:
        """
        Process user message and generate response
        Stores conversation in database
        """
        try:
            # Get relevant document context
            context_docs = self.get_document_context(user_message)

            # Build context from uploaded documents
            document_context = ""
            if context_docs:
                document_context = self.build_document_context(context_docs)

            # Create system prompt with context
            system_prompt = f"""You are a financial report analysis assistant. You can help users analyze financial data, generate reports, and answer questions about uploaded financial documents.

Available capabilities:
1. Analyze financial data from uploaded Excel files
2. Generate comprehensive financial reports
3. Answer questions about financial metrics and indicators
4. Provide insights and recommendations

{document_context}

Please provide helpful, accurate financial analysis and be specific about which documents you're referencing when possible."""

            # Build conversation context
            conversation_context = []
            for msg in self.conversation_history[-10:]:  # Last 10 messages
                conversation_context.append({"role": "user", "content": msg["user"]})
                conversation_context.append({"role": "assistant", "content": msg["assistant"]})

            # Generate response
            messages = [
                {"role": "system", "content": system_prompt},
                *conversation_context,
                {"role": "user", "content": user_message}
            ]

            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                max_tokens=2000,
                temperature=0.7
            )

            assistant_response = response.choices[0].message.content

            # Store conversation in memory
            self.conversation_history.append({
                "user": user_message,
                "assistant": assistant_response,
                "timestamp": datetime.now().isoformat(),
                "context_docs": context_docs
            })

            # Store in database
            db_manager.save_chat_message(
                session_id=self.current_session_id,
                user_message=user_message,
                bot_response=assistant_response,
                context_documents=context_docs
            )

            return assistant_response

        except Exception as e:
            error_msg = f"Error processing message: {str(e)}"
            print(error_msg)
            return error_msg

    def build_document_context(self, document_ids: List[str]) -> str:
        """
        Build context string from document IDs
        """
        context_parts = []

        for doc_id in document_ids:
            doc_info = db_manager.get_uploaded_file(doc_id)
            if doc_info:
                # Add basic file info
                context_parts.append(f"Document: {doc_info['filename']} (ID: {doc_id})")

                try:
                    # Load and analyze the actual file content
                    file_path = doc_info['file_path']
                    if os.path.exists(file_path):
                        # Load the Excel file data
                        df = load_financial_data(file_path)

                        # Add data summary to context
                        context_parts.append(f"  - File contains {len(df)} rows and {len(df.columns)} columns")
                        context_parts.append(f"  - Columns: {', '.join(df.columns.tolist())}")

                        # Add sample data (first few rows)
                        sample_data = df.head(5).to_string()
                        context_parts.append(f"  - Sample data:\n{sample_data}")

                        # Add basic statistics
                        numeric_columns = df.select_dtypes(include=['number']).columns
                        if len(numeric_columns) > 0:
                            context_parts.append(f"  - Numeric columns: {', '.join(numeric_columns)}")

                            # Add summary statistics for key columns
                            stats_summary = df[numeric_columns].describe().to_string()
                            context_parts.append(f"  - Statistical summary:\n{stats_summary}")

                    else:
                        context_parts.append(f"  - Warning: File path not found: {file_path}")

                except Exception as e:
                    context_parts.append(f"  - Error loading file data: {str(e)}")

                # Try to get extracted data if available
                doc_record = db_manager.get_uploaded_document(doc_id)
                if doc_record and doc_record.extracted_data:
                    context_parts.append(f"  - Extracted data preview: {str(doc_record.extracted_data)[:200]}...")

                # Get related reports
                reports = db_manager.get_reports_for_document(doc_id)
                if reports:
                    context_parts.append(f"  - {len(reports)} analysis reports available")

        if context_parts:
            return f"\nCurrent document context:\n" + "\n".join(context_parts) + "\n"

        return ""

    def get_conversation_history(self) -> List[Dict]:
        """Get conversation history for current session"""
        return self.conversation_history

    def clear_conversation(self):
        """Clear conversation history and start new session"""
        self.conversation_history = []
        self.current_session_id = str(uuid.uuid4())

    def get_database_chat_history(self, session_id: str = None) -> List[Dict]:
        """Get chat history from database"""
        if session_id is None:
            session_id = self.current_session_id

        chat_history = db_manager.get_chat_history(session_id)
        return [
            {
                "user_message": chat.user_message,
                "bot_response": chat.bot_response,
                "timestamp": chat.timestamp.isoformat(),
                "document_id": chat.document_id,
                "context_documents": chat.context_documents
            }
            for chat in chat_history
        ]

    async def analyze_document(self, file_id: str) -> Dict[str, Any]:
        """
        Analyze a specific document and generate report
        """
        try:
            # Get file info from database
            file_info = db_manager.get_uploaded_file(file_id)
            if not file_info:
                return {"error": "File not found"}

            file_path = file_info["file_path"]

            # Load and analyze the financial data
            df = load_financial_data(file_path)
            balance_str, income_str, cf_str = load_financial_indicators()

            # Generate comprehensive report
            report_text = generate_financial_report(self.client, df, balance_str, income_str, cf_str)

            # Extract structured data
            simple_table = extract_simple_table(report_text)
            structured_tables = extract_structured_tables(report_text)

            # Prepare response
            analysis_result = {
                "file_id": file_id,
                "filename": file_info["filename"],
                "analysis_summary": report_text,
                "tables": {},
                "generated_at": datetime.now().isoformat()
            }

            # Add tables to response
            if simple_table is not None:
                analysis_result["tables"]["summary"] = simple_table.to_dict(orient="records")

            if structured_tables:
                for table_name, table_df in structured_tables.items():
                    analysis_result["tables"][table_name] = table_df.to_dict(orient="records")

            # Store analysis in database
            db_manager.save_generated_report(
                document_id=file_id,
                report_type="agent_analysis",
                summary=report_text,
                tables=analysis_result["tables"],
                model_used="gpt-4o"
            )

            return analysis_result

        except Exception as e:
            return {"error": f"Error analyzing document: {str(e)}"}

    def get_available_documents(self) -> Dict[str, Any]:
        """
        Get list of available documents for analysis
        """
        return {
            "uploaded_files": db_manager.list_uploaded_files(),
            "generated_reports": db_manager.list_generated_reports(),
            "session_id": self.current_session_id
        }
