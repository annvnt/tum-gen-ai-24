"""
Statement of Changes in Equity and Retained Earnings generator.
Creates comprehensive equity statements showing changes in equity accounts.
"""

from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional
import logging

from financial_analysis.models.accounting_models import (
    TrialBalance, StatementOfEquity, EquityChange, AccountType, AccountSubType
)

logger = logging.getLogger(__name__)


class EquityStatementGenerator:
    """Service for generating statements of changes in equity."""
    
    def __init__(self):
        self.equity_accounts = [
            AccountSubType.PAID_IN_CAPITAL,
            AccountSubType.RETAINED_EARNINGS,
            AccountSubType.TREASURY_STOCK,
            AccountSubType.ACCUMULATED_OTHER_COMPREHENSIVE_INCOME
        ]
    
    def generate_equity_statement(self, trial_balance: TrialBalance,
                                net_income: Decimal,
                                dividends: Optional[Decimal] = None,
                                period_start: Optional[date] = None,
                                period_end: Optional[date] = None) -> StatementOfEquity:
        """
        Generate statement of changes in equity from trial balance.
        
        Args:
            trial_balance: Validated trial balance
            net_income: Net income from income statement
            dividends: Dividends declared during period (optional)
            period_start: Start date of period (defaults to trial balance period)
            period_end: End date of period (defaults to trial balance period)
            
        Returns:
            Complete StatementOfEquity object
        """
        if period_start is None:
            period_start = trial_balance.period_start
        if period_end is None:
            period_end = trial_balance.period_end
        
        # Get equity accounts from trial balance
        equity_accounts = [
            acc for acc in trial_balance.accounts
            if acc.account_type == AccountType.EQUITY
        ]
        
        # Calculate beginning equity (this would typically come from prior period)
        # For now, we'll use current equity balances as proxy
        current_equity = self._calculate_current_equity(equity_accounts)
        
        # Build changes in equity
        changes = self._build_equity_changes(
            equity_accounts, net_income, dividends or Decimal('0')
        )
        
        # Calculate ending equity
        ending_equity = current_equity + sum(
            change.amount if change.is_addition else -change.amount
            for change in changes
        )
        
        equity_statement = StatementOfEquity(
            entity_name=trial_balance.entity_name,
            period_start=period_start,
            period_end=period_end,
            beginning_equity=current_equity,  # This should be from prior period
            changes=changes,
            ending_equity=ending_equity
        )
        
        # Validate equity statement
        self._validate_equity_statement(equity_statement)
        
        logger.info(f"Generated equity statement for {trial_balance.entity_name}")
        return equity_statement
    
    def _calculate_current_equity(self, equity_accounts: List) -> Decimal:
        """Calculate total current equity from equity accounts."""
        total_equity = Decimal('0')
        
        for account in equity_accounts:
            if account.account_subtype == AccountSubType.TREASURY_STOCK:
                # Treasury stock reduces equity
                total_equity -= abs(account.net_balance)
            else:
                # Other equity accounts increase equity
                total_equity += account.net_balance
        
        return total_equity
    
    def _build_equity_changes(self, equity_accounts: List, net_income: Decimal,
                            dividends: Decimal) -> List[EquityChange]:
        """Build list of changes in equity during the period."""
        changes = []
        
        # Net income (increases retained earnings)
        if net_income != 0:
            changes.append(EquityChange(
                description="Net Income",
                amount=net_income,
                is_addition=True
            ))
        
        # Dividends (decrease retained earnings)
        if dividends > 0:
            changes.append(EquityChange(
                description="Dividends Declared",
                amount=dividends,
                is_addition=False
            ))
        
        # Additional paid-in capital changes
        paid_in_capital_changes = [
            acc for acc in equity_accounts
            if acc.account_subtype == AccountSubType.PAID_IN_CAPITAL
        ]
        
        for account in paid_in_capital_changes:
            if account.net_balance != 0:
                changes.append(EquityChange(
                    description=f"{account.account_name}",
                    amount=abs(account.net_balance),
                    is_addition=account.net_balance > 0
                ))
        
        # Treasury stock transactions
        treasury_changes = [
            acc for acc in equity_accounts
            if acc.account_subtype == AccountSubType.TREASURY_STOCK
        ]
        
        for account in treasury_changes:
            if account.net_balance != 0:
                changes.append(EquityChange(
                    description=f"{account.account_name}",
                    amount=abs(account.net_balance),
                    is_addition=account.net_balance < 0  # Treasury stock reduces equity
                ))
        
        # Other comprehensive income changes
        oci_changes = [
            acc for acc in equity_accounts
            if acc.account_subtype == AccountSubType.ACCUMULATED_OTHER_COMPREHENSIVE_INCOME
        ]
        
        for account in oci_changes:
            if account.net_balance != 0:
                changes.append(EquityChange(
                    description=f"{account.account_name}",
                    amount=abs(account.net_balance),
                    is_addition=account.net_balance > 0
                ))
        
        return changes
    
    def generate_retained_earnings_statement(self, trial_balance: TrialBalance,
                                           net_income: Decimal,
                                           beginning_retained_earnings: Decimal,
                                           dividends: Optional[Decimal] = None,
                                           period_start: Optional[date] = None,
                                           period_end: Optional[date] = None) -> StatementOfEquity:
        """
        Generate simple retained earnings statement.
        
        Args:
            trial_balance: Validated trial balance
            net_income: Net income for the period
            beginning_retained_earnings: Retained earnings from prior period
            dividends: Dividends declared during period
            period_start: Start date of period
            period_end: End date of period
            
        Returns:
            StatementOfEquity focused on retained earnings
        """
        if period_start is None:
            period_start = trial_balance.period_start
        if period_end is None:
            period_end = trial_balance.period_end
        
        dividends_amount = dividends or Decimal('0')
        
        changes = [
            EquityChange(
                description="Beginning Retained Earnings",
                amount=beginning_retained_earnings,
                is_addition=True
            ),
            EquityChange(
                description="Net Income",
                amount=net_income,
                is_addition=True
            ),
            EquityChange(
                description="Dividends Declared",
                amount=dividends_amount,
                is_addition=False
            )
        ]
        
        ending_retained_earnings = (
            beginning_retained_earnings +
            net_income -
            dividends_amount
        )
        
        equity_statement = StatementOfEquity(
            entity_name=trial_balance.entity_name,
            period_start=period_start,
            period_end=period_end,
            beginning_equity=beginning_retained_earnings,
            changes=changes,
            ending_equity=ending_retained_earnings
        )
        
        return equity_statement
    
    def _validate_equity_statement(self, equity_statement: StatementOfEquity) -> None:
        """Validate equity statement calculations."""
        
        # Calculate ending equity from changes
        calculated_ending = equity_statement.beginning_equity
        for change in equity_statement.changes:
            if change.is_addition:
                calculated_ending += change.amount
            else:
                calculated_ending -= change.amount
        
        if abs(calculated_ending - equity_statement.ending_equity) > Decimal('0.01'):
            raise ValueError(
                f"Equity statement calculation error: "
                f"calculated ending equity={calculated_ending}, "
                f"reported ending equity={equity_statement.ending_equity}"
            )
        
        # Log validation success
        logger.info(
            f"Equity statement validated successfully: "
            f"Beginning Equity=${equity_statement.beginning_equity}, "
            f"Ending Equity=${equity_statement.ending_equity}"
        )
    
    def get_equity_analysis(self, equity_statement: StatementOfEquity) -> Dict:
        """Generate equity statement analysis metrics."""
        beginning_equity = equity_statement.beginning_equity
        ending_equity = equity_statement.ending_equity
        
        # Calculate changes
        total_additions = Decimal('0')
        total_deductions = Decimal('0')
        
        for change in equity_statement.changes:
            if change.description not in ["Beginning Retained Earnings", "Beginning Equity"]:
                if change.is_addition:
                    total_additions += change.amount
                else:
                    total_deductions += change.amount
        
        net_change = ending_equity - beginning_equity
        
        # Calculate growth rate
        growth_rate = (
            (net_change / beginning_equity * 100) if beginning_equity > 0 else Decimal('0')
        )
        
        # Identify key changes
        key_changes = [
            {
                "description": change.description,
                "amount": float(change.amount),
                "type": "addition" if change.is_addition else "deduction"
            }
            for change in equity_statement.changes
            if change.description not in ["Beginning Retained Earnings", "Beginning Equity"]
        ]
        
        return {
            "beginning_equity": float(beginning_equity),
            "ending_equity": float(ending_equity),
            "net_change": float(net_change),
            "growth_rate": float(growth_rate),
            "total_additions": float(total_additions),
            "total_deductions": float(total_deductions),
            "key_changes": key_changes
        }