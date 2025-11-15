"""Tavily web search integration helpers."""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Any

from tavily import TavilyClient


class TavilyNotConfiguredError(RuntimeError):
    """Raised when the Tavily API key is missing."""


def _get_api_key() -> str:
    api_key = os.getenv("TAVILY_API_KEY", "").strip()
    if not api_key:
        raise TavilyNotConfiguredError(
            "TAVILY_API_KEY environment variable is required for web search."
        )
    return api_key


@lru_cache(maxsize=1)
def _get_client() -> TavilyClient:
    """Create or return a cached Tavily client instance."""
    return TavilyClient(api_key=_get_api_key())


def is_web_search_configured() -> bool:
    """Return True if Tavily search can be used."""
    return bool(os.getenv("TAVILY_API_KEY"))


def run_web_search(query: str, max_results: int = 5) -> list[dict[str, Any]]:
    """
    Run a Tavily web search and return structured results.

    Returns a list of dictionaries containing title, url, and content snippet.
    """
    client = _get_client()
    response = client.search(query=query, max_results=max_results)
    return response.get("results", [])

