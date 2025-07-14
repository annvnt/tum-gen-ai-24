import { NextRequest, NextResponse } from 'next/server'
import * as XLSX from 'xlsx'

export async function POST(
  request: NextRequest,
  { params }: { params: { reportId: string } }
) {
  try {
    // In a real app, you would fetch the report from database
    // For now, we'll create a sample export
    
    // Parse the request body to get report data
    const body = await request.json().catch(() => ({}))
    
    // Create a new workbook
    const wb = XLSX.utils.book_new()
    
    // Add Summary sheet
    const summaryData = [
      ['Financial Analysis Report'],
      ['Report ID:', params.reportId],
      ['Generated:', new Date().toLocaleString()],
      [''],
      ['Executive Summary'],
      ['This is a placeholder summary. In production, this would contain the actual report summary.']
    ]
    const summaryWs = XLSX.utils.aoa_to_sheet(summaryData)
    XLSX.utils.book_append_sheet(wb, summaryWs, 'Summary')
    
    // Add Balance Sheet
    const balanceSheetData = [
      ['Balance Sheet Analysis'],
      ['Indicator', 'Current Year', 'Previous Year', 'Change %'],
      ['Total Assets', '1,000,000', '900,000', '11.1%'],
      ['Total Liabilities', '400,000', '350,000', '14.3%'],
      ['Total Equity', '600,000', '550,000', '9.1%']
    ]
    const balanceSheetWs = XLSX.utils.aoa_to_sheet(balanceSheetData)
    XLSX.utils.book_append_sheet(wb, balanceSheetWs, 'Balance Sheet')
    
    // Add Income Statement
    const incomeData = [
      ['Income Statement Analysis'],
      ['Indicator', 'Current Year', 'Previous Year', 'Change %'],
      ['Revenue', '2,000,000', '1,800,000', '11.1%'],
      ['Cost of Goods Sold', '1,200,000', '1,100,000', '9.1%'],
      ['Net Profit', '300,000', '250,000', '20.0%']
    ]
    const incomeWs = XLSX.utils.aoa_to_sheet(incomeData)
    XLSX.utils.book_append_sheet(wb, incomeWs, 'Income Statement')
    
    // Add Cash Flow Statement
    const cashFlowData = [
      ['Cash Flow Statement Analysis'],
      ['Indicator', 'Current Year', 'Previous Year', 'Change %'],
      ['Operating Activities', '400,000', '350,000', '14.3%'],
      ['Investing Activities', '-100,000', '-80,000', '25.0%'],
      ['Financing Activities', '-50,000', '-40,000', '25.0%']
    ]
    const cashFlowWs = XLSX.utils.aoa_to_sheet(cashFlowData)
    XLSX.utils.book_append_sheet(wb, cashFlowWs, 'Cash Flow')
    
    // Generate buffer
    const buffer = XLSX.write(wb, { bookType: 'xlsx', type: 'buffer' })
    
    // Return the Excel file
    return new NextResponse(buffer, {
      headers: {
        'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'Content-Disposition': `attachment; filename="financial-report-${params.reportId}.xlsx"`
      }
    })
    
  } catch (error) {
    console.error('Error generating Excel:', error)
    return NextResponse.json({ 
      success: false, 
      error: 'Failed to generate Excel file' 
    }, { status: 500 })
  }
}