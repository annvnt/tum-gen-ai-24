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
    env_path = Path(__file__).parent.parent.parent / ".env"
    load_dotenv(dotenv_path=env_path)

    # Get API key from environment
    api_key = os.getenv("API_KEY")
    if not api_key:
        raise ValueError("API_KEY not found in environment variables")

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
    # Load indicators from project root
    indicator_path = Path(__file__).parent.parent.parent / "full_financial_indicators.xlsx"
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
    """Generate prompt for GPT based on financial data"""
    table_str = df.to_string(index=False)

    prompt = f"""
    You are a financial analyst. Below is a table of daily financial data, which contains two key columns representing financial figures for two years.
    The columns may have names such as "2023" and "2024", or "Last Year" and "Current Year", or similar variants.

    {table_str}

    Below is a list of financial indicators that belong to the Balance Sheet section:

    Balance Sheet Indicators:
    {balance_str}

    Income Statement Indicators:
    {income_str}

    Cash Flow Statement Indicators:
    {cf_str}

    Please:

    1. Automatically detect and use the two columns that represent the two years (previous year and current year) to extract numeric data for all calculations.

    2. Calculate all main financial indicators for both years based on these two columns.

    3. Organize the financial indicators into three separate, clean Excel-style tables:
    Each table must begin with a heading in the following format:
     #### Balance Sheet Table
     #### Income Statement Table
     #### Cash Flow Statement Table

    4. Each table must include two columns with numeric values: one for the current year and one for the previous year, enabling year-over-year comparison.

    5. Generate a professional, human-readable financial summary report in English that highlights:
      - Key revenue figures
      - Cost and expense analysis
      - Profitability overview
      - Cash flow performance
      - Meaningful comments on significant changes between the two years, based strictly on the numeric data from the two year columns

    6. Avoid including qualitative or vague comments inside the tables—only present numeric financial figures.

    7. Output two parts:
      - A concise, professional financial summary report in English
      - Three clearly formatted Excel-style tables with numeric data for both years side-by-side, ready for export

    Use professional English.
    """
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
