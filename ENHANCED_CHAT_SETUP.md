# Enhanced Chat-Based File Selection and PDF Report Generation System

## Overview

This system provides a comprehensive chat-based interface for financial document analysis with the following capabilities:

- **Smart File Selection**: Automatic file detection, semantic search, and manual selection
- **PDF Generation**: Professional financial reports with customizable templates
- **Knowledge Base Integration**: Vector-based semantic search across uploaded documents
- **Enhanced Chat Interface**: Context-aware conversations with file management
- **Complete Workflow**: From upload → selection → analysis → PDF export

## Architecture

### Backend Services

1. **ChatFileManager**: Enhanced file management with search and selection
2. **FinancialPDFGenerator**: Professional PDF report generation
3. **EnhancedChatAgent**: Advanced chat interface with file context
4. **VectorService**: Semantic search using Jina embeddings and Qdrant

### API Endpoints

- `/api/enhanced/chat` - Enhanced chat with file context
- `/api/enhanced/files/search` - Semantic file search
- `/api/enhanced/files/available` - List available files
- `/api/enhanced/reports/generate` - Generate PDF reports
- `/api/vector/process` - Process files for vector search
- `/api/vector/search` - Semantic document search

### Frontend Components

1. **EnhancedChatInterface.tsx** - Main chat interface with file selection
2. **KnowledgeBaseManager.tsx** - File upload and management
3. **FileSelector** - Modal for file selection
4. **ReportGenerator** - PDF report configuration

## Installation

### Backend Dependencies

```bash
# Install additional Python packages
pip install reportlab matplotlib pandas openpyxl
pip install qdrant-client jina
```

### Frontend Dependencies

The frontend already includes all necessary dependencies via the existing Next.js setup.

## Configuration

### Environment Variables

Add these to your `.env` file:

```bash
# Google Cloud Storage
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json
GCS_BUCKET_NAME=your-bucket-name

# Qdrant Configuration
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=your-api-key

# Jina Embeddings
JINA_API_KEY=your-jina-api-key
```

### Database Setup

The system uses the existing SQLite database with enhanced schema:

```sql
-- Additional tables are automatically created
-- No manual setup required
```

## Usage

### 1. File Upload

**Via Knowledge Base:**
- Navigate to `/knowledge-base`
- Upload Excel files (.xlsx, .xls, .csv)
- Files are automatically processed for vector search

**Via Chat:**
- Use the enhanced chat interface
- Files can be selected after upload

### 2. File Selection

**Methods:**
- **Auto-selection**: AI automatically selects relevant files based on context
- **Semantic search**: Search by meaning and content
- **Manual selection**: Browse and select files via UI
- **Filename search**: Quick search by file names

### 3. Chat Interactions

**Supported Commands:**
```
"List all available files"
"Search for files about Q1 2024"
"Analyze the financial data in file abc123"
"Generate a comprehensive report"
"Create an executive summary"
"Calculate financial ratios"
```

**Context Awareness:**
- Remembers selected files across sessions
- Provides file context in responses
- Tracks analysis history

### 4. PDF Report Generation

**Templates:**
- **Comprehensive**: Full analysis with all statements
- **Executive**: High-level overview
- **Ratios Only**: Focus on financial ratios

**Customization:**
- Select specific files
- Choose template type
- Add custom sections

## API Usage Examples

### Chat with File Context

```javascript
const response = await fetch('/api/enhanced/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    message: "Generate a report about Q1 financial performance",
    session_id: "user_session_123",
    context: {
      file_ids: ["file1", "file2"],
      template: "comprehensive"
    }
  })
});
```

### Search Files

```javascript
const results = await fetch('/api/enhanced/files/search', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    query: "quarterly revenue",
    search_type: "semantic",
    limit: 10
  })
});
```

### Generate Report

```javascript
const report = await fetch('/api/enhanced/reports/generate', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    file_ids: ["file1", "file2"],
    template: "comprehensive"
  })
});
```

## Features

### Smart File Selection
- **Semantic understanding**: Uses vector embeddings to understand file content
- **Context matching**: Matches files to user queries
- **Priority scoring**: Ranks files by relevance
- **Auto-selection**: Automatically selects best files for analysis

### PDF Reports
- **Professional formatting**: Clean, business-ready reports
- **Multiple templates**: Different report types available
- **Customizable sections**: Add/remove report sections
- **Charts and tables**: Visual data representation
- **Executive summaries**: Key insights and recommendations

### Knowledge Base Features
- **Semantic search**: Search by meaning, not just keywords
- **Content preview**: See file content before selection
- **Processing status**: Track vector processing progress
- **File management**: Upload, delete, and organize files

## Testing

Run integration tests:

```bash
# Run all tests
pytest test_integration.py -v

# Run specific test
pytest test_integration.py::TestEnhancedChatSystem::test_complete_workflow -v
```

## Troubleshooting

### Common Issues

1. **Files not appearing in search**
   - Check if files are processed for vectors
   - Verify file format (Excel, CSV supported)
   - Check processing status in knowledge base

2. **PDF generation fails**
   - Ensure files contain valid financial data
   - Check if required analysis data is available
   - Verify PDF service dependencies

3. **Search returns no results**
   - Ensure files are processed for vector search
   - Try different search terms
   - Check file content relevance

### Debug Commands

```bash
# Check service status
curl http://localhost:8000/api/server/info

# List available files
curl http://localhost:8000/api/enhanced/files/available

# Check vector processing status
curl http://localhost:8000/api/vector/stats
```

## Performance Optimization

### Backend
- Use background tasks for heavy processing
- Implement caching for search results
- Optimize database queries

### Frontend
- Lazy loading for large file lists
- Debounced search input
- Optimistic UI updates

## Security

- File type validation
- Size limits on uploads
- Session-based file access
- Secure API endpoints

## Monitoring

- Track file processing status
- Monitor API response times
- Log search queries and results
- Track report generation metrics