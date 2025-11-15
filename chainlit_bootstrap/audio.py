"""Audio transcription functionality using OpenAI Whisper API."""

import logging
import os
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict

from openai import OpenAI

logger = logging.getLogger(__name__)

# Get OpenAI API key from environment
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is required")

# Initialize OpenAI client
_openai_client = OpenAI(api_key=OPENAI_API_KEY)

# Get audio persist directory from environment
# Resolve relative paths to absolute paths
_audio_persist_dir_str = os.getenv("AUDIO_PERSIST_DIR", ".local/data/audio/")
AUDIO_PERSIST_DIR = Path(_audio_persist_dir_str).resolve()
AUDIO_PERSIST_DIR.mkdir(parents=True, exist_ok=True)


def is_audio_file(mime: str, filename: str) -> bool:
    """
    Check if a file is a supported audio format.

    Args:
        mime: MIME type of the file
        filename: Name of the file

    Returns:
        True if the file is a supported audio format (.mp3, .wav, .m4a)
    """
    supported_mimes = {
        "audio/mpeg",
        "audio/mp3",
        "audio/wav",
        "audio/wave",
        "audio/x-m4a",
        "audio/mp4",
        "audio/x-m4a",
    }

    supported_extensions = {".mp3", ".wav", ".m4a"}

    # Check MIME type
    if mime and mime.lower() in supported_mimes:
        return True

    # Check file extension as fallback
    if filename:
        ext = Path(filename).suffix.lower()
        if ext in supported_extensions:
            return True

    return False


def transcribe_audio(file_path: str, original_filename: str) -> Dict[str, str]:
    """
    Transcribe an audio file using OpenAI Whisper API and save it to persistent storage.

    Args:
        file_path: Path to the temporary uploaded audio file
        original_filename: Original name of the uploaded file

    Returns:
        Dictionary containing:
        - transcription: Transcribed text
        - audio_path: Path to the stored audio file
        - format: Audio format (from filename extension)
        - original_filename: Original filename

    Raises:
        Exception: If transcription fails or file operations fail
    """
    try:
        # Generate unique filename for storage
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        file_ext = Path(original_filename).suffix
        stored_filename = f"{timestamp}_{unique_id}_{original_filename}"
        stored_path = AUDIO_PERSIST_DIR / stored_filename

        # Copy audio file to persistent storage
        shutil.copy2(file_path, stored_path)
        logger.info(f"Audio file saved to {stored_path}")

        # Transcribe using OpenAI Whisper API
        with open(stored_path, "rb") as audio_file:
            transcript_response = _openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
            )

        transcription_text = transcript_response.text

        logger.info(
            f"Transcription completed for {original_filename}: "
            f"{len(transcription_text)} characters"
        )

        return {
            "transcription": transcription_text,
            "audio_path": str(stored_path),
            "format": file_ext.lstrip(".").lower() if file_ext else "unknown",
            "original_filename": original_filename,
        }

    except Exception as e:
        logger.error(f"Failed to transcribe audio file {original_filename}: {e}")
        # Clean up stored file if transcription failed
        if stored_path.exists():
            try:
                stored_path.unlink()
            except Exception:
                pass
        raise

