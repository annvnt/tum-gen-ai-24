# Financial Analyzer - Next.js Application

A web application for uploading and analyzing financial Excel files using OpenAI GPT-4.

## Features

- Excel file upload (drag & drop)
- Automatic financial data extraction
- AI-powered financial analysis
- Interactive report display
- Excel export functionality
- Responsive design

## Setup

1. Install dependencies:
```bash
npm install
```

2. Set up environment variables:
Create a `.env.local` file and add your OpenAI API key:
```
OPENAI_API_KEY=your_openai_api_key_here
```

3. Run the development server:
```bash
npm run dev
```

4. Open [http://localhost:3000](http://localhost:3000)

## Project Structure

```
financial-analyzer/
├── app/
│   ├── api/
│   │   └── financial/
│   │       ├── upload/         # Excel upload endpoint
│   │       └── export/         # Report export endpoint
│   ├── components/
│   │   ├── FileUpload.tsx      # File upload component
│   │   └── ReportDisplay.tsx   # Report display component
│   ├── lib/
│   │   ├── openai.ts          # OpenAI integration
│   │   └── indicators.ts       # Financial indicators
│   ├── types/
│   │   └── financial.ts        # TypeScript types
│   ├── globals.css            # Global styles
│   ├── layout.tsx             # Root layout
│   └── page.tsx               # Home page
├── public/                     # Static assets
├── .env.local                 # Environment variables
├── next.config.js             # Next.js config
├── tailwind.config.js         # Tailwind config
├── tsconfig.json              # TypeScript config
└── package.json               # Dependencies
```

## API Endpoints

### POST /api/financial/upload
Upload Excel file and get financial analysis

### POST /api/financial/export/{reportId}
Export report as Excel file

## Technologies Used

- Next.js 14+ (App Router)
- TypeScript
- Tailwind CSS
- OpenAI GPT-4
- XLSX for Excel processing
- React Dropzone
- Lucide React icons