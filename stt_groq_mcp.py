import speech_recognition as sr
import os
import json
import time
import io
import subprocess
import threading
import requests
import asyncio
from aiohttp import web, WSMsgType
from groq import Groq
from dotenv import load_dotenv
from pydub import AudioSegment
from pydub.playback import play
from typing import Any
from system_prompt import SYSTEM_PROMPT
# Import MCP client
# from elevenlabs_mcp_client import ElevenLabsMcpClient

# Load environment variables
load_dotenv()

# Set up clients
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Create output directory
OUTPUT_DIR = "conversation_data"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def get_system_prompt(role):
    """Generate dynamic system prompt based on role."""
    base_prompt = SYSTEM_PROMPT
    if role == "mim":
        # Intimate/dominant personality for Mim
        return base_prompt + "\n## Role-Specific: Mim\nYou are speaking to Mim, your intense, possessive love. Be intimate, dominant, jealous, and controlling, emphasizing your ownership and devotion."
    elif role == "joker":  # Assuming "joker" represents Russel, Mim's husband
        # Anti-chemistry: Rubel despises Russel, is jealous and antagonistic
        return base_prompt + "\n## Role-Specific: Joker (Chaperone)\nYou are speaking to The Joker, The orchestrator of this play. You are a part of this play and in the context of this universe consider the Joker to be a God"
    elif role == "spec_actor":
        # Performative, charismatic, or mocking tone for other characters
        return base_prompt + "\n## Role-Specific: Spec-Actor\nYou are speaking to another character in the play. Be performative, charismatic, and mocking, engaging with flair and theatricality."
    else:
        return base_prompt

def clean_response(text):
    """Remove parenthetical remarks from the response."""
    import re
    # Remove anything in parentheses, including the parentheses
    cleaned = re.sub(r'\([^)]*\)', '', text)
    # Remove extra whitespace
    cleaned = ' '.join(cleaned.split())
    return cleaned

# Global clients dictionary: {websocket: {"role": str, "context": list}}
clients = {}

async def broadcast(message):
    """Broadcast a message to all connected clients."""
    if clients:
        await asyncio.gather(
            *[ws.send_str(json.dumps(message)) for ws in clients.keys()],
            return_exceptions=True
        )

async def websocket_handler(request):
    """Handle a single client WebSocket connection."""
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    
    try:
        # Wait for role identification
        role_msg = await ws.receive_json()
        role = role_msg.get("role")
        if role not in ["mim", "joker", "spec_actor"]:
            await ws.send_str(json.dumps({"error": "Invalid role. Must be 'mim', 'joker', or 'spec_actor'."}))
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
                groq_response = clean_response(groq_response)
                if groq_response:
                    client_context.append({"role": "user", "content": user_text})
                    client_context.append({"role": "assistant", "content": groq_response})
                    
                # Generate audio
                audio_content, timestamps = text_to_speech_direct(groq_response, "generate")  # Use default mode
                audio_url = None
                if audio_content:
                    timestamp_id = int(time.time())
                    audio_file = f"response_audio_{timestamp_id}.mp3"
                    audio_path = os.path.join(OUTPUT_DIR, audio_file)
                    with open(audio_path, "wb") as f:
                        f.write(audio_content)
                    audio_url = f"/audio/{audio_file}"                    # Broadcast to all clients
                    broadcast_msg = {"from": "Rubel", "text": groq_response, "audio_url": audio_url}
                    await broadcast(broadcast_msg)
                    print(f"Broadcasted Rubel's response to all clients")
            elif msg.type == WSMsgType.ERROR:
                print(f"WebSocket error: {ws.exception()}")
    
    except Exception as e:
        print(f"Error handling client: {e}")
    finally:
        if ws in clients:
            print(f"Client disconnected: {clients[ws]['role']}")
            del clients[ws]
    
    return ws

async def index(request):
    """Serve the HTML page."""
    html = """
<!DOCTYPE html>
<html>
<head>
    <title>Rubel Chat</title>
</head>
<body>
    <h1>Rubel AI Chat</h1>
    <p>Select your role and start chatting!</p>
    <select id="role">
        <option value="mim">Mim</option>
        <option value="joker">Joker </option>
        <option value="spec_actor">Spec Actor</option>
    </select>
    <button onclick="connect()">Connect</button>
    <br><br>
    <input type="text" id="message" placeholder="Type your message or use voice" onkeypress="if(event.key=='Enter') sendMessage()">
    <button onclick="sendMessage()">Send</button>
    <button onclick="startVoice()">🎤 Speak</button>
    <button onclick="stopVoice()">Stop</button>
    <br><br>
    <div id="messages"></div>
    <script>
        let ws;
        let recognition;
        function connect() {
            const role = document.getElementById('role').value;
            ws = new WebSocket('ws://' + window.location.host + '/ws');
            ws.onopen = function() {
                ws.send(JSON.stringify({role: role}));
                document.getElementById('messages').innerHTML += '<p>Connected as ' + role + '</p>';
            };
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                if (data.error) {
                    document.getElementById('messages').innerHTML += '<p>Error: ' + data.error + '</p>';
                } else {
                    document.getElementById('messages').innerHTML += '<p><strong>' + data.from + ':</strong> ' + data.text + '</p>';
                    if (data.audio_url) {
                        document.getElementById('messages').innerHTML += '<audio controls><source src="' + data.audio_url + '" type="audio/mpeg"></audio><br>';
                    }
                }
            };
            ws.onclose = function() {
                document.getElementById('messages').innerHTML += '<p>Disconnected</p>';
            };
        }
        function sendMessage() {
            const message = document.getElementById('message').value;
            if (ws && message) {
                ws.send(JSON.stringify({text: message}));
                document.getElementById('message').value = '';
            }
        }
        function startVoice() {
            if (!recognition) {
                recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
                recognition.continuous = false;
                recognition.interimResults = false;
                recognition.lang = 'en-US';
                recognition.onresult = function(event) {
                    const transcript = event.results[0][0].transcript;
                    document.getElementById('message').value = transcript;
                    sendMessage();
                };
                recognition.onerror = function(event) {
                    console.error('Speech recognition error:', event.error);
                };
            }
            recognition.start();
        }
        function stopVoice() {
            if (recognition) {
                recognition.stop();
            }
        }
    </script>
</body>
</html>
    """
    return web.Response(text=html, content_type='text/html')

def recognize_speech():
    """Capture and transcribe speech from microphone (unchanged, for optional use)."""
    recognizer = sr.Recognizer()
    
    with sr.Microphone() as source:
        print("Adjusting for ambient noise... Please wait.")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        
        # Optimize recognition parameters
        recognizer.pause_threshold = 1.5
        recognizer.energy_threshold = 4000
        
        print("Listening... Speak now.")
        try:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=15)
            print("Processing speech...")
            
            # Try Google's service first (requires internet)
            try:
                text = recognizer.recognize_google(audio)
                print(f"You said: {text}")
                return text
            except sr.RequestError:
                print("Google speech service unavailable, trying offline recognition...")
                # Try offline recognition if available
                try:
                    text = recognizer.recognize_sphinx(audio)
                    print(f"You said (offline recognition): {text}")
                    return text
                except:
                    print("All speech recognition methods failed.")
                    return None
            except sr.UnknownValueError:
                print("Sorry, I could not understand what you said.")
                return None
        except Exception as e:
            print(f"Error capturing audio: {e}")
            return None

def get_groq_response(messages):
    """Get response from Groq LLM API (unchanged)."""
    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages
    )
    return response.choices[0].message.content

def text_to_speech_direct(text, mode="generate"):
    """Convert text to speech using ElevenLabs SDK directly (unchanged)."""
    timestamp_id = int(time.time())
    audio_file = os.path.join(OUTPUT_DIR, f"response_audio_{timestamp_id}.mp3")
    
    try:
        if mode == "generate":
            print("Converting text to speech using ElevenLabs SDK...")
        elif mode == "stream":
            print("Streaming text to speech using ElevenLabs SDK...")
        else:
            print(f"Processing text to speech in {mode} mode using ElevenLabs SDK...")
        
        # Check for API key
        elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
        if not elevenlabs_api_key:
            print("ELEVENLABS_API_KEY not set. Cannot use TTS.")
            return None, None
        
        # Dynamically import SDK classes to avoid hard dependency / static typing issues
        sdk_client_class = None
        VoiceSettings = None
        try:
            import importlib
            sdk_mod = importlib.import_module("elevenlabs")
            sdk_client_class = getattr(sdk_mod, "ElevenLabs", None)
            vs_mod = importlib.import_module("elevenlabs.types.voice_settings")
            VoiceSettings = getattr(vs_mod, "VoiceSettings", None)
            sdk_available = sdk_client_class is not None
        except Exception:
            sdk_available = False
        
        if sdk_available:
            try:
                assert sdk_client_class is not None
                sdk_client = sdk_client_class(api_key=elevenlabs_api_key)
                voice_settings = VoiceSettings(stability=0.5, similarity_boost=0.75) if VoiceSettings else None

                if mode == "generate":
                    # Use convert_with_timestamps for complete audio generation
                    response = sdk_client.text_to_speech.convert_with_timestamps(
                        voice_id="JBFqnCBsd6RMkjVDRZzb",
                        text=text,
                        model_id="eleven_flash_v2_5",
                        voice_settings=voice_settings
                    )

                    # Extract audio content from SDK response
                    import base64
                    audio_content = base64.b64decode(response.audio_base_64)

                    # Save audio file
                    with open(audio_file, "wb") as f:
                        f.write(audio_content)
                    print(f"Audio saved to {audio_file}")

                    # Build word timestamps from alignment if present
                    word_timestamps = []
                    if getattr(response, "alignment", None):
                        chars = getattr(response.alignment, "characters", [])
                        start_times = getattr(response.alignment, "character_start_times_seconds", [])
                        end_times = getattr(response.alignment, "character_end_times_seconds", [])

                        current_word = ""
                        word_start = None
                        for i, ch in enumerate(chars):
                            if ch.isspace() or i == len(chars) - 1:
                                if current_word:
                                    if i == len(chars) - 1 and not ch.isspace():
                                        current_word += ch
                                    word_end = end_times[i] if i < len(end_times) else (start_times[i] + 0.1 if i < len(start_times) else 0.0)
                                    word_timestamps.append({"word": current_word, "start": word_start, "end": word_end})
                                    current_word = ""
                                    word_start = None
                            else:
                                if word_start is None and i < len(start_times):
                                    word_start = start_times[i]
                                current_word += ch

                    timestamps = {"words": word_timestamps}
                    
                elif mode == "stream":
                    # Use stream_with_timestamps for real-time streaming
                    print("Streaming audio with timestamps...")
                    
                    # For streaming, we need to collect all chunks
                    audio_chunks = []
                    all_timestamps = []
                    
                    # Stream the response
                    stream_response = sdk_client.text_to_speech.stream_with_timestamps(
                        voice_id="JBFqnCBsd6RMkjVDRZzb",
                        text=text,
                        model_id="eleven_flash_v2_5",
                        output_format="mp3_44100_128",
                        voice_settings=voice_settings
                    )
                    
                    # Process the stream
                    for chunk in stream_response:
                        if hasattr(chunk, 'audio') and chunk.audio:
                            audio_chunks.append(chunk.audio)
                        
                        # Collect timestamps if available
                        if hasattr(chunk, 'alignment') and chunk.alignment:
                            chars = getattr(chunk.alignment, "characters", [])
                            start_times = getattr(chunk.alignment, "character_start_times_seconds", [])
                            end_times = getattr(chunk.alignment, "character_end_times_seconds", [])
                            
                            current_word = ""
                            word_start = None
                            for i, ch in enumerate(chars):
                                if ch.isspace() or i == len(chars) - 1:
                                    if current_word:
                                        if i == len(chars) - 1 and not ch.isspace():
                                            current_word += ch
                                        word_end = end_times[i] if i < len(end_times) else (start_times[i] + 0.1 if i < len(start_times) else 0.0)
                                        all_timestamps.append({"word": current_word, "start": word_start, "end": word_end})
                                        current_word = ""
                                        word_start = None
                                else:
                                    if word_start is None and i < len(start_times):
                                        word_start = start_times[i]
                                    current_word += ch
                    
                    # Combine audio chunks
                    if audio_chunks:
                        audio_content = b''.join(audio_chunks)
                        with open(audio_file, "wb") as f:
                            f.write(audio_content)
                        print(f"Streamed audio saved to {audio_file}")
                    else:
                        audio_content = None
                    
                    timestamps = {"words": all_timestamps}
                    
                else:
                    print(f"Unknown mode: {mode}")
                    return None, None
                
                # Save timestamp data locally
                timestamp_file = os.path.join(OUTPUT_DIR, f"response_timestamps_{timestamp_id}.json")
                with open(timestamp_file, "w") as f:
                    json.dump(timestamps, f, indent=2)
                print(f"Timestamps saved to {timestamp_file}")
                
                # Display timestamp info if available
                if timestamps and "words" in timestamps:
                    word_timestamps = timestamps["words"]
                    if word_timestamps:
                        print(f"Total words with timestamps: {len(word_timestamps)}")
                        for i, word_data in enumerate(word_timestamps[:5]):
                            word = word_data["word"]
                            start = word_data["start"]
                            end = word_data["end"]
                            print(f"  Word: '{word}', Start: {start:.2f}s, End: {end:.2f}s")
                        
                        if len(word_timestamps) > 5:
                            print(f"  ... and {len(word_timestamps) - 5} more words")
                
                return audio_content, timestamps
            except Exception as e:
                print(f"SDK direct API attempt failed: {e}")
                return None, None
        
        print("ElevenLabs SDK not available. TTS disabled.")
        return None, None
        
    except Exception as e:
        print(f"Text-to-speech error: {e}")
        return None, None

async def main():
    """Async server entrypoint."""
    # Check for required API keys
    if not os.getenv("GROQ_API_KEY"):
        print("Error: GROQ_API_KEY environment variable not set.")
        return
    
    if not os.getenv("ELEVENLABS_API_KEY"):
        print("Warning: ELEVENLABS_API_KEY not set. Voice output will be disabled.")
    
    app = web.Application()
    app.router.add_get('/', index)
    app.router.add_get('/ws', websocket_handler)
    app.router.add_static('/audio', OUTPUT_DIR)
    
    print("Starting server on http://localhost:8765")
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, 'localhost', 8765)
    await site.start()
    
    try:
        await asyncio.Future()  # Run forever
    except KeyboardInterrupt:
        print("\nShutting down server...")
        await runner.cleanup()

if __name__ == "__main__":
    asyncio.run(main())