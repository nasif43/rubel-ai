"""
ElevenLabs MCP Client

This module provides a client for the ElevenLabs Model Context Protocol (MCP) server,
enabling easy integration with the TTS functionality in other parts of the application.
"""

import os
import json
import base64
import requests
from typing import Dict, Any, Tuple, Optional
import io
from pydub import AudioSegment

class ElevenLabsMcpClient:
    """Client for the ElevenLabs MCP server"""
    
    def __init__(self, base_url: str = "http://localhost:8080"):
        """Initialize the client with the server base URL"""
        self.base_url = base_url
        
    def check_server_status(self) -> bool:
        """Check if the MCP server is running"""
        try:
            response = requests.get(f"{self.base_url}/", timeout=2)
            return response.status_code == 200
        except requests.RequestException:
            return False
    
    def generate_speech(self, text: str, voice_id: str = None, 
                        model_id: str = "eleven_flash_v2_5", 
                        stability: float = 0.5, 
                        similarity_boost: float = 0.75,
                        return_timestamps: bool = True) -> Tuple[Optional[bytes], Optional[Dict[str, Any]]]:
        """
        Generate speech from text using the MCP server
        
        Args:
            text: The text to convert to speech
            voice_id: ElevenLabs voice ID (optional)
            model_id: ElevenLabs model ID
            stability: Voice stability
            similarity_boost: Voice similarity boost
            return_timestamps: Whether to return word-level timestamps
            
        Returns:
            Tuple of (audio_content, timestamps)
        """
        try:
            # Prepare request data
            data = {
                "text": text,
                "model_id": model_id,
                "stability": stability,
                "similarity_boost": similarity_boost,
                "return_timestamps": return_timestamps
            }
            
            # Add voice_id if provided
            if voice_id:
                data["voice_id"] = voice_id
            
            # Make the request
            response = requests.post(f"{self.base_url}/v1/tts", json=data)
            response.raise_for_status()
            
            # Parse response
            result = response.json()
            
            # Get audio content from base64
            audio_content = None
            if "audio_base64" in result and result["audio_base64"]:
                audio_content = base64.b64decode(result["audio_base64"])
                
            # Get timestamps
            timestamps = result.get("timestamps", {"words": []})
            
            return audio_content, timestamps
            
        except Exception as e:
            print(f"Error generating speech via MCP: {e}")
            return None, None
    
    def generate_speech_async(self, text: str, voice_id: str = None,
                             model_id: str = "eleven_flash_v2_5", 
                             stability: float = 0.5, 
                             similarity_boost: float = 0.75,
                             return_timestamps: bool = True) -> str:
        """
        Generate speech asynchronously
        
        Returns:
            request_id for status checking
        """
        try:
            # Prepare request data
            data = {
                "text": text,
                "model_id": model_id,
                "stability": stability,
                "similarity_boost": similarity_boost,
                "return_timestamps": return_timestamps
            }
            
            # Add voice_id if provided
            if voice_id:
                data["voice_id"] = voice_id
            
            # Make the request
            response = requests.post(f"{self.base_url}/v1/tts/async", json=data)
            response.raise_for_status()
            
            # Parse response
            result = response.json()
            
            return result["request_id"]
            
        except Exception as e:
            print(f"Error generating speech asynchronously via MCP: {e}")
            return None
    
    def check_async_status(self, request_id: str) -> Dict[str, Any]:
        """Check status of async TTS job"""
        try:
            response = requests.get(f"{self.base_url}/v1/tts/status/{request_id}")
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            print(f"Error checking async status via MCP: {e}")
            return {"status": "error", "error": str(e)}
    
    def list_voices(self) -> Dict[str, Any]:
        """List available ElevenLabs voices"""
        try:
            response = requests.get(f"{self.base_url}/v1/voices")
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            print(f"Error listing voices via MCP: {e}")
            return {"error": str(e)}
    
    def list_models(self) -> Dict[str, Any]:
        """List available ElevenLabs models"""
        try:
            response = requests.get(f"{self.base_url}/v1/models")
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            print(f"Error listing models via MCP: {e}")
            return {"error": str(e)}
            
    def play_audio(self, audio_content: bytes) -> None:
        """Play audio content"""
        try:
            audio = AudioSegment.from_file(io.BytesIO(audio_content), format="mp3")
            from pydub.playback import play
            play(audio)
            return True
        except Exception as e:
            print(f"Error playing audio: {e}")
            return False