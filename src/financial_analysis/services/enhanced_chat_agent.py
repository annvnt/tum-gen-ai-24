"""
EnhancedChatAgent - Advanced chat interface with file context and knowledge base
Provides intelligent file selection, context-aware responses, and PDF generation
"""

import json
import uuid
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import logging

from .chat_file_manager import ChatFileManager
from .pdf_generator import FinancialPDFGenerator
from .financial_agent import FinancialReportAgent
from ..storage.database_manager import db_manager


logger = logging.getLogger(__name__)


class EnhancedChatAgent:
    """Enhanced chat agent with file context and knowledge base"""
    
    def __init__(self):
        """Initialize enhanced chat agent"""
        self.file_manager = ChatFileManager()
        self.pdf_generator = FinancialPDFGenerator()
        self.base_agent = FinancialReportAgent()
        
        # Session management
        self.active_sessions = {}
        self.max_sessions = 100
    
    async def process_message(self, 
                            message: str,
                            session_id: str,
                            context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process chat message with enhanced context
        
        Args:
            message: User message
            session_id: Session identifier
            context: Additional context (file_ids, preferences, etc.)
            
        Returns:
            Response with analysis and file context
        """
        try:
            # Get or create session
            session = self._get_session(session_id)
            
            # Extract file context from message
            file_context = await self._extract_file_context(message, context)
            
            # Process with enhanced context
            response = await self._generate_response(message, file_context, session)
            
            # Update session
            self._update_session(session, message, response, file_context)
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return {
                'response': f"I encountered an error processing your request: {str(e)}",
                'session_id': session_id,
                'status': 'error'
            }
    
    async def _extract_file_context(self, 
                                  message: str,
                                  context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract relevant file context from message and context"""
        file_context = {
            'explicit_files': [],
            'suggested_files': [],
            'auto_selected': [],
            'search_results': []
        }
        
        # Check for explicit file references
        explicit_files = self._extract_file_references(message)
        file_context['explicit_files'] = explicit_files
        
        # Check context for file IDs
        if context and 'file_ids' in context:
            file_context['explicit_files'].extend(context['file_ids'])
        
        # Auto-select files if none specified
        if not file_context['explicit_files']:
            suggested = self.file_manager.auto_select_files(
                context=message,
                max_files=3,
                criteria=context.get('selection_criteria') if context else None
            )
            file_context['auto_selected'] = suggested
        
        # Search for files if requested
        if self._is_search_request(message):
            search_query = self._extract_search_query(message)
            search_results = self.file_manager.search_files(
                query=search_query,
                search_type="semantic",
                limit=5
            )
            file_context['search_results'] = search_results
        
        return file_context
    
    async def _generate_response(self, 
                               message: str,
                               file_context: Dict[str, Any],
                               session: Dict[str, Any]) -> Dict[str, Any]:
        """Generate response based on message and file context"""
        
        # Determine response type
        if self._is_report_request(message):
            return await self._handle_report_request(message, file_context, session)
        elif self._is_analysis_request(message):
            return await self._handle_analysis_request(message, file_context, session)
        elif self._is_file_list_request(message):
            return await self._handle_file_list_request(message, file_context, session)
        elif self._is_search_request(message):
            return await self._handle_search_request(message, file_context, session)
        else:
            return await self._handle_general_chat(message, file_context, session)
    
    async def _handle_report_request(self, 
                                   message: str,
                                   file_context: Dict[str, Any],
                                   session: Dict[str, Any]) -> Dict[str, Any]:
        """Handle PDF report generation requests"""
        
        # Determine files to include
        files_to_include = file_context['explicit_files'] or [
            f['id'] for f in file_context['auto_selected']
        ]
        
        if not files_to_include:
            return {
                'response': "I don't see any files to generate a report from. Please upload some financial documents first, or specify which files you'd like to include.",
                'session_id': session['id'],
                'status': 'needs_files',
                'available_files': await self._get_available_files_summary()
            }
        
        # Extract report configuration
        report_config = self._extract_report_config(message)
        
        try:
            # Generate PDF report
            report_result = await self.pdf_generator.generate_custom_report(
                report_config=report_config,
                file_ids=files_to_include
            )
            
            return {
                'response': f"I've generated a comprehensive financial report for you. The report includes analysis of {len(files_to_include)} file(s) and is ready for download.",
                'session_id': session['id'],
                'status': 'report_generated',
                'report_id': report_result['report_id'],
                'download_url': report_result['download_url'],
                'files_included': files_to_include
            }
            
        except Exception as e:
            return {
                'response': f"I encountered an error generating the report: {str(e)}",
                'session_id': session['id'],
                'status': 'error'
            }
    
    async def _handle_analysis_request(self, 
                                     message: str,
                                     file_context: Dict[str, Any],
                                     session: Dict[str, Any]) -> Dict[str, Any]:
        """Handle financial analysis requests"""
        
        files_to_analyze = file_context['explicit_files'] or [
            f['id'] for f in file_context['auto_selected']
        ]
        
        if not files_to_analyze:
            return {
                'response': "I need some files to analyze. Please specify which files you'd like me to analyze, or let me help you find relevant ones.",
                'session_id': session['id'],
                'status': 'needs_files',
                'suggested_files': file_context['auto_selected']
            }
        
        # Perform analysis for each file
        analysis_results = []
        for file_id in files_to_analyze:
            try:
                file_info = self.file_manager.get_file_context(file_id)
                analysis = await self.base_agent.analyze_document(file_id)
                analysis_results.append({
                    'file_id': file_id,
                    'filename': file_info.get('file_info', {}).get('filename', ''),
                    'analysis': analysis
                })
            except Exception as e:
                analysis_results.append({
                    'file_id': file_id,
                    'error': str(e)
                })
        
        # Generate summary response
        response_text = self._format_analysis_response(analysis_results, message)
        
        return {
            'response': response_text,
            'session_id': session['id'],
            'status': 'analysis_complete',
            'analysis_results': analysis_results,
            'files_analyzed': files_to_analyze
        }
    
    async def _handle_file_list_request(self, 
                                      message: str,
                                      file_context: Dict[str, Any],
                                      session: Dict[str, Any]) -> Dict[str, Any]:
        """Handle requests for file listings"""
        
        available_files = self.file_manager.get_available_files(limit=20)
        
        if not available_files:
            return {
                'response': "I don't see any uploaded files yet. Please upload some financial documents to get started.",
                'session_id': session['id'],
                'status': 'no_files'
            }
        
        # Format file list
        file_summary = []
        for file_info in available_files:
            file_summary.append({
                'id': file_info['id'],
                'filename': file_info['filename'],
                'uploaded_at': file_info['uploaded_at'],
                'vector_processed': file_info.get('vector_processed', False),
                'size_category': file_info.get('size_category', 'unknown')
            })
        
        response_text = f"I found {len(available_files)} file(s) available for analysis:\n\n"
        for file_info in file_summary:
            processed_status = "✅ processed" if file_info['vector_processed'] else "⏳ not processed"
            response_text += f"• {file_info['filename']} ({processed_status})\n"
        
        return {
            'response': response_text,
            'session_id': session['id'],
            'status': 'file_list',
            'files': file_summary
        }
    
    async def _handle_search_request(self, 
                                   message: str,
                                   file_context: Dict[str, Any],
                                   session: Dict[str, Any]) -> Dict[str, Any]:
        """Handle file search requests"""
        
        search_query = self._extract_search_query(message)
        search_results = file_context['search_results']
        
        if not search_results:
            return {
                'response': f"I couldn't find any files matching '{search_query}'. Try different keywords or upload new files.",
                'session_id': session['id'],
                'status': 'no_results',
                'query': search_query
            }
        
        # Format search results
        response_text = f"I found {len(search_results)} file(s) matching '{search_query}':\n\n"
        for i, result in enumerate(search_results, 1):
            score = result.get('relevance_score', 0)
            filename = result['filename']
            response_text += f"{i}. {filename} (relevance: {score:.2f})\n"
        
        return {
            'response': response_text,
            'session_id': session['id'],
            'status': 'search_results',
            'query': search_query,
            'results': search_results
        }
    
    async def _handle_general_chat(self, 
                                 message: str,
                                 file_context: Dict[str, Any],
                                 session: Dict[str, Any]) -> Dict[str, Any]:
        """Handle general chat messages with file context"""
        
        # Use base agent for general conversation
        base_response = await self.base_agent.process_message(message)
        
        # Enhance with file context
        context_info = ""
        if file_context['auto_selected']:
            context_info = f"\n\nI'm aware of {len(file_context['auto_selected'])} file(s) that might be relevant to your question."
        
        enhanced_response = base_response + context_info
        
        return {
            'response': enhanced_response,
            'session_id': session['id'],
            'status': 'chat_response',
            'context_files': file_context['auto_selected']
        }
    
    def _extract_file_references(self, message: str) -> List[str]:
        """Extract file IDs or names from message"""
        import re
        
        # Look for file IDs (UUID format)
        uuid_pattern = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
        file_ids = re.findall(uuid_pattern, message, re.IGNORECASE)
        
        # Look for filenames
        filename_patterns = [
            r'"([^"]*\.xlsx?)"',
            r'"([^"]*\.csv)"',
            r'file\s+([^.]*\.xlsx?)',
            r'document\s+([^.]*\.xlsx?)'
        ]
        
        filenames = []
        for pattern in filename_patterns:
            matches = re.findall(pattern, message, re.IGNORECASE)
            filenames.extend(matches)
        
        # Convert filenames to IDs if possible
        for filename in filenames:
            file_info = db_manager.get_uploaded_file_by_filename(filename)
            if file_info:
                file_ids.append(file_info['id'])
        
        return list(set(file_ids))  # Remove duplicates
    
    def _is_report_request(self, message: str) -> bool:
        """Check if message is requesting a report"""
        keywords = [
            'generate report', 'create report', 'pdf report', 'download report',
            'export as pdf', 'financial report', 'analysis report'
        ]
        return any(keyword in message.lower() for keyword in keywords)
    
    def _is_analysis_request(self, message: str) -> bool:
        """Check if message is requesting analysis"""
        keywords = [
            'analyze', 'analysis', 'examine', 'review', 'evaluate',
            'calculate ratios', 'financial health', 'performance'
        ]
        return any(keyword in message.lower() for keyword in keywords)
    
    def _is_file_list_request(self, message: str) -> bool:
        """Check if message is requesting file list"""
        keywords = [
            'list files', 'show files', 'available files', 'uploaded files',
            'what files', 'which files', 'files available'
        ]
        return any(keyword in message.lower() for keyword in keywords)
    
    def _is_search_request(self, message: str) -> bool:
        """Check if message is requesting file search"""
        keywords = [
            'search files', 'find files', 'look for', 'search for',
            'find document', 'find report', 'search documents'
        ]
        return any(keyword in message.lower() for keyword in keywords)
    
    def _extract_search_query(self, message: str) -> str:
        """Extract search query from message"""
        # Remove search keywords
        keywords = [
            'search files', 'find files', 'look for', 'search for',
            'find document', 'find report', 'search documents',
            'files about', 'documents about', 'reports about'
        ]
        
        query = message.lower()
        for keyword in keywords:
            query = query.replace(keyword, '')
        
        # Remove extra whitespace
        query = ' '.join(query.split())
        return query.strip()
    
    def _extract_report_config(self, message: str) -> Dict[str, Any]:
        """Extract report configuration from message"""
        config = {
            'format': 'pdf',
            'template': 'comprehensive',
            'sections': None
        }
        
        # Check for template preferences
        if 'executive summary' in message.lower():
            config['template'] = 'executive'
        elif 'ratios only' in message.lower():
            config['template'] = 'ratios_only'
        
        return config
    
    def _format_analysis_response(self, 
                                analysis_results: List[Dict[str, Any]],
                                original_message: str) -> str:
        """Format analysis results into readable response"""
        
        if not analysis_results:
            return "I couldn't analyze any of the specified files."
        
        response = "Here's my analysis:\n\n"
        
        for result in analysis_results:
            if 'error' in result:
                response += f"❌ **{result.get('filename', 'File')}**: {result['error']}\n"
            else:
                filename = result['filename']
                analysis = result['analysis']
                
                response += f"📊 **{filename}**:\n"
                if isinstance(analysis, dict) and 'summary' in analysis:
                    response += f"{analysis['summary']}\n"
                else:
                    response += str(analysis) + "\n"
                response += "\n"
        
        return response
    
    async def _get_available_files_summary(self) -> List[Dict[str, Any]]:
        """Get summary of available files"""
        files = self.file_manager.get_available_files(limit=10)
        return [
            {
                'id': f['id'],
                'filename': f['filename'],
                'uploaded_at': f['uploaded_at']
            }
            for f in files
        ]
    
    def _get_session(self, session_id: str) -> Dict[str, Any]:
        """Get or create session"""
        if session_id not in self.active_sessions:
            # Clean old sessions if needed
            if len(self.active_sessions) >= self.max_sessions:
                oldest = min(self.active_sessions.keys(), 
                           key=lambda k: self.active_sessions[k]['last_activity'])
                del self.active_sessions[oldest]
            
            self.active_sessions[session_id] = {
                'id': session_id,
                'created_at': datetime.utcnow(),
                'last_activity': datetime.utcnow(),
                'conversation_history': [],
                'active_files': [],
                'preferences': {}
            }
        
        self.active_sessions[session_id]['last_activity'] = datetime.utcnow()
        return self.active_sessions[session_id]
    
    def _update_session(self, 
                       session: Dict[str, Any],
                       message: str,
                       response: Dict[str, Any],
                       file_context: Dict[str, Any]) -> None:
        """Update session with new interaction"""
        session['conversation_history'].append({
            'timestamp': datetime.utcnow().isoformat(),
            'message': message,
            'response': response['response'],
            'status': response['status'],
            'file_context': file_context
        })
        
        # Update active files
        all_files = (
            file_context['explicit_files'] +
            [f['id'] for f in file_context['auto_selected']]
        )
        session['active_files'] = list(set(session['active_files'] + all_files))
    
    async def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get summary of session activity"""
        if session_id not in self.active_sessions:
            return {'error': 'Session not found'}
        
        session = self.active_sessions[session_id]
        return {
            'session_id': session_id,
            'created_at': session['created_at'],
            'last_activity': session['last_activity'],
            'message_count': len(session['conversation_history']),
            'active_files': session['active_files'],
            'recent_interactions': session['conversation_history'][-5:]
        }
    
    async def clear_session(self, session_id: str) -> Dict[str, Any]:
        """Clear session history"""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            return {'success': True, 'message': 'Session cleared'}
        return {'error': 'Session not found'}
    
    async def get_available_templates(self) -> List[Dict[str, Any]]:
        """Get available report templates"""
        return self.pdf_generator.get_report_template_options()