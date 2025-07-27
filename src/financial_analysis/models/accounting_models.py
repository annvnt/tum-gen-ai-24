"""
Comprehensive accounting data models for financial statement generation.
Provides Pydantic models for trial balances, financial statements, and accounting data.
"""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator


class AccountType(str, Enum):
    """Standard account types following GAAP/IFRS classification."""
    ASSET = "ASSET"
    LIABILITY = "LIABILITY"
    EQUITY = "EQUITY"
    REVENUE = "REVENUE"
    EXPENSE = "EXPENSE"
    GAIN = "GAIN"
    LOSS = "LOSS"


class AccountSubType(str, Enum):
    """Detailed account subtypes for proper financial statement classification."""
    # Assets
    CURRENT_ASSET = "CURRENT_ASSET"
    NON_CURRENT_ASSET = "NON_CURRENT_ASSET"
    INVESTMENT = "INVESTMENT"
    PROPERTY_PLANT_EQUIPMENT = "PROPERTY_PLANT_EQUIPMENT"
    INTANGIBLE_ASSET = "INTANGIBLE_ASSET"
    
    # Liabilities
    CURRENT_LIABILITY = "CURRENT_LIABILITY"
    NON_CURRENT_LIABILITY = "NON_CURRENT_LIABILITY"
    
    # Equity
    PAID_IN_CAPITAL = "PAID_IN_CAPITAL"
    RETAINED_EARNINGS = "RETAINED_EARNINGS"
    TREASURY_STOCK = "TREASURY_STOCK"
    ACCUMULATED_OTHER_COMPREHENSIVE_INCOME = "ACCUMULATED_OTHER_COMPREHENSIVE_INCOME"
    
    # Revenue
    OPERATING_REVENUE = "OPERATING_REVENUE"
    NON_OPERATING_REVENUE = "NON_OPERATING_REVENUE"
    
    # Expenses
    COST_OF_GOODS_SOLD = "COST_OF_GOODS_SOLD"
    OPERATING_EXPENSE = "OPERATING_EXPENSE"
    SELLING_EXPENSE = "SELLING_EXPENSE"
    ADMINISTRATIVE_EXPENSE = "ADMINISTRATIVE_EXPENSE"
    DEPRECIATION_EXPENSE = "DEPRECIATION_EXPENSE"
    INTEREST_EXPENSE = "INTEREST_EXPENSE"
    TAX_EXPENSE = "TAX_EXPENSE"


class TrialBalanceAccount(BaseModel):
    """Individual account in a trial balance."""
    account_code: str = Field(..., description="Unique account identifier")
    account_name: str = Field(..., description="Account description")
    account_type: AccountType = Field(..., description="Primary account classification")
    account_subtype: AccountSubType = Field(..., description="Detailed account classification")
    debit_balance: Optional[Decimal] = Field(None, decimal_places=2, description="Debit balance")
    credit_balance: Optional[Decimal] = Field(None, decimal_places=2, description="Credit balance")
    
    @validator('debit_balance', 'credit_balance')
    def validate_balances(cls, v):
        if v is not None and v < 0:
            raise ValueError("Balances must be non-negative")
        return v
    
    @property
    def net_balance(self) -> Decimal:
        """Calculate net balance (debit - credit)."""
        debit = self.debit_balance or Decimal('0')
        credit = self.credit_balance or Decimal('0')
        return debit - credit


class TrialBalance(BaseModel):
    """Complete trial balance for a specific period."""
    entity_name: str = Field(..., description="Name of the business entity")
    period_start: date = Field(..., description="Start date of the accounting period")
    period_end: date = Field(..., description="End date of the accounting period")
    accounts: List[TrialBalanceAccount] = Field(..., description="List of all accounts")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    @validator('period_end')
    def validate_period(cls, v, values):
        if 'period_start' in values and v < values['period_start']:
            raise ValueError("Period end must be after period start")
        return v
    
    @property
    def total_debits(self) -> Decimal:
        """Calculate total debits across all accounts."""
        return sum((acc.debit_balance or Decimal('0') for acc in self.accounts), Decimal('0'))
    
    @property
    def total_credits(self) -> Decimal:
        """Calculate total credits across all accounts."""
        return sum((acc.credit_balance or Decimal('0') for acc in self.accounts), Decimal('0'))
    
    @property
    def is_balanced(self) -> bool:
        """Check if trial balance is balanced (debits = credits)."""
        return abs(self.total_debits - self.total_credits) < Decimal('0.01')


class BalanceSheetItem(BaseModel):
    """Individual item in balance sheet."""
    account_code: str
    account_name: str
    amount: Decimal = Field(..., decimal_places=2)
    account_subtype: AccountSubType
    
    class Config:
        json_encoders = {Decimal: str}


class BalanceSheetSection(BaseModel):
    """Section of balance sheet (Assets, Liabilities, or Equity)."""
    section_name: str
    total_amount: Decimal = Field(..., decimal_places=2)
    items: List[BalanceSheetItem] = []
    
    class Config:
        json_encoders = {Decimal: str}


class BalanceSheet(BaseModel):
    """Complete balance sheet statement."""
    entity_name: str
    statement_date: date
    assets: BalanceSheetSection
    liabilities: BalanceSheetSection
    equity: BalanceSheetSection
    
    @property
    def total_assets(self) -> Decimal:
        return self.assets.total_amount
    
    @property
    def total_liabilities_and_equity(self) -> Decimal:
        return self.liabilities.total_amount + self.equity.total_amount
    
    @property
    def is_balanced(self) -> bool:
        return abs(self.total_assets - self.total_liabilities_and_equity) < Decimal('0.01')
    
    class Config:
        json_encoders = {Decimal: str}


class IncomeStatementItem(BaseModel):
    """Individual item in income statement."""
    account_code: str
    account_name: str
    amount: Decimal = Field(..., decimal_places=2)
    is_deduction: bool = False  # True for expenses/losses
    
    class Config:
        json_encoders = {Decimal: str}


class IncomeStatementSection(BaseModel):
    """Section of income statement."""
    section_name: str
    total_amount: Decimal = Field(..., decimal_places=2)
    items: List[IncomeStatementItem] = []
    
    class Config:
        json_encoders = {Decimal: str}


class IncomeStatement(BaseModel):
    """Complete income statement (multi-step format)."""
    entity_name: str
    period_start: date
    period_end: date
    
    # Revenue section
    revenue: IncomeStatementSection
    
    # Cost of goods sold
    cost_of_goods_sold: IncomeStatementSection
    
    # Gross profit
    gross_profit: Decimal = Field(..., decimal_places=2)
    
    # Operating expenses
    operating_expenses: IncomeStatementSection
    
    # Operating income
    operating_income: Decimal = Field(..., decimal_places=2)
    
    # Non-operating items
    other_income: IncomeStatementSection
    other_expenses: IncomeStatementSection
    
    # Income before tax
    income_before_tax: Decimal = Field(..., decimal_places=2)
    
    # Tax expense
    tax_expense: IncomeStatementSection
    
    # Net income
    net_income: Decimal = Field(..., decimal_places=2)
    
    class Config:
        json_encoders = {Decimal: str}


class EquityChange(BaseModel):
    """Individual change in equity during the period."""
    description: str
    amount: Decimal = Field(..., decimal_places=2)
    is_addition: bool = True


class StatementOfEquity(BaseModel):
    """Statement of changes in equity."""
    entity_name: str
    period_start: date
    period_end: date
    
    beginning_equity: Decimal = Field(..., decimal_places=2)
    changes: List[EquityChange] = []
    ending_equity: Decimal = Field(..., decimal_places=2)
    
    class Config:
        json_encoders = {Decimal: str}


class CashFlowActivity(str, Enum):
    """Cash flow activity classification."""
    OPERATING = "OPERATING"
    INVESTING = "INVESTING"
    FINANCING = "FINANCING"


class CashFlowItem(BaseModel):
    """Individual item in cash flow statement."""
    description: str
    amount: Decimal = Field(..., decimal_places=2)
    activity: CashFlowActivity
    is_inflow: bool = True
    
    class Config:
        json_encoders = {Decimal: str}


class CashFlowStatement(BaseModel):
    """Complete cash flow statement."""
    entity_name: str
    period_start: date
    period_end: date
    
    # Operating activities
    operating_activities: List[CashFlowItem] = []
    net_cash_operating: Decimal = Field(..., decimal_places=2)
    
    # Investing activities
    investing_activities: List[CashFlowItem] = []
    net_cash_investing: Decimal = Field(..., decimal_places=2)
    
    # Financing activities
    financing_activities: List[CashFlowItem] = []
    net_cash_financing: Decimal = Field(..., decimal_places=2)
    
    # Net change and ending balance
    net_change_in_cash: Decimal = Field(..., decimal_places=2)
    beginning_cash_balance: Decimal = Field(..., decimal_places=2)
    ending_cash_balance: Decimal = Field(..., decimal_places=2)
    
    class Config:
        json_encoders = {Decimal: str}


class FinancialRatios(BaseModel):
    """Key financial ratios for analysis."""
    entity_name: str
    statement_date: date
    
    # Liquidity ratios
    current_ratio: Decimal = Field(..., decimal_places=4)
    quick_ratio: Decimal = Field(..., decimal_places=4)
    cash_ratio: Decimal = Field(..., decimal_places=4)
    
    # Profitability ratios
    gross_profit_margin: Decimal = Field(..., decimal_places=4)
    operating_profit_margin: Decimal = Field(..., decimal_places=4)
    net_profit_margin: Decimal = Field(..., decimal_places=4)
    return_on_assets: Decimal = Field(..., decimal_places=4)
    return_on_equity: Decimal = Field(..., decimal_places=4)
    
    # Leverage ratios
    debt_to_equity: Decimal = Field(..., decimal_places=4)
    debt_to_assets: Decimal = Field(..., decimal_places=4)
    equity_multiplier: Decimal = Field(..., decimal_places=4)
    
    # Efficiency ratios
    asset_turnover: Decimal = Field(..., decimal_places=4)
    inventory_turnover: Optional[Decimal] = Field(None, decimal_places=4)
    receivables_turnover: Optional[Decimal] = Field(None, decimal_places=4)
    
    class Config:
        json_encoders = {Decimal: str}


class CompleteFinancialStatements(BaseModel):
    """Complete set of financial statements for a period."""
    entity_name: str
    period_start: date
    period_end: date
    
    trial_balance: TrialBalance
    balance_sheet: BalanceSheet
    income_statement: IncomeStatement
    statement_of_equity: StatementOfEquity
    cash_flow_statement: CashFlowStatement
    financial_ratios: FinancialRatios
    
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {Decimal: str}