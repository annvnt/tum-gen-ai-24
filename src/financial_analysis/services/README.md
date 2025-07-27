# Accounting Insights Generator

A simple Python module that extracts key financial metrics from analysis data and generates simple, actionable insights for non-accountants.

## Features

- **Key Warnings**: Detects negative revenue, losses, cash flow problems
- **Positive Indicators**: Highlights good performance and improvement trends
- **Immediate Actions**: Provides 3-4 specific, actionable steps
- **Simple Explanations**: Uses plain language for non-accountants
- **Excel Integration**: Formats output for easy Excel import

## Usage

### Basic Usage

```python
from src.financial_analysis.services.accounting_insights import AccountingInsights

# Create or load your financial data
financial_data = load_your_financial_data()

# Generate insights
generator = AccountingInsights()
insights = generator.generate_insights(financial_data)

# Access the insights
print(insights['executive_summary'])  # Quick overview
print(insights['formatted_text'])     # Detailed insights for Excel
```

### Output Format

The generator provides insights in these categories:

1. **Revenue Analysis**
   - Revenue levels and trends
   - Sales performance indicators

2. **Profitability Analysis**
   - Net profit/loss warnings
   - Profit margin assessments

3. **Liquidity Analysis**
   - Cash flow warnings
   - Ability to pay bills

4. **Cash Flow Analysis**
   - Operating cash flow health
   - Cash position assessment

5. **Debt Analysis**
   - Debt level warnings
   - Financial leverage insights

## Example Output

```
ACCOUNTING INSIGHTS SUMMARY
==================================================

⚠️  WARNINGS:

CRITICAL: 🚨 BUSINESS IS LOSING MONEY - Net loss of $5,000.00
What this means: Your expenses exceed your revenue by $5,000.00. This means you're losing money on every sale.

CRITICAL: 🚨 CASH FLOW PROBLEM - May struggle to pay bills
What this means: Your current ratio is 0.80, which means you don't have enough short-term assets to cover short-term debts.

✅ POSITIVE INDICATORS:

✅ Revenue of $100,000.00 shows business activity
Why this matters: Your business is generating sales, which is a good foundation for growth.

📋 IMMEDIATE ACTIONS:

1. Cut costs immediately (URGENT priority)
   How to do it: Review all expenses and eliminate non-essential spending. Focus on high-impact cost reductions.

2. Review sales strategy immediately (URGENT priority)
   How to do it: Check if products/services are being sold, pricing is correct, or if there are collection issues
```

## Integration with Existing Analysis

This module is designed to work with your existing financial analysis pipeline. Simply:

1. Load your financial statements (Income Statement, Balance Sheet, Cash Flow)
2. Create a CompleteFinancialStatements object
3. Pass it to the AccountingInsights generator
4. Use the formatted output in your Excel reports

## File Structure

- `accounting_insights.py` - Main insights generator
- `README.md` - This documentation
- `insights_example.py` - Usage example
EOF < /dev/null