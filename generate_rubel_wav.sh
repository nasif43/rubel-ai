#!/bin/bash

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/Scripts/activate
fi

# Generate WAV audio for Rubel's dialogue from JSON
python generate_rubel_wav_from_json.py --json rubel_dialogue.json