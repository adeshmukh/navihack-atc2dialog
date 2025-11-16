import os
from dotenv import load_dotenv
from openai import OpenAI
import argparse
import sys

# project root (one level up from scripts/)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# load .env from project root
load_dotenv(dotenv_path=os.path.join(PROJECT_ROOT, ".env"))

# default fallback path (resolved against project root)
DEFAULT_PATH = os.path.normpath(
    os.path.join(PROJECT_ROOT, "audio_files", "ATC_recordings", "closeKBOS-Twr-Oct-30-2025-2000Z.mp3")
)

# helper to resolve user/relative paths to absolute paths under project root
def resolve_audio_path(p: str) -> str:
    if not p:
        return p
    p = os.path.expanduser(p)
    if not os.path.isabs(p):
        p = os.path.join(PROJECT_ROOT, p)
    return os.path.normpath(p)

# parse CLI arg (positional path)
parser = argparse.ArgumentParser(description="Transcribe an audio file using OpenAI")
parser.add_argument("path", nargs="?", help="path to audio file (overrides AUDIO_PATH/.env)")
args = parser.parse_args()

# choose path: CLI -> .env AUDIO_PATH -> default, then resolve to absolute path
raw_path = args.path or os.getenv("AUDIO_PATH", DEFAULT_PATH)
path = resolve_audio_path(raw_path)

if not os.path.isfile(path):
    print(f"Error: audio file not found at: {path}", file=sys.stderr)
    sys.exit(1)
# ...existing code...


client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

with open(path, "rb") as f:
    transcript = client.audio.transcriptions.create(
        model="gpt-4o-transcribe",
        file=f
    )

print(transcript.text)
