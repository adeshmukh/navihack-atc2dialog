"""Audio transcription functionality using OpenAI Whisper API."""

import hashlib
import json
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

# Get transcript cache directory
_transcript_cache_dir_str = os.getenv("TRANSCRIPT_CACHE_DIR", "./.local/cache/transcripts/")
TRANSCRIPT_CACHE_DIR = Path(_transcript_cache_dir_str).resolve()
TRANSCRIPT_CACHE_DIR.mkdir(parents=True, exist_ok=True)


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


def _compute_file_md5(file_path: str) -> str:
    """
    Compute MD5 hash of a file's content.
    
    Args:
        file_path: Path to the file
        
    Returns:
        MD5 hash as hexadecimal string
    """
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def _get_cached_transcript(md5_hash: str) -> str | None:
    """
    Retrieve cached transcript for a given MD5 hash.
    
    Args:
        md5_hash: MD5 hash of the audio file
        
    Returns:
        Cached transcript text if found, None otherwise
    """
    cache_file = TRANSCRIPT_CACHE_DIR / f"{md5_hash}.json"
    if cache_file.exists():
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                cache_data = json.load(f)
                return cache_data.get("transcription")
        except Exception as e:
            logger.warning(f"Failed to read cache file {cache_file}: {e}")
            return None
    return None


def _save_transcript_to_cache(md5_hash: str, transcription: str, original_filename: str) -> None:
    """
    Save transcript to cache.
    
    Args:
        md5_hash: MD5 hash of the audio file
        transcription: Transcribed text
        original_filename: Original filename for reference
    """
    cache_file = TRANSCRIPT_CACHE_DIR / f"{md5_hash}.json"
    try:
        cache_data = {
            "transcription": transcription,
            "original_filename": original_filename,
            "cached_at": datetime.now().isoformat(),
        }
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, indent=2)
        logger.info(f"Transcript cached for {original_filename} (MD5: {md5_hash})")
    except Exception as e:
        logger.warning(f"Failed to save transcript to cache: {e}")


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
    stored_path = None
    try:
        # Compute MD5 hash of the audio file for caching
        md5_hash = _compute_file_md5(file_path)
        logger.info(f"Computed MD5 hash for {original_filename}: {md5_hash}")
        
        # Check cache first
        cached_transcription = _get_cached_transcript(md5_hash)
        if cached_transcription is not None:
            logger.info(f"Using cached transcript for {original_filename} (MD5: {md5_hash})")
            transcription_text = cached_transcription
        else:
            # Transcribe using OpenAI Whisper API
            logger.info(f"Transcribing {original_filename} with OpenAI API (MD5: {md5_hash})")
            with open(file_path, "rb") as audio_file:
                transcript_response = _openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                )
            transcription_text = transcript_response.text
            
            # Save to cache
            _save_transcript_to_cache(md5_hash, transcription_text, original_filename)
        
        # Generate unique filename for storage
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        file_ext = Path(original_filename).suffix
        stored_filename = f"{timestamp}_{unique_id}_{original_filename}"
        stored_path = AUDIO_PERSIST_DIR / stored_filename

        # Copy audio file to persistent storage
        shutil.copy2(file_path, stored_path)
        logger.info(f"Audio file saved to {stored_path}")

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
        # Clean up stored file if transcription failed and file was created
        if stored_path is not None and stored_path.exists():
            try:
                stored_path.unlink()
            except Exception:
                pass
        raise

