#!/usr/bin/env python3
"""
Test script to diagnose server startup issues
"""

import sys
import os

print("🔍 Testing server startup...")
print(f"Python version: {sys.version}")
print(f"Current directory: {os.getcwd()}")

# Test imports one by one
try:
    print("\n1. Testing basic imports...")
    import pandas as pd
    print("✅ pandas imported successfully")
except Exception as e:
    print(f"❌ Error importing pandas: {e}")

try:
    import fastapi
    print("✅ fastapi imported successfully")
except Exception as e:
    print(f"❌ Error importing fastapi: {e}")

try:
    import uvicorn
    print("✅ uvicorn imported successfully")
except Exception as e:
    print(f"❌ Error importing uvicorn: {e}")

try:
    print("\n2. Testing OpenAI setup...")
    from financial_report_llm_demo import setup_environment
    client = setup_environment()
    print("✅ OpenAI client initialized successfully")
except Exception as e:
    print(f"❌ Error setting up OpenAI: {e}")

try:
    print("\n3. Testing financial agent...")
    from financial_agent import FinancialReportAgent
    agent = FinancialReportAgent()
    print("✅ Financial agent initialized successfully")
except Exception as e:
    print(f"❌ Error initializing agent: {e}")

try:
    print("\n4. Testing API server import...")
    import api_server
    print("✅ API server module imported successfully")
except Exception as e:
    print(f"❌ Error importing api_server: {e}")

print("\n✨ If all tests passed, try running:")
print("   python -m uvicorn api_server:app --reload --host 0.0.0.0 --port 8000")