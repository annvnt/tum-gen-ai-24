"""
GAAP/IFRS compliant Balance Sheet generator.
Creates professional balance sheets from trial balance data with proper classification.
"""

from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional
import logging

from financial_analysis.models.accounting_models import (
    TrialBalance, BalanceSheet, BalanceSheetSection, BalanceSheetItem,
    AccountType, AccountSubType
)

logger = logging.getLogger(__name__)


class BalanceSheetGenerator:
    """Service for generating GAAP/IFRS compliant balance sheets."""
    
    def __init__(self):
        self.current_ratio_threshold = Decimal('1.0')  # 1 year threshold for current vs non-current
    
    def generate_balance_sheet(self, trial_balance: TrialBalance, 
                             statement_date: Optional[date] = None) -> BalanceSheet:
        """
        Generate comprehensive balance sheet from trial balance.
        
        Args:
            trial_balance: Validated trial balance
            statement_date: Date for the balance sheet (defaults to period end)
            
        Returns:
            Complete BalanceSheet object
        """
        if statement_date is None:
            statement_date = trial_balance.period_end
        
        # Classify accounts into balance sheet sections
        assets = self._classify_assets(trial_balance)
        liabilities = self._classify_liabilities(trial_balance)
        equity = self._classify_equity(trial_balance)
        
        # Create balance sheet
        balance_sheet = BalanceSheet(
            entity_name=trial_balance.entity_name,
            statement_date=statement_date,
            assets=assets,
            liabilities=liabilities,
            equity=equity
        )
        
        # Validate balance sheet
        self._validate_balance_sheet(balance_sheet)
        
        logger.info(f"Generated balance sheet for {trial_balance.entity_name}")
        return balance_sheet
    
    def _classify_assets(self, trial_balance: TrialBalance) -> BalanceSheetSection:
        """Classify asset accounts into balance sheet format."""
        asset_accounts = [
            acc for acc in trial_balance.accounts 
            if acc.account_type == AccountType.ASSET
        ]
        
        # Sort by liquidity (current first, then non-current)
        current_assets = []
        non_current_assets = []
        
        for account in asset_accounts:
            item = BalanceSheetItem(
                account_code=account.account_code,
                account_name=account.account_name,
                amount=abs(account.net_balance),
                account_subtype=account.account_subtype
            )
            
            if account.account_subtype in [
                AccountSubType.CURRENT_ASSET,
                AccountSubType.INVESTMENT  # Short-term investments
            ]:
                current_assets.append(item)
            else:
                non_current_assets.append(item)
        
        # Group by subtype for better organization
        current_assets_grouped = self._group_by_subtype(current_assets)
        non_current_assets_grouped = self._group_by_subtype(non_current_assets)
        
        # Combine all assets
        all_assets = current_assets_grouped + non_current_assets_grouped
        total_assets = sum(asset.amount for asset in all_assets)
        
        return BalanceSheetSection(
            section_name="Assets",
            total_amount=total_assets,
            items=all_assets
        )
    
    def _classify_liabilities(self, trial_balance: TrialBalance) -> BalanceSheetSection:
        """Classify liability accounts into balance sheet format."""
        liability_accounts = [
            acc for acc in trial_balance.accounts 
            if acc.account_type == AccountType.LIABILITY
        ]
        
        current_liabilities = []
        non_current_liabilities = []
        
        for account in liability_accounts:
            item = BalanceSheetItem(
                account_code=account.account_code,
                account_name=account.account_name,
                amount=account.net_balance,  # Liabilities are normally credit balances
                account_subtype=account.account_subtype
            )
            
            if account.account_subtype == AccountSubType.CURRENT_LIABILITY:
                current_liabilities.append(item)
            else:
                non_current_liabilities.append(item)
        
        # Group by subtype
        current_liabilities_grouped = self._group_by_subtype(current_liabilities)
        non_current_liabilities_grouped = self._group_by_subtype(non_current_liabilities)
        
        # Combine all liabilities
        all_liabilities = current_liabilities_grouped + non_current_liabilities_grouped
        total_liabilities = sum(liab.amount for liab in all_liabilities)
        
        return BalanceSheetSection(
            section_name="Liabilities",
            total_amount=total_liabilities,
            items=all_liabilities
        )
    
    def _classify_equity(self, trial_balance: TrialBalance) -> BalanceSheetSection:
        """Classify equity accounts into balance sheet format."""
        equity_accounts = [
            acc for acc in trial_balance.accounts 
            if acc.account_type == AccountType.EQUITY
        ]
        
        equity_items = []
        for account in equity_accounts:
            # Treasury stock is normally negative (debit balance)
            amount = account.net_balance
            if account.account_subtype == AccountSubType.TREASURY_STOCK:
                amount = -abs(amount)  # Ensure negative
            
            item = BalanceSheetItem(
                account_code=account.account_code,
                account_name=account.account_name,
                amount=abs(amount),
                account_subtype=account.account_subtype
            )
            equity_items.append(item)
        
        # Sort equity accounts in standard order
        equity_order = [
            AccountSubType.PAID_IN_CAPITAL,
            AccountSubType.RETAINED_EARNINGS,
            AccountSubType.TREASURY_STOCK,
            AccountSubType.ACCUMULATED_OTHER_COMPREHENSIVE_INCOME
        ]
        
        # Group by subtype in order
        ordered_equity = []
        for subtype in equity_order:
            for item in equity_items:
                if item.account_subtype == subtype:
                    ordered_equity.append(item)
        
        # Add remaining items
        for item in equity_items:
            if item not in ordered_equity:
                ordered_equity.append(item)
        
        total_equity = sum(item.amount for item in ordered_equity)
        
        return BalanceSheetSection(
            section_name="Stockholders' Equity",
            total_amount=total_equity,
            items=ordered_equity
        )
    
    def _group_by_subtype(self, items: List[BalanceSheetItem]) -> List[BalanceSheetItem]:
        """Group items by subtype and sort within each group."""
        if not items:
            return []
        
        # Group by subtype
        grouped = {}
        for item in items:
            if item.account_subtype not in grouped:
                grouped[item.account_subtype] = []
            grouped[item.account_subtype].append(item)
        
        # Sort each group and flatten
        result = []
        subtype_order = [
            # Current assets
            AccountSubType.CURRENT_ASSET,
            # Non-current assets
            AccountSubType.INVESTMENT,
            AccountSubType.PROPERTY_PLANT_EQUIPMENT,
            AccountSubType.INTANGIBLE_ASSET,
            AccountSubType.NON_CURRENT_ASSET,
            # Current liabilities
            AccountSubType.CURRENT_LIABILITY,
            # Non-current liabilities
            AccountSubType.NON_CURRENT_LIABILITY,
            # Equity
            AccountSubType.PAID_IN_CAPITAL,
            AccountSubType.RETAINED_EARNINGS,
            AccountSubType.TREASURY_STOCK,
            AccountSubType.ACCUMULATED_OTHER_COMPREHENSIVE_INCOME
        ]
        
        for subtype in subtype_order:
            if subtype in grouped:
                # Sort items within subtype by account code
                sorted_items = sorted(grouped[subtype], key=lambda x: x.account_code)
                result.extend(sorted_items)
        
        # Add any remaining items
        for subtype, items in grouped.items():
            if subtype not in subtype_order:
                sorted_items = sorted(items, key=lambda x: x.account_code)
                result.extend(sorted_items)
        
        return result
    
    def _validate_balance_sheet(self, balance_sheet: BalanceSheet) -> None:
        """Validate balance sheet for GAAP/IFRS compliance."""
        if not balance_sheet.is_balanced:
            difference = abs(balance_sheet.total_assets - balance_sheet.total_liabilities_and_equity)
            raise ValueError(
                f"Balance sheet is not balanced. Difference: ${difference}. "
                f"Assets: ${balance_sheet.total_assets}, "
                f"Liabilities + Equity: ${balance_sheet.total_liabilities_and_equity}"
            )
        
        # Check for zero or negative total assets
        if balance_sheet.total_assets <= 0:
            raise ValueError("Total assets must be positive")
        
        # Log validation success
        logger.info(
            f"Balance sheet validated successfully: "
            f"Assets=${balance_sheet.total_assets}, "
            f"Liabilities=${balance_sheet.liabilities.total_amount}, "
            f"Equity=${balance_sheet.equity.total_amount}"
        )
    
    def get_balance_sheet_analysis(self, balance_sheet: BalanceSheet) -> Dict:
        """Generate balance sheet analysis metrics."""
        total_assets = balance_sheet.total_assets
        total_liabilities = balance_sheet.liabilities.total_amount
        total_equity = balance_sheet.equity.total_amount
        
        # Calculate ratios
        debt_to_equity = (total_liabilities / total_equity) if total_equity > 0 else Decimal('0')
        equity_ratio = (total_equity / total_assets) if total_assets > 0 else Decimal('0')
        debt_ratio = (total_liabilities / total_assets) if total_assets > 0 else Decimal('0')
        
        # Current vs non-current classification
        current_assets = sum(
            item.amount for item in balance_sheet.assets.items
            if item.account_subtype == AccountSubType.CURRENT_ASSET
        )
        
        current_liabilities = sum(
            item.amount for item in balance_sheet.liabilities.items
            if item.account_subtype == AccountSubType.CURRENT_LIABILITY
        )
        
        current_ratio = (current_assets / current_liabilities) if current_liabilities > 0 else Decimal('0')
        working_capital = current_assets - current_liabilities
        
        return {
            "total_assets": float(total_assets),
            "total_liabilities": float(total_liabilities),
            "total_equity": float(total_equity),
            "debt_to_equity_ratio": float(debt_to_equity),
            "equity_ratio": float(equity_ratio),
            "debt_ratio": float(debt_ratio),
            "current_ratio": float(current_ratio),
            "working_capital": float(working_capital),
            "current_assets": float(current_assets),
            "current_liabilities": float(current_liabilities)
        }