#!/usr/bin/env python3
"""
Financial Report LLM Demo - Python Script Version
This script processes financial data from Excel files and uses OpenAI's GPT to generate
professional financial reports with structured tables for Balance Sheet, Income Statement,
and Cash Flow Statement.
"""

import os
import re
import pandas as pd
import openai
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path

def setup_environment():
    """Setup environment variables and OpenAI client"""
    # Load from .env file - works both in Docker and locally
    load_dotenv()

    # Get API key from environment
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY or API_KEY not found in environment variables")

    openai.api_key = api_key
    print("API Key loaded successfully")

    # Initialize OpenAI client
    client = OpenAI(api_key=api_key)
    return client

def load_financial_data(file_path):
    """Load financial data from Excel file and process it"""
    # Read Excel file without headers
    df = pd.read_excel(file_path, header=None)

    # Find the row containing "code" to determine data start
    mask = df.apply(lambda row: row.astype(str).str.lower().str.contains("code").any(), axis=1)
    matches = df[mask]

    if matches.empty:
        raise ValueError("No 'code' column found in the data")

    # Extract data from the code row onwards
    start_index = matches.index[0]
    df_from_code = df.iloc[start_index:].reset_index(drop=True)

    # Set first row as header
    df_from_code.columns = df_from_code.iloc[0]
    df_from_code = df_from_code[1:].reset_index(drop=True)

    return df_from_code

def load_financial_indicators():
    """Load financial indicators from the reference Excel file"""
    # Load indicators from multiple possible locations
    possible_paths = [
        Path(__file__).parent.parent / "data" / "full_financial_indicators.xlsx",
        Path(__file__).parent / "data" / "full_financial_indicators.xlsx",
        Path.cwd() / "src" / "financial_analysis" / "data" / "full_financial_indicators.xlsx",
        Path("/app/src/financial_analysis/data/full_financial_indicators.xlsx"),  # Docker path
    ]
    
    indicator_path = None
    for path in possible_paths:
        if path.exists():
            indicator_path = path
            break
    
    if not indicator_path:
        raise FileNotFoundError(f"Could not find full_financial_indicators.xlsx in any expected location")
    
    indicator = pd.read_excel(indicator_path)

    # Extract indicators for each financial statement
    balance_items = indicator['Balance Sheet'].dropna().tolist()
    balance_str = "\n".join(f"- {item}" for item in balance_items)

    income_items = indicator['Income Statement'].dropna().tolist()
    income_str = "\n".join(f"- {item}" for item in income_items)

    cf_items = indicator['Cash Flow Statement'].dropna().tolist()
    cf_str = "\n".join(f"- {item}" for item in cf_items)

    return balance_str, income_str, cf_str

def generate_prompt_from_df(df, balance_str, income_str, cf_str):
    """Generate a tailored prompt for GPT to produce well-formatted tables, a brief introduction, and an extensive CPA report with context retention."""
    table_str = df.to_string(index=False)

    prompt = f'''You are a Certified Public Accountant (CPA) and senior financial analyst.

Begin your response with a concise introduction that outlines the purpose of the analysis and sets expectations for the detailed report. Then proceed with the following:

Source Data:
{table_str}

Indicators:
- Balance Sheet: {balance_str}
- Income Statement: {income_str}
- Cash Flow Statement: {cf_str}

Your tasks:
- Identify the two year columns and base all comparisons on these.
- Calculate each listed indicator for both years.
- Present three tables: Balance Sheet, Income Statement, and Cash Flow:
  • Use plain-text tables with aligned columns and even spacing.
  • Enclose each table in triple backticks.
  • Format numeric values with comma separators and two decimal places (e.g., 1,234,567.89).
  • Right-align numeric columns with consistent widths.
  • Omit any row where Prev Year or Curr Year is missing or "N/A".
  Example:
  ```
  Indicator                        Prev Year      Curr Year
  Cash and Cash Equivalents        1,000.00        1,000.00
  ```
- After tables, include a comprehensive introduction to the detailed analysis, then provide an extensive, element-by-element CPA-style report:
  • Define each indicator.
  • Present values for both years.
  • Calculate and state absolute and percentage changes.
  • Interpret each change (positive, negative, neutral) with precise accounting terminology.
- Use dashes for section headings (e.g., "- Balance Sheet Analysis").
- Ensure the output is clear, professional, and retains the dataset and results for follow-up queries.

Output structure:
- A short introductory paragraph explaining the analysis objective.
- - Balance Sheet Table
  ```
  [Balance Sheet contents]
  ```
- - Income Statement Table
  ```
  [Income Statement contents]
  ```
- - Cash Flow Table
  ```
  [Cash Flow contents]
  ```
- - Detailed Analysis Report (each section starts with a dash)

Write in professional English, using dashes for sections and backticks around tables for clarity, and provide thorough explanations throughout.'''
    return prompt

def generate_financial_report(client, df, balance_str, income_str, cf_str):
    """Generate financial report using OpenAI GPT"""
    prompt = generate_prompt_from_df(df, balance_str, income_str, cf_str)

    print("Generated prompt:")
    print(prompt)
    print("\n" + "="*50 + "\n")

    # Call GPT to generate report
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a financial analyst"},
            {"role": "user", "content": prompt}
        ]
    )

    report_text = response.choices[0].message.content
    print("Generated Report:")
    print(report_text)

    return report_text

def extract_simple_table(report_text):
    """Extract simple table from GPT output"""
    lines = report_text.splitlines()
    table_lines = [l for l in lines if "|" in l and "---" not in l]

    # Remove leading/trailing | and split by |
    rows = [re.split(r"\s*\|\s*", l.strip().strip('|')) for l in table_lines]

    if len(rows) > 1:
        df_summary = pd.DataFrame(rows[1:], columns=rows[0])

        # Create output directory if it doesn't exist
        output_dir = Path(__file__).parent.parent.parent / "output"
        output_dir.mkdir(exist_ok=True)

        # Save to output directory
        output_path = output_dir / "financial_summary.xlsx"
        df_summary.to_excel(output_path, index=False)
        print(f"✅ Saved simple table to {output_path}")
        return df_summary
    else:
        print("⚠️ No summary table found.")
        return None

def extract_structured_tables(report_text):
    """Extract structured tables (Balance Sheet, Income Statement, Cash Flow) from GPT output"""
    lines = report_text.splitlines()

    tables = {}
    current_table_name = None
    table_lines = []

    def save_table(name, lines):
        rows = [re.split(r"\s*\|\s*", l.strip().strip('|')) for l in lines]
        if len(rows) > 1:
            df = pd.DataFrame(rows[1:], columns=rows[0])
            tables[name] = df

    for line in lines:
        # Match headings like: #### Balance Sheet Table
        match = re.match(r"^####\s+(.*?)\s+Table", line.strip())
        if match:
            # Save previous table if exists
            if current_table_name and table_lines:
                save_table(current_table_name, table_lines)
                table_lines = []

            # Update current table name
            current_table_name = match.group(1)

        elif "|" in line and "---" not in line:
            table_lines.append(line)

    # Save last table if exists
    if current_table_name and table_lines:
        save_table(current_table_name, table_lines)

    # Write to Excel with multiple sheets in output directory
    if tables:
        # Create output directory if it doesn't exist
        output_dir = Path(__file__).parent.parent.parent / "output"
        output_dir.mkdir(exist_ok=True)

        # Save to output directory
        output_path = output_dir / "financial_statements_from_gpt.xlsx"
        with pd.ExcelWriter(output_path, engine="xlsxwriter") as writer:
            for sheet_name, df in tables.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)
        print(f"✅ Saved structured tables to {output_path}")
        return tables
    else:
        print("⚠️ No tables found in report_text.")
        return None

def ask_calculation_question(client, df, question):
    """Ask GPT about specific calculations"""
    prompt = f'{question} from {df}'

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a financial analyst"},
            {"role": "user", "content": prompt}
        ]
    )

    answer = response.choices[0].message.content
    print(f"Question: {question}")
    print(f"Answer: {answer}")
    return answer

def main():
    """Main function to run the financial report generation process"""
    try:
        # Setup environment and client
        client = setup_environment()

        # Load financial data - you can specify the file path here
        # For now, assuming demo_data.xlsx exists in the input directory
        demo_path = Path(__file__).parent.parent.parent / "input" / "demo_data.xlsx"
        df = load_financial_data(str(demo_path))
        print("Financial data loaded successfully")
        print(f"Data shape: {df.shape}")

        # Load financial indicators
        balance_str, income_str, cf_str = load_financial_indicators()
        print("Financial indicators loaded successfully")

        # Generate financial report
        report_text = generate_financial_report(client, df, balance_str, income_str, cf_str)

        # Extract tables from the report
        print("\n" + "="*50)
        print("Extracting tables from report...")

        # Extract simple table
        simple_table = extract_simple_table(report_text)

        # Extract structured tables
        structured_tables = extract_structured_tables(report_text)

        # Example of asking a specific calculation question
        print("\n" + "="*50)
        print("Asking calculation question...")
        ask_calculation_question(client, df, "How do you calculate Total Cost of Goods Sold")

        print("\n✅ Financial report generation completed successfully!")

    except Exception as e:
        print(f"❌ Error occurred: {str(e)}")
        raise

if __name__ == "__main__":
    main()
