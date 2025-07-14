#!/bin/bash
# HTTP Test Script for Financial Report API
# Quick manual testing using curl commands

BASE_URL="http://localhost:8000"
UPLOAD_FILE="demo_data.xlsx"

echo "🧪 Financial Report API - HTTP Test Script"
echo "=========================================="

# Test 1: Health Check
echo "1. Testing health check..."
curl -s "$BASE_URL/" | jq '.'
echo -e "\n"

# Test 2: Get Financial Indicators
echo "2. Testing financial indicators..."
curl -s "$BASE_URL/api/financial/indicators" | jq '.'
echo -e "\n"

# Test 3: Upload File
echo "3. Testing file upload..."
if [ -f "$UPLOAD_FILE" ]; then
    UPLOAD_RESPONSE=$(curl -s -X POST "$BASE_URL/api/financial/upload" -F "file=@$UPLOAD_FILE")
    echo $UPLOAD_RESPONSE | jq '.'
    FILE_ID=$(echo $UPLOAD_RESPONSE | jq -r '.file_id')
    echo "📁 File ID: $FILE_ID"
else
    echo "❌ $UPLOAD_FILE not found"
    exit 1
fi
echo -e "\n"

# Test 4: List Files
echo "4. Testing list files..."
curl -s "$BASE_URL/api/financial/files" | jq '.'
echo -e "\n"

# Test 5: Analyze Financial Data
echo "5. Testing financial analysis..."
echo "⏳ This may take a while (GPT processing)..."
ANALYZE_RESPONSE=$(curl -s -X POST "$BASE_URL/api/financial/analyze" \
    -H "Content-Type: application/json" \
    -d "{\"file_id\": \"$FILE_ID\", \"custom_params\": {\"test\": \"value\"}}")
echo $ANALYZE_RESPONSE | jq '.'
REPORT_ID=$(echo $ANALYZE_RESPONSE | jq -r '.report_id')
echo "📊 Report ID: $REPORT_ID"
echo -e "\n"

# Test 6: Get Report
echo "6. Testing get report..."
curl -s "$BASE_URL/api/financial/report/$REPORT_ID" | jq '.'
echo -e "\n"

# Test 7: List Reports
echo "7. Testing list reports..."
curl -s "$BASE_URL/api/financial/reports" | jq '.'
echo -e "\n"

# Test 8: Export Report
echo "8. Testing export report..."
curl -s -X POST "$BASE_URL/api/financial/export/$REPORT_ID" \
    -H "Accept: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" \
    -o "exported_report_$REPORT_ID.xlsx"
echo "📁 Report exported to: exported_report_$REPORT_ID.xlsx"
echo -e "\n"

# Test 9: Delete File
echo "9. Testing delete file..."
curl -s -X DELETE "$BASE_URL/api/financial/file/$FILE_ID" | jq '.'
echo -e "\n"

# Test 10: Error Cases
echo "10. Testing error cases..."
echo "Testing non-existent report:"
curl -s "$BASE_URL/api/financial/report/non-existent-id" | jq '.'
echo -e "\n"

echo "✅ All HTTP tests completed!"
echo "📚 Check the interactive docs at: $BASE_URL/docs"
