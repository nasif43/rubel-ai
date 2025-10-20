#!/bin/bash

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/Scripts/activate
fi

# Run the conversation with MCP support
python stt_groq_mcp.py