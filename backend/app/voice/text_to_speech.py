def synthesize_speech(text: str, language: str = "ar") -> dict:
    """
    Synthesizes speech audio configuration / metadata.
    Provides web browser SpeechSynthesis payload / parameters.
    """
    return {
        "text": text,
        "language": language,
        "pitch": 1.0,
        "rate": 0.95
    }
