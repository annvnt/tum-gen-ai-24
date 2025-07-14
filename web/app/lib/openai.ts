import OpenAI from 'openai'

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
})

export async function analyzeFinancialData(tableData: string, indicators: {
  balanceSheet: string[],
  incomeStatement: string[],
  cashFlowStatement: string[]
}): Promise<{ summary: string, tables: any }> {
  const balanceStr = indicators.balanceSheet.map(item => `- ${item}`).join('\n')
  const incomeStr = indicators.incomeStatement.map(item => `- ${item}`).join('\n')
  const cfStr = indicators.cashFlowStatement.map(item => `- ${item}`).join('\n')

  const prompt = `
    You are a financial analyst. Below is a table of daily financial data, which contains two key columns representing financial figures for two years.
    The columns may have names such as "2023" and "2024", or "Last Year" and "Current Year", or similar variants.

    ${tableData}

    Below is a list of financial indicators that belong to the Balance Sheet section:

    Balance Sheet Indicators:
    ${balanceStr}

    Income Statement Indicators:
    ${incomeStr}

    Cash Flow Statement Indicators:
    ${cfStr}

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
  `

  const response = await openai.chat.completions.create({
    model: 'gpt-4o',
    messages: [
      { role: 'system', content: 'You are a financial analyst' },
      { role: 'user', content: prompt }
    ],
    temperature: 0.7,
    max_tokens: 4000,
  })

  const content = response.choices[0].message.content || ''
  
  // Parse the response to extract summary and tables
  const lines = content.split('\n')
  let summary = ''
  const tables: any = {
    balanceSheet: [],
    incomeStatement: [],
    cashFlowStatement: []
  }
  
  let currentSection = 'summary'
  let currentTable: any[] = []
  
  for (const line of lines) {
    if (line.includes('#### Balance Sheet Table')) {
      currentSection = 'balanceSheet'
      continue
    } else if (line.includes('#### Income Statement Table')) {
      currentSection = 'incomeStatement'
      continue
    } else if (line.includes('#### Cash Flow Statement Table')) {
      currentSection = 'cashFlowStatement'
      continue
    }
    
    if (currentSection === 'summary' && !line.includes('####')) {
      summary += line + '\n'
    } else if (currentSection !== 'summary' && line.includes('|') && !line.includes('---')) {
      const cells = line.split('|').map(cell => cell.trim()).filter(cell => cell)
      if (cells.length >= 3) {
        if (currentSection === 'balanceSheet') {
          tables.balanceSheet.push({
            indicator: cells[0],
            currentYear: cells[1],
            previousYear: cells[2]
          })
        } else if (currentSection === 'incomeStatement') {
          tables.incomeStatement.push({
            indicator: cells[0],
            currentYear: cells[1],
            previousYear: cells[2]
          })
        } else if (currentSection === 'cashFlowStatement') {
          tables.cashFlowStatement.push({
            indicator: cells[0],
            currentYear: cells[1],
            previousYear: cells[2]
          })
        }
      }
    }
  }
  
  return { summary: summary.trim(), tables }
}

export { openai }