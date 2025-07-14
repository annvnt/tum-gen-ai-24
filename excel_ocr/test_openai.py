#!/usr/bin/env python3
"""
Simple OpenAI API Test Script
Tests the OpenAI API connection with a basic prompt
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

def test_openai_api():
    """Test OpenAI API with a simple prompt"""
    print("🧪 Testing OpenAI API Connection")
    print("=" * 40)

    # Load environment variables from parent directory
    env_path = Path(__file__).parent.parent / ".env"
    load_dotenv(dotenv_path=env_path)

    # Get API key
    api_key = os.getenv("API_KEY")
    if not api_key:
        print("❌ API_KEY not found in environment variables")
        return False

    print(f"✅ API Key found: {api_key[:10]}...")

    try:
        # Initialize OpenAI client
        client = OpenAI(api_key=api_key)
        print("✅ OpenAI client initialized")

        # Test prompt: 100-word action story
        test_prompt = "Write a 100-word action story about a spy infiltrating a high-tech facility."

        print(f"📝 Sending test prompt: {test_prompt}")
        print("⏳ Waiting for GPT response...")

        # Call GPT API
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a creative storyteller."},
                {"role": "user", "content": test_prompt}
            ],
            max_tokens=150,
            temperature=0.7
        )

        # Extract response
        story = response.choices[0].message.content

        print("✅ GPT API test successful!")
        print("\n📖 Generated Story:")
        print("-" * 40)
        print(story)
        print("-" * 40)

        # Word count check
        word_count = len(story.split())
        print(f"📊 Word count: {word_count}")

        return True

    except Exception as e:
        print(f"❌ OpenAI API test failed: {str(e)}")
        return False

def main():
    """Main function"""
    success = test_openai_api()

    if success:
        print("\n🎉 OpenAI API is working correctly!")
        print("💡 You can now proceed with the financial analysis tests.")
    else:
        print("\n🔧 OpenAI API test failed. Please check:")
        print("   - Your API key is valid and has credits")
        print("   - The .env file exists in the parent directory")
        print("   - The API_KEY variable is set correctly")

if __name__ == "__main__":
    main()
