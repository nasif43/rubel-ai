# ElevenLabs MCP Integration

This document describes the ElevenLabs Model Context Protocol (MCP) server integration for the AI roleplay conversation system.

## Overview

The ElevenLabs MCP server provides a structured interface for text-to-speech generation with advanced features:

- Word-level timestamps for accurate lip-sync
- Voice and model selection
- Asynchronous TTS processing
- Audio format control

## Architecture

The MCP integration consists of two main components:

1. **ElevenLabs MCP Server** (`elevenlabs_mcp.py`): A FastAPI server implementing the MCP protocol for TTS generation
2. **ElevenLabs MCP Client** (`elevenlabs_mcp_client.py`): A Python client library for interacting with the MCP server

## Running the MCP Server

You can run the MCP server in two ways:

### 1. Standalone Mode

```bash
# Run the server directly
bash run_mcp_server.sh

# Or manually with
uvicorn elevenlabs_mcp:app --reload --host 0.0.0.0 --port 8080
```

### 2. Auto-start Mode

The updated conversation script (`stt_groq_mcp.py`) will attempt to start the MCP server automatically if it's not already running.

## Using the MCP-enabled Conversation

```bash
# Run the MCP-enabled conversation script
bash run_conversation_mcp.sh

# Or manually with
python stt_groq_mcp.py
```

## API Endpoints

The MCP server exposes the following endpoints:

- `GET /`: Server status check
- `POST /v1/tts`: Generate speech from text
- `POST /v1/tts/async`: Generate speech asynchronously
- `GET /v1/tts/status/{request_id}`: Check status of async TTS job
- `GET /v1/voices`: List available ElevenLabs voices
- `GET /v1/models`: List available ElevenLabs models

## Integration with Existing Code

The MCP integration provides a seamless fallback mechanism:

1. It tries to use the MCP server first for enhanced features like timestamps
2. If the MCP server is unavailable, it falls back to direct API calls
3. The client provides a simple interface that matches the existing code structure

## Future Enhancements

- Support for streaming audio responses
- Caching of frequently used responses
- More voice customization options
- Integration with the planned conversation API server