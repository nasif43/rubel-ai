"""
Configuration module for Rubel AI Chat Application.

This module handles all configuration-related tasks including:
- Loading environment variables
- Setting up API clients
- Defining constants used throughout the application
- Managing output directories
"""

import os
from groq import Groq
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Constants
OUTPUT_DIR = "conversation_data"
VALID_ROLES = ["mim", "joker", "spec_actor","russel","baba","ammu"]

# API Keys (loaded from environment)
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

# Voice settings for ElevenLabs
VOICE_ID = "JBFqnCBsd6RMkjVDRZzb"
MODEL_ID = "eleven_flash_v2_5"
VOICE_SETTINGS = {"stability": 0.5, "similarity_boost": 0.75}

# Server configuration
HOST = '0.0.0.0'  # Bind to all network interfaces for LAN access
PORT = 8765

# Initialize API clients
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

def create_output_directory():
    """Create the output directory if it doesn't exist."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

def validate_environment():
    """Validate that required environment variables are set."""
    errors = []
    if not GROQ_API_KEY:
        errors.append("GROQ_API_KEY environment variable not set.")
    if not ELEVENLABS_API_KEY:
        errors.append("ELEVENLABS_API_KEY not set. Voice output will be disabled.")
    return errors