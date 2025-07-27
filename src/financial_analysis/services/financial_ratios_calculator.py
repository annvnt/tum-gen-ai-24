"""
Comprehensive financial ratios calculator for financial statement analysis.
Calculates liquidity, profitability, leverage, and efficiency ratios.
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Optional
import logging

from financial_analysis.models.accounting_models import (
    BalanceSheet, IncomeStatement, CashFlowStatement, FinancialRatios,
    AccountSubType
)

logger = logging.getLogger(__name__)


class FinancialRatiosCalculator:
    """Service for calculating comprehensive financial ratios."""
    
    def __init__(self):
        self.decimal_places = 4
    
    def calculate_financial_ratios(self, balance_sheet: BalanceSheet,
                                 income_statement: IncomeStatement,
                                 cash_flow_statement: Optional[CashFlowStatement] = None) -> FinancialRatios:
        """
        Calculate comprehensive financial ratios from financial statements.
        
        Args:
            balance_sheet: Balance sheet data
            income_statement: Income statement data
            cash_flow_statement: Cash flow statement data (optional)
            
        Returns:
            Complete FinancialRatios object
        """
        
        # Calculate liquidity ratios
        liquidity_ratios = self._calculate_liquidity_ratios(balance_sheet)
        
        # Calculate profitability ratios
        profitability_ratios = self._calculate_profitability_ratios(
            balance_sheet, income_statement
        )
        
        # Calculate leverage ratios
        leverage_ratios = self._calculate_leverage_ratios(balance_sheet)
        
        # Calculate efficiency ratios
        efficiency_ratios = self._calculate_efficiency_ratios(
            balance_sheet, income_statement
        )
        
        # Create financial ratios object
        financial_ratios = FinancialRatios(
            entity_name=balance_sheet.entity_name,
            statement_date=balance_sheet.statement_date,
            **liquidity_ratios,
            **profitability_ratios,
            **leverage_ratios,
            **efficiency_ratios
        )
        
        logger.info(f"Calculated financial ratios for {balance_sheet.entity_name}")
        return financial_ratios
    
    def _calculate_liquidity_ratios(self, balance_sheet: BalanceSheet) -> Dict:
        """Calculate liquidity ratios."""
        
        # Extract current assets and liabilities
        current_assets = sum(
            item.amount for item in balance_sheet.assets.items
            if item.account_subtype == AccountSubType.CURRENT_ASSET
        )
        
        current_liabilities = sum(
            item.amount for item in balance_sheet.liabilities.items
            if item.account_subtype == AccountSubType.CURRENT_LIABILITY
        )
        
        # Extract cash and cash equivalents
        cash = sum(
            item.amount for item in balance_sheet.assets.items
            if item.account_subtype == AccountSubType.CURRENT_ASSET and
            any(keyword in item.account_name.lower() for keyword in ['cash', 'bank'])
        )
        
        # Extract marketable securities (quick assets)
        marketable_securities = sum(
            item.amount for item in balance_sheet.assets.items
            if item.account_subtype == AccountSubType.CURRENT_ASSET and
            any(keyword in item.account_name.lower() for keyword in ['investment', 'marketable'])
        )
        
        # Extract accounts receivable
        accounts_receivable = sum(
            item.amount for item in balance_sheet.assets.items
            if item.account_subtype == AccountSubType.CURRENT_ASSET and
            any(keyword in item.account_name.lower() for keyword in ['receivable', 'ar'])
        )
        
        # Calculate ratios
        current_ratio = self._safe_divide(current_assets, current_liabilities)
        quick_ratio = self._safe_divide(
            cash + marketable_securities + accounts_receivable,
            current_liabilities
        )
        cash_ratio = self._safe_divide(cash, current_liabilities)
        
        return {
            "current_ratio": current_ratio,
            "quick_ratio": quick_ratio,
            "cash_ratio": cash_ratio
        }
    
    def _calculate_profitability_ratios(self, balance_sheet: BalanceSheet,
                                      income_statement: IncomeStatement) -> Dict:
        """Calculate profitability ratios."""
        
        # Extract key figures
        revenue = income_statement.revenue.total_amount
        net_income = income_statement.net_income
        gross_profit = income_statement.gross_profit
        operating_income = income_statement.operating_income
        total_assets = balance_sheet.total_assets
        total_equity = balance_sheet.equity.total_amount
        
        # Calculate ratios
        gross_profit_margin = self._safe_divide(gross_profit * 100, revenue)
        operating_profit_margin = self._safe_divide(operating_income * 100, revenue)
        net_profit_margin = self._safe_divide(net_income * 100, revenue)
        return_on_assets = self._safe_divide(net_income * 100, total_assets)
        return_on_equity = self._safe_divide(net_income * 100, total_equity)
        
        return {
            "gross_profit_margin": gross_profit_margin,
            "operating_profit_margin": operating_profit_margin,
            "net_profit_margin": net_profit_margin,
            "return_on_assets": return_on_assets,
            "return_on_equity": return_on_equity
        }
    
    def _calculate_leverage_ratios(self, balance_sheet: BalanceSheet) -> Dict:
        """Calculate leverage ratios."""
        
        # Extract key figures
        total_liabilities = balance_sheet.liabilities.total_amount
        total_equity = balance_sheet.equity.total_amount
        total_assets = balance_sheet.total_assets
        
        # Calculate ratios
        debt_to_equity = self._safe_divide(total_liabilities, total_equity)
        debt_to_assets = self._safe_divide(total_liabilities, total_assets)
        equity_multiplier = self._safe_divide(total_assets, total_equity)
        
        return {
            "debt_to_equity": debt_to_equity,
            "debt_to_assets": debt_to_assets,
            "equity_multiplier": equity_multiplier
        }
    
    def _calculate_efficiency_ratios(self, balance_sheet: BalanceSheet,
                                   income_statement: IncomeStatement) -> Dict:
        """Calculate efficiency ratios."""
        
        # Extract key figures
        revenue = income_statement.revenue.total_amount
        total_assets = balance_sheet.total_assets
        
        # Extract inventory
        inventory = sum(
            item.amount for item in balance_sheet.assets.items
            if item.account_subtype == AccountSubType.CURRENT_ASSET and
            any(keyword in item.account_name.lower() for keyword in ['inventory', 'stock'])
        )
        
        # Extract accounts receivable
        accounts_receivable = sum(
            item.amount for item in balance_sheet.assets.items
            if item.account_subtype == AccountSubType.CURRENT_ASSET and
            any(keyword in item.account_name.lower() for keyword in ['receivable', 'ar'])
        )
        
        # Calculate ratios
        asset_turnover = self._safe_divide(revenue, total_assets)
        inventory_turnover = self._safe_divide(income_statement.cost_of_goods_sold.total_amount, inventory)
        receivables_turnover = self._safe_divide(revenue, accounts_receivable)
        
        return {
            "asset_turnover": asset_turnover,
            "inventory_turnover": inventory_turnover if inventory > 0 else None,
            "receivables_turnover": receivables_turnover if accounts_receivable > 0 else None
        }
    
    def _safe_divide(self, numerator: Decimal, denominator: Decimal) -> Decimal:
        """Safely divide two decimals, handling zero divisions."""
        if denominator == 0:
            return Decimal('0')
        
        result = numerator / denominator
        return result.quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)
    
    def get_ratio_analysis(self, financial_ratios: FinancialRatios) -> Dict:
        """Generate comprehensive ratio analysis with interpretations."""
        
        analysis = {
            "liquidity_analysis": self._analyze_liquidity_ratios(financial_ratios),
            "profitability_analysis": self._analyze_profitability_ratios(financial_ratios),
            "leverage_analysis": self._analyze_leverage_ratios(financial_ratios),
            "efficiency_analysis": self._analyze_efficiency_ratios(financial_ratios),
            "overall_assessment": self._generate_overall_assessment(financial_ratios)
        }
        
        return analysis
    
    def _analyze_liquidity_ratios(self, ratios: FinancialRatios) -> Dict:
        """Analyze liquidity ratios and provide interpretations."""
        
        current_ratio = float(ratios.current_ratio)
        quick_ratio = float(ratios.quick_ratio)
        cash_ratio = float(ratios.cash_ratio)
        
        interpretations = []
        
        # Current ratio analysis
        if current_ratio >= 2.0:
            interpretations.append("Strong liquidity position - company can easily meet short-term obligations")
        elif current_ratio >= 1.0:
            interpretations.append("Adequate liquidity - company can meet short-term obligations")
        else:
            interpretations.append("Liquidity concerns - company may struggle to meet short-term obligations")
        
        # Quick ratio analysis
        if quick_ratio >= 1.0:
            interpretations.append("Good quick ratio - company has sufficient liquid assets")
        elif quick_ratio >= 0.5:
            interpretations.append("Moderate quick ratio - company has some liquid assets")
        else:
            interpretations.append("Low quick ratio - company may face liquidity challenges")
        
        return {
            "current_ratio": current_ratio,
            "current_ratio_interpretation": "Strong" if current_ratio >= 2.0 else "Moderate" if current_ratio >= 1.0 else "Weak",
            "quick_ratio": quick_ratio,
            "quick_ratio_interpretation": "Strong" if quick_ratio >= 1.0 else "Moderate" if quick_ratio >= 0.5 else "Weak",
            "cash_ratio": cash_ratio,
            "interpretations": interpretations
        }
    
    def _analyze_profitability_ratios(self, ratios: FinancialRatios) -> Dict:
        """Analyze profitability ratios and provide interpretations."""
        
        gross_margin = float(ratios.gross_profit_margin)
        operating_margin = float(ratios.operating_profit_margin)
        net_margin = float(ratios.net_profit_margin)
        roa = float(ratios.return_on_assets)
        roe = float(ratios.return_on_equity)
        
        interpretations = []
        
        # Margin analysis
        if gross_margin >= 40:
            interpretations.append("Strong gross margin - company has pricing power")
        elif gross_margin >= 20:
            interpretations.append("Moderate gross margin - typical for most industries")
        else:
            interpretations.append("Low gross margin - company faces pricing pressure")
        
        # ROE analysis
        if roe >= 15:
            interpretations.append("Excellent return on equity - creating significant value for shareholders")
        elif roe >= 10:
            interpretations.append("Good return on equity - creating value for shareholders")
        elif roe >= 5:
            interpretations.append("Moderate return on equity - acceptable but could improve")
        else:
            interpretations.append("Low return on equity - may need to improve profitability")
        
        return {
            "gross_profit_margin": gross_margin,
            "operating_profit_margin": operating_margin,
            "net_profit_margin": net_margin,
            "return_on_assets": roa,
            "return_on_equity": roe,
            "interpretations": interpretations
        }
    
    def _analyze_leverage_ratios(self, ratios: FinancialRatios) -> Dict:
        """Analyze leverage ratios and provide interpretations."""
        
        debt_to_equity = float(ratios.debt_to_equity)
        debt_to_assets = float(ratios.debt_to_assets)
        equity_multiplier = float(ratios.equity_multiplier)
        
        interpretations = []
        
        # Debt-to-equity analysis
        if debt_to_equity <= 0.5:
            interpretations.append("Conservative debt structure - low financial risk")
        elif debt_to_equity <= 1.0:
            interpretations.append("Moderate debt structure - balanced financial risk")
        elif debt_to_equity <= 2.0:
            interpretations.append("Elevated debt structure - increased financial risk")
        else:
            interpretations.append("High debt structure - significant financial risk")
        
        return {
            "debt_to_equity": debt_to_equity,
            "debt_to_assets": debt_to_assets,
            "equity_multiplier": equity_multiplier,
            "debt_to_equity_interpretation": "Conservative" if debt_to_equity <= 0.5 else "Moderate" if debt_to_equity <= 1.0 else "High",
            "interpretations": interpretations
        }
    
    def _analyze_efficiency_ratios(self, ratios: FinancialRatios) -> Dict:
        """Analyze efficiency ratios and provide interpretations."""
        
        asset_turnover = float(ratios.asset_turnover)
        inventory_turnover = float(ratios.inventory_turnover or 0)
        receivables_turnover = float(ratios.receivables_turnover or 0)
        
        interpretations = []
        
        # Asset turnover analysis
        if asset_turnover >= 1.5:
            interpretations.append("High asset turnover - efficient use of assets")
        elif asset_turnover >= 1.0:
            interpretations.append("Moderate asset turnover - reasonable asset utilization")
        else:
            interpretations.append("Low asset turnover - may need to improve asset efficiency")
        
        return {
            "asset_turnover": asset_turnover,
            "inventory_turnover": inventory_turnover,
            "receivables_turnover": receivables_turnover,
            "asset_turnover_interpretation": "High" if asset_turnover >= 1.5 else "Moderate" if asset_turnover >= 1.0 else "Low",
            "interpretations": interpretations
        }
    
    def _generate_overall_assessment(self, ratios: FinancialRatios) -> Dict:
        """Generate overall financial health assessment."""
        
        # Score calculation
        scores = {
            "liquidity_score": self._score_liquidity(ratios),
            "profitability_score": self._score_profitability(ratios),
            "leverage_score": self._score_leverage(ratios),
            "efficiency_score": self._score_efficiency(ratios)
        }
        
        overall_score = sum(scores.values()) / len(scores)
        
        # Determine overall health
        if overall_score >= 80:
            overall_health = "Excellent"
            recommendation = "Company is in strong financial position"
        elif overall_score >= 60:
            overall_health = "Good"
            recommendation = "Company is financially healthy with room for improvement"
        elif overall_score >= 40:
            overall_health = "Fair"
            recommendation = "Company has some financial concerns that need attention"
        else:
            overall_health = "Poor"
            recommendation = "Company faces significant financial challenges"
        
        return {
            "overall_score": overall_score,
            "overall_health": overall_health,
            "recommendation": recommendation,
            "component_scores": scores
        }
    
    def _score_liquidity(self, ratios: FinancialRatios) -> float:
        """Score liquidity ratios."""
        current_ratio = float(ratios.current_ratio)
        quick_ratio = float(ratios.quick_ratio)
        
        score = 0
        if current_ratio >= 2.0:
            score += 50
        elif current_ratio >= 1.0:
            score += 30
        elif current_ratio >= 0.5:
            score += 10
        
        if quick_ratio >= 1.0:
            score += 50
        elif quick_ratio >= 0.5:
            score += 30
        elif quick_ratio >= 0.25:
            score += 10
        
        return score
    
    def _score_profitability(self, ratios: FinancialRatios) -> float:
        """Score profitability ratios."""
        net_margin = float(ratios.net_profit_margin)
        roe = float(ratios.return_on_equity)
        
        score = 0
        if net_margin >= 10:
            score += 50
        elif net_margin >= 5:
            score += 30
        elif net_margin >= 2:
            score += 10
        
        if roe >= 15:
            score += 50
        elif roe >= 10:
            score += 30
        elif roe >= 5:
            score += 10
        
        return score
    
    def _score_leverage(self, ratios: FinancialRatios) -> float:
        """Score leverage ratios."""
        debt_to_equity = float(ratios.debt_to_equity)
        
        score = 0
        if debt_to_equity <= 0.5:
            score = 100
        elif debt_to_equity <= 1.0:
            score = 75
        elif debt_to_equity <= 1.5:
            score = 50
        elif debt_to_equity <= 2.0:
            score = 25
        else:
            score = 0
        
        return score
    
    def _score_efficiency(self, ratios: FinancialRatios) -> float:
        """Score efficiency ratios."""
        asset_turnover = float(ratios.asset_turnover)
        
        score = 0
        if asset_turnover >= 2.0:
            score = 100
        elif asset_turnover >= 1.5:
            score = 75
        elif asset_turnover >= 1.0:
            score = 50
        elif asset_turnover >= 0.5:
            score = 25
        else:
            score = 0
        
        return score