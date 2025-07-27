"""
Multi-step Income Statement generator with GAAP/IFRS compliance.
Creates comprehensive income statements including gross profit, operating income, and net income.
"""

from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional, Tuple
import logging

from financial_analysis.models.accounting_models import (
    TrialBalance, IncomeStatement, IncomeStatementSection, IncomeStatementItem,
    AccountType, AccountSubType
)

logger = logging.getLogger(__name__)


class IncomeStatementGenerator:
    """Service for generating multi-step income statements."""
    
    def __init__(self):
        self.revenue_threshold = Decimal('0.01')  # Minimum revenue to report
    
    def generate_income_statement(self, trial_balance: TrialBalance,
                                period_start: Optional[date] = None,
                                period_end: Optional[date] = None) -> IncomeStatement:
        """
        Generate comprehensive multi-step income statement from trial balance.
        
        Args:
            trial_balance: Validated trial balance
            period_start: Start date of income period (defaults to trial balance period)
            period_end: End date of income period (defaults to trial balance period)
            
        Returns:
            Complete IncomeStatement object
        """
        if period_start is None:
            period_start = trial_balance.period_start
        if period_end is None:
            period_end = trial_balance.period_end
        
        # Categorize all revenue and expense accounts
        revenue_accounts = self._get_revenue_accounts(trial_balance)
        expense_accounts = self._get_expense_accounts(trial_balance)
        
        # Build income statement sections
        revenue = self._build_revenue_section(revenue_accounts)
        cost_of_goods_sold = self._build_cogs_section(expense_accounts)
        
        # Calculate gross profit
        gross_profit = revenue.total_amount - cost_of_goods_sold.total_amount
        
        operating_expenses = self._build_operating_expenses_section(expense_accounts)
        
        # Calculate operating income
        operating_income = gross_profit - operating_expenses.total_amount
        
        other_income = self._build_other_income_section(revenue_accounts)
        other_expenses = self._build_other_expenses_section(expense_accounts)
        
        # Calculate income before tax
        other_income_total = other_income.total_amount
        other_expenses_total = other_expenses.total_amount
        income_before_tax = operating_income + other_income_total - other_expenses_total
        
        tax_expense = self._build_tax_expense_section(expense_accounts)
        
        # Calculate net income
        net_income = income_before_tax - tax_expense.total_amount
        
        # Create income statement
        income_statement = IncomeStatement(
            entity_name=trial_balance.entity_name,
            period_start=period_start,
            period_end=period_end,
            revenue=revenue,
            cost_of_goods_sold=cost_of_goods_sold,
            gross_profit=gross_profit,
            operating_expenses=operating_expenses,
            operating_income=operating_income,
            other_income=other_income,
            other_expenses=other_expenses,
            income_before_tax=income_before_tax,
            tax_expense=tax_expense,
            net_income=net_income
        )
        
        # Validate income statement
        self._validate_income_statement(income_statement)
        
        logger.info(f"Generated income statement for {trial_balance.entity_name}")
        return income_statement
    
    def _get_revenue_accounts(self, trial_balance) -> List:
        """Get all revenue and gain accounts from trial balance."""
        return [
            acc for acc in trial_balance.accounts
            if acc.account_type in [AccountType.REVENUE, AccountType.GAIN]
        ]
    
    def _get_expense_accounts(self, trial_balance) -> List:
        """Get all expense and loss accounts from trial balance."""
        return [
            acc for acc in trial_balance.accounts
            if acc.account_type in [AccountType.EXPENSE, AccountType.LOSS]
        ]
    
    def _build_revenue_section(self, revenue_accounts: List) -> IncomeStatementSection:
        """Build revenue section of income statement."""
        revenue_items = []
        
        for account in revenue_accounts:
            if account.account_subtype == AccountSubType.OPERATING_REVENUE:
                item = IncomeStatementItem(
                    account_code=account.account_code,
                    account_name=account.account_name,
                    amount=abs(account.net_balance),
                    is_deduction=False
                )
                revenue_items.append(item)
        
        # Sort by account code
        revenue_items.sort(key=lambda x: x.account_code)
        
        total_revenue = sum(item.amount for item in revenue_items)
        
        return IncomeStatementSection(
            section_name="Revenue",
            total_amount=total_revenue,
            items=revenue_items
        )
    
    def _build_cogs_section(self, expense_accounts: List) -> IncomeStatementSection:
        """Build cost of goods sold section."""
        cogs_items = []
        
        for account in expense_accounts:
            if account.account_subtype == AccountSubType.COST_OF_GOODS_SOLD:
                item = IncomeStatementItem(
                    account_code=account.account_code,
                    account_name=account.account_name,
                    amount=abs(account.net_balance),
                    is_deduction=True
                )
                cogs_items.append(item)
        
        # Sort by account code
        cogs_items.sort(key=lambda x: x.account_code)
        
        total_cogs = sum(item.amount for item in cogs_items)
        
        return IncomeStatementSection(
            section_name="Cost of Goods Sold",
            total_amount=total_cogs,
            items=cogs_items
        )
    
    def _build_operating_expenses_section(self, expense_accounts: List) -> IncomeStatementSection:
        """Build operating expenses section."""
        operating_expense_items = []
        
        # Include relevant expense subtypes
        operating_subtypes = [
            AccountSubType.SELLING_EXPENSE,
            AccountSubType.ADMINISTRATIVE_EXPENSE,
            AccountSubType.DEPRECIATION_EXPENSE,
            AccountSubType.OPERATING_EXPENSE
        ]
        
        for account in expense_accounts:
            if account.account_subtype in operating_subtypes:
                item = IncomeStatementItem(
                    account_code=account.account_code,
                    account_name=account.account_name,
                    amount=abs(account.net_balance),
                    is_deduction=True
                )
                operating_expense_items.append(item)
        
        # Group by subtype for better organization
        grouped_expenses = self._group_expenses_by_subtype(operating_expense_items)
        
        total_operating_expenses = sum(item.amount for item in grouped_expenses)
        
        return IncomeStatementSection(
            section_name="Operating Expenses",
            total_amount=total_operating_expenses,
            items=grouped_expenses
        )
    
    def _build_other_income_section(self, revenue_accounts: List) -> IncomeStatementSection:
        """Build other income section (non-operating)."""
        other_income_items = []
        
        for account in revenue_accounts:
            if account.account_subtype == AccountSubType.NON_OPERATING_REVENUE:
                item = IncomeStatementItem(
                    account_code=account.account_code,
                    account_name=account.account_name,
                    amount=abs(account.net_balance),
                    is_deduction=False
                )
                other_income_items.append(item)
        
        # Sort by account code
        other_income_items.sort(key=lambda x: x.account_code)
        
        total_other_income = sum(item.amount for item in other_income_items)
        
        return IncomeStatementSection(
            section_name="Other Income",
            total_amount=total_other_income,
            items=other_income_items
        )
    
    def _build_other_expenses_section(self, expense_accounts: List) -> IncomeStatementSection:
        """Build other expenses section (non-operating)."""
        other_expense_items = []
        
        # Include non-operating expenses
        non_operating_subtypes = [
            AccountSubType.INTEREST_EXPENSE,
            AccountSubType.LOSS
        ]
        
        for account in expense_accounts:
            if account.account_subtype in non_operating_subtypes:
                item = IncomeStatementItem(
                    account_code=account.account_code,
                    account_name=account.account_name,
                    amount=abs(account.net_balance),
                    is_deduction=True
                )
                other_expense_items.append(item)
        
        # Sort by account code
        other_expense_items.sort(key=lambda x: x.account_code)
        
        total_other_expenses = sum(item.amount for item in other_expense_items)
        
        return IncomeStatementSection(
            section_name="Other Expenses",
            total_amount=total_other_expenses,
            items=other_expense_items
        )
    
    def _build_tax_expense_section(self, expense_accounts: List) -> IncomeStatementSection:
        """Build tax expense section."""
        tax_items = []
        
        for account in expense_accounts:
            if account.account_subtype == AccountSubType.TAX_EXPENSE:
                item = IncomeStatementItem(
                    account_code=account.account_code,
                    account_name=account.account_name,
                    amount=abs(account.net_balance),
                    is_deduction=True
                )
                tax_items.append(item)
        
        # Sort by account code
        tax_items.sort(key=lambda x: x.account_code)
        
        total_tax_expense = sum(item.amount for item in tax_items)
        
        return IncomeStatementSection(
            section_name="Income Tax Expense",
            total_amount=total_tax_expense,
            items=tax_items
        )
    
    def _group_expenses_by_subtype(self, expense_items: List[IncomeStatementItem]) -> List[IncomeStatementItem]:
        """Group expenses by subtype for better organization."""
        if not expense_items:
            return []
        
        # Define order of expense subtypes
        expense_order = [
            AccountSubType.SELLING_EXPENSE,
            AccountSubType.ADMINISTRATIVE_EXPENSE,
            AccountSubType.DEPRECIATION_EXPENSE,
            AccountSubType.OPERATING_EXPENSE
        ]
        
        grouped_expenses = []
        
        # Add items in order
        for subtype in expense_order:
            for item in expense_items:
                if item.account_subtype == subtype:
                    grouped_expenses.append(item)
        
        # Add remaining items
        for item in expense_items:
            if item not in grouped_expenses:
                grouped_expenses.append(item)
        
        return grouped_expenses
    
    def _validate_income_statement(self, income_statement: IncomeStatement) -> None:
        """Validate income statement calculations."""
        
        # Check gross profit calculation
        calculated_gross_profit = (
            income_statement.revenue.total_amount -
            income_statement.cost_of_goods_sold.total_amount
        )
        
        if abs(calculated_gross_profit - income_statement.gross_profit) > Decimal('0.01'):
            raise ValueError(
                f"Gross profit calculation error: "
                f"calculated={calculated_gross_profit}, "
                f"reported={income_statement.gross_profit}"
            )
        
        # Check operating income calculation
        calculated_operating_income = (
            income_statement.gross_profit -
            income_statement.operating_expenses.total_amount
        )
        
        if abs(calculated_operating_income - income_statement.operating_income) > Decimal('0.01'):
            raise ValueError(
                f"Operating income calculation error: "
                f"calculated={calculated_operating_income}, "
                f"reported={income_statement.operating_income}"
            )
        
        # Check income before tax calculation
        calculated_income_before_tax = (
            income_statement.operating_income +
            income_statement.other_income.total_amount -
            income_statement.other_expenses.total_amount
        )
        
        if abs(calculated_income_before_tax - income_statement.income_before_tax) > Decimal('0.01'):
            raise ValueError(
                f"Income before tax calculation error: "
                f"calculated={calculated_income_before_tax}, "
                f"reported={income_statement.income_before_tax}"
            )
        
        # Check net income calculation
        calculated_net_income = (
            income_statement.income_before_tax -
            income_statement.tax_expense.total_amount
        )
        
        if abs(calculated_net_income - income_statement.net_income) > Decimal('0.01'):
            raise ValueError(
                f"Net income calculation error: "
                f"calculated={calculated_net_income}, "
                f"reported={income_statement.net_income}"
            )
        
        # Check for negative revenue
        if income_statement.revenue.total_amount < 0:
            raise ValueError("Total revenue cannot be negative")
        
        # Log validation success
        logger.info(
            f"Income statement validated successfully: "
            f"Revenue=${income_statement.revenue.total_amount}, "
            f"Net Income=${income_statement.net_income}"
        )
    
    def get_income_statement_analysis(self, income_statement: IncomeStatement) -> Dict:
        """Generate income statement analysis metrics."""
        revenue = income_statement.revenue.total_amount
        cogs = income_statement.cost_of_goods_sold.total_amount
        gross_profit = income_statement.gross_profit
        operating_expenses = income_statement.operating_expenses.total_amount
        operating_income = income_statement.operating_income
        net_income = income_statement.net_income
        
        # Profitability ratios
        gross_profit_margin = (gross_profit / revenue * 100) if revenue > 0 else Decimal('0')
        operating_margin = (operating_income / revenue * 100) if revenue > 0 else Decimal('0')
        net_profit_margin = (net_income / revenue * 100) if revenue > 0 else Decimal('0')
        
        # Expense ratios
        cogs_ratio = (cogs / revenue * 100) if revenue > 0 else Decimal('0')
        operating_expense_ratio = (operating_expenses / revenue * 100) if revenue > 0 else Decimal('0')
        
        return {
            "revenue": float(revenue),
            "cost_of_goods_sold": float(cogs),
            "gross_profit": float(gross_profit),
            "operating_expenses": float(operating_expenses),
            "operating_income": float(operating_income),
            "net_income": float(net_income),
            "gross_profit_margin": float(gross_profit_margin),
            "operating_margin": float(operating_margin),
            "net_profit_margin": float(net_profit_margin),
            "cogs_ratio": float(cogs_ratio),
            "operating_expense_ratio": float(operating_expense_ratio),
            "total_revenue": float(revenue),
            "total_expenses": float(cogs + operating_expenses + income_statement.other_expenses.total_amount + income_statement.tax_expense.total_amount)
        }