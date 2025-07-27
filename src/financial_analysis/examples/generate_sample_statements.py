"""
Example script to demonstrate the complete accounting report generation system.
Creates sample trial balance data and generates all financial statements.
"""

import pandas as pd
from datetime import date, timedelta
from decimal import Decimal
import os

from financial_analysis.services.complete_financial_service import CompleteFinancialService
from financial_analysis.services.trial_balance_processor import TrialBalanceProcessor
from financial_analysis.models.accounting_models import (
    TrialBalance, TrialBalanceAccount, AccountType, AccountSubType
)


def create_sample_trial_balance() -> TrialBalance:
    """Create a sample trial balance for demonstration."""
    
    # Sample accounts for a retail business
    accounts = [
        # Assets - Current
        TrialBalanceAccount(
            account_code="1000",
            account_name="Cash",
            account_type=AccountType.ASSET,
            account_subtype=AccountSubType.CURRENT_ASSET,
            debit_balance=Decimal("25000.00"),
            credit_balance=None
        ),
        TrialBalanceAccount(
            account_code="1100",
            account_name="Accounts Receivable",
            account_type=AccountType.ASSET,
            account_subtype=AccountSubType.CURRENT_ASSET,
            debit_balance=Decimal("15000.00"),
            credit_balance=None
        ),
        TrialBalanceAccount(
            account_code="1200",
            account_name="Inventory",
            account_type=AccountType.ASSET,
            account_subtype=AccountSubType.CURRENT_ASSET,
            debit_balance=Decimal("35000.00"),
            credit_balance=None
        ),
        TrialBalanceAccount(
            account_code="1300",
            account_name="Prepaid Expenses",
            account_type=AccountType.ASSET,
            account_subtype=AccountSubType.CURRENT_ASSET,
            debit_balance=Decimal("5000.00"),
            credit_balance=None
        ),
        
        # Assets - Non-Current
        TrialBalanceAccount(
            account_code="1500",
            account_name="Equipment",
            account_type=AccountType.ASSET,
            account_subtype=AccountSubType.PROPERTY_PLANT_EQUIPMENT,
            debit_balance=Decimal("80000.00"),
            credit_balance=None
        ),
        TrialBalanceAccount(
            account_code="1510",
            account_name="Accumulated Depreciation - Equipment",
            account_type=AccountType.ASSET,
            account_subtype=AccountSubType.PROPERTY_PLANT_EQUIPMENT,
            debit_balance=None,
            credit_balance=Decimal("20000.00")
        ),
        
        # Liabilities - Current
        TrialBalanceAccount(
            account_code="2000",
            account_name="Accounts Payable",
            account_type=AccountType.LIABILITY,
            account_subtype=AccountSubType.CURRENT_LIABILITY,
            debit_balance=None,
            credit_balance=Decimal("12000.00")
        ),
        TrialBalanceAccount(
            account_code="2100",
            account_name="Accrued Expenses",
            account_type=AccountType.LIABILITY,
            account_subtype=AccountSubType.CURRENT_LIABILITY,
            debit_balance=None,
            credit_balance=Decimal("8000.00")
        ),
        
        # Equity
        TrialBalanceAccount(
            account_code="3000",
            account_name="Common Stock",
            account_type=AccountType.EQUITY,
            account_subtype=AccountSubType.PAID_IN_CAPITAL,
            debit_balance=None,
            credit_balance=Decimal("50000.00")
        ),
        TrialBalanceAccount(
            account_code="3100",
            account_name="Retained Earnings",
            account_type=AccountType.EQUITY,
            account_subtype=AccountSubType.RETAINED_EARNINGS,
            debit_balance=None,
            credit_balance=Decimal("45000.00")
        ),
        
        # Revenue
        TrialBalanceAccount(
            account_code="4000",
            account_name="Sales Revenue",
            account_type=AccountType.REVENUE,
            account_subtype=AccountSubType.OPERATING_REVENUE,
            debit_balance=None,
            credit_balance=Decimal("200000.00")
        ),
        
        # Cost of Goods Sold
        TrialBalanceAccount(
            account_code="5000",
            account_name="Cost of Goods Sold",
            account_type=AccountType.EXPENSE,
            account_subtype=AccountSubType.COST_OF_GOODS_SOLD,
            debit_balance=Decimal("120000.00"),
            credit_balance=None
        ),
        
        # Operating Expenses
        TrialBalanceAccount(
            account_code="6000",
            account_name="Selling Expenses",
            account_type=AccountType.EXPENSE,
            account_subtype=AccountSubType.SELLING_EXPENSE,
            debit_balance=Decimal("25000.00"),
            credit_balance=None
        ),
        TrialBalanceAccount(
            account_code="6100",
            account_name="Administrative Expenses",
            account_type=AccountType.EXPENSE,
            account_subtype=AccountSubType.ADMINISTRATIVE_EXPENSE,
            debit_balance=Decimal("15000.00"),
            credit_balance=None
        ),
        TrialBalanceAccount(
            account_code="6200",
            account_name="Depreciation Expense",
            account_type=AccountType.EXPENSE,
            account_subtype=AccountSubType.DEPRECIATION_EXPENSE,
            debit_balance=Decimal("8000.00"),
            credit_balance=None
        ),
        
        # Other Expenses
        TrialBalanceAccount(
            account_code="6300",
            account_name="Interest Expense",
            account_type=AccountType.EXPENSE,
            account_subtype=AccountSubType.INTEREST_EXPENSE,
            debit_balance=Decimal("3000.00"),
            credit_balance=None
        ),
        TrialBalanceAccount(
            account_code="6400",
            account_name="Income Tax Expense",
            account_type=AccountType.EXPENSE,
            account_subtype=AccountSubType.TAX_EXPENSE,
            debit_balance=Decimal("9000.00"),
            credit_balance=None
        ),
    ]
    
    period_end = date(2024, 12, 31)
    period_start = date(2024, 1, 1)
    
    trial_balance = TrialBalance(
        entity_name="Sample Retail Company Inc.",
        period_start=period_start,
        period_end=period_end,
        accounts=accounts
    )
    
    return trial_balance


def create_sample_excel_file(file_path: str) -> None:
    """Create a sample Excel trial balance file."""
    
    data = [
        # Account Code, Account Name, Debit, Credit
        ["1000", "Cash", 25000.00, 0.00],
        ["1100", "Accounts Receivable", 15000.00, 0.00],
        ["1200", "Inventory", 35000.00, 0.00],
        ["1300", "Prepaid Expenses", 5000.00, 0.00],
        ["1500", "Equipment", 80000.00, 0.00],
        ["1510", "Accumulated Depreciation", 0.00, 20000.00],
        ["2000", "Accounts Payable", 0.00, 12000.00],
        ["2100", "Accrued Expenses", 0.00, 8000.00],
        ["3000", "Common Stock", 0.00, 50000.00],
        ["3100", "Retained Earnings", 0.00, 45000.00],
        ["4000", "Sales Revenue", 0.00, 200000.00],
        ["5000", "Cost of Goods Sold", 120000.00, 0.00],
        ["6000", "Selling Expenses", 25000.00, 0.00],
        ["6100", "Administrative Expenses", 15000.00, 0.00],
        ["6200", "Depreciation Expense", 8000.00, 0.00],
        ["6300", "Interest Expense", 3000.00, 0.00],
        ["6400", "Income Tax Expense", 9000.00, 0.00],
    ]
    
    df = pd.DataFrame(data, columns=["Account Code", "Account Name", "Debit", "Credit"])
    df.to_excel(file_path, index=False, sheet_name="Trial Balance")
    
    print(f"Sample Excel file created at: {file_path}")


def demonstrate_complete_system():
    """Demonstrate the complete accounting report generation system."""
    
    print("=== Financial Statement Generation Demo ===\n")
    
    # Initialize services
    service = CompleteFinancialService()
    
    # Create sample data
    trial_balance = create_sample_trial_balance()
    
    # Generate complete financial statements
    beginning_cash_balance = Decimal("20000.00")
    beginning_retained_earnings = Decimal("40000.00")
    dividends = Decimal("5000.00")
    
    print("1. Generating complete financial statements...")
    complete_statements = service.generate_complete_financial_statements(
        trial_balance=trial_balance,
        beginning_cash_balance=beginning_cash_balance,
        beginning_retained_earnings=beginning_retained_earnings,
        dividends=dividends,
        cash_flow_method="indirect"
    )
    
    print("✓ Complete financial statements generated successfully\n")
    
    # Display key results
    print("2. Key Financial Results:")
    print(f"   Entity: {complete_statements.entity_name}")
    print(f"   Period: {complete_statements.period_start} to {complete_statements.period_end}")
    print(f"   Net Income: ${complete_statements.income_statement.net_income:,.2f}")
    print(f"   Total Assets: ${complete_statements.balance_sheet.total_assets:,.2f}")
    print(f"   Total Equity: ${complete_statements.balance_sheet.equity.total_amount:,.2f}")
    print(f"   Cash Position: ${complete_statements.cash_flow_statement.ending_cash_balance:,.2f}")
    
    # Display financial ratios
    print("\n3. Key Financial Ratios:")
    ratios = complete_statements.financial_ratios
    print(f"   Current Ratio: {ratios.current_ratio:.2f}x")
    print(f"   Net Profit Margin: {ratios.net_profit_margin:.2f}%")
    print(f"   Return on Equity: {ratios.return_on_equity:.2f}%")
    print(f"   Debt-to-Equity: {ratios.debt_to_equity:.2f}x")
    
    # Get comprehensive analysis
    print("\n4. Comprehensive Analysis:")
    analysis = service.get_comprehensive_analysis(complete_statements)
    
    overall_health = analysis["ratios_analysis"]["overall_assessment"]["overall_health"]
    recommendation = analysis["ratios_analysis"]["overall_assessment"]["recommendation"]
    
    print(f"   Overall Financial Health: {overall_health}")
    print(f"   Recommendation: {recommendation}")
    
    # Export to Excel
    print("\n5. Exporting to Excel...")
    output_path = "sample_financial_statements.xlsx"
    service.export_to_excel(complete_statements, output_path)
    print(f"✓ Financial statements exported to: {output_path}")
    
    # Demonstrate Excel import
    print("\n6. Testing Excel import...")
    excel_path = "sample_trial_balance.xlsx"
    create_sample_excel_file(excel_path)
    
    excel_statements = service.generate_from_excel(
        file_path=excel_path,
        entity_name="Sample Company from Excel",
        period_start=date(2024, 1, 1),
        period_end=date(2024, 12, 31),
        beginning_cash_balance=Decimal("20000.00"),
        beginning_retained_earnings=Decimal("40000.00"),
        dividends=Decimal("5000.00")
    )
    
    print("✓ Excel import and processing completed successfully")
    print(f"   Net Income from Excel: ${excel_statements.income_statement.net_income:,.2f}")
    
    return complete_statements


if __name__ == "__main__":
    try:
        complete_statements = demonstrate_complete_system()
        print("\n=== Demo Completed Successfully ===")
    except Exception as e:
        print(f"Error during demo: {str(e)}")
        import traceback
        traceback.print_exc()