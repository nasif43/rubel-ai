"""
Main entry point for Rubel AI Chat Application.

This module serves as the main entry point that initializes and runs
the Rubel AI chat server with WebSocket support, speech recognition,
and text-to-speech capabilities.
"""

import asyncio
from config import create_output_directory, validate_environment
from server import run_server

async def main():
    """
    Main asynchronous entry point for the application.

    This function performs initial setup and starts the server:
    1. Creates necessary output directories
    2. Validates environment configuration
    3. Starts the web server with WebSocket support
    """
    # Create output directory for audio files
    create_output_directory()

    # Validate environment and API keys
    errors = validate_environment()
    if errors:
        for error in errors:
            print(f"Error: {error}")
        return

    # Run the server
    await run_server()

if __name__ == "__main__":
    asyncio.run(main())