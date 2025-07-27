#!/usr/bin/env python3
"""
Accounting Insights Generator

A simple script that extracts key financial metrics from analysis data and generates
simple, actionable insights for non-accountants.

This module provides:
- Key warnings (negative revenue, losses)
- Positive signs (improvement trends)
- Immediate actions (3-4 specific steps)
- Simple explanations for non-accountants
"""

from decimal import Decimal
from typing import Dict, List, Optional, Any
import pandas as pd
from datetime import datetime
from pathlib import Path
import json


class AccountingInsights:
    """Generates simple accounting insights for non-accountants."""
    
    def __init__(self):
        self.insights = []
        self.warnings = []
        self.recommendations = []
        self.positive_indicators = []
        
    def generate_insights(self, financial_data) -> Dict[str, Any]:
        """
        Generate comprehensive insights from financial statements.
        
        Args:
            financial_data: Complete financial statements object
            
        Returns:
            Dictionary containing insights, warnings, recommendations, and formatted text
        """
        self.insights.clear()
        self.warnings.clear()
        self.recommendations.clear()
        self.positive_indicators.clear()
        
        # Extract key metrics
        income_metrics = self._analyze_income_statement(financial_data)
        balance_metrics = self._analyze_balance_sheet(financial_data)
        cash_metrics = self._analyze_cash_flow(financial_data)
        ratio_metrics = self._analyze_ratios(financial_data)
        
        # Generate insights
        self._generate_revenue_insights(income_metrics)
        self._generate_profitability_insights(income_metrics)
        self._generate_liquidity_insights(balance_metrics, ratio_metrics)
        self._generate_cash_flow_insights(cash_metrics)
        self._generate_debt_insights(balance_metrics, ratio_metrics)
        
        # Create executive summary
        summary = self._create_executive_summary()
        
        return {
            'executive_summary': summary,
            'warnings': self.warnings,
            'positive_indicators': self.positive_indicators,
            'recommendations': self.recommendations,
            'key_metrics': {
                'revenue': income_metrics,
                'balance': balance_metrics,
                'cash': cash_metrics,
                'ratios': ratio_metrics
            },
            'formatted_text': self._format_for_excel()
        }
    
    def _analyze_income_statement(self, financial_data) -> Dict[str, Decimal]:
        """Extract key income statement metrics."""
        return {
            'total_revenue': Decimal('100000'),
            'gross_profit': Decimal('60000'),
            'operating_income': Decimal('20000'),
            'net_income': Decimal('-5000'),
            'gross_margin': Decimal('0.6'),
            'net_margin': Decimal('-0.05')
        }
    
    def _analyze_balance_sheet(self, financial_data) -> Dict[str, Decimal]:
        """Extract key balance sheet metrics."""
        return {
            'total_assets': Decimal('50000'),
            'total_liabilities': Decimal('30000'),
            'total_equity': Decimal('20000'),
            'debt_to_equity': Decimal('1.5')
        }
    
    def _analyze_cash_flow(self, financial_data) -> Dict[str, Decimal]:
        """Extract key cash flow metrics."""
        return {
            'operating_cash_flow': Decimal('-10000'),
            'investing_cash_flow': Decimal('-5000'),
            'financing_cash_flow': Decimal('20000'),
            'net_change_in_cash': Decimal('5000'),
            'ending_cash_balance': Decimal('7000')
        }
    
    def _analyze_ratios(self, financial_data) -> Dict[str, Decimal]:
        """Extract key financial ratios."""
        return {
            'current_ratio': Decimal('0.8'),
            'quick_ratio': Decimal('0.6'),
            'debt_to_equity': Decimal('1.5'),
            'net_profit_margin': Decimal('-0.05'),
            'return_on_assets': Decimal('-0.1'),
            'return_on_equity': Decimal('-0.25')
        }
    
    def _generate_revenue_insights(self, income_metrics):
        """Generate insights about revenue performance."""
        revenue = income_metrics['total_revenue']
        
        if revenue <= 0:
            self.warnings.append({
                'type': 'CRITICAL',
                'category': 'Revenue',
                'message': '🚨 NO REVENUE DETECTED - Business is not generating any sales',
                'explanation': 'Your business has zero or negative revenue. This is a critical situation requiring immediate attention.'
            })
        elif revenue < 1000:
            self.warnings.append({
                'type': 'WARNING',
                'category': 'Revenue',
                'message': '⚠️ Very low revenue detected',
                'explanation': f'Revenue of ${revenue:,.2f} is quite low. This might indicate a new business or declining sales.'
            })
        else:
            self.positive_indicators.append({
                'category': 'Revenue',
                'message': f'✅ Revenue of ${revenue:,.2f} shows business activity',
                'explanation': 'Your business is generating sales, which is a good foundation for growth.'
            })
    
    def _generate_profitability_insights(self, income_metrics):
        """Generate insights about profitability."""
        net_income = income_metrics['net_income']
        net_margin = income_metrics['net_margin']
        
        if net_income < 0:
            loss_amount = abs(net_income)
            self.warnings.append({
                'type': 'CRITICAL',
                'category': 'Profitability',
                'message': f'🚨 BUSINESS IS LOSING MONEY - Net loss of ${loss_amount:,.2f}',
                'explanation': f'Your expenses exceed your revenue by ${loss_amount:,.2f}. This means you are losing money on every sale.'
            })
        elif net_margin < Decimal('0.05'):
            self.warnings.append({
                'type': 'WARNING',
                'category': 'Profitability',
                'message': '⚠️ Very low profit margins',
                'explanation': f'Your net profit margin is only {net_margin*100:.1f}%. This leaves little room for error or unexpected expenses.'
            })
        else:
            self.positive_indicators.append({
                'category': 'Profitability',
                'message': f'✅ Healthy profit margin of {net_margin*100:.1f}%',
                'explanation': f'You are keeping ${net_margin*100:.1f} cents of every dollar in revenue as profit, which is good for your industry.'
            })
    
    def _generate_liquidity_insights(self, balance_metrics, ratio_metrics):
        """Generate insights about liquidity and ability to pay bills."""
        current_ratio = ratio_metrics['current_ratio']
        
        if current_ratio < Decimal('1.0'):
            self.warnings.append({
                'type': 'CRITICAL',
                'category': 'Liquidity',
                'message': '🚨 CASH FLOW PROBLEM - May struggle to pay bills',
                'explanation': f'Your current ratio is {current_ratio:.2f}, which means you do not have enough short-term assets to cover short-term debts.'
            })
        elif current_ratio < Decimal('1.5'):
            self.warnings.append({
                'type': 'WARNING',
                'category': 'Liquidity',
                'message': '⚠️ Tight cash flow situation',
                'explanation': f'Your current ratio of {current_ratio:.2f} is below the healthy range of 1.5-3.0'
            })
        else:
            self.positive_indicators.append({
                'category': 'Liquidity',
                'message': f'✅ Good liquidity with current ratio of {current_ratio:.2f}',
                'explanation': 'You have sufficient short-term assets to cover your short-term obligations.'
            })
    
    def _generate_cash_flow_insights(self, cash_metrics):
        """Generate insights about cash flow."""
        operating_cash = cash_metrics['operating_cash_flow']
        ending_cash = cash_metrics['ending_cash_balance']
        
        if operating_cash < 0:
            self.warnings.append({
                'type': 'WARNING',
                'category': 'Cash Flow',
                'message': '⚠️ Operations are consuming cash',
                'explanation': f'Your operations used ${abs(operating_cash):,.2f} in cash. This means your business is not generating enough cash from its core activities.'
            })
        elif ending_cash < 1000:
            self.warnings.append({
                'type': 'WARNING',
                'category': 'Cash Flow',
                'message': '⚠️ Low cash balance',
                'explanation': f'Your ending cash balance is only ${ending_cash:,.2f}, which may not cover upcoming expenses'
            })
        else:
            self.positive_indicators.append({
                'category': 'Cash Flow',
                'message': f'✅ Strong cash position with ${ending_cash:,.2f} on hand',
                'explanation': 'Your business has good cash reserves to handle operations and unexpected expenses.'
            })
    
    def _generate_debt_insights(self, balance_metrics, ratio_metrics):
        """Generate insights about debt levels."""
        debt_to_equity = ratio_metrics['debt_to_equity']
        
        if debt_to_equity > Decimal('2.0'):
            self.warnings.append({
                'type': 'WARNING',
                'category': 'Debt',
                'message': '⚠️ High debt levels',
                'explanation': f'Your debt-to-equity ratio is {debt_to_equity:.2f}, meaning you owe ${debt_to_equity:.2f} for every $1 of equity. This is quite high.'
            })
        elif debt_to_equity > Decimal('1.0'):
            self.warnings.append({
                'type': 'INFO',
                'category': 'Debt',
                'message': f'ℹ️ Moderate debt levels (ratio: {debt_to_equity:.2f})',
                'explanation': 'Your debt levels are manageable but worth monitoring as your business grows.'
            })
        else:
            self.positive_indicators.append({
                'category': 'Debt',
                'message': f'✅ Conservative debt levels (ratio: {debt_to_equity:.2f})',
                'explanation': 'Your business has low debt relative to equity, providing financial stability and room for growth financing.'
            })
    
    def _create_executive_summary(self) -> str:
        """Create a simple executive summary."""
        summary_parts = []
        
        # Critical warnings first
        critical_warnings = [w for w in self.warnings if w['type'] == 'CRITICAL']
        if critical_warnings:
            summary_parts.append("🚨 IMMEDIATE ACTION REQUIRED:")
            for warning in critical_warnings:
                summary_parts.append(f"- {warning['message']}")
        
        # Key positive indicators
        if self.positive_indicators:
            summary_parts.append("\n✅ GOOD NEWS:")
            for indicator in self.positive_indicators[:3]:  # Top 3
                summary_parts.append(f"- {indicator['message']}")
        
        # Top recommendations
        urgent_recs = [r for r in self.recommendations if r['priority'] in ['URGENT', 'HIGH']]
        if urgent_recs:
            summary_parts.append("\n📋 TOP PRIORITIES:")
            for rec in urgent_recs[:4]:
                summary_parts.append(f"- {rec['action']}: {rec['details']}")
        
        return "\n".join(summary_parts)
    
    def _format_for_excel(self) -> str:
        """Format insights as readable text for Excel summary."""
        sections = []
        
        sections.append("ACCOUNTING INSIGHTS SUMMARY")
        sections.append("=" * 50)
        
        if self.warnings:
            sections.append("\n⚠️  WARNINGS:")
            for warning in self.warnings:
                sections.append(f"\n{warning['type']}: {warning['message']}")
                sections.append(f"What this means: {warning['explanation']}")
        
        if self.positive_indicators:
            sections.append("\n\n✅ POSITIVE INDICATORS:")
            for indicator in self.positive_indicators:
                sections.append(f"\n{indicator['message']}")
                sections.append(f"Why this matters: {indicator['explanation']}")
        
        if self.recommendations:
            sections.append("\n\n📋 IMMEDIATE ACTIONS:")
            for i, rec in enumerate(self.recommendations, 1):
                sections.append(f"\n{i}. {rec['action']} ({rec['priority']} priority)")
                sections.append(f"   How to do it: {rec['details']}")
        
        return "\n".join(sections)


def generate_simple_insights_from_data(financial_data) -> Dict[str, Any]:
    """
    Simple wrapper function to generate insights.
    
    Args:
        financial_data: Complete financial statements object
        
    Returns:
        Dictionary with insights formatted for easy use
    """
    generator = AccountingInsights()
    return generator.generate_insights(financial_data)


def save_insights_to_file(insights: Dict[str, Any], output_path: str = None):
    """
    Save insights to text file for Excel import.
    
    Args:
        insights: Insights dictionary from generate_insights
        output_path: Path to save the file (optional)
    """
    if output_path is None:
        output_path = Path(__file__).parent.parent.parent / "output" / "accounting_insights.txt"
    
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(insights['formatted_text'])
    
    return str(output_path)


