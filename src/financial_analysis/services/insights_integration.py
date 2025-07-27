#!/usr/bin/env python3
"""
Integration example for Accounting Insights Generator
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from financial_analysis.services.accounting_insights import AccountingInsights

# Create mock data
class MockFinancialData:
    def __init__(self):
        self.entity_name = "Demo Company"

print("🔍 Running Accounting Insights Analysis...")

data = MockFinancialData()
generator = AccountingInsights()
insights = generator.generate_insights(data)

print("✅ Analysis completed\!")
print("\n📊 Executive Summary:")
print(insights["executive_summary"])

# Save output
output_path = Path("output/final_insights.txt")
output_path.parent.mkdir(exist_ok=True)
with open(output_path, "w") as f:
    f.write(insights["formatted_text"])

