"""
Financial Analysis Package

A comprehensive financial analysis system that processes Excel files,
generates reports using AI, and provides API endpoints for financial data analysis.
"""

__version__ = "1.0.0"
__author__ = "Financial Analysis Team"

from .core.financial_analyzer import (
    setup_environment,
    load_financial_data,
    load_financial_indicators,
    generate_financial_report,
    extract_simple_table,
    extract_structured_tables
)

from .services.financial_agent import FinancialReportAgent
from .storage.database_manager import db_manager
from .storage.gcs_client import get_gcs_client

__all__ = [
    "setup_environment",
    "load_financial_data",
    "load_financial_indicators",
    "generate_financial_report",
    "extract_simple_table",
    "extract_structured_tables",
    "FinancialReportAgent",
    "db_manager",
    "get_gcs_client",
]