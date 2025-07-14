import { NextRequest, NextResponse } from 'next/server'
import * as XLSX from 'xlsx'
import { analyzeFinancialData } from '@/app/lib/openai'
import { financialIndicators } from '@/app/lib/indicators'

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData()
    const file = formData.get('file') as File
    
    if (!file) {
      return NextResponse.json({ success: false, error: 'No file provided' }, { status: 400 })
    }

    // Read the Excel file
    const buffer = await file.arrayBuffer()
    const workbook = XLSX.read(buffer, { type: 'array' })
    const sheetName = workbook.SheetNames[0]
    const worksheet = workbook.Sheets[sheetName]
    
    // Convert to JSON
    const data = XLSX.utils.sheet_to_json(worksheet, { header: 1 })
    
    // Find the row with "Code"
    let startIndex = -1
    for (let i = 0; i < data.length; i++) {
      const row = data[i] as any[]
      if (row.some(cell => String(cell).toLowerCase().includes('code'))) {
        startIndex = i
        break
      }
    }
    
    if (startIndex === -1) {
      return NextResponse.json({ success: false, error: 'Could not find "Code" column in the Excel file' }, { status: 400 })
    }
    
    // Extract data from the Code row onwards
    const headers = data[startIndex] as string[]
    const rows = data.slice(startIndex + 1)
    
    // Convert to table string for GPT
    let tableStr = headers.join('\t') + '\n'
    for (const row of rows) {
      tableStr += (row as any[]).join('\t') + '\n'
    }
    
    // Analyze with GPT
    const analysis = await analyzeFinancialData(tableStr, financialIndicators)
    
    // Generate report ID
    const reportId = Date.now().toString()
    
    const report = {
      reportId,
      createdAt: new Date().toISOString(),
      summary: analysis.summary,
      tables: analysis.tables
    }
    
    // In a real app, you would save this to a database
    // For now, we'll just return it
    
    return NextResponse.json({ success: true, report })
    
  } catch (error) {
    console.error('Error processing file:', error)
    return NextResponse.json({ 
      success: false, 
      error: error instanceof Error ? error.message : 'Failed to process file' 
    }, { status: 500 })
  }
}