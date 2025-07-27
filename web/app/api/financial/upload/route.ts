import { NextRequest, NextResponse } from 'next/server';
export const dynamic = 'force-dynamic';
const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8000';

export async function POST(request: NextRequest) {
  try {
    // Get the form data from the request
    const formData = await request.formData();
    
    // Upload to backend
    const uploadResponse = await fetch(`${BACKEND_URL}/api/financial/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!uploadResponse.ok) {
      const errorText = await uploadResponse.text();
      throw new Error(`Backend upload failed: ${errorText}`);
    }

    const uploadResult = await uploadResponse.json();

    // Immediately analyze the uploaded file
    const analyzeResponse = await fetch(`${BACKEND_URL}/api/financial/analyze`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        file_id: uploadResult.file_id,
      }),
    });

    if (!analyzeResponse.ok) {
      const errorText = await analyzeResponse.text();
      throw new Error(`Backend analysis failed: ${errorText}`);
    }

    const analysisResult = await analyzeResponse.json();

    // Transform backend response to match frontend expectations
    const report = {
      reportId: analysisResult.report_id,
      createdAt: new Date().toISOString(),
      summary: analysisResult.summary,
      tables: {
        balanceSheet: transformTableData(analysisResult.tables?.balance_sheet || []),
        incomeStatement: transformTableData(analysisResult.tables?.income_statement || []),
        cashFlowStatement: transformTableData(analysisResult.tables?.cash_flow_statement || []),
      },
    };

    return NextResponse.json({
      success: true,
      report,
    });

  } catch (error) {
    console.error('API Error:', error);
    return NextResponse.json(
      {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error occurred',
      },
      { status: 500 }
    );
  }
}

function transformTableData(backendData: any[]): any[] {
  if (!Array.isArray(backendData)) {
    return [];
  }

  return backendData.map((item: any) => {
    // Handle different possible structures from backend
    if (typeof item === 'object' && item !== null) {
      // Try to find indicator name and year columns
      const keys = Object.keys(item);
      const indicatorKey = keys.find(key => 
        key.toLowerCase().includes('indicator') || 
        key.toLowerCase().includes('item') ||
        key.toLowerCase().includes('name') ||
        keys.indexOf(key) === 0
      ) || keys[0];

      const currentYearKey = keys.find(key => 
        key.includes('2024') || 
        key.toLowerCase().includes('current') ||
        key.toLowerCase().includes('this') ||
        keys.indexOf(key) === 1
      ) || keys[1];

      const previousYearKey = keys.find(key => 
        key.includes('2023') || 
        key.toLowerCase().includes('previous') ||
        key.toLowerCase().includes('last') ||
        keys.indexOf(key) === 2
      ) || keys[2];

      return {
        indicator: item[indicatorKey] || 'Unknown',
        currentYear: item[currentYearKey] || 0,
        previousYear: item[previousYearKey] || 0,
      };
    }

    return {
      indicator: 'Unknown',
      currentYear: 0,
      previousYear: 0,
    };
  });
}