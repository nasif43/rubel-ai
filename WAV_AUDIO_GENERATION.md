# Generate WAV Audio for Rubel's Dialogue

This script generates high-quality WAV audio files for Rubel's dialogue lines using ElevenLabs TTS, with word-level timestamps for lip-sync and animation.

## Features

- **WAV Format**: Generates WAV files instead of MP3 for higher quality
- **Word Timestamps**: Includes precise word-level timing data for lip-sync
- **Scene Organization**: Organizes audio files by scene and line number
- **Fallback Support**: Uses MCP server when available, falls back to direct API
- **Progress Tracking**: Shows detailed progress and timestamp information

## Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Environment Variables**:
   Make sure your `.env` file contains:
   ```
   ELEVENLABS_API_KEY=your_elevenlabs_api_key
   ```

## Usage

### Method 1: Using the provided JSON file

The script comes with `rubel_dialogue.json` containing all Rubel's lines organized by scenes.

```bash
# Run the WAV generation script
python generate_rubel_wav_from_json.py --json rubel_dialogue.json
```

Or use the convenience script:
```bash
bash generate_rubel_wav.sh
```

### Method 2: Using your own JSON file

Create a JSON file with this structure:
```json
[
  {
    "scene": "1",
    "lines": [
      "Your dialogue line here.",
      "Another line in the same scene."
    ]
  },
  {
    "scene": "2",
    "lines": [
      "Lines for scene 2."
    ]
  }
]
```

Then run:
```bash
python generate_rubel_wav_from_json.py --json your_dialogue.json
```

## Output

The script creates:

1. **WAV Audio Files**: `rubel_wav_audio/scene_X_line_Y_timestamp.wav`
2. **Metadata JSON**: `rubel_wav_audio/rubel_dialogue_wav_data_timestamp.json`

### Example Output Structure:
```
rubel_wav_audio/
├── scene_1_line_1_1734567890.wav
├── scene_2_line_1_1734567891.wav
├── scene_2_line_2_1734567892.wav
├── ...
└── rubel_dialogue_wav_data_1734567890.json
```

### Metadata JSON Structure:
```json
[
  {
    "scene": "1",
    "lines": [
      {
        "line_index": 1,
        "text": "HELLO MIM, I AM RUBEL AND I HAVE BEEN WAITING FOR YOU.",
        "wav_file": "rubel_wav_audio/scene_1_line_1_1734567890.wav",
        "timestamps": {
          "words": [
            {"word": "HELLO", "start": 0.0, "end": 0.5},
            {"word": "MIM", "start": 0.6, "end": 0.8},
            ...
          ]
        }
      }
    ]
  }
]
```

## Voice Configuration

The script uses these default voice settings (can be modified in the script):
- **Voice ID**: `JBFqnCBsd6RMkjVDRZzb` (Rubel's voice)
- **Model**: `eleven_flash_v2_5`
- **Stability**: 0.5
- **Similarity Boost**: 0.75

## MCP Server

The script automatically:
1. Checks if the ElevenLabs MCP server is running
2. Starts it if needed
3. Falls back to direct API calls if MCP fails

To run the MCP server manually:
```bash
uvicorn elevenlabs_mcp:app --reload --host 0.0.0.0 --port 8080
```

## Troubleshooting

### Common Issues:

1. **MCP Server Won't Start**:
   - Check if port 8080 is available
   - Ensure all dependencies are installed
   - The script will automatically fall back to direct API

2. **API Rate Limiting**:
   - The script includes delays between requests
   - ElevenLabs has rate limits; wait if you hit them

3. **Audio Quality Issues**:
   - WAV conversion preserves quality
   - Check your ElevenLabs API key and voice settings

## Integration with Animation/Lip-Sync

The generated timestamps can be used for:
- Lip-sync animation
- Subtitle timing
- Audio-visual synchronization
- Game development
- Video production

Each word in the timestamp data includes:
- `word`: The actual word text
- `start`: Start time in seconds
- `end`: End time in seconds