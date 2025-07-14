#!/usr/bin/env python3
"""
Financial Report Agent
This agent handles chat interactions and can generate financial reports
by utilizing the financial_report_llm_demo.py functionality.
"""

import os
import json
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
import pandas as pd

from financial_report_llm_demo import (
    setup_environment,
    load_financial_data,
    load_financial_indicators,
    generate_financial_report,
    extract_simple_table,
    extract_structured_tables
)

class FinancialReportAgent:
    """
    Agent that can chat with users and generate financial reports
    """

    def __init__(self):
        self.client = None
        self.conversation_history = []
        self.available_files = []
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
        """Scan for available Excel files in the input directory"""
        input_dir = Path("input")
        if input_dir.exists():
            excel_files = list(input_dir.glob("*.xlsx")) + list(input_dir.glob("*.xls"))
            self.available_files = [f.name for f in excel_files]
        else:
            self.available_files = []

    def get_agent_persona(self) -> str:
        """Define the agent's personality and capabilities"""
        return """You are a Financial Report Assistant AI agent. Your capabilities include:

1. **Financial Analysis**: I can analyze Excel files containing financial data and generate comprehensive reports
2. **Report Generation**: I create professional financial reports with Balance Sheet, Income Statement, and Cash Flow analysis
3. **Data Interpretation**: I can explain financial metrics and provide insights from your data
4. **File Management**: I can work with Excel files in your input directory

Available commands:
- "generate report" or "create financial report" - I'll analyze your financial data
- "list files" - Show available Excel files
- "help" - Show what I can do
- Ask me questions about financial analysis or accounting

I'm here to help you with your financial reporting needs!"""

    def detect_intent(self, message: str) -> str:
        """Detect user intent from the message"""
        message_lower = message.lower()

        # Financial report generation intents
        report_keywords = [
            "generate report", "create report", "financial report",
            "accounting report", "analyze data", "generate analysis",
            "create financial analysis", "run analysis", "process data"
        ]

        # File management intents
        file_keywords = ["list files", "show files", "available files", "what files"]

        # Help intents
        help_keywords = ["help", "what can you do", "capabilities", "commands"]

        if any(keyword in message_lower for keyword in report_keywords):
            return "generate_report"
        elif any(keyword in message_lower for keyword in file_keywords):
            return "list_files"
        elif any(keyword in message_lower for keyword in help_keywords):
            return "help"
        else:
            return "chat"

    def list_available_files(self) -> str:
        """List available Excel files"""
        if not self.available_files:
            return "❌ No Excel files found in the input directory. Please upload an Excel file to the input/ folder."

        files_list = "📁 Available Excel files:\n"
        for i, file in enumerate(self.available_files, 1):
            files_list += f"{i}. {file}\n"

        return files_list

    def select_file_for_analysis(self, message: str) -> Optional[str]:
        """Select which file to analyze based on user input or default"""
        # If user mentions a specific file
        for file in self.available_files:
            if file.lower() in message.lower():
                return file

        # Default to demo_data.xlsx if available
        if "demo_data.xlsx" in self.available_files:
            return "demo_data.xlsx"

        # Otherwise, use the first available file
        if self.available_files:
            return self.available_files[0]

        return None

    async def generate_financial_report_async(self, filename: str) -> Dict[str, Any]:
        """Generate financial report asynchronously"""
        try:
            # Load financial data
            file_path = f"input/{filename}"
            if not Path(file_path).exists():
                return {
                    "success": False,
                    "error": f"File {filename} not found in input directory"
                }

            df = load_financial_data(file_path)

            # Load financial indicators
            balance_str, income_str, cf_str = load_financial_indicators()

            # Generate report using OpenAI
            report_text = generate_financial_report(self.client, df, balance_str, income_str, cf_str)

            # Extract tables with error handling
            simple_table = None
            structured_tables = None

            try:
                simple_table = extract_simple_table(report_text)
            except Exception as e:
                print(f"⚠️ Warning: Could not extract simple table: {e}")

            try:
                structured_tables = extract_structured_tables(report_text)
            except Exception as e:
                print(f"⚠️ Warning: Could not extract structured tables: {e}")

            # Generate timestamp for the report
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            return {
                "success": True,
                "filename": filename,
                "report_text": report_text,
                "simple_table": simple_table,
                "structured_tables": structured_tables,
                "timestamp": timestamp,
                "data_shape": df.shape,
                "data_columns": df.columns.tolist()
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def format_report_summary(self, report_data: Dict[str, Any]) -> str:
        """Format the report data into a chat-friendly summary"""
        if not report_data["success"]:
            return f"❌ Failed to generate report: {report_data['error']}"

        summary = f"""✅ **Financial Report Generated Successfully!**

📊 **Analysis Summary:**
- **File analyzed**: {report_data['filename']}
- **Data size**: {report_data['data_shape'][0]} rows × {report_data['data_shape'][1]} columns
- **Generated at**: {report_data['timestamp']}

📝 **Report Preview:**
{report_data['report_text'][:500]}...

📁 **Output Files Created:**
- `output/financial_summary.xlsx` - Summary table
- `output/financial_statements_from_gpt.xlsx` - Detailed financial statements

💡 **Next Steps:**
- Check the output directory for your Excel files
- Use the API to export specific reports
- Ask me questions about the analysis results
"""
        return summary

    async def process_message(self, message: str) -> str:
        """Process user message and return response"""
        # Add message to conversation history
        self.conversation_history.append({
            "role": "user",
            "content": message,
            "timestamp": datetime.now().isoformat()
        })

        # Detect intent
        intent = self.detect_intent(message)

        if intent == "generate_report":
            # Check if files are available
            if not self.available_files:
                response = "�� No Excel files found. Please upload an Excel file to the input/ directory first."
            else:
                # Select file for analysis
                selected_file = self.select_file_for_analysis(message)

                if selected_file:
                    response = f"🔄 Generating financial report for {selected_file}...\n"
                    response += "⏳ This may take 30-60 seconds while I analyze your data with GPT.\n\n"

                    # Generate report
                    report_data = await self.generate_financial_report_async(selected_file)
                    response += self.format_report_summary(report_data)
                else:
                    response = "❌ Could not select a file for analysis. Please specify which file to analyze."

        elif intent == "list_files":
            response = self.list_available_files()

        elif intent == "help":
            response = self.get_agent_persona()

        else:
            # General chat using OpenAI
            response = await self.chat_with_context(message)

        # Add response to conversation history
        self.conversation_history.append({
            "role": "assistant",
            "content": response,
            "timestamp": datetime.now().isoformat()
        })

        return response

    async def chat_with_context(self, message: str) -> str:
        """Handle general chat with context about financial reporting"""
        try:
            # Build context with recent conversation
            context_messages = [
                {
                    "role": "system",
                    "content": f"""You are a helpful Financial Report Assistant. {self.get_agent_persona()}
                    
Available files in input directory: {', '.join(self.available_files) if self.available_files else 'None'}

Keep responses concise but helpful. If users ask about generating reports, guide them to use commands like 'generate report' or 'create financial report'."""
                }
            ]

            # Add recent conversation history (last 5 messages)
            recent_history = self.conversation_history[-10:] if len(self.conversation_history) > 10 else self.conversation_history
            for msg in recent_history:
                context_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

            # Add current message
            context_messages.append({
                "role": "user",
                "content": message
            })

            # Call OpenAI
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=context_messages,
                max_tokens=500,
                temperature=0.7
            )

            return response.choices[0].message.content

        except Exception as e:
            return f"❌ Sorry, I encountered an error: {str(e)}. Please try again or ask for help."

    def get_conversation_history(self) -> List[Dict]:
        """Get the conversation history"""
        return self.conversation_history

    def clear_conversation(self):
        """Clear the conversation history"""
        self.conversation_history = []
        print("🔄 Conversation history cleared")

# Example usage and testing
async def main():
    """Test the agent functionality"""
    agent = FinancialReportAgent()

    print("🤖 Financial Report Agent Test")
    print("Type 'quit' to exit")
    print("="*50)

    while True:
        try:
            user_input = input("\n👤 You: ")
            if user_input.lower() in ['quit', 'exit', 'q']:
                break

            response = await agent.process_message(user_input)
            print(f"\n🤖 Agent: {response}")

        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
