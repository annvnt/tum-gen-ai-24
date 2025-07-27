"""
Simple PDF Generator MVP - Uses existing financial statement generators directly
Bypasses broken database lookup and uses analysis data directly
"""

import os
import tempfile
from datetime import datetime
from typing import Dict, Any
import logging

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib import colors

from ..core.financial_analyzer import FinancialAnalyzer
from ..storage.gcs_client import GCSClient

logger = logging.getLogger(__name__)

class SimplePDFGenerator:
    """MVP PDF generator that uses existing financial analysis data"""
    
    def __init__(self):
        self.gcs_client = GCSClient()
        self.analyzer = FinancialAnalyzer()
        
        # Basic styles
        self.styles = getSampleStyleSheet()
        self.styles.add(ParagraphStyle(
            'FinancialTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=1,  # Center
            textColor=colors.darkblue
        ))
        self.styles.add(ParagraphStyle(
            'SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=16,
            spaceAfter=12,
            textColor=colors.darkgreen
        ))
    
    async def generate_simple_pdf(self, file_id: str, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate PDF directly from analysis data"""
        try:
            logger.info(f"Starting simple PDF generation for file: {file_id}")
            
            # Step 1: Get file info
            from ..storage.database_manager import db_manager
            file_info = db_manager.get_uploaded_file(file_id)
            if not file_info:
                raise ValueError(f"File {file_id} not found")
            
            # Step 2: Create PDF
            pdf_path = await self._create_simple_pdf(file_info, analysis_data)
            
            # Step 3: Upload to GCS
            pdf_url = await self._upload_pdf_to_gcs(pdf_path, file_id)
            
            return {
                'pdf_url': pdf_url,
                'file_id': file_id,
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in simple PDF generation: {e}")
            raise
    
    async def _create_simple_pdf(self, file_info: Dict[str, Any], analysis_data: Dict[str, Any]) -> str:
        """Create basic PDF with financial analysis"""
        
        temp_dir = tempfile.mkdtemp()
        pdf_path = os.path.join(temp_dir, f"report_{file_info['file_id']}.pdf")
        
        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        story = []
        
        # Title page
        story.append(Paragraph("Financial Analysis Report", self.styles['FinancialTitle']))
        story.append(Paragraph(f"Source: {file_info['filename']}", self.styles['Heading2']))
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y')}", 
                             self.styles['Normal']))
        story.append(PageBreak())
        
        # Analysis content
        if 'summary' in analysis_data:
            story.append(Paragraph("Executive Summary", self.styles['SectionHeader']))
            story.append(Paragraph(analysis_data['summary'], self.styles['Normal']))
            story.append(PageBreak())
        
        # Financial tables
        if 'tables' in analysis_data:
            story.append(Paragraph("Financial Statements", self.styles['SectionHeader']))
            
            # Balance Sheet
            if 'balance_sheet' in analysis_data['tables']:
                story.append(Paragraph("Balance Sheet", self.styles['Heading2']))
                story.append(Paragraph("Balance sheet data will be displayed here", 
                                     self.styles['Normal']))
            
            # Income Statement  
            if 'income_statement' in analysis_data['tables']:
                story.append(Paragraph("Income Statement", self.styles['Heading2']))
                story.append(Paragraph("Income statement data will be displayed here", 
                                     self.styles['Normal']))
        
        doc.build(story)
        return pdf_path
    
    async def _upload_pdf_to_gcs(self, pdf_path: str, file_id: str) -> str:
        """Upload PDF to GCS"""
        try:
            with open(pdf_path, 'rb') as f:
                blob_name = f"reports/{file_id}/financial_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                gcs_url = await self.gcs_client.upload_file(f, blob_name, 'application/pdf')
                return gcs_url
        except Exception as e:
            logger.error(f"Error uploading PDF: {e}")
            raise
