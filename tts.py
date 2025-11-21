"""
Text-to-Speech module for Rubel AI Chat Application.

This module handles all text-to-speech functionality using ElevenLabs API including:
- Converting text to speech with timestamps
- Streaming audio generation
- Audio file management and playback
- Voice configuration and settings
"""

import os
import time
import json
import io
import base64
import asyncio
import threading
import subprocess
import shutil
sa = None
from typing import Tuple, Dict, List, Any
from config import OUTPUT_DIR
from pydub import AudioSegment
from pydub.playback import play

async def play_audio_async(audio_content: bytes) -> None:
    """
    Play audio content asynchronously without blocking the event loop.
    """
    def play_in_thread():
        try:
            print(f"Playing audio on server, size: {len(audio_content)} bytes")
            audio = AudioSegment.from_file(io.BytesIO(audio_content), format="mp3")
            print(f"Audio loaded: {len(audio)}ms duration")
            play(audio)
            print("Audio played successfully on server.")
        except Exception as e:
            print(f"Error playing audio: {e}")
            import traceback
            traceback.print_exc()
    
    # Run audio playback in a thread pool to avoid blocking asyncio
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, play_in_thread)

# Global variable to track current audio playback
current_audio_thread = None
audio_stop_event = threading.Event()
# simpleaudio play object for immediate stop
current_play_obj = None
# subprocess used for fallback playback (when simpleaudio not available)
current_subprocess = None

def text_to_speech_direct(text: str, mode: str = "generate") -> Tuple[bytes | None, Dict | None]:
    """
    Convert text to speech using ElevenLabs SDK directly.

    This function handles text-to-speech conversion with support for different modes:
    - "generate": Generate complete audio with timestamps
    - "stream": Stream audio in real-time (not fully implemented for playback)

    Args:
        text (str): The text to convert to speech
        mode (str): The generation mode ("generate" or "stream")

    Returns:
        Tuple[bytes | None, Dict | None]: A tuple containing:
            - Audio content as bytes, or None if failed
            - Timestamp data as dict, or None if failed

    Note:
        Requires ELEVENLABS_API_KEY environment variable to be set.
        Audio is saved to the conversation_data directory.
    """
    from config import OUTPUT_DIR, ELEVENLABS_API_KEY, VOICE_ID, MODEL_ID, VOICE_SETTINGS

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
        if not ELEVENLABS_API_KEY:
            print("ELEVENLABS_API_KEY not set. Cannot use TTS.")
            return None, None

        # Dynamically import SDK classes to avoid hard dependency/static typing issues
        sdk_client_class = None
        VoiceSettings = None
        try:
            import importlib
            sdk_mod = importlib.import_module("elevenlabs")
            sdk_client_class = getattr(sdk_mod, "ElevenLabs", None)
            vs_mod = importlib.import_module("elevenlabs.types.voice_settings")
            VoiceSettings = getattr(vs_mod, "VoiceSettings", None)
            sdk_available = sdk_client_class is not None
        except Exception as import_error:
            print(f"Failed to import ElevenLabs SDK: {import_error}")
            sdk_available = False

        if sdk_available:
            try:
                assert sdk_client_class is not None
                sdk_client = sdk_client_class(api_key=ELEVENLABS_API_KEY)
                voice_settings = VoiceSettings(**VOICE_SETTINGS) if VoiceSettings else None

                if mode == "generate":
                    response = sdk_client.text_to_speech.convert_with_timestamps(
                        voice_id=VOICE_ID,
                        text=text,
                        model_id=MODEL_ID,
                        voice_settings=voice_settings
                    )

                    # Extract audio content from SDK response
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
                        voice_id=VOICE_ID,
                        text=text,
                        model_id=MODEL_ID,
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
            except Exception as sdk_error:
                print(f"SDK direct API attempt failed: {sdk_error}")
                return None, None

        print("ElevenLabs SDK not available. TTS disabled.")
        return None, None

    except Exception as e:
        print(f"Text-to-speech error: {e}")
        return None, None

def play_audio_interruptible(audio_content: bytes) -> None:
    """
    Play audio content on the server in a background thread and allow interruption.

    This prefers `simpleaudio` for low-latency playback. If `simpleaudio` is not
    available, it falls back to launching a subprocess player (platform-specific).

    The function returns immediately; actual playback occurs in `current_audio_thread`.
    """
    global current_audio_thread, audio_stop_event, current_play_obj, current_subprocess

    # Stop any currently playing audio
    stop_audio()

    def audio_thread():
        global current_play_obj, current_subprocess
        try:
            print(f"Playing audio on server, size: {len(audio_content)} bytes")
            # Decode MP3 bytes into AudioSegment
            audio = AudioSegment.from_file(io.BytesIO(audio_content), format="mp3")
            print(f"Audio loaded: {len(audio)}ms duration")

            # Export to WAV and play via subprocess so we can reliably terminate playback
            import tempfile
            fd, temp_wav = tempfile.mkstemp(suffix=".wav", dir=OUTPUT_DIR)
            os.close(fd)
            try:
                # Export decoded audio to WAV (PCM)
                audio.export(temp_wav, format='wav')

                if os.name == 'nt':
                    # Use PowerShell SoundPlayer synchronously in this thread; terminating the process will stop playback
                    cmd = ['powershell', '-c', f"(New-Object Media.SoundPlayer '{temp_wav}').PlaySync()"]
                else:
                    if shutil.which('ffplay'):
                        cmd = ['ffplay', '-nodisp', '-autoexit', '-loglevel', 'quiet', temp_wav]
                    elif shutil.which('mpg123'):
                        cmd = ['mpg123', '-q', temp_wav]
                    else:
                        # As last resort, use pydub play (less interruptible)
                        play(audio)
                        cmd = None

                if cmd:
                    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    current_subprocess = proc
                    while proc.poll() is None:
                        if audio_stop_event.is_set():
                            try:
                                proc.terminate()
                            except Exception:
                                pass
                            break
                        time.sleep(0.05)
                    current_subprocess = None
            finally:
                try:
                    os.remove(temp_wav)
                except Exception:
                    pass

            print("Audio playback finished")

        except Exception as e:
            print(f"Error in audio playback thread: {e}")
            import traceback
            traceback.print_exc()

    # Reset stop event and start thread
    audio_stop_event.clear()
    current_audio_thread = threading.Thread(target=audio_thread, daemon=True)
    current_audio_thread.start()
    print("Audio playback thread started")

def stop_audio() -> None:
    """
    Stop any currently playing audio.
    """
    global current_audio_thread, audio_stop_event
    if current_audio_thread and current_audio_thread.is_alive():
        audio_stop_event.set()
        current_audio_thread.join(timeout=1.0)  # Wait up to 1 second for thread to stop
        print("Audio playback stopped.")

def play_audio(audio_content: bytes) -> None:
    """
    Play audio content locally using pydub (legacy function).
    This is kept for backward compatibility but play_audio_interruptible is preferred.
    """
    try:
        audio = AudioSegment.from_file(io.BytesIO(audio_content), format="mp3")
        play(audio)
        print("Audio played locally on server.")
    except Exception as e:
        print(f"Error playing audio: {e}")