#!/usr/bin/env python3
"""
Main entry point for the Financial Analysis Application

This script provides a unified interface to run different components:
- API Server: Run the FastAPI backend
- Tests: Run the test suite
- Demo: Run the financial analysis demo
"""

import sys
import argparse
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

def run_api_server():
    """Run the FastAPI server"""
    import uvicorn
    from financial_analysis.api.app import app
    
    print("🚀 Starting Financial Analysis API Server...")
    print("📍 Server will be available at: http://localhost:8000")
    print("📚 API Documentation: http://localhost:8000/docs")
    
    uvicorn.run(
        "financial_analysis.api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

def run_tests():
    """Run the test suite"""
    try:
        from financial_analysis.tests.test_api import APITester
        from financial_analysis.tests.test_agent import AgentTester
        
        print("🧪 Running API Tests...")
        api_tester = APITester()
        api_success = api_tester.run_all_tests()
        
        print("\n🤖 Running Agent Tests...")
        agent_tester = AgentTester()
        agent_tester.test_conversation_flow()
        agent_tester.test_agent_endpoints()
        
        if api_success:
            print("\n✅ All tests completed successfully!")
        else:
            print("\n❌ Some tests failed. Check output above.")
            
    except Exception as e:
        print(f"❌ Error running tests: {e}")

def run_demo():
    """Run the financial analysis demo"""
    try:
        from financial_analysis.core.financial_analyzer import main
        print("📊 Running Financial Analysis Demo...")
        main()
    except Exception as e:
        print(f"❌ Error running demo: {e}")

def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(description="Financial Analysis Application")
    parser.add_argument(
        "command",
        choices=["api", "test", "demo"],
        help="Command to run: api (start server), test (run tests), demo (run demo)"
    )
    
    args = parser.parse_args()
    
    if args.command == "api":
        run_api_server()
    elif args.command == "test":
        run_tests()
    elif args.command == "demo":
        run_demo()

if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("📋 Financial Analysis Application")
        print("Usage: python main.py <command>")
        print("Commands:")
        print("  api   - Start the FastAPI server")
        print("  test  - Run the test suite")
        print("  demo  - Run the financial analysis demo")
    else:
        main()