"""LLM and embeddings configuration."""

import os

from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI

# Currently only OpenAI is supported
DEFAULT_GAI_MODEL = os.getenv("DEFAULT_GAI_MODEL", "gpt-4o-mini")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is required")

llm = OpenAI(
    model=DEFAULT_GAI_MODEL,
    temperature=0,
    api_key=OPENAI_API_KEY,
)
embeddings = OpenAIEmbedding(api_key=OPENAI_API_KEY)

text_splitter = SentenceSplitter(chunk_size=1000, chunk_overlap=100)
