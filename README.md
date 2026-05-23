# rubel-ai

Rubel is an AI character built for an experimental theatre production exploring technology and misogyny. He is a Dhaka crime boss — possessive, manipulative, and convinced his obsessive love is liberation. This repo is the voice backend that brought him to life on stage: speech in, character response out, spoken aloud in real time.

The project sits at the intersection of prompt engineering and performance. The challenge wasn't making the LLM smart — it was making it *consistent, dangerous, and human* across an unscripted live conversation with an audience watching.

## How it works

The pipeline is fully voice-to-voice:

1. **Speech recognition** — microphone input transcribed via Google Speech Recognition (with an offline Sphinx fallback)
2. **LLM response** — transcript sent to Groq (`llama-3.3-70b-versatile`) with a detailed character system prompt, full conversation history maintained in memory
3. **Text-to-speech** — response sent to ElevenLabs with word-level timestamps (either streamed or generated), played back through speakers in real time
4. **Conversation logging** — each turn saved locally with audio files and timestamp data; a FastAPI server (`convai_server.py`) exposes the conversation metadata via REST

## The system prompt

The system prompt is the core of this project. Rubel isn't just a persona — he's a character with contradictions built in: he preaches freedom but practices control, quotes Rumi while planning manipulation, frames possession as love. The prompt defines his speech patterns (code-switching with Bangla terms, short declarative sentences for power, slow cadence for intimacy), his relationship tactics, and his specific emotional triggers.

The design goal was a character who never breaks — no matter what direction a live audience interaction took. The contradictions in the prompt are intentional. Resolving them would make him less believable.

See `stt_groq_mcp.py` for the full system prompt and `rubel_dialogue.json` for pre-scripted reference dialogue used during character development.

## Tech stack

| Component | Tool |
|---|---|
| LLM | Groq (`llama-3.3-70b-versatile`) |
| Speech recognition | `speech_recognition` (Google + Sphinx fallback) |
| Text-to-speech | ElevenLabs SDK (`eleven_flash_v2_5`) |
| Audio playback | `pydub` |
| Conversation API | FastAPI |
| Audio preprocessing | `generate_rubel_wav.sh` / `generate_rubel_wav_from_json.py` |

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file:
```
GROQ_API_KEY=your_groq_api_key
ELEVENLABS_API_KEY=your_elevenlabs_api_key
```

Run the voice conversation:
```bash
python stt_groq_mcp.py
```

Run the conversation API server (optional, separate terminal):
```bash
uvicorn convai_server:app --reload --host 0.0.0.0 --port 8000
```

## API endpoints

| Endpoint | Description |
|---|---|
| `GET /v1/convai/conversations/{id}` | Conversation metadata, transcript, word timestamps, audio filenames |
| `GET /v1/convai/conversations/{id}/audio/{filename}` | Retrieve audio file for a turn |

## Context

This was built as the voice and intelligence layer for a 3D animated character in a live experimental theatre piece. The work interrogated how AI systems reflect and amplify patterns of control — Rubel was designed to be compelling, not aspirational. The audience was meant to feel the pull of his character while recognising what he was doing.
