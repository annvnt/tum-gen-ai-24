import { NextRequest, NextResponse } from 'next/server';
export const dynamic = 'force-dynamic';
const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8000';

export async function POST(request: NextRequest) {
  try {
    const { message } = await request.json();

    if (!message) {
      return NextResponse.json(
        { error: 'Message is required' },
        { status: 400 }
      );
    }

    // Forward request to backend agent chat endpoint
    const response = await fetch(`${BACKEND_URL}/api/agent/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ message }),
    });

    if (!response.ok) {
      const errorData = await response.text();
      console.error('Backend chat error:', errorData);
      return NextResponse.json(
        { error: 'Backend chat service unavailable' },
        { status: response.status }
      );
    }

    const data = await response.json();
    
    return NextResponse.json({
      response: data.response,
      timestamp: data.timestamp,
    });

  } catch (error) {
    console.error('Chat API error:', error);
    return NextResponse.json(
      { error: 'Failed to process chat message' },
      { status: 500 }
    );
  }
}

export async function GET() {
  try {
    // Get conversation history from backend
    const response = await fetch(`${BACKEND_URL}/api/agent/conversation`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      return NextResponse.json(
        { error: 'Failed to get conversation history' },
        { status: response.status }
      );
    }

    const data = await response.json();
    
    return NextResponse.json({
      conversation: data.conversation,
    });

  } catch (error) {
    console.error('Chat history API error:', error);
    return NextResponse.json(
      { error: 'Failed to get conversation history' },
      { status: 500 }
    );
  }
}

export async function DELETE() {
  try {
    // Clear conversation history
    const response = await fetch(`${BACKEND_URL}/api/agent/clear`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      return NextResponse.json(
        { error: 'Failed to clear conversation' },
        { status: response.status }
      );
    }

    return NextResponse.json({
      message: 'Conversation cleared successfully',
    });

  } catch (error) {
    console.error('Clear chat API error:', error);
    return NextResponse.json(
      { error: 'Failed to clear conversation' },
      { status: 500 }
    );
  }
}