#!/usr/bin/env python3
"""
Test script to upload a file and ask questions about it
"""

import requests
import json
import os

# Server URL
BASE_URL = "http://localhost:8000"

def upload_file(file_path):
    """Upload a file to the knowledge base"""
    print(f"📁 Uploading file: {file_path}")

    with open(file_path, 'rb') as f:
        files = {'file': f}
        response = requests.post(f"{BASE_URL}/api/financial/upload", files=files)

    if response.status_code == 200:
        result = response.json()
        print(f"✅ File uploaded successfully!")
        print(f"   File ID: {result['file_id']}")
        print(f"   Status: {result['status']}")
        return result['file_id']
    else:
        print(f"❌ Upload failed: {response.status_code}")
        print(f"   Error: {response.text}")
        return None

def ask_question(question, session_id="test_session", file_id=None):
    """Ask a question about the uploaded file"""
    print(f"\n💬 Asking question: {question}")

    payload = {
        "message": question,
        "session_id": session_id,
        "use_context": True
    }

    if file_id:
        payload["document_id"] = file_id

    response = requests.post(f"{BASE_URL}/api/agent/chat", json=payload)

    if response.status_code == 200:
        result = response.json()
        print(f"🤖 Response: {result['response']}")
        return result
    else:
        print(f"❌ Question failed: {response.status_code}")
        print(f"   Error: {response.text}")
        return None

def main():
    # Test file path
    test_file = "/Users/koussy/PycharmProjects/tum-gen-ai-24/excel_ocr/input/demo_data.xlsx"

    # Upload file
    file_id = upload_file(test_file)

    if file_id:
        print(f"\n🎉 Ready to ask questions about the uploaded file!")
        print(f"File ID: {file_id}")

        # Ask some test questions
        questions = [
            "What type of data is in this file?",
            "Can you summarize the main financial information?",
            "What are the key financial metrics shown?",
            "Are there any trends or patterns in the data?"
        ]

        for question in questions:
            ask_question(question, file_id=file_id)
            print("-" * 50)

if __name__ == "__main__":
    main()
