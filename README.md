Overview

This workspace runs a local roleplay assistant (Tanvir) using Groq for text and ElevenLabs for TTS, and exposes a small API to retrieve conversation metadata (timestamps, transcripts, audio files).

Setup

1. Create a virtual environment and activate it.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Add a `.env` file with keys:

```
GROQ_API_KEY=your_groq_api_key
ELEVENLABS_API_KEY=your_elevenlabs_api_key
```

Run the conversation (microphone input):

```bash
# Original version
python stt_groq.py

# Simplified version with improved microphone handling
python stt_groq_simplified.py
```

Run the API server (in another terminal):

```bash
uvicorn convai_server:app --reload --host 0.0.0.0 --port 8000
```

Usage

- GET /v1/convai/conversations/{conversation_id} returns metadata JSON with turns, transcript, word timestamps, and audio file names.
- GET /v1/convai/conversations/{conversation_id}/audio/{filename} returns the audio file for playback.
# rubel-ai
