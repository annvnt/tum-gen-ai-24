export interface FinancialIndicator {
  indicator: string
  currentYear: number | string
  previousYear: number | string
}

export interface FinancialTable {
  name: string
  data: FinancialIndicator[]
}

export interface FinancialReport {
  reportId: string
  createdAt: string
  summary: string
  tables: {
    balanceSheet: FinancialIndicator[]
    incomeStatement: FinancialIndicator[]
    cashFlowStatement: FinancialIndicator[]
  }
}

export interface UploadResponse {
  success: boolean
  report?: FinancialReport
  error?: string
}