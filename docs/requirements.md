# Project Requirements

## Overview

This project is a Chainlit-based conversational AI application that enables users to upload documents and ask questions about them. The application includes features for document question-answering and voice input capabilities.

## Core Features

### 1. Document Question-Answering (QA)
- **Status**: ✅ Implemented
- **Description**: Users can upload text documents and ask questions about their content
- **Implementation**: 
  - Uses LangChain's `ConversationalRetrievalChain` for RAG (Retrieval-Augmented Generation)
  - ChromaDB vector store for document embeddings
  - OpenAI GPT-4o-mini for LLM responses
  - Recursive text splitting with 1000 character chunks and 100 character overlap
- **Current Limitations**:
  - Only supports plain text files (`.txt`)
  - PDF support mentioned but not yet implemented (requires additional libraries like `pypdf`)

### 2. Voice Input
- **Status**: 🚧 Partially Implemented
- **Description**: Support for real-time voice input using microphone
- **Current State**:
  - Chainlit audio chunk handling is implemented (`on_audio_chunk` callback)
  - Placeholder for OpenAI Realtime API integration
  - Currently acknowledges audio input but doesn't process it
- **TODO**: 
  - Integrate OpenAI Realtime API for speech-to-text
  - Implement audio transcription and streaming responses

### 3. Authentication
- **Status**: ✅ Configured with Multiple Modes
- **Description**: Supports three authentication modes that are automatically configured based on environment variables
- **Authentication Modes**:
  1. **Local Dev Mode** (Default when OAuth is not configured):
     - Automatically logs in as a configured user without requiring OAuth
     - Enabled when `OAUTH_GOOGLE_CLIENT_ID`, `OAUTH_GOOGLE_CLIENT_SECRET`, or `OAUTH_REDIRECT_URI` are not set
     - User identity configured via `LOCAL_USER_ID` environment variable (defaults to `user@chainlit.local.ai`)
     - Uses header-based authentication internally
     - Perfect for `make dev` at `http://localhost:8000`
  2. **OAuth Mode** (Production):
     - Full Google OAuth authentication
     - Enabled when all OAuth environment variables are set
     - OAuth callback handler in `chainlit_bootstrap/auth.py` allows all authenticated Google users
     - Can be customized to restrict access by domain or other criteria
     - Required for `make dev-https` at `https://chainlit.local.ai`
  3. **No-Login Mode** (Testing):
     - Disables authentication completely
     - Enabled by setting `CHAINLIT_NO_LOGIN` to any non-empty value (e.g., `1`, `true`)
     - Useful for automated testing
- **Configuration**: 
  - Authentication mode is dynamically configured at startup in `app.py`
  - The `chainlit.toml` file is automatically updated based on detected mode

### 4. File Upload
- **Status**: ✅ Implemented
- **Description**: Users can upload files with messages
- **Configuration**:
  - Accepts all file types (`accept = ["*/*"]`)
  - Maximum 10 files per upload
  - Maximum 10 MB per file
  - Document upload required at chat start (20 MB limit)

### 5. Persistent Sessions
- **Status**: ✅ Enabled
- **Description**: Users can create and switch between different conversation threads
- **Storage**: SQLite database with aiosqlite

### 6. Web Search
- **Status**: ✅ Implemented
- **Description**: Live Tavily-powered web search for up-to-date answers outside uploaded documents
- **Usage**: Users can type `/search your question` (or `search: your question`) to fetch the latest information
- **Implementation**:
  - `tavily-python` client
  - Snippets returned as a formatted message
- **Current Limitations**:
  - Requires a valid `TAVILY_API_KEY`
  - Commands must be prefixed (general chat won't automatically call the search tool)

## Environment Requirements

### Required Environment Variables
- `OPENAI_API_KEY`: OpenAI API key for LLM and embeddings (always required)

### Authentication Environment Variables
Authentication mode is automatically determined based on which variables are set:

**For Local Dev Mode** (auto-login without OAuth):
- Leave OAuth variables unset or empty
- Optional: `LOCAL_USER_ID` - Email/identifier for auto-login (default: `user@chainlit.local.ai`)
- Use with: `make dev` at `http://localhost:8000`

**For OAuth Mode** (Google authentication):
- `OAUTH_GOOGLE_CLIENT_ID`: Google OAuth client ID
- `OAUTH_GOOGLE_CLIENT_SECRET`: Google OAuth client secret
- `OAUTH_REDIRECT_URI`: OAuth redirect URI (e.g., `https://chainlit.local.ai/auth/callback`)
- `CHAINLIT_AUTH_SECRET`: Secret key for signing authentication tokens. Generate with: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
- Use with: `make dev-https` at `https://chainlit.local.ai`

**For No-Login Mode** (testing only):
- `CHAINLIT_NO_LOGIN`: Set to any non-empty value (e.g., `1`, `true`) to disable authentication completely

### Optional Environment Variables
- `DEFAULT_GAI_MODEL`: LLM model name (default: `gpt-4o-mini`)
- `CHAINLIT_PORT`: Port for Chainlit server (default: `8000`)
- `CHAINLIT_HOST`: Host for Chainlit server (default: `0.0.0.0`)
- `TAVILY_API_KEY`: Enables the Tavily web search integration used by the `/search` command

## Current Limitations and Future Enhancements

### Known Limitations
1. **PDF Support**: Currently only supports plain text files. PDF parsing requires additional implementation.
2. **Voice Input**: Audio processing is not fully functional; needs OpenAI Realtime API integration.
3. **Model Support**: Currently hardcoded to OpenAI models only (though architecture supports others).

### Potential Enhancements
1. Add PDF parsing support using `pypdf` or similar libraries
2. Complete OpenAI Realtime API integration for voice input
3. Support for additional LLM providers (Anthropic, Cohere, etc.)
4. Document metadata extraction and indexing
5. Support for multiple document uploads in a single session
6. Export conversation history
7. Advanced retrieval strategies (hybrid search, reranking)

## Project State

- **Version**: 0.1.0
- **Python Version**: 3.12 (required)
- **Status**: Functional core features implemented, voice input pending

