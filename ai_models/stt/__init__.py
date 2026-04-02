# backend/ai_models/stt/__init__.py
from .transcriber import get_stt_transcriber, STTTranscriber

__all__ = ["get_stt_transcriber", "STTTranscriber"]
