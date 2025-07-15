#!/bin/bash

echo "🧹 Creating completely fresh virtual environment..."

# Stop any running servers
echo "🛑 Stopping existing servers..."
pkill -f "python.*api_server" 2>/dev/null || true
sleep 2

# Get script directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$DIR"

# Deactivate any current environment
deactivate 2>/dev/null || true

# Remove old environment completely
echo "🗑️ Removing old virtual environment..."
rm -rf venv
rm -rf __pycache__
find . -name "*.pyc" -delete 2>/dev/null || true

# Create fresh virtual environment
echo "🆕 Creating fresh virtual environment..."
python3 -m venv venv

# Activate new environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip first
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install packages one by one with specific versions
echo "📦 Installing dependencies..."
pip install --no-cache-dir fastapi==0.104.1
pip install --no-cache-dir uvicorn[standard]==0.24.0
pip install --no-cache-dir python-multipart==0.0.6
pip install --no-cache-dir python-dotenv==1.0.0

# Install pandas and openpyxl together to avoid conflicts
echo "📊 Installing pandas and openpyxl..."
pip install --no-cache-dir pandas==2.2.0 openpyxl==3.1.5

# Install remaining packages
pip install --no-cache-dir openai==1.6.1
pip install --no-cache-dir xlsxwriter==3.1.9
pip install --no-cache-dir pydantic==2.5.0

# Verify installations
echo ""
echo "✅ Installation complete! Versions:"
echo "Python: $(which python)"
echo "Pip: $(pip --version)"
echo "FastAPI: $(python -c 'import fastapi; print(fastapi.__version__)')"
echo "Pandas: $(python -c 'import pandas; print(pandas.__version__)')"
echo "Openpyxl: $(python -c 'import openpyxl; print(openpyxl.__version__)')"
echo "OpenAI: $(python -c 'import openai; print(openai.__version__)')"

# Test Excel functionality
echo ""
echo "🧪 Testing Excel functionality..."
python -c "
import pandas as pd
import tempfile
import os
df = pd.DataFrame({'A': [1, 2], 'B': [3, 4]})
with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
    df.to_excel(f.name, index=False)
    df2 = pd.read_excel(f.name)
    os.unlink(f.name)
print('✅ Excel operations work perfectly!')
"

echo ""
echo "🎉 Fresh environment ready!"
echo "Now you can start the server with: python api_server.py"