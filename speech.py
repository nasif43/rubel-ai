"""
Speech recognition module for Rubel AI Chat Application.

This module handles all speech-to-text functionality including:
- Microphone audio capture
- Speech recognition using online and offline services
- Audio processing and optimization
"""

import speech_recognition as sr

def recognize_speech() -> str | None:
    """
    Capture and transcribe speech from the microphone.

    This function handles the complete speech recognition pipeline:
    1. Adjusts for ambient noise
    2. Listens for audio input
    3. Attempts recognition using multiple services
    4. Returns transcribed text or None if recognition fails

    Returns:
        str | None: The transcribed text, or None if recognition failed

    Note:
        This function will block until speech is detected and processed.
        It tries Google's online service first, then falls back to offline
        recognition if available.
    """
    recognizer = sr.Recognizer()

    with sr.Microphone() as source:
        print("Adjusting for ambient noise... Please wait.")
        recognizer.adjust_for_ambient_noise(source, duration=1)

        # Optimize recognition parameters for better accuracy
        recognizer.pause_threshold = 1.5  # Seconds of silence to consider end of phrase
        recognizer.energy_threshold = 4000  # Minimum audio energy to consider speech

        print("Listening... Speak now.")
        try:
            # Listen with timeout and phrase time limit
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=15)
            print("Processing speech...")

            # Try Google's online speech recognition service first
            try:
                text = recognizer.recognize_google(audio)
                print(f"You said: {text}")
                return text
            except sr.RequestError:
                print("Google speech service unavailable, trying offline recognition...")
                # Fall back to offline recognition using CMU Sphinx
                try:
                    text = recognizer.recognize_sphinx(audio)
                    print(f"You said (offline recognition): {text}")
                    return text
                except Exception as offline_error:
                    print(f"Offline recognition also failed: {offline_error}")
                    return None
            except sr.UnknownValueError:
                print("Sorry, I could not understand what you said.")
                return None
        except Exception as e:
            print(f"Error capturing audio: {e}")
            return None