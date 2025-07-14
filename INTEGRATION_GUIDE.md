# Financial Analysis App - Integration Guide

This guide shows how to run both the Python backend and Next.js frontend together.

## Prerequisites

1. Python 3.8+ with required packages:
   - FastAPI
   - uvicorn
   - pandas
   - openai
   - python-dotenv
   - xlsxwriter

2. Node.js 18+ with npm

3. OpenAI API Key

## Setup

### 1. Environment Variables

Create a `.env` file in the root directory:
```
API_KEY=your_openai_api_key_here
```

Update `web/.env.local` with your OpenAI API key:
```
OPENAI_API_KEY=your_openai_api_key_here
NEXT_PUBLIC_API_URL=http://localhost:3000
BACKEND_URL=http://localhost:8000
```

### 2. Install Dependencies

**Backend (Python):**
```bash
pip install fastapi uvicorn pandas openai python-dotenv xlsxwriter
```

**Frontend (Next.js):**
```bash
cd web
npm install
```

## Running the Application

### 1. Start the Backend (Terminal 1)
```bash
cd excel_ocr
python api_server.py
```
Backend will run on http://localhost:8000

### 2. Start the Frontend (Terminal 2)
```bash
cd web
npm run dev
```
Frontend will run on http://localhost:3000

## Using the Application

1. Open http://localhost:3000 in your browser
2. Upload an Excel file with financial data
3. The system will:
   - Upload the file to the backend
   - Analyze it using OpenAI GPT
   - Display financial tables and summary
   - Allow you to download the results as Excel

## API Endpoints

The Next.js frontend proxies these backend endpoints:

- `POST /api/financial/upload` - Upload and analyze Excel file
- `POST /api/financial/export/{reportId}` - Export report to Excel

## Backend Endpoints (Direct)

- `POST /api/financial/upload` - Upload Excel file
- `POST /api/financial/analyze` - Analyze uploaded file
- `GET /api/financial/export/{report_id}` - Export report
- `GET /api/financial/indicators` - Get financial indicators
- `GET /api/financial/files` - List uploaded files
- `GET /api/financial/reports` - List generated reports

## Troubleshooting

1. **Backend not starting**: Check that all Python dependencies are installed
2. **Frontend API errors**: Ensure backend is running on port 8000
3. **OpenAI errors**: Verify your API key is correct and has credits
4. **File upload errors**: Ensure Excel file has a 'code' column to identify data start

## File Structure

```
├── excel_ocr/
│   ├── api_server.py           # FastAPI backend
│   ├── financial_report_llm_demo.py  # Core analysis logic
│   └── full_financial_indicators.xlsx  # Reference indicators
├── web/
│   ├── app/
│   │   ├── api/financial/      # Next.js API routes (proxy to backend)
│   │   ├── components/         # React components
│   │   └── types/             # TypeScript types
│   └── package.json
└── .env                       # Backend environment variables
```