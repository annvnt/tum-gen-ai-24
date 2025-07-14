import openai
from openai import OpenAI
import os
from dotenv import load_dotenv
import re
import pandas as pd

# Load API Key from .env file
load_dotenv()

# Get API_KEY
openai.api_key = os.getenv("API_KEY")

print("API Key:", openai.api_key)

client = OpenAI(api_key=openai.api_key)

file_name = 'demo_data.xlsx'  #adjust to receive uploaded file
df = pd.read_excel(file_name, header=None)
# df.head(10

mask = df.apply(lambda row: row.astype(str).str.lower().str.contains("code").any(), axis=1)
matches = df[mask]

start_index = matches.index[0]
df_from_code = df.iloc[start_index:].reset_index(drop=True)

# Set first row to header
df_from_code.columns = df_from_code.iloc[0]
df_from_code = df_from_code[1:].reset_index(drop=True)

indicator = pd.read_excel("full_financial_indicators.xlsx")

balance_items = indicator['Balance Sheet'].dropna().tolist()
balance_str = "\n".join(f"- {item}" for item in balance_items)

income_items = indicator['Income Statement'].dropna().tolist()
income_str = "\n".join(f"- {item}" for item in income_items)

cf_items = indicator['Cash Flow Statement'].dropna().tolist()
cf_str = "\n".join(f"- {item}" for item in cf_items)

## 4. Create prompt from input data
def generate_prompt_from_df(df):
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

prompt = generate_prompt_from_df(df_from_code)
# print(prompt)

## 5. Call GPT to generate report
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": "You are a financial analyst"},
        {"role": "user", "content": prompt}
    ]
)

report_text = response.choices[0].message.content
# print(report_text)

# 7. Extract data from output of prompt

# report_text is output from GPT
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
    # Identify line with format: #### Balance Sheet Table
    match = re.match(r"^####\s+(.*?)\s+Table", line.strip())
    if match:
        # Save table
        if current_table_name and table_lines:
            save_table(current_table_name, table_lines)
            table_lines = []

        # Update table name
        current_table_name = match.group(1)

    elif "|" in line and "---" not in line:
        table_lines.append(line)

# Save final file
if current_table_name and table_lines:
    save_table(current_table_name, table_lines)

# Write to excel file with multiple sheets
if tables:
    with pd.ExcelWriter("financial_statements_from_gpt.xlsx", engine="xlsxwriter") as writer:
        for sheet_name, df in tables.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    #files.download("financial_statements_from_gpt.xlsx") #modify this line to let file download
    print("✅ Saved to financial_statements_from_gpt.xlsx")
else:
    print("⚠️ No tables found in report_text.")

#Random prompt to explain how GPT calculate terms in the sheet
# prompt = f'How do you calculate Total Cost of Goods Sold from {df}'
# response = client.chat.completions.create(
#     model="gpt-4o",
#     messages=[
#         {"role": "system", "content": "You are a financial analyst"},
#         {"role": "user", "content": prompt}
#     ]
# )

# report_text = response.choices[0].message.content
# print(report_text)

