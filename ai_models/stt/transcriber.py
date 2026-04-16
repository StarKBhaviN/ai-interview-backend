from faster_whisper import WhisperModel
import tempfile
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class STTTranscriber:
    """
    Speech-to-Text inference engine using Faster Whisper.
    Centralized in ai_models/stt for modularity.
    """
    def __init__(self, model_size="tiny", device="cpu", compute_type="int8"):
        logger.info(f"Initializing WhisperModel ({model_size}) on {device}...")
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)

    def transcribe(self, file_bytes: bytes) -> str:
        if not file_bytes:
            logger.warning("Empty audio bytes received")
            return ""

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name

        try:
            # beam_size=5 for accuracy, vad_filter=True to ignore silence/noise
            segments, info = self.model.transcribe(tmp_path, beam_size=5, vad_filter=True)

            transcript = ""
            for segment in segments:
                transcript += segment.text + " "
            
            final_transcript = transcript.strip()
            logger.info(f"STT Complete. Detected: {info.language} ({info.language_probability:.2f})")
            
            return final_transcript

        except Exception as e:
            logger.error(f"STT Error: {str(e)}")
            return ""

        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

# Global singleton
_transcriber = None

def get_stt_transcriber():
    global _transcriber
    if _transcriber is None:
        _transcriber = STTTranscriber()
    return _transcriber
