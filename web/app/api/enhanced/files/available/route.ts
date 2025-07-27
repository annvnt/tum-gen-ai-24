import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const limit = searchParams.get('limit') || '50';
    const offset = searchParams.get('offset') || '0';
    const search = searchParams.get('search') || '';
    const fileTypes = searchParams.get('file_types') || '';

    // Forward request to the Python backend
    const backendUrl = `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/enhanced/files/available`;
    const params = new URLSearchParams({
      limit,
      offset,
      ...(search && { search }),
      ...(fileTypes && { file_types: fileTypes }),
    });

    const response = await fetch(`${backendUrl}?${params}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Backend API error: ${response.statusText}`);
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error fetching available files:', error);
    return NextResponse.json(
      { error: 'Failed to fetch available files' },
      { status: 500 }
    );
  }
}