import speech_recognition as sr
import os
import json
import time
import io
import subprocess
import threading
import requests
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


def recognize_speech():
    """Capture and transcribe speech from microphone"""
    recognizer: Any = sr.Recognizer()
    
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
    """Get response from Groq LLM API"""
    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages
    )
    return response.choices[0].message.content

def text_to_speech_direct(text, mode="generate"):
    """Convert text to speech using ElevenLabs SDK directly
    
    Args:
        text: Text to convert to speech
        mode: "generate" for convert_with_timestamps or "stream" for stream_with_timestamps
    """
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


def main():
    # Check for required API keys
    if not os.getenv("GROQ_API_KEY"):
        print("Error: GROQ_API_KEY environment variable not set.")
        return
    
    if not os.getenv("ELEVENLABS_API_KEY"):
        print("Warning: ELEVENLABS_API_KEY not set. Voice output will be disabled.")
    
    # Choose TTS mode
    print("\n=== ElevenLabs TTS Mode Selection ===")
    print("1. Generate audio with timestamps (download complete audio)")
    print("2. Stream audio with timestamps (real-time streaming)")
    while True:
        try:
            choice = input("Choose mode (1 or 2): ").strip()
            if choice == "1":
                tts_mode = "generate"
                break
            elif choice == "2":
                tts_mode = "stream"
                break
            else:
                print("Please enter 1 or 2.")
        except KeyboardInterrupt:
            print("\nExiting...")
            return
    
    print(f"\nSelected mode: {tts_mode}")
    
    # Initialize conversation
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    print("\n=== Starting conversation with Rubel ===")
    print("Speak to begin. Press Ctrl+C to stop.\n")
    
    try:
        while True:
            # Step 1: Get user input via speech recognition
            user_input = recognize_speech()
            if not user_input:
                continue
            
            # Step 2: Add user message to conversation history
            messages.append({"role": "user", "content": user_input})
            
            # Step 3: Get AI response
            groq_response = get_groq_response(messages)
            messages.append({"role": "assistant", "content": groq_response or ""})
            
            # Step 4: Display text response
            print(f"\nRubel: {groq_response}\n")
            
            # Step 5: Generate speech
            if os.getenv("ELEVENLABS_API_KEY"):
                audio_content, timestamps = text_to_speech_direct(groq_response, tts_mode)
                
                if audio_content:
                    # Convert bytes to audio and play
                    audio = AudioSegment.from_file(io.BytesIO(audio_content), format="mp3")
                    play(audio)
                    print("\n=== Audio playback complete ===\n")
    
    except KeyboardInterrupt:
        print("\n\n=== Conversation ended ===")

if __name__ == "__main__":
    main()