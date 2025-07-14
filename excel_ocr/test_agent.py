#!/usr/bin/env python3
"""
Test script for the Financial Report Agent
This demonstrates how the agent works with chat interactions
"""

import requests
import json
import time

class AgentTester:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()

    def test_agent_chat(self, message: str):
        """Test the agent chat endpoint"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/agent/chat",
                json={"message": message},
                timeout=120
            )

            if response.status_code == 200:
                data = response.json()
                return data["response"]
            else:
                return f"Error: {response.status_code} - {response.text}"

        except Exception as e:
            return f"Error: {str(e)}"

    def test_conversation_flow(self):
        """Test a complete conversation flow"""
        print("🤖 Testing Financial Report Agent")
        print("=" * 50)

        # Test conversation flow
        test_messages = [
            "Hello! What can you do?",
            "Can you list the available files?",
            "Please generate a financial report",
            "What insights did you find in the data?",
            "Thank you for your help!"
        ]

        for message in test_messages:
            print(f"\n👤 User: {message}")
            print("⏳ Processing...")

            response = self.test_agent_chat(message)
            print(f"🤖 Agent: {response}")

            # Add a small delay between messages
            time.sleep(2)

    def test_agent_endpoints(self):
        """Test all agent endpoints"""
        print("\n🧪 Testing Agent Endpoints")
        print("=" * 30)

        # Test available files
        print("\n📁 Testing file listing...")
        try:
            response = self.session.get(f"{self.base_url}/api/agent/files")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Found {data['count']} files: {data['files']}")
            else:
                print(f"❌ Error: {response.status_code}")
        except Exception as e:
            print(f"❌ Error: {e}")

        # Test conversation history
        print("\n📜 Testing conversation history...")
        try:
            response = self.session.get(f"{self.base_url}/api/agent/conversation")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Conversation has {len(data['conversation'])} messages")
            else:
                print(f"❌ Error: {response.status_code}")
        except Exception as e:
            print(f"❌ Error: {e}")

        # Test clear conversation
        print("\n🔄 Testing clear conversation...")
        try:
            response = self.session.post(f"{self.base_url}/api/agent/clear")
            if response.status_code == 200:
                print("✅ Conversation cleared successfully")
            else:
                print(f"❌ Error: {response.status_code}")
        except Exception as e:
            print(f"❌ Error: {e}")

def main():
    """Main test function"""
    print("🚀 Financial Report Agent Test Suite")
    print()

    # Check if server is running
    try:
        response = requests.get("http://localhost:8000/", timeout=5)
        if response.status_code != 200:
            print("❌ Server not running at http://localhost:8000")
            print("💡 Start the server with: python -m uvicorn api_server:app --reload")
            return
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server at http://localhost:8000")
        print("💡 Start the server with: python -m uvicorn api_server:app --reload")
        return

    tester = AgentTester()

    # Test conversation flow
    tester.test_conversation_flow()

    # Test all endpoints
    tester.test_agent_endpoints()

    print("\n✅ Agent testing completed!")
    print("\n🎯 Integration Points for Frontend:")
    print("   - POST /api/agent/chat - Main chat interface")
    print("   - GET /api/agent/conversation - Get chat history")
    print("   - POST /api/agent/clear - Clear conversation")
    print("   - GET /api/agent/files - List available files")

if __name__ == "__main__":
    main()
