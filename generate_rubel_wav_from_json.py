"""
Generate WAV audio files for Rubel's dialogue lines from JSON data using ElevenLabs TTS.

This script takes JSON dialogue data with scenes and lines, generates WAV audio
for each Rubel line using ElevenLabs MCP, and includes word-level timestamps.

Usage:
    python generate_rubel_wav_from_json.py --json dialogue.json
"""

import os
import json
import time
import argparse
import io
from typing import List, Dict, Any
from dotenv import load_dotenv
from pydub import AudioSegment
from elevenlabs import ElevenLabs

# Load environment variables
load_dotenv()

# Set up directories
OUTPUT_DIR = "rubel_wav_audio"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Voice ID for Rubel (default voice ID)
VOICE_ID = "JBFqnCBsd6RMkjVDRZzb"

# Initialize ElevenLabs client
elevenlabs_client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))

# Voice ID for Rubel (default voice ID)
VOICE_ID = "JBFqnCBsd6RMkjVDRZzb"

def load_dialogue_json(json_file):
    """Load dialogue data from JSON file"""
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"Error loading JSON file: {e}")
        return None

def generate_wav_audio_for_dialogue(dialogue_data):
    """Generate WAV audio for each dialogue line using ElevenLabs SDK with timestamps"""
    if not dialogue_data:
        print("No dialogue data found.")
        return

    print("Using ElevenLabs SDK with timestamps")

    # Create a JSON file to store all dialogue with audio file references
    all_dialogue_data = []

    total_lines = sum(len(scene["lines"]) for scene in dialogue_data)
    line_counter = 0

    print(f"Found {len(dialogue_data)} scenes with {total_lines} total lines to process.")

    # Process each scene
    for scene in dialogue_data:
        scene_number = scene["scene"]
        lines = scene["lines"]

        print(f"\n=== Processing Scene {scene_number} ===")

        scene_data = {
            "scene": scene_number,
            "lines": []
        }

        # Generate audio for each line in the scene
        for line_index, line_text in enumerate(lines):
            line_counter += 1
            print(f"\nProcessing line {line_counter}/{total_lines} (Scene {scene_number}, Line {line_index+1}):")
            print(f"Rubel: {line_text}")

            # Generate a unique filename for this line
            timestamp = int(time.time())
            wav_filename = f"scene_{scene_number}_line_{line_index+1}_{timestamp}.wav"
            wav_path = os.path.join(OUTPUT_DIR, wav_filename)

            try:
                # Use ElevenLabs SDK with timestamps
                audio_content, timestamps = generate_audio_with_timestamps_sdk(line_text)

                if audio_content:
                    # Convert audio bytes to WAV
                    audio_segment = AudioSegment.from_file(io.BytesIO(audio_content), format="mp3")
                    audio_segment.export(wav_path, format="wav")

                    print(f"WAV audio saved to {wav_path}")

                    # Store line data
                    line_data = {
                        "line_index": line_index + 1,
                        "text": line_text,
                        "wav_file": wav_path,
                        "timestamps": timestamps
                    }

                    # Display timestamp info if available
                    if timestamps and "words" in timestamps and timestamps["words"]:
                        word_timestamps = timestamps["words"]
                        print(f"  Word-level timestamps: {len(word_timestamps)} words")
                        for i, word_data in enumerate(word_timestamps[:3]):
                            word = word_data["word"]
                            start = word_data["start"]
                            end = word_data["end"]
                            print(f"    '{word}': {start:.2f}s - {end:.2f}s")

                        if len(word_timestamps) > 3:
                            print(f"    ... and {len(word_timestamps) - 3} more words")

                    scene_data["lines"].append(line_data)

                    # Add a small delay between API calls to avoid rate limiting
                    time.sleep(0.5)
                else:
                    print("Failed to generate audio for this line.")
                    scene_data["lines"].append({
                        "line_index": line_index + 1,
                        "text": line_text,
                        "error": "Failed to generate audio"
                    })

            except Exception as e:
                print(f"Error processing line {line_index+1}: {e}")
                scene_data["lines"].append({
                    "line_index": line_index + 1,
                    "text": line_text,
                    "error": str(e)
                })

        all_dialogue_data.append(scene_data)

    # Save dialogue data to JSON
    json_path = os.path.join(OUTPUT_DIR, f"rubel_dialogue_wav_data_{int(time.time())}.json")
    with open(json_path, "w") as f:
        json.dump(all_dialogue_data, f, indent=2)

    print(f"\n=== Processing Complete ===")
    print(f"All dialogue data saved to {json_path}")
    print(f"Total scenes processed: {len(dialogue_data)}")
    print(f"Total lines processed: {total_lines}")
    print(f"WAV files saved to {OUTPUT_DIR}")

def generate_audio_with_timestamps_sdk(text):
    """Generate audio with timestamps using ElevenLabs SDK"""
    from elevenlabs.types.voice_settings import VoiceSettings
    import base64
    
    try:
        print("Using ElevenLabs SDK with timestamps...")

        # Use the SDK method for timestamps
        response = elevenlabs_client.text_to_speech.convert_with_timestamps(
            voice_id=VOICE_ID,
            text=text,
            model_id="eleven_flash_v2_5",
            voice_settings=VoiceSettings(stability=0.5, similarity_boost=0.75)
        )

        # Extract audio content from base64
        audio_content = base64.b64decode(response.audio_base_64)
        
        # Process character alignment into word timestamps
        word_timestamps = []
        if response.alignment:
            characters = response.alignment.characters
            start_times = response.alignment.character_start_times_seconds
            end_times = response.alignment.character_end_times_seconds
            
            # Group characters into words
            current_word = ""
            word_start = None
            
            for i, char in enumerate(characters):
                if char.isspace() or i == len(characters) - 1:
                    # End of word
                    if current_word:
                        if i == len(characters) - 1 and not char.isspace():
                            current_word += char
                        
                        word_end = end_times[i] if i < len(end_times) else start_times[i] + 0.1
                        word_timestamps.append({
                            "word": current_word,
                            "start": word_start,
                            "end": word_end
                        })
                        current_word = ""
                        word_start = None
                else:
                    # Continue building word
                    if word_start is None:
                        word_start = start_times[i]
                    current_word += char

        timestamps = {"words": word_timestamps}

        print(f"Successfully generated audio ({len(audio_content)} bytes) with {len(word_timestamps)} word timestamps")
        return audio_content, timestamps

    except Exception as e:
        print(f"SDK error: {e}")
        return None, None

def main():
    parser = argparse.ArgumentParser(description='Generate WAV audio for Rubel dialogue lines from JSON')
    parser.add_argument('--json', '-j', required=True, help='Path to JSON file with dialogue data')
    args = parser.parse_args()

    # Load dialogue data from JSON file
    dialogue_data = load_dialogue_json(args.json)
    if not dialogue_data:
        return

    # Generate WAV audio for dialogue
    generate_wav_audio_for_dialogue(dialogue_data)

if __name__ == "__main__":
    main()