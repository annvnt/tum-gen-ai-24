import { NextRequest, NextResponse } from "next/server";
export const dynamic = 'force-dynamic';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { 
      context, 
      max_files = 5, 
      criteria = { prefer_processed: true, prefer_recent: true } 
    } = body;

    if (!context) {
      return NextResponse.json(
        { error: "Context parameter is required" },
        { status: 400 }
      );
    }

    const backendUrl = `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/enhanced/files/auto-select`;
    
    const response = await fetch(backendUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        context,
        max_files,
        criteria,
      }),
    });

    if (!response.ok) {
      throw new Error(`Backend API error: ${response.statusText}`);
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Error auto-selecting files:", error);
    return NextResponse.json(
      { error: "Failed to auto-select files" },
      { status: 500 }
    );
  }
}
