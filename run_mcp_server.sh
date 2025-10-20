#!/bin/bash

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/Scripts/activate
fi

# Run the ElevenLabs MCP server
uvicorn elevenlabs_mcp:app --reload --host 0.0.0.0 --port 8080