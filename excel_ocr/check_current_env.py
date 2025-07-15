#!/usr/bin/env python3
"""Check what environment we're actually using"""

import sys
import os

print(f"Python executable: {sys.executable}")
print(f"Python version: {sys.version}")
print(f"Virtual env: {os.environ.get('VIRTUAL_ENV', 'Not in virtual env')}")

try:
    import pandas as pd
    print(f"pandas version: {pd.__version__}")
    print(f"pandas location: {pd.__file__}")
except Exception as e:
    print(f"pandas error: {e}")

try:
    import openpyxl
    print(f"openpyxl version: {openpyxl.__version__}")
    print(f"openpyxl location: {openpyxl.__file__}")
except Exception as e:
    print(f"openpyxl error: {e}")

# Test if they work together
try:
    df = pd.DataFrame({'A': [1, 2], 'B': [3, 4]})
    df.to_excel('/tmp/test.xlsx', index=False)
    df2 = pd.read_excel('/tmp/test.xlsx')
    print("✅ Excel operations work successfully")
    os.remove('/tmp/test.xlsx')
except Exception as e:
    print(f"❌ Excel test failed: {e}")