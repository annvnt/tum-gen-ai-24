#!/usr/bin/env python3
"""
CLI Chat Demo for Financial Report Agent (demo_data.xlsx)
Uses the analyzed report generated from financial_report_llm_demo.py on demo_data.xlsx.
"""

import sys
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).parent.parent))

from excel_ocr.financial_report_llm_demo import setup_environment, load_financial_data, load_financial_indicators, generate_financial_report
import os

SCRIPT_DIR = Path(__file__).resolve().parent
REPORT_CACHE_PATH = SCRIPT_DIR / "output/demo_data_report.txt"

# Step 1: Setup OpenAI client
try:
    client = setup_environment()
except Exception as e:
    print(f"[ERROR] Failed to setup OpenAI client: {e}")
    sys.exit(1)

# Step 2: Load or generate the analyzed report
if os.path.exists(REPORT_CACHE_PATH):
    with open(REPORT_CACHE_PATH, "r") as f:
        report_text = f.read()
    print(f"[INFO] Loaded cached report from {REPORT_CACHE_PATH}")
else:
    try:
        print("[INFO] No cached report found. Generating a new one...")
        input_file = SCRIPT_DIR / "input/demo_data.xlsx"
        df = load_financial_data(input_file)
        balance_str, income_str, cf_str = load_financial_indicators()
        report_text = generate_financial_report(client, df, balance_str, income_str, cf_str)
        
        output_dir = SCRIPT_DIR / "output"
        os.makedirs(output_dir, exist_ok=True)
        
        with open(REPORT_CACHE_PATH, "w") as f:
            f.write(report_text)
        print(f"[INFO] Generated and cached report to {REPORT_CACHE_PATH}")
    except Exception as e:
        print(f"[ERROR] Failed to analyze demo_data.xlsx: {e}")
        sys.exit(1)

print("\n🚀 Financial Report Agent CLI Chat Demo (demo_data.xlsx)")
print("Type your question and press Enter. Type 'exit' to quit.\n")

while True:
    user_input = input("👤 You: ").strip()
    if user_input.lower() in {"exit", "quit"}:
        print("👋 Exiting chat. Goodbye!")
        break
    try:
        prompt = f"{user_input}\n\nHere is the financial report analysis of demo_data.xlsx:\n{report_text}\n\nPlease answer the user's question based only on this analysis."
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a financial analyst."},
                {"role": "user", "content": prompt}
            ]
        )
        answer = response.choices[0].message.content
        print(f"🤖 Agent: {answer}")
    except Exception as e:
        print(f"[Exception]: {e}")