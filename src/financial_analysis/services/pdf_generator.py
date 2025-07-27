"""
PDFGenerator - Professional PDF report generation for financial analysis
Creates comprehensive accounting reports with charts, tables, and analysis
"""

import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from decimal import Decimal
import logging

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.backends.backend_pdf import PdfPages
import pandas as pd
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, 
    PageBreak, Image, KeepTogether
)
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.graphics.shapes import Drawing, String
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.linecharts import LineChart
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.widgets.markers import makeMarker

from ..storage.database_manager import db_manager
from ..storage.gcs_client import GCSClient
from .document_storage import GCSMetadataManager
from ..security.input_validator import InputValidator
from ..security.path_sanitizer import PathSanitizer


logger = logging.getLogger(__name__)


class FinancialPDFGenerator:
    """Professional PDF generator for financial reports"""
    
    def __init__(self):
        """Initialize PDF generator"""
        self.gcs_manager = GCSMetadataManager()
        self.gcs_client = GCSClient()
        
        # ReportLab styles
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom styles for financial reports"""
        self.styles.add(ParagraphStyle(
            name='FinancialTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        ))
        
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=16,
            spaceAfter=12,
            textColor=colors.darkgreen
        ))
        
        self.styles.add(ParagraphStyle(
            name='FinancialData',
            parent=self.styles['Normal'],
            fontSize=10,
            fontName='Helvetica',
            alignment=TA_RIGHT
        ))
        
        self.styles.add(ParagraphStyle(
            name='TableHeader',
            parent=self.styles['Normal'],
            fontSize=10,
            fontName='Helvetica-Bold',
            textColor=colors.whitesmoke,
            alignment=TA_CENTER
        ))
    
    async def generate_comprehensive_report(self, 
                                          report_id: str,
                                          file_id: str,
                                          analysis_data: Dict[str, Any],
                                          output_format: str = "pdf") -> Dict[str, Any]:
        """
        Generate comprehensive financial report as PDF
        
        Args:
            report_id: Report ID for tracking
            file_id: Source file ID
            analysis_data: Financial analysis data
            output_format: "pdf" or "excel"
            
        Returns:
            Dictionary with report metadata and download links
        """
        try:
            # Validate inputs
            if not InputValidator.validate_uuid(report_id):
                raise ValueError("Invalid report ID format")
            
            if not InputValidator.validate_uuid(file_id):
                raise ValueError("Invalid file ID format")
            
            if output_format not in ["pdf", "excel"]:
                raise ValueError("Invalid output format")
            
            # Validate analysis_data
            if not isinstance(analysis_data, dict):
                raise ValueError("Analysis data must be a dictionary")
            
            # Sanitize analysis data
            analysis_data = InputValidator.sanitize_dict_values(analysis_data)
            
            # Get file information
            file_info = db_manager.get_uploaded_file(file_id)
            if not file_info:
                raise ValueError(f"File {file_id} not found")
            
            # Validate file info
            if not file_info.get('filename') or not file_info.get('file_path'):
                raise ValueError("Invalid file information")
            
            # Generate PDF
            pdf_path = await self._create_pdf_report(
                report_id=report_id,
                file_info=file_info,
                analysis_data=analysis_data
            )
            
            if not pdf_path or not os.path.exists(pdf_path):
                raise ValueError("Failed to generate PDF")
            
            # Validate PDF file
            if os.path.getsize(pdf_path) == 0:
                raise ValueError("Generated PDF is empty")
            
            # Upload to GCS
            gcs_path = await self._upload_to_gcs(pdf_path, report_id)
            
            if not gcs_path:
                raise ValueError("Failed to upload to GCS")
            
            # Store report metadata
            report_metadata = {
                'report_id': report_id,
                'file_id': file_id,
                'filename': InputValidator.sanitize_filename(file_info['filename']),
                'generated_at': datetime.utcnow().isoformat(),
                'gcs_path': gcs_path,
                'file_size': os.path.getsize(pdf_path),
                'analysis_summary': str(analysis_data.get('summary', ''))[:1000],  # Limit summary length
                'report_type': 'comprehensive_financial_analysis'
            }
            
            # Store metadata in GCS
            metadata_id = self.gcs_manager.store_document(
                document_data=report_metadata,
                doc_id=f"report_{report_id}",
                metadata={'type': 'pdf_report', 'source_file': file_id}
            )
            
            return {
                'report_id': report_id,
                'download_url': gcs_path,
                'metadata_id': metadata_id,
                'generated_at': report_metadata['generated_at'],
                'file_size': report_metadata['file_size']
            }
            
        except Exception as e:
            logger.error(f"Error generating PDF report: {e}")
            raise
    
    async def _create_pdf_report(self, 
                               report_id: str,
                               file_info: Dict[str, Any],
                               analysis_data: Dict[str, Any]) -> str:
        """Create the actual PDF report"""
        try:
            # Validate report ID
            if not InputValidator.validate_uuid(report_id):
                raise ValueError("Invalid report ID format")
            
            # Create secure temporary file path
            pdf_path = PathSanitizer.get_safe_report_path(report_id, '.pdf')
            if not pdf_path:
                raise ValueError("Failed to create secure file path")
            
            # Validate the path is within allowed directories
            if not PathSanitizer.validate_path(pdf_path):
                raise ValueError("Invalid file path")
            
            # Create PDF document
            doc = SimpleDocTemplate(
                pdf_path,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )
            
            # Build report content
            story = []
            
            # Title page
            story.extend(self._create_title_page(file_info))
            story.append(PageBreak())
            
            # Executive summary
            story.extend(self._create_executive_summary(analysis_data))
            story.append(PageBreak())
            
            # Financial statements
            story.extend(self._create_financial_statements(analysis_data))
            story.append(PageBreak())
            
            # Analysis and insights
            story.extend(self._create_analysis_section(analysis_data))
            story.append(PageBreak())
            
            # Charts and visualizations
            story.extend(self._create_charts_section(analysis_data))
            story.append(PageBreak())
            
            # Appendices
            story.extend(self._create_appendices(analysis_data))
            
            # Build PDF
            doc.build(story)
            
            return pdf_path
            
        except Exception as e:
            logger.error(f"Error creating PDF: {e}")
            raise
    
    def _create_title_page(self, file_info: Dict[str, Any]) -> List[Any]:
        """Create title page content"""
        story = []
        
        # Title
        title = Paragraph("Comprehensive Financial Analysis Report", self.styles['FinancialTitle'])
        story.append(title)
        story.append(Spacer(1, 0.5*inch))
        
        # Subtitle
        subtitle = Paragraph(f"Analysis of {file_info['filename']}", self.styles['Heading2'])
        story.append(subtitle)
        story.append(Spacer(1, 1*inch))
        
        # Metadata
        metadata_data = [
            ["Report Generated:", datetime.now().strftime("%B %d, %Y")],
            ["Source File:", file_info['filename']],
            ["File ID:", file_info['id']],
            ["Upload Date:", file_info['uploaded_at']],
            ["Analysis Type:", "Comprehensive Financial Analysis"]
        ]
        
        metadata_table = Table(metadata_data, colWidths=[2*inch, 3*inch])
        metadata_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(metadata_table)
        story.append(Spacer(1, 1*inch))
        
        # Disclaimer
        disclaimer = Paragraph(
            "This report is generated using automated financial analysis tools. "
            "Please consult with qualified financial professionals before making "
            "investment decisions based on this analysis.",
            self.styles['Normal']
        )
        story.append(disclaimer)
        
        return story
    
    def _create_executive_summary(self, analysis_data: Dict[str, Any]) -> List[Any]:
        """Create executive summary section"""
        story = []
        
        story.append(Paragraph("Executive Summary", self.styles['SectionHeader']))
        story.append(Spacer(1, 12))
        
        # Key metrics summary
        if 'summary' in analysis_data:
            summary_text = analysis_data['summary']
            story.append(Paragraph(summary_text, self.styles['Normal']))
            story.append(Spacer(1, 12))
        
        # Key financial ratios
        if 'ratios' in analysis_data.get('tables', {}):
            story.append(Paragraph("Key Financial Ratios", self.styles['Heading3']))
            
            ratios_data = analysis_data['tables']['ratios']
            if isinstance(ratios_data, list):
                ratio_table_data = [["Metric", "Value", "Interpretation"]]
                for ratio in ratios_data[:10]:  # Limit to first 10
                    ratio_table_data.append([
                        ratio.get('metric', ''),
                        str(ratio.get('value', '')),
                        ratio.get('interpretation', '')
                    ])
                
                ratio_table = Table(ratio_table_data)
                ratio_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                story.append(ratio_table)
        
        return story
    
    def _create_financial_statements(self, analysis_data: Dict[str, Any]) -> List[Any]:
        """Create financial statements section"""
        story = []
        
        story.append(Paragraph("Financial Statements", self.styles['SectionHeader']))
        story.append(Spacer(1, 12))
        
        # Balance Sheet
        if 'balance_sheet' in analysis_data.get('tables', {}):
            story.append(Paragraph("Balance Sheet", self.styles['Heading3']))
            bs_data = analysis_data['tables']['balance_sheet']
            if isinstance(bs_data, list):
                bs_table = self._create_financial_table(bs_data)
                story.append(bs_table)
                story.append(Spacer(1, 12))
        
        # Income Statement
        if 'income_statement' in analysis_data.get('tables', {}):
            story.append(Paragraph("Income Statement", self.styles['Heading3']))
            is_data = analysis_data['tables']['income_statement']
            if isinstance(is_data, list):
                is_table = self._create_financial_table(is_data)
                story.append(is_table)
                story.append(Spacer(1, 12))
        
        # Cash Flow Statement
        if 'cash_flow' in analysis_data.get('tables', {}):
            story.append(Paragraph("Cash Flow Statement", self.styles['Heading3']))
            cf_data = analysis_data['tables']['cash_flow']
            if isinstance(cf_data, list):
                cf_table = self._create_financial_table(cf_data)
                story.append(cf_table)
        
        return story
    
    def _create_financial_table(self, data: List[Dict[str, Any]]) -> Table:
        """Create a formatted financial table"""
        if not data:
            return Table([["No data available"]])
        
        # Get headers from first item
        headers = list(data[0].keys())
        table_data = [headers]
        
        for row in data:
            table_data.append([str(row.get(header, '')) for header in headers])
        
        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.lightgrey, colors.white])
        ]))
        
        return table
    
    def _create_analysis_section(self, analysis_data: Dict[str, Any]) -> List[Any]:
        """Create analysis and insights section"""
        story = []
        
        story.append(Paragraph("Financial Analysis & Insights", self.styles['SectionHeader']))
        story.append(Spacer(1, 12))
        
        # Trend analysis
        if 'trends' in analysis_data:
            story.append(Paragraph("Trend Analysis", self.styles['Heading3']))
            story.append(Paragraph(analysis_data['trends'], self.styles['Normal']))
            story.append(Spacer(1, 12))
        
        # Risk assessment
        if 'risks' in analysis_data:
            story.append(Paragraph("Risk Assessment", self.styles['Heading3']))
            story.append(Paragraph(analysis_data['risks'], self.styles['Normal']))
            story.append(Spacer(1, 12))
        
        # Recommendations
        if 'recommendations' in analysis_data:
            story.append(Paragraph("Recommendations", self.styles['Heading3']))
            story.append(Paragraph(analysis_data['recommendations'], self.styles['Normal']))
        
        return story
    
    def _create_charts_section(self, analysis_data: Dict[str, Any]) -> List[Any]:
        """Create charts and visualizations section"""
        story = []
        
        story.append(Paragraph("Charts & Visualizations", self.styles['SectionHeader']))
        story.append(Spacer(1, 12))
        
        # Add placeholder for charts
        story.append(Paragraph(
            "Detailed charts and visualizations would be included here based on the financial data.",
            self.styles['Normal']
        ))
        
        return story
    
    def _create_appendices(self, analysis_data: Dict[str, Any]) -> List[Any]:
        """Create appendices section"""
        story = []
        
        story.append(Paragraph("Appendices", self.styles['SectionHeader']))
        story.append(Spacer(1, 12))
        
        # Data sources
        story.append(Paragraph("A. Data Sources", self.styles['Heading3']))
        story.append(Paragraph(
            "This report is based on data extracted from the uploaded financial documents "
            "and analyzed using advanced financial analysis techniques.",
            self.styles['Normal']
        ))
        story.append(Spacer(1, 12))
        
        # Methodology
        story.append(Paragraph("B. Methodology", self.styles['Heading3']))
        story.append(Paragraph(
            "Financial ratios and metrics are calculated using standard accounting principles "
            "and industry best practices.",
            self.styles['Normal']
        ))
        
        return story
    
    async def _upload_to_gcs(self, local_path: str, report_id: str) -> str:
        """Upload PDF to Google Cloud Storage"""
        try:
            # Validate inputs
            if not local_path or not os.path.exists(local_path):
                raise ValueError("Invalid local file path")
            
            if not InputValidator.validate_uuid(report_id):
                raise ValueError("Invalid report ID format")
            
            # Validate file size
            file_size = os.path.getsize(local_path)
            if not InputValidator.validate_file_size(file_size):
                raise ValueError("File size exceeds maximum allowed")
            
            # Generate secure GCS path
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_report_id = InputValidator.sanitize_filename(report_id)
            
            gcs_path = f"reports/financial_report_{safe_report_id}_{timestamp}.pdf"
            
            # Validate GCS path
            if not PathSanitizer.validate_gcs_path(gcs_path):
                raise ValueError("Invalid GCS path")
            
            # Sanitize GCS object name
            gcs_path = PathSanitizer.sanitize_gcs_object_name(gcs_path)
            
            # Upload file with security checks
            with open(local_path, 'rb') as pdf_file:
                # Validate file content
                content = pdf_file.read(1024)  # Read first 1KB to check content
                if b'%PDF-' not in content:
                    raise ValueError("Invalid PDF file format")
                
                pdf_file.seek(0)  # Reset file pointer
                
                self.gcs_client.upload_file(
                    file_data=pdf_file,
                    destination_blob_name=gcs_path,
                    content_type="application/pdf"
                )
            
            return gcs_path
            
        except Exception as e:
            logger.error(f"Error uploading to GCS: {e}")
            raise
    
    async def generate_custom_report(self, 
                                   report_config: Dict[str, Any],
                                   file_ids: List[str]) -> Dict[str, Any]:
        """
        Generate custom report based on configuration
        
        Args:
            report_config: Report configuration (sections, format, etc.)
            file_ids: List of file IDs to include
            
        Returns:
            Report metadata and download information
        """
        try:
            report_id = str(uuid.uuid4())
            
            # Collect data from all files
            combined_data = await self._combine_file_data(file_ids)
            
            # Generate report based on configuration
            if report_config.get('format') == 'pdf':
                return await self.generate_comprehensive_report(
                    report_id=report_id,
                    file_id=file_ids[0],  # Primary file
                    analysis_data=combined_data
                )
            
        except Exception as e:
            logger.error(f"Error generating custom report: {e}")
            raise
    
    async def _combine_file_data(self, file_ids: List[str]) -> Dict[str, Any]:
        """Combine data from multiple files"""
        combined_data = {
            'summary': '',
            'tables': {},
            'trends': '',
            'risks': '',
            'recommendations': ''
        }
        
        for file_id in file_ids:
            reports = db_manager.get_reports_for_file(file_id)
            for report in reports:
                if report.get('tables'):
                    for table_name, table_data in report['tables'].items():
                        if table_name not in combined_data['tables']:
                            combined_data['tables'][table_name] = []
                        combined_data['tables'][table_name].extend(table_data)
        
        return combined_data
    
    def get_report_template_options(self) -> List[Dict[str, Any]]:
        """Get available report template options"""
        return [
            {
                'id': 'comprehensive',
                'name': 'Comprehensive Financial Analysis',
                'description': 'Complete analysis with all financial statements and ratios',
                'sections': ['title', 'summary', 'statements', 'analysis', 'charts', 'appendices']
            },
            {
                'id': 'executive',
                'name': 'Executive Summary',
                'description': 'High-level overview with key metrics and recommendations',
                'sections': ['title', 'summary', 'key_metrics', 'recommendations']
            },
            {
                'id': 'ratios_only',
                'name': 'Financial Ratios',
                'description': 'Focus on financial ratios and trend analysis',
                'sections': ['title', 'ratios', 'trends', 'comparison']
            }
        ]