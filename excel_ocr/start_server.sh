#!/bin/bash

echo "🔧 Starting server with correct environment..."

# Get the directory of this script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$DIR"

# Kill any existing server processes
echo "🔄 Stopping any existing servers..."
pkill -f "python.*api_server" 2>/dev/null || true

# Activate virtual environment
echo "🐍 Activating virtual environment..."
source venv/bin/activate

# Verify environment
echo "✅ Environment check:"
echo "Python: $(which python)"
echo "Pandas: $(python -c 'import pandas; print(pandas.__version__)')"
echo "Openpyxl: $(python -c 'import openpyxl; print(openpyxl.__version__)')"

# Start server
echo "🚀 Starting API server..."
python api_server.py