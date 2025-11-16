"""ATC conversation parsing using LLM to identify roles and message boundaries."""

import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from .llm import llm

logger = logging.getLogger(__name__)

# Get parsed conversation cache directory (reuse transcript cache directory)
_transcript_cache_dir_str = os.getenv("TRANSCRIPT_CACHE_DIR", "./.local/cache/transcripts/")
PARSED_CACHE_DIR = Path(_transcript_cache_dir_str).resolve()
PARSED_CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Few-shot examples for ATC conversation parsing
FEW_SHOT_EXAMPLES = """
Example 1:
Transcript: "San Diego Tower, United 123, ready for departure runway 27. United 123, cleared for takeoff runway 27, wind 270 at 10. United 123, rolling. United 123, contact departure on 124.5. United 123, switching to departure."

Output:
[
  {"role": "pilot", "message": "San Diego Tower, United 123, ready for departure runway 27.", "annotations": [{"text": "United 123", "type": "who"}, {"text": "ready for departure", "type": "what"}]},
  {"role": "atc", "message": "United 123, cleared for takeoff runway 27, wind 270 at 10.", "annotations": [{"text": "United 123", "type": "who"}, {"text": "cleared for takeoff", "type": "what"}]},
  {"role": "pilot", "message": "United 123, rolling.", "annotations": [{"text": "United 123", "type": "who"}, {"text": "rolling", "type": "what"}]},
  {"role": "atc", "message": "United 123, contact departure on 124.5.", "annotations": [{"text": "United 123", "type": "who"}, {"text": "contact departure", "type": "what"}]},
  {"role": "pilot", "message": "United 123, switching to departure.", "annotations": [{"text": "United 123", "type": "who"}, {"text": "switching", "type": "what"}]}
]

Example 2:
Transcript: "Ground, American 456, request taxi to runway 18. American 456, taxi via Alpha, Bravo, hold short of runway 18. American 456, taxiing via Alpha, Bravo, hold short runway 18. American 456, runway 18, cleared for takeoff. American 456, cleared for takeoff runway 18."

Output:
[
  {"role": "pilot", "message": "Ground, American 456, request taxi to runway 18.", "annotations": [{"text": "American 456", "type": "who"}, {"text": "request taxi", "type": "what"}]},
  {"role": "atc", "message": "American 456, taxi via Alpha, Bravo, hold short of runway 18.", "annotations": [{"text": "American 456", "type": "who"}, {"text": "taxi", "type": "what"}]},
  {"role": "pilot", "message": "American 456, taxiing via Alpha, Bravo, hold short runway 18.", "annotations": [{"text": "American 456", "type": "who"}, {"text": "taxiing", "type": "what"}]},
  {"role": "atc", "message": "American 456, runway 18, cleared for takeoff.", "annotations": [{"text": "American 456", "type": "who"}, {"text": "cleared for takeoff", "type": "what"}]},
  {"role": "pilot", "message": "American 456, cleared for takeoff runway 18.", "annotations": [{"text": "American 456", "type": "who"}, {"text": "cleared for takeoff", "type": "what"}]}
]

Example 3:
Transcript: "Tower, Delta 789, ready for departure. Delta 789, line up and wait runway 27. Delta 789, lining up runway 27. Tower, Southwest 321, ready for departure runway 27. Southwest 321, hold position. Delta 789, cleared for takeoff runway 27. Delta 789, taking off."

Output:
[
  {"role": "pilot", "message": "Tower, Delta 789, ready for departure.", "annotations": [{"text": "Delta 789", "type": "who"}, {"text": "ready for departure", "type": "what"}]},
  {"role": "atc", "message": "Delta 789, line up and wait runway 27.", "annotations": [{"text": "Delta 789", "type": "who"}, {"text": "line up and wait", "type": "what"}]},
  {"role": "pilot", "message": "Delta 789, lining up runway 27.", "annotations": [{"text": "Delta 789", "type": "who"}, {"text": "lining up", "type": "what"}]},
  {"role": "pilot", "message": "Tower, Southwest 321, ready for departure runway 27.", "annotations": [{"text": "Southwest 321", "type": "who"}, {"text": "ready for departure", "type": "what"}]},
  {"role": "atc", "message": "Southwest 321, hold position.", "annotations": [{"text": "Southwest 321", "type": "who"}, {"text": "hold position", "type": "what"}]},
  {"role": "atc", "message": "Delta 789, cleared for takeoff runway 27.", "annotations": [{"text": "Delta 789", "type": "who"}, {"text": "cleared for takeoff", "type": "what"}]},
  {"role": "pilot", "message": "Delta 789, taking off.", "annotations": [{"text": "Delta 789", "type": "who"}, {"text": "taking off", "type": "what"}]}
]
"""

PROMPT_TEMPLATE_NO_USER = """You are an expert at parsing Air Traffic Control (ATC) radio communications transcripts. Your task is to identify the speaker role (ATC or pilot), break the transcript into individual messages, and annotate each message with "who" and "what" components using MINIMAL text spans.

Guidelines:
- ATC messages typically contain clearances, instructions, frequencies, and control commands
- Pilot messages typically contain readbacks, acknowledgments, requests, and position reports
- When multiple pilots are present, they are identified by their callsigns (e.g., "United 123", "Delta 789")
- Break messages at natural conversation boundaries
- Each message should be a complete thought or exchange

Annotation Guidelines:
- "who": Callsign/aircraft ID ONLY - use the minimal text span (e.g., "United 123", "Delta 789", "American 456")
- "what": Action/instruction/clearance ONLY - use the MINIMAL text span that captures the core action (e.g., "cleared for takeoff", "taxi", "ready for departure", "rolling", "switching")
- DO NOT annotate "why" - skip this entirely
- Use MINIMAL text spans - highlight only the essential words, not entire phrases
- For "what", focus on the core verb/action (e.g., "taxi" not "taxi via Alpha, Bravo, hold short of runway 18")
- Only annotate parts of the message that clearly answer who/what - do not force annotations
- Each annotation should be an exact text span from the message
- A message may have zero or more annotations of each type
- Output ONLY valid JSON array format, no additional text

Few-shot examples:
{FEW_SHOT_EXAMPLES}

Now parse this transcript:

Transcript: {transcript}

Output JSON array:"""

PROMPT_TEMPLATE_WITH_USER = """You are an expert at parsing Air Traffic Control (ATC) radio communications transcripts. Your task is to identify the speaker role (ATC or pilot), break the transcript into individual messages, and annotate each message with "who" and "what" components using MINIMAL text spans.

Guidelines:
- ATC messages typically contain clearances, instructions, frequencies, and control commands
- Pilot messages typically contain readbacks, acknowledgments, requests, and position reports
- When multiple pilots are present, they are identified by their callsigns (e.g., "United 123", "Delta 789")
- Break messages at natural conversation boundaries
- Each message should be a complete thought or exchange

User Context:
- The user identifies as: {user_callsign}
- For ATC messages, if the message is directed at {user_callsign} (i.e., the message contains or references this specific callsign), set "highlight_for_user": true
- For all other messages, set "highlight_for_user": false
- Compare callsigns carefully - "{user_callsign}" should match variations like "{user_callsign}" (exact match)

Annotation Guidelines:
- "who": Callsign/aircraft ID ONLY - use the minimal text span (e.g., "United 123", "Delta 789", "American 456")
- "what": Action/instruction/clearance ONLY - use the MINIMAL text span that captures the core action (e.g., "cleared for takeoff", "taxi", "ready for departure", "rolling", "switching")
- DO NOT annotate "why" - skip this entirely
- Use MINIMAL text spans - highlight only the essential words, not entire phrases
- For "what", focus on the core verb/action (e.g., "taxi" not "taxi via Alpha, Bravo, hold short of runway 18")
- Only annotate parts of the message that clearly answer who/what - do not force annotations
- Each annotation should be an exact text span from the message
- A message may have zero or more annotations of each type
- Include "highlight_for_user" field in each message (true/false)
- Output ONLY valid JSON array format, no additional text

Few-shot examples:
{FEW_SHOT_EXAMPLES}

Now parse this transcript:

Transcript: {transcript}

Output JSON array:"""


def _get_cached_parsed_conversation(md5_hash: str) -> List[Dict[str, str]] | None:
    """
    Retrieve cached parsed conversation for a given MD5 hash.
    
    Args:
        md5_hash: MD5 hash of the audio file
        
    Returns:
        Cached parsed conversation list if found, None otherwise
    """
    cache_file = PARSED_CACHE_DIR / f"{md5_hash}_parsed.json"
    if cache_file.exists():
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                cache_data = json.load(f)
                return cache_data.get("parsed_conversation")
        except Exception as e:
            logger.warning(f"Failed to read parsed cache file {cache_file}: {e}")
            return None
    return None


def _save_parsed_conversation_to_cache(md5_hash: str, parsed_conversation: List[Dict[str, str]]) -> None:
    """
    Save parsed conversation to cache.
    
    Args:
        md5_hash: MD5 hash of the audio file
        parsed_conversation: Parsed conversation list
    """
    cache_file = PARSED_CACHE_DIR / f"{md5_hash}_parsed.json"
    try:
        cache_data = {
            "parsed_conversation": parsed_conversation,
            "cached_at": datetime.now().isoformat(),
        }
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, indent=2)
        logger.info(f"Parsed conversation cached (MD5: {md5_hash})")
    except Exception as e:
        logger.warning(f"Failed to save parsed conversation to cache: {e}")


def parse_atc_conversation(transcript: str, md5_hash: str | None = None, user_callsign: str | None = None) -> List[Dict[str, str]]:
    """
    Parse an ATC transcript into structured conversation format with role identification and annotations.

    Args:
        transcript: Raw transcript text from audio transcription
        md5_hash: Optional MD5 hash of the audio file for caching
        user_callsign: Optional user's callsign to highlight ATC messages directed at them

    Returns:
        List of dictionaries with 'role', 'message', 'annotations', and optional 'highlight_for_user' keys:
        [{"role": "atc"|"pilot", "message": "...", "annotations": [{"text": "...", "type": "who|what"}, ...], "highlight_for_user": true|false}, ...]
        Note: Only "who" and "what" annotations are processed (not "why").

    Raises:
        ValueError: If parsing fails or returns invalid format
    """
    if not transcript or not transcript.strip():
        logger.warning("Empty transcript provided to parser")
        return []

    # Check cache if MD5 hash is provided
    if md5_hash:
        cached_parsed = _get_cached_parsed_conversation(md5_hash)
        if cached_parsed is not None:
            logger.info(f"Using cached parsed conversation (MD5: {md5_hash})")
            # Add a 3-second pause to simulate processing time when using cache
            time.sleep(3)
            return cached_parsed

    logger.info(f"Parsing ATC conversation from transcript ({len(transcript)} chars)")

    try:
        # Build the prompt based on whether user_callsign is provided
        if user_callsign:
            logger.info(f"Parsing with user callsign: {user_callsign}")
            prompt = PROMPT_TEMPLATE_WITH_USER.format(
                FEW_SHOT_EXAMPLES=FEW_SHOT_EXAMPLES,
                transcript=transcript.strip(),
                user_callsign=user_callsign
            )
        else:
            prompt = PROMPT_TEMPLATE_NO_USER.format(
                FEW_SHOT_EXAMPLES=FEW_SHOT_EXAMPLES,
                transcript=transcript.strip()
            )

        # Call LLM with temperature=0 for consistent parsing
        logger.debug("Calling LLM for ATC conversation parsing")
        response = llm.complete(prompt)
        
        # Extract text from response (llama_index CompletionResponse has .text attribute)
        if hasattr(response, 'text'):
            response_text = response.text.strip()
        else:
            response_text = str(response).strip()
        
        # Try to extract JSON if wrapped in code blocks
        if "```json" in response_text:
            start = response_text.find("```json") + 7
            end = response_text.find("```", start)
            response_text = response_text[start:end].strip()
        elif "```" in response_text:
            start = response_text.find("```") + 3
            end = response_text.find("```", start)
            response_text = response_text[start:end].strip()

        # Parse JSON
        try:
            parsed_conversation = json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed: {e}")
            logger.error(f"Response text: {response_text[:500]}")
            raise ValueError(f"Failed to parse LLM response as JSON: {e}")

        # Validate structure
        if not isinstance(parsed_conversation, list):
            raise ValueError("LLM response is not a list")

        # Validate each item has required keys
        for idx, item in enumerate(parsed_conversation):
            if not isinstance(item, dict):
                raise ValueError(f"Item {idx} is not a dictionary")
            if "role" not in item or "message" not in item:
                raise ValueError(f"Item {idx} missing 'role' or 'message' key")
            if item["role"] not in ["atc", "pilot"]:
                logger.warning(f"Unexpected role '{item['role']}' in item {idx}, normalizing")
                # Normalize role to valid values
                item["role"] = "atc" if item["role"].lower() in ["atc", "controller", "tower", "ground"] else "pilot"
            
            # Validate annotations if present (optional field for backward compatibility)
            if "annotations" in item:
                if not isinstance(item["annotations"], list):
                    logger.warning(f"Item {idx} has invalid annotations format, removing annotations")
                    item["annotations"] = []
                else:
                    # Validate each annotation
                    valid_annotations = []
                    for ann_idx, ann in enumerate(item["annotations"]):
                        if isinstance(ann, dict) and "text" in ann and "type" in ann:
                            if ann["type"] in ["who", "what"]:
                                valid_annotations.append(ann)
                            elif ann["type"] == "why":
                                # Skip "why" annotations - we no longer process them
                                logger.debug(f"Item {idx}, annotation {ann_idx} has type 'why', skipping")
                            else:
                                logger.warning(f"Item {idx}, annotation {ann_idx} has invalid type '{ann['type']}', skipping")
                        else:
                            logger.warning(f"Item {idx}, annotation {ann_idx} missing 'text' or 'type' field, skipping")
                    item["annotations"] = valid_annotations
            else:
                # Add empty annotations list for backward compatibility
                item["annotations"] = []

        logger.info(f"Successfully parsed {len(parsed_conversation)} conversation messages")
        
        # Save to cache if MD5 hash is provided
        if md5_hash:
            _save_parsed_conversation_to_cache(md5_hash, parsed_conversation)
        
        return parsed_conversation

    except Exception as e:
        logger.error(f"Failed to parse ATC conversation: {e}", exc_info=True)
        raise ValueError(f"ATC conversation parsing failed: {str(e)}")

