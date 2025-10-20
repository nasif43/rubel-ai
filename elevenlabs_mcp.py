"""
ElevenLabs Model Context Protocol (MCP) Server

This module provides a FastAPI server implementing the Model Context Protocol (MCP)
for ElevenLabs TTS integration. It handles text-to-speech generation with advanced
features like word-level timestamps for lip sync.

Usage:
  uvicorn elevenlabs_mcp:app --reload --host 0.0.0.0 --port 8080
"""

import os
import json
import time
import base64
import asyncio
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import requests
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
VOICE_ID = "JBFqnCBsd6RMkjVDRZzb"  # Default voice ID
OUTPUT_DIR = "conversation_data"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# FastAPI app
app = FastAPI(
    title="ElevenLabs MCP Server",
    description="Model Context Protocol server for ElevenLabs TTS integration",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class TtsRequest(BaseModel):
    """Request for text-to-speech generation"""
    text: str
    voice_id: Optional[str] = Field(default=VOICE_ID, description="ElevenLabs voice ID")
    model_id: Optional[str] = Field(default="eleven_flash_v2_5", description="Model ID")
    stability: Optional[float] = Field(default=0.5, description="Voice stability")
    similarity_boost: Optional[float] = Field(default=0.75, description="Voice similarity boost")
    return_timestamps: Optional[bool] = Field(default=True, description="Return word-level timestamps")

class TtsResponse(BaseModel):
    """Response for text-to-speech generation"""
    audio_file: str
    timestamp_file: Optional[str] = None
    audio_base64: Optional[str] = None
    timestamps: Optional[Dict[str, Any]] = None
    request_id: str

class TtsAsyncStatusResponse(BaseModel):
    """Response for async TTS status check"""
    status: str
    request_id: str
    audio_file: Optional[str] = None
    timestamp_file: Optional[str] = None
    error: Optional[str] = None

# Store for async TTS jobs
tts_jobs = {}

@app.get("/")
async def root():
    return {"status": "ElevenLabs MCP Server is running"}

@app.post("/v1/tts", response_model=TtsResponse)
async def generate_speech(request: TtsRequest):
    """Generate speech from text using ElevenLabs API"""
    if not ELEVENLABS_API_KEY:
        raise HTTPException(status_code=500, detail="ELEVENLABS_API_KEY not set")
    
    timestamp_id = int(time.time())
    request_id = f"{timestamp_id}"
    
    audio_file = os.path.join(OUTPUT_DIR, f"response_audio_{timestamp_id}.mp3")
    timestamp_file = os.path.join(OUTPUT_DIR, f"response_timestamps_{timestamp_id}.json")
    
    try:
        # Prepare API request
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{request.voice_id}"
        headers = {
            "xi-api-key": ELEVENLABS_API_KEY,
            "Content-Type": "application/json"
        }
        
        data = {
            "text": request.text,
            "model_id": request.model_id,
            "voice_settings": {
                "stability": request.stability,
                "similarity_boost": request.similarity_boost
            }
        }
        
        # Add timestamp support if requested
        if request.return_timestamps:
            data["return_word_timings"] = True
            data["output_format"] = "json"
        
        # Make API request
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        
        timestamps = None
        audio_content = None
        
        # Process response based on content type
        content_type = response.headers.get("Content-Type", "")
        
        if "application/json" in content_type and request.return_timestamps:
            response_data = response.json()
            
            # Extract audio content
            if "audio" in response_data and isinstance(response_data["audio"], str):
                audio_content = base64.b64decode(response_data["audio"])
                
                # Save audio file
                with open(audio_file, "wb") as f:
                    f.write(audio_content)
                
                # Process word timings
                word_timestamps = []
                if "word_timings" in response_data:
                    for timing in response_data["word_timings"]:
                        if len(timing) >= 2:
                            word = timing[0]
                            times = timing[1]
                            if len(times) >= 2:
                                word_timestamps.append({
                                    "word": word,
                                    "start": times[0],
                                    "end": times[1]
                                })
                
                # Save timestamp data
                timestamps = {"words": word_timestamps}
                with open(timestamp_file, "w") as f:
                    json.dump(timestamps, f, indent=2)
                
        else:
            # Direct audio response
            audio_content = response.content
            with open(audio_file, "wb") as f:
                f.write(audio_content)
            
            # Create empty timestamp data if timestamps were requested
            if request.return_timestamps:
                timestamps = {"words": []}
                with open(timestamp_file, "w") as f:
                    json.dump(timestamps, f, indent=2)
        
        # Prepare response
        return TtsResponse(
            audio_file=audio_file,
            timestamp_file=timestamp_file if request.return_timestamps else None,
            audio_base64=base64.b64encode(audio_content).decode("utf-8"),
            timestamps=timestamps,
            request_id=request_id
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS generation failed: {str(e)}")

@app.post("/v1/tts/async", response_model=TtsAsyncStatusResponse)
async def generate_speech_async(request: TtsRequest, background_tasks: BackgroundTasks):
    """Generate speech asynchronously"""
    if not ELEVENLABS_API_KEY:
        raise HTTPException(status_code=500, detail="ELEVENLABS_API_KEY not set")
    
    timestamp_id = int(time.time())
    request_id = f"{timestamp_id}"
    
    # Store job status
    tts_jobs[request_id] = {"status": "pending", "request": request.dict()}
    
    # Schedule background task
    background_tasks.add_task(process_tts_async, request_id, request)
    
    return TtsAsyncStatusResponse(
        status="pending",
        request_id=request_id
    )

@app.get("/v1/tts/status/{request_id}", response_model=TtsAsyncStatusResponse)
async def get_tts_status(request_id: str):
    """Get status of async TTS job"""
    if request_id not in tts_jobs:
        raise HTTPException(status_code=404, detail=f"Job with ID {request_id} not found")
    
    job = tts_jobs[request_id]
    
    return TtsAsyncStatusResponse(
        status=job["status"],
        request_id=request_id,
        audio_file=job.get("audio_file"),
        timestamp_file=job.get("timestamp_file"),
        error=job.get("error")
    )

async def process_tts_async(request_id: str, request: TtsRequest):
    """Process TTS request asynchronously"""
    audio_file = os.path.join(OUTPUT_DIR, f"response_audio_{request_id}.mp3")
    timestamp_file = os.path.join(OUTPUT_DIR, f"response_timestamps_{request_id}.json")
    
    try:
        # Prepare API request
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{request.voice_id}"
        headers = {
            "xi-api-key": ELEVENLABS_API_KEY,
            "Content-Type": "application/json"
        }
        
        data = {
            "text": request.text,
            "model_id": request.model_id,
            "voice_settings": {
                "stability": request.stability,
                "similarity_boost": request.similarity_boost
            }
        }
        
        # Add timestamp support if requested
        if request.return_timestamps:
            data["return_word_timings"] = True
            data["output_format"] = "json"
        
        # Make API request
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        
        # Process response based on content type
        content_type = response.headers.get("Content-Type", "")
        
        if "application/json" in content_type and request.return_timestamps:
            response_data = response.json()
            
            # Extract audio content
            if "audio" in response_data and isinstance(response_data["audio"], str):
                audio_content = base64.b64decode(response_data["audio"])
                
                # Save audio file
                with open(audio_file, "wb") as f:
                    f.write(audio_content)
                
                # Process word timings
                word_timestamps = []
                if "word_timings" in response_data:
                    for timing in response_data["word_timings"]:
                        if len(timing) >= 2:
                            word = timing[0]
                            times = timing[1]
                            if len(times) >= 2:
                                word_timestamps.append({
                                    "word": word,
                                    "start": times[0],
                                    "end": times[1]
                                })
                
                # Save timestamp data
                timestamps = {"words": word_timestamps}
                with open(timestamp_file, "w") as f:
                    json.dump(timestamps, f, indent=2)
                
        else:
            # Direct audio response
            audio_content = response.content
            with open(audio_file, "wb") as f:
                f.write(audio_content)
            
            # Create empty timestamp data if timestamps were requested
            if request.return_timestamps:
                timestamps = {"words": []}
                with open(timestamp_file, "w") as f:
                    json.dump(timestamps, f, indent=2)
        
        # Update job status
        tts_jobs[request_id] = {
            "status": "completed",
            "audio_file": audio_file,
            "timestamp_file": timestamp_file if request.return_timestamps else None
        }
        
    except Exception as e:
        # Update job status with error
        tts_jobs[request_id] = {
            "status": "failed",
            "error": str(e)
        }

@app.get("/v1/voices")
async def list_voices():
    """List available ElevenLabs voices"""
    if not ELEVENLABS_API_KEY:
        raise HTTPException(status_code=500, detail="ELEVENLABS_API_KEY not set")
    
    try:
        url = "https://api.elevenlabs.io/v1/voices"
        headers = {
            "xi-api-key": ELEVENLABS_API_KEY
        }
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        return response.json()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list voices: {str(e)}")

@app.get("/v1/models")
async def list_models():
    """List available ElevenLabs models"""
    if not ELEVENLABS_API_KEY:
        raise HTTPException(status_code=500, detail="ELEVENLABS_API_KEY not set")
    
    try:
        url = "https://api.elevenlabs.io/v1/models"
        headers = {
            "xi-api-key": ELEVENLABS_API_KEY
        }
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        return response.json()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list models: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("elevenlabs_mcp:app", host="0.0.0.0", port=8080, reload=True)