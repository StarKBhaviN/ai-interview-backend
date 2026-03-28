from faster_whisper import WhisperModel
import tempfile
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load model (Singleton-like behavior at module level)
# "base" is a good balance of speed and accuracy. 
# For lower resource usage, "tiny" can be used. For better accuracy, "small" or "medium".
model = WhisperModel("base", device="cpu", compute_type="int8")

def transcribe_audio(file_bytes):
    if not file_bytes:
        logger.warning("Empty audio bytes received")
        return ""

    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    try:
        logger.info(f"Starting transcription for {tmp_path}")
        # beam_size=5 is standard for better quality. 
        # vad_filter=True helps remove silence and non-speech noise.
        segments, info = model.transcribe(tmp_path, beam_size=5, vad_filter=True)

        transcript = ""
        for segment in segments:
            transcript += segment.text + " "
        
        final_transcript = transcript.strip()
        logger.info(f"Transcription complete. Detected language: {info.language} with probability {info.language_probability:.2f}")
        
        return final_transcript

    except Exception as e:
        logger.error(f"Error during transcription: {str(e)}")
        return ""

    finally:
        try:
            os.remove(tmp_path)
        except Exception as e:
            logger.error(f"Failed to remove temp file {tmp_path}: {e}")