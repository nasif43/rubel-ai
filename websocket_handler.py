"""
WebSocket handler module for Rubel AI Chat Application.

This module manages WebSocket connections and message handling including:
- Client connection management
- Role-based authentication
- Message broadcasting
- Conversation context maintenance
"""

import json
import asyncio
from typing import Dict, List, Any
from aiohttp import web, WSMsgType

from prompts import get_system_prompt
from utility import clean_response
from groq_client import get_groq_response
from tts import text_to_speech_direct, play_audio_interruptible
from config import VALID_ROLES

# Global clients dictionary: {websocket: {"role": str, "context": list}}
clients: Dict[web.WebSocketResponse, Dict[str, Any]] = {}

async def broadcast(message: Dict[str, Any]) -> None:
    """
    Broadcast a message to all connected clients.

    This function sends a message to all active WebSocket clients.
    It handles exceptions gracefully to prevent one failed client
    from affecting others.

    Args:
        message (Dict[str, Any]): The message to broadcast
    """
    if clients:
        await asyncio.gather(
            *[ws.send_str(json.dumps(message)) for ws in clients.keys()],
            return_exceptions=True
        )

async def websocket_handler(request: web.Request) -> web.WebSocketResponse:
    """
    Handle a single client WebSocket connection.

    This is the main WebSocket handler that manages the lifecycle of
    client connections, including:
    - Role identification and validation
    - Message processing and AI response generation
    - Audio generation and playback
    - Context management
    - Connection cleanup

    Args:
        request (web.Request): The incoming WebSocket request

    Returns:
        web.WebSocketResponse: The WebSocket response object
    """
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    
    global clients  # Declare clients as global since it's modified

    try:
        # Wait for role identification
        role_msg = await ws.receive_json()
        role = role_msg.get("role")
        if role not in VALID_ROLES:
            await ws.send_str(json.dumps({"error": f"Invalid role. Must be one of: {', '.join(VALID_ROLES)}."}))
            await ws.close()
            return ws

        # Register client
        clients[ws] = {"role": role, "context": []}
        print(f"Client connected with role: {role}")

        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                data = json.loads(msg.data)
                user_text = data.get("text", "").strip()
                if not user_text:
                    continue

                print(f"Received from {role}: {user_text}")

                # Get dynamic prompt and context
                system_prompt = get_system_prompt(role)
                client_context = clients[ws]["context"]
                messages = [{"role": "system", "content": system_prompt}] + client_context + [{"role": "user", "content": user_text}]

                # Generate response
                groq_response = get_groq_response(messages)
                if groq_response:
                    groq_response = clean_response(groq_response)
                    client_context.append({"role": "user", "content": user_text})
                    client_context.append({"role": "assistant", "content": groq_response})

                    # Generate audio
                    print(f"Generating audio for response: {groq_response[:50]}...")
                    audio_content, timestamps = text_to_speech_direct(groq_response, "generate")  # Use default mode
                    if audio_content:
                        print(f"Audio generated successfully, size: {len(audio_content)} bytes")
                        # Play audio locally on the server (interruptible)
                        play_audio_interruptible(audio_content)
                    else:
                        print("Failed to generate audio content")

                    # Broadcast only text to all clients
                    broadcast_msg = {"from": "Rubel", "text": groq_response}
                    await broadcast(broadcast_msg)
                    print(f"Broadcasted Rubel's response to all clients")
                else:
                    print("Failed to generate Groq response")
            elif msg.type == WSMsgType.ERROR:
                print(f"WebSocket error: {ws.exception()}")

    except Exception as e:
        print(f"Error handling client: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if ws in clients:
            print(f"Client disconnected: {clients[ws]['role']}")
            del clients[ws]

    return ws