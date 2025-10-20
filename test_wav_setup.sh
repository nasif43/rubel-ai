#!/bin/bash

# Test script to verify WAV audio generation setup

echo "=== Testing WAV Audio Generation Setup ==="

# Check if virtual environment exists and activate it
if [ -d ".venv" ]; then
    echo "Activating virtual environment..."
    source .venv/Scripts/activate
fi

# Check Python
echo "Checking Python..."
python --version

# Check if required files exist
echo "Checking required files..."
if [ -f "rubel_dialogue.json" ]; then
    echo "✓ rubel_dialogue.json found"
else
    echo "✗ rubel_dialogue.json not found"
fi

if [ -f "generate_rubel_wav_from_json.py" ]; then
    echo "✓ generate_rubel_wav_from_json.py found"
else
    echo "✗ generate_rubel_wav_from_json.py not found"
fi

if [ -f "elevenlabs_mcp_client.py" ]; then
    echo "✓ elevenlabs_mcp_client.py found"
else
    echo "✗ elevenlabs_mcp_client.py not found"
fi

# Check environment variables
echo "Checking environment variables..."
if [ -f ".env" ]; then
    echo "✓ .env file found"
    if grep -q "ELEVENLABS_API_KEY" .env; then
        echo "✓ ELEVENLABS_API_KEY found in .env"
    else
        echo "✗ ELEVENLABS_API_KEY not found in .env"
    fi
else
    echo "✗ .env file not found"
fi

# Test MCP client import
echo "Testing MCP client import..."
python -c "from elevenlabs_mcp_client import ElevenLabsMcpClient; print('✓ MCP client import successful')"

echo "=== Setup Check Complete ==="
echo ""
echo "To generate WAV audio, run:"
echo "python generate_rubel_wav_from_json.py --json rubel_dialogue.json"