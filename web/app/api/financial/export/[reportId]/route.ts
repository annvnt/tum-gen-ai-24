import { NextRequest, NextResponse } from 'next/server';
export const dynamic = 'force-dynamic';
const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8000';

export async function POST(
  request: NextRequest,
  { params }: { params: { reportId: string } }
) {
  try {
    // Proxy the export request to the backend
    const response = await fetch(`${BACKEND_URL}/api/financial/export/${params.reportId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Backend export failed: ${response.statusText}`);
    }

    // Get the Excel file buffer from the backend
    const buffer = await response.arrayBuffer();

    // Return the Excel file with proper headers
    return new NextResponse(buffer, {
      headers: {
        'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'Content-Disposition': `attachment; filename="financial-report-${params.reportId}.xlsx"`
      }
    });
    
  } catch (error) {
    console.error('Error exporting Excel:', error);
    return NextResponse.json({ 
      success: false, 
      error: 'Failed to export Excel file' 
    }, { status: 500 });
  }
}