"""ATC conversation parsing using LLM to identify roles and message boundaries."""

import json
import logging
from typing import Dict, List

from .llm import llm

logger = logging.getLogger(__name__)

# Few-shot examples for ATC conversation parsing
FEW_SHOT_EXAMPLES = """
Example 1:
Transcript: "San Diego Tower, United 123, ready for departure runway 27. United 123, cleared for takeoff runway 27, wind 270 at 10. United 123, rolling. United 123, contact departure on 124.5. United 123, switching to departure."

Output:
[
  {"role": "pilot", "message": "San Diego Tower, United 123, ready for departure runway 27."},
  {"role": "atc", "message": "United 123, cleared for takeoff runway 27, wind 270 at 10."},
  {"role": "pilot", "message": "United 123, rolling."},
  {"role": "atc", "message": "United 123, contact departure on 124.5."},
  {"role": "pilot", "message": "United 123, switching to departure."}
]

Example 2:
Transcript: "Ground, American 456, request taxi to runway 18. American 456, taxi via Alpha, Bravo, hold short of runway 18. American 456, taxiing via Alpha, Bravo, hold short runway 18. American 456, runway 18, cleared for takeoff. American 456, cleared for takeoff runway 18."

Output:
[
  {"role": "pilot", "message": "Ground, American 456, request taxi to runway 18."},
  {"role": "atc", "message": "American 456, taxi via Alpha, Bravo, hold short of runway 18."},
  {"role": "pilot", "message": "American 456, taxiing via Alpha, Bravo, hold short runway 18."},
  {"role": "atc", "message": "American 456, runway 18, cleared for takeoff."},
  {"role": "pilot", "message": "American 456, cleared for takeoff runway 18."}
]

Example 3:
Transcript: "Tower, Delta 789, ready for departure. Delta 789, line up and wait runway 27. Delta 789, lining up runway 27. Tower, Southwest 321, ready for departure runway 27. Southwest 321, hold position. Delta 789, cleared for takeoff runway 27. Delta 789, taking off."

Output:
[
  {"role": "pilot", "message": "Tower, Delta 789, ready for departure."},
  {"role": "atc", "message": "Delta 789, line up and wait runway 27."},
  {"role": "pilot", "message": "Delta 789, lining up runway 27."},
  {"role": "pilot", "message": "Tower, Southwest 321, ready for departure runway 27."},
  {"role": "atc", "message": "Southwest 321, hold position."},
  {"role": "atc", "message": "Delta 789, cleared for takeoff runway 27."},
  {"role": "pilot", "message": "Delta 789, taking off."}
]
"""

PROMPT_TEMPLATE = """You are an expert at parsing Air Traffic Control (ATC) radio communications transcripts. Your task is to identify the speaker role (ATC or pilot) and break the transcript into individual messages.

Guidelines:
- ATC messages typically contain clearances, instructions, frequencies, and control commands
- Pilot messages typically contain readbacks, acknowledgments, requests, and position reports
- When multiple pilots are present, they are identified by their callsigns (e.g., "United 123", "Delta 789")
- Break messages at natural conversation boundaries
- Each message should be a complete thought or exchange
- Output ONLY valid JSON array format, no additional text

Few-shot examples:
{FEW_SHOT_EXAMPLES}

Now parse this transcript:

Transcript: {transcript}

Output JSON array:"""


def parse_atc_conversation(transcript: str) -> List[Dict[str, str]]:
    """
    Parse an ATC transcript into structured conversation format with role identification.

    Args:
        transcript: Raw transcript text from audio transcription

    Returns:
        List of dictionaries with 'role' and 'message' keys:
        [{"role": "atc"|"pilot", "message": "..."}, ...]

    Raises:
        ValueError: If parsing fails or returns invalid format
    """
    if not transcript or not transcript.strip():
        logger.warning("Empty transcript provided to parser")
        return []

    logger.info(f"Parsing ATC conversation from transcript ({len(transcript)} chars)")

    try:
        # Build the prompt
        prompt = PROMPT_TEMPLATE.format(
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

        logger.info(f"Successfully parsed {len(parsed_conversation)} conversation messages")
        return parsed_conversation

    except Exception as e:
        logger.error(f"Failed to parse ATC conversation: {e}", exc_info=True)
        raise ValueError(f"ATC conversation parsing failed: {str(e)}")

