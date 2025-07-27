"""
Cash Flow Statement generator with both direct and indirect methods.
Creates comprehensive cash flow statements from trial balance and income statement data.
"""

from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional, Tuple
import logging

from financial_analysis.models.accounting_models import (
    TrialBalance, CashFlowStatement, CashFlowItem, CashFlowActivity,
    AccountType, AccountSubType, BalanceSheet
)

logger = logging.getLogger(__name__)


class CashFlowGenerator:
    """Service for generating cash flow statements using direct and indirect methods."""
    
    def __init__(self):
        self.cash_account_codes = ['1000', '1010', '1020']  # Standard cash account codes
    
    def generate_cash_flow_statement(self, trial_balance: TrialBalance,
                                   net_income: Decimal,
                                   beginning_cash_balance: Decimal,
                                   method: str = "indirect",
                                   period_start: Optional[date] = None,
                                   period_end: Optional[date] = None) -> CashFlowStatement:
        """
        Generate comprehensive cash flow statement.
        
        Args:
            trial_balance: Validated trial balance
            net_income: Net income from income statement
            beginning_cash_balance: Cash balance at beginning of period
            method: "direct" or "indirect" method for operating activities
            period_start: Start date of period
            period_end: End date of period
            
        Returns:
            Complete CashFlowStatement object
        """
        if period_start is None:
            period_start = trial_balance.period_start
        if period_end is None:
            period_end = trial_balance.period_end
        
        # Calculate ending cash balance from trial balance
        ending_cash_balance = self._get_ending_cash_balance(trial_balance)
        
        # Build cash flow sections based on method
        if method.lower() == "direct":
            operating_activities = self._build_operating_activities_direct(trial_balance)
        else:
            operating_activities = self._build_operating_activities_indirect(
                trial_balance, net_income
            )
        
        investing_activities = self._build_investing_activities(trial_balance)
        financing_activities = self._build_financing_activities(trial_balance)
        
        # Calculate net cash flows
        net_cash_operating = sum(
            item.amount if item.is_inflow else -item.amount
            for item in operating_activities
        )
        
        net_cash_investing = sum(
            item.amount if item.is_inflow else -item.amount
            for item in investing_activities
        )
        
        net_cash_financing = sum(
            item.amount if item.is_inflow else -item.amount
            for item in financing_activities
        )
        
        # Calculate net change
        net_change_in_cash = net_cash_operating + net_cash_investing + net_cash_financing
        
        # Validate cash flow
        expected_ending = beginning_cash_balance + net_change_in_cash
        if abs(expected_ending - ending_cash_balance) > Decimal('0.01'):
            logger.warning(
                f"Cash flow reconciliation warning: "
                f"expected ending cash={expected_ending}, "
                f"actual ending cash={ending_cash_balance}"
            )
        
        cash_flow_statement = CashFlowStatement(
            entity_name=trial_balance.entity_name,
            period_start=period_start,
            period_end=period_end,
            operating_activities=operating_activities,
            net_cash_operating=net_cash_operating,
            investing_activities=investing_activities,
            net_cash_investing=net_cash_investing,
            financing_activities=financing_activities,
            net_cash_financing=net_cash_financing,
            net_change_in_cash=net_change_in_cash,
            beginning_cash_balance=beginning_cash_balance,
            ending_cash_balance=ending_cash_balance
        )
        
        # Validate cash flow statement
        self._validate_cash_flow_statement(cash_flow_statement)
        
        logger.info(f"Generated cash flow statement for {trial_balance.entity_name}")
        return cash_flow_statement
    
    def _get_ending_cash_balance(self, trial_balance) -> Decimal:
        """Get ending cash balance from trial balance."""
        cash_accounts = [
            acc for acc in trial_balance.accounts
            if (acc.account_type == AccountType.ASSET and
                acc.account_subtype == AccountSubType.CURRENT_ASSET and
                any(code in acc.account_code for code in self.cash_account_codes))
        ]
        
        total_cash = sum(
            acc.net_balance for acc in cash_accounts
            if acc.net_balance > 0
        )
        
        return total_cash
    
    def _build_operating_activities_direct(self, trial_balance) -> List[CashFlowItem]:
        """Build operating activities using direct method."""
        operating_items = []
        
        # Cash receipts from customers
        revenue_accounts = [
            acc for acc in trial_balance.accounts
            if acc.account_type == AccountType.REVENUE
        ]
        total_revenue = sum(abs(acc.net_balance) for acc in revenue_accounts)
        
        if total_revenue > 0:
            operating_items.append(CashFlowItem(
                description="Cash received from customers",
                amount=total_revenue,
                activity=CashFlowActivity.OPERATING,
                is_inflow=True
            ))
        
        # Cash payments to suppliers
        cogs_accounts = [
            acc for acc in trial_balance.accounts
            if acc.account_subtype == AccountSubType.COST_OF_GOODS_SOLD
        ]
        total_cogs = sum(abs(acc.net_balance) for acc in cogs_accounts)
        
        if total_cogs > 0:
            operating_items.append(CashFlowItem(
                description="Cash paid to suppliers",
                amount=total_cogs,
                activity=CashFlowActivity.OPERATING,
                is_inflow=False
            ))
        
        # Cash payments for operating expenses
        operating_expense_accounts = [
            acc for acc in trial_balance.accounts
            if acc.account_subtype in [
                AccountSubType.SELLING_EXPENSE,
                AccountSubType.ADMINISTRATIVE_EXPENSE,
                AccountSubType.OPERATING_EXPENSE
            ]
        ]
        total_operating_expenses = sum(abs(acc.net_balance) for acc in operating_expense_accounts)
        
        if total_operating_expenses > 0:
            operating_items.append(CashFlowItem(
                description="Cash paid for operating expenses",
                amount=total_operating_expenses,
                activity=CashFlowActivity.OPERATING,
                is_inflow=False
            ))
        
        # Cash payments for interest and taxes
        interest_accounts = [
            acc for acc in trial_balance.accounts
            if acc.account_subtype == AccountSubType.INTEREST_EXPENSE
        ]
        total_interest = sum(abs(acc.net_balance) for acc in interest_accounts)
        
        if total_interest > 0:
            operating_items.append(CashFlowItem(
                description="Interest paid",
                amount=total_interest,
                activity=CashFlowActivity.OPERATING,
                is_inflow=False
            ))
        
        tax_accounts = [
            acc for acc in trial_balance.accounts
            if acc.account_subtype == AccountSubType.TAX_EXPENSE
        ]
        total_tax = sum(abs(acc.net_balance) for acc in tax_accounts)
        
        if total_tax > 0:
            operating_items.append(CashFlowItem(
                description="Income taxes paid",
                amount=total_tax,
                activity=CashFlowActivity.OPERATING,
                is_inflow=False
            ))
        
        return operating_items
    
    def _build_operating_activities_indirect(self, trial_balance, net_income: Decimal) -> List[CashFlowItem]:
        """Build operating activities using indirect method."""
        operating_items = []
        
        # Start with net income
        operating_items.append(CashFlowItem(
            description="Net income",
            amount=net_income,
            activity=CashFlowActivity.OPERATING,
            is_inflow=True
        ))
        
        # Add back depreciation and amortization
        depreciation_accounts = [
            acc for acc in trial_balance.accounts
            if acc.account_subtype == AccountSubType.DEPRECIATION_EXPENSE
        ]
        total_depreciation = sum(abs(acc.net_balance) for acc in depreciation_accounts)
        
        if total_depreciation > 0:
            operating_items.append(CashFlowItem(
                description="Depreciation and amortization",
                amount=total_depreciation,
                activity=CashFlowActivity.OPERATING,
                is_inflow=True
            ))
        
        # Changes in working capital accounts
        working_capital_changes = self._calculate_working_capital_changes(trial_balance)
        
        for change in working_capital_changes:
            operating_items.append(CashFlowItem(
                description=change["description"],
                amount=change["amount"],
                activity=CashFlowActivity.OPERATING,
                is_inflow=change["is_inflow"]
            ))
        
        return operating_items
    
    def _calculate_working_capital_changes(self, trial_balance) -> List[Dict]:
        """Calculate changes in working capital accounts."""
        changes = []
        
        # Current assets (increase is outflow, decrease is inflow)
        current_asset_accounts = [
            acc for acc in trial_balance.accounts
            if acc.account_subtype == AccountSubType.CURRENT_ASSET
        ]
        
        for account in current_asset_accounts:
            if account.account_code not in self.cash_account_codes:
                balance = account.net_balance
                if balance > 0:
                    changes.append({
                        "description": f"Increase in {account.account_name}",
                        "amount": abs(balance),
                        "is_inflow": False
                    })
                elif balance < 0:
                    changes.append({
                        "description": f"Decrease in {account.account_name}",
                        "amount": abs(balance),
                        "is_inflow": True
                    })
        
        # Current liabilities (increase is inflow, decrease is outflow)
        current_liability_accounts = [
            acc for acc in trial_balance.accounts
            if acc.account_subtype == AccountSubType.CURRENT_LIABILITY
        ]
        
        for account in current_liability_accounts:
            balance = account.net_balance
            if balance > 0:
                changes.append({
                    "description": f"Increase in {account.account_name}",
                    "amount": abs(balance),
                    "is_inflow": True
                })
            elif balance < 0:
                changes.append({
                    "description": f"Decrease in {account.account_name}",
                    "amount": abs(balance),
                    "is_inflow": False
                })
        
        return changes
    
    def _build_investing_activities(self, trial_balance) -> List[CashFlowItem]:
        """Build investing activities section."""
        investing_items = []
        
        # Property, plant, and equipment changes
        ppe_accounts = [
            acc for acc in trial_balance.accounts
            if acc.account_subtype == AccountSubType.PROPERTY_PLANT_EQUIPMENT
        ]
        
        for account in ppe_accounts:
            balance = account.net_balance
            if balance > 0:
                investing_items.append(CashFlowItem(
                    description=f"Purchase of {account.account_name}",
                    amount=abs(balance),
                    activity=CashFlowActivity.INVESTING,
                    is_inflow=False
                ))
            elif balance < 0:
                investing_items.append(CashFlowItem(
                    description=f"Sale of {account.account_name}",
                    amount=abs(balance),
                    activity=CashFlowActivity.INVESTING,
                    is_inflow=True
                ))
        
        # Investment changes
        investment_accounts = [
            acc for acc in trial_balance.accounts
            if acc.account_subtype == AccountSubType.INVESTMENT
        ]
        
        for account in investment_accounts:
            balance = account.net_balance
            if balance > 0:
                investing_items.append(CashFlowItem(
                    description=f"Purchase of {account.account_name}",
                    amount=abs(balance),
                    activity=CashFlowActivity.INVESTING,
                    is_inflow=False
                ))
            elif balance < 0:
                investing_items.append(CashFlowItem(
                    description=f"Sale of {account.account_name}",
                    amount=abs(balance),
                    activity=CashFlowActivity.INVESTING,
                    is_inflow=True
                ))
        
        # Intangible asset changes
        intangible_accounts = [
            acc for acc in trial_balance.accounts
            if acc.account_subtype == AccountSubType.INTANGIBLE_ASSET
        ]
        
        for account in intangible_accounts:
            balance = account.net_balance
            if balance > 0:
                investing_items.append(CashFlowItem(
                    description=f"Purchase of {account.account_name}",
                    amount=abs(balance),
                    activity=CashFlowActivity.INVESTING,
                    is_inflow=False
                ))
            elif balance < 0:
                investing_items.append(CashFlowItem(
                    description=f"Sale of {account.account_name}",
                    amount=abs(balance),
                    activity=CashFlowActivity.INVESTING,
                    is_inflow=True
                ))
        
        return investing_items
    
    def _build_financing_activities(self, trial_balance) -> List[CashFlowItem]:
        """Build financing activities section."""
        financing_items = []
        
        # Long-term liability changes
        long_term_liabilities = [
            acc for acc in trial_balance.accounts
            if acc.account_subtype == AccountSubType.NON_CURRENT_LIABILITY
        ]
        
        for account in long_term_liabilities:
            balance = account.net_balance
            if balance > 0:
                financing_items.append(CashFlowItem(
                    description=f"Proceeds from {account.account_name}",
                    amount=abs(balance),
                    activity=CashFlowActivity.FINANCING,
                    is_inflow=True
                ))
            elif balance < 0:
                financing_items.append(CashFlowItem(
                    description=f"Repayment of {account.account_name}",
                    amount=abs(balance),
                    activity=CashFlowActivity.FINANCING,
                    is_inflow=False
                ))
        
        # Equity changes (excluding retained earnings)
        equity_accounts = [
            acc for acc in trial_balance.accounts
            if acc.account_type == AccountType.EQUITY
        ]
        
        for account in equity_accounts:
            if account.account_subtype in [AccountSubType.PAID_IN_CAPITAL]:
                balance = account.net_balance
                if balance > 0:
                    financing_items.append(CashFlowItem(
                        description=f"Proceeds from {account.account_name}",
                        amount=abs(balance),
                        activity=CashFlowActivity.FINANCING,
                        is_inflow=True
                    ))
                elif balance < 0:
                    financing_items.append(CashFlowItem(
                        description=f"Repurchase of {account.account_name}",
                        amount=abs(balance),
                        activity=CashFlowActivity.FINANCING,
                        is_inflow=False
                    ))
        
        # Treasury stock transactions
        treasury_accounts = [
            acc for acc in equity_accounts
            if account.account_subtype == AccountSubType.TREASURY_STOCK
        ]
        
        for account in treasury_accounts:
            balance = account.net_balance
            if balance > 0:
                financing_items.append(CashFlowItem(
                    description=f"Purchase of treasury stock",
                    amount=abs(balance),
                    activity=CashFlowActivity.FINANCING,
                    is_inflow=False
                ))
            elif balance < 0:
                financing_items.append(CashFlowItem(
                    description=f"Sale of treasury stock",
                    amount=abs(balance),
                    activity=CashFlowActivity.FINANCING,
                    is_inflow=True
                ))
        
        return financing_items
    
    def _validate_cash_flow_statement(self, cash_flow_statement: CashFlowStatement) -> None:
        """Validate cash flow statement calculations."""
        
        # Check net change calculation
        expected_net_change = (
            cash_flow_statement.net_cash_operating +
            cash_flow_statement.net_cash_investing +
            cash_flow_statement.net_cash_financing
        )
        
        if abs(expected_net_change - cash_flow_statement.net_change_in_cash) > Decimal('0.01'):
            raise ValueError(
                f"Net change calculation error: "
                f"calculated={expected_net_change}, "
                f"reported={cash_flow_statement.net_change_in_cash}"
            )
        
        # Check ending balance calculation
        expected_ending = (
            cash_flow_statement.beginning_cash_balance +
            cash_flow_statement.net_change_in_cash
        )
        
        if abs(expected_ending - cash_flow_statement.ending_cash_balance) > Decimal('0.01'):
            raise ValueError(
                f"Ending cash balance calculation error: "
                f"calculated={expected_ending}, "
                f"reported={cash_flow_statement.ending_cash_balance}"
            )
        
        # Log validation success
        logger.info(
            f"Cash flow statement validated successfully: "
            f"Operating=${cash_flow_statement.net_cash_operating}, "
            f"Investing=${cash_flow_statement.net_cash_investing}, "
            f"Financing=${cash_flow_statement.net_cash_financing}"
        )
    
    def get_cash_flow_analysis(self, cash_flow_statement: CashFlowStatement) -> Dict:
        """Generate cash flow statement analysis metrics."""
        
        operating_cash_flow = cash_flow_statement.net_cash_operating
        investing_cash_flow = cash_flow_statement.net_cash_investing
        financing_cash_flow = cash_flow_statement.net_cash_financing
        net_change = cash_flow_statement.net_change_in_cash
        
        # Quality metrics
        operating_cash_flow_ratio = (
            abs(operating_cash_flow / operating_cash_flow) if operating_cash_flow != 0 else Decimal('0')
        )
        
        # Cash flow patterns
        cash_flow_pattern = self._determine_cash_flow_pattern(
            operating_cash_flow, investing_cash_flow, financing_cash_flow
        )
        
        return {
            "net_operating_cash_flow": float(operating_cash_flow),
            "net_investing_cash_flow": float(investing_cash_flow),
            "net_financing_cash_flow": float(financing_cash_flow),
            "net_change_in_cash": float(net_change),
            "beginning_cash_balance": float(cash_flow_statement.beginning_cash_balance),
            "ending_cash_balance": float(cash_flow_statement.ending_cash_balance),
            "operating_cash_flow_ratio": float(operating_cash_flow_ratio),
            "cash_flow_pattern": cash_flow_pattern,
            "is_positive_operating": operating_cash_flow > 0,
            "is_positive_investing": investing_cash_flow > 0,
            "is_positive_financing": financing_cash_flow > 0
        }
    
    def _determine_cash_flow_pattern(self, operating: Decimal, investing: Decimal, financing: Decimal) -> str:
        """Determine cash flow pattern based on signs of cash flows."""
        patterns = {
            (True, False, True): "Growth (O+, I-, F+)",
            (True, False, False): "Mature (O+, I-, F-)",
            (True, True, False): "Declining (O+, I+, F-)",
            (False, False, True): "Startup (O-, I-, F+)",
            (False, True, True): "Turnaround (O-, I+, F+)",
            (False, True, False): "Distress (O-, I+, F-)",
        }
        
        key = (operating > 0, investing > 0, financing > 0)
        return patterns.get(key, "Mixed Pattern")