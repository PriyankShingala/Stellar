"""
Offline Text-to-Speech (TTS) Voice Engine for Audio Warnings.
Uses pyttsx3 or local offline audio synthesizers.
"""

import logging

logger = logging.getLogger("TTSEngine")

class OfflineTTSEngine:
    """Handles local text-to-speech audio synthesis without cloud connectivity."""
    def __init__(self, speech_rate: int = 150):
        self.speech_rate = speech_rate
        logger.info("Offline TTS Engine initialized.")

    def speak(self, text: str):
        """Synthesize and speak alert prompt locally."""
        logger.info(f"[AUDIO ALERT]: '{text}'")
        try:
            import pyttsx3
            engine = pyttsx3.init()
            engine.setProperty('rate', self.speech_rate)
            engine.say(text)
            engine.runAndWait()
        except Exception as e:
            logger.warning(f"Fallback voice alert log: '{text}' (Error: {e})")
