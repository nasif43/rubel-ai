#!/usr/bin/env python3
"""
Quick test script to verify ElevenLabs direct API works
"""

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_elevenlabs_api():
    """Test ElevenLabs API directly"""
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        print("❌ ELEVENLABS_API_KEY not found in .env")
        return False

    voice_id = "JBFqnCBsd6RMkjVDRZzb"
    test_text = "Hello, this is a test of the ElevenLabs API."

    try:
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        headers = {
            "xi-api-key": api_key,
            "Content-Type": "application/json"
        }

        data = {
            "text": test_text,
            "model_id": "eleven_flash_v2_5",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75
            }
        }

        print("🔄 Testing ElevenLabs API...")
        print(f"URL: {url}")
        print(f"Text: {test_text}")

        response = requests.post(url, json=data, headers=headers, timeout=30)

        if response.status_code == 200:
            audio_content = response.content
            print(f"✅ API call successful! Received {len(audio_content)} bytes of audio data")

            # Save test audio
            with open("test_audio.mp3", "wb") as f:
                f.write(audio_content)
            print("💾 Saved test audio to test_audio.mp3")

            return True
        else:
            print(f"❌ API call failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Error testing API: {e}")
        return False

if __name__ == "__main__":
    print("=== ElevenLabs API Test ===")
    success = test_elevenlabs_api()
    if success:
        print("\n🎉 API test passed! Ready to generate audio.")
    else:
        print("\n💥 API test failed. Check your API key and internet connection.")