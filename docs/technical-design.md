# Technical Design

## Technology Stack

### Core Framework
- **Chainlit** (>=1.0.0): Modern Python framework for building conversational AI applications with a built-in UI
  - Provides chat interface, file upload, authentication, and session management
  - Supports streaming responses and real-time updates

### LLM & AI
- **OpenAI** (>=1.0.0): Primary LLM provider
  - `llama-index-llms-openai` (>=0.1.0): LlamaIndex integration for OpenAI
  - Models: GPT-4o-mini (default, configurable via `DEFAULT_GAI_MODEL`)
  - Used for both chat completions and text embeddings
- **Tavily** (>=0.3.8 via `tavily-python`): Real-time web search provider accessed through explicit `/search` commands

### LlamaIndex Ecosystem
- **llama-index-core** (>=0.10.0): Core orchestration framework for RAG and document processing
- **llama-index-llms-openai** (>=0.1.0): OpenAI LLM integration
- **llama-index-embeddings-openai** (>=0.1.0): OpenAI embeddings integration
- **llama-index-vector-stores-chroma** (>=0.1.0): ChromaDB vector store integration
- **Components Used**:
  - `VectorStoreIndex`: RAG index with vector store backend
  - `SentenceSplitter`: Document chunking (1000 chars, 100 overlap)
  - `ChatMemoryBuffer`: Maintains chat history
  - `SimpleChatEngine` / `as_chat_engine`: Conversational chat engines with memory

### Vector Database
- **ChromaDB** (>=0.4.0): Embedded vector database for document embeddings
  - Stores document chunks as vectors
  - Enables semantic search over uploaded documents
  - Metadata tracking for source attribution

### Database
- **SQLAlchemy** (>=2.0.0): ORM for database operations
- **aiosqlite** (>=0.19.0): Async SQLite driver
  - Used for persistent session storage
  - Database path: `./data/chainlit.db`

### Development Tools
- **ruff** (>=0.1.0): Fast Python linter and formatter
  - Replaces black, isort, flake8, and other tools
  - Configured in `pyproject.toml`
- **pytest** (>=7.4.0): Testing framework
- **pytest-asyncio** (>=0.21.0): Async test support

### Package Management
- **uv**: Fast Python package installer and resolver
  - Used for dependency management and virtual environment creation
  - Faster than pip, written in Rust

### Containerization
- **Docker**: Container runtime
- **Docker Compose**: Multi-container orchestration
  - Hot reload support for development
  - Volume mounting for code changes
  - Health checks configured

## Architecture

### Application Flow

```
User Uploads Document
    ↓
Text Extraction & Chunking
    ↓
Embedding Generation (OpenAI)
    ↓
Vector Store Creation (ChromaDB)
    ↓
User Query
    ↓
Assistant Routing (if active)
    ↓
Retrieval from Vector Store (if document loaded)
    ↓
RAG Chat Engine (LlamaIndex)
    ↓
LLM Response
    ↓
Stream Response to User
```

### Key Components

1. **Document Processing Pipeline**
   - File upload → Text extraction → Chunking → Embedding → Vector storage

2. **Query Processing Pipeline**
   - User input → Assistant routing (if active) → Vector retrieval → RAG → Streaming output

3. **Session Management**
   - Persistent sessions stored in SQLite
   - Conversation history maintained via LlamaIndex memory
   - Assistant state stored per session

4. **Security Layer**
   - Google OAuth authentication (can be bypassed in dev mode via `CHAINLIT_NO_LOGIN`)

## Developer Quickstart

### Prerequisites
- Python 3.12 (required)
- Docker and Docker Compose (optional, for containerized development)
- `uv` package manager (recommended) or `pip`
- OpenAI API key

### Local Development Setup

#### Option 1: Using uv (Recommended)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd chainlit-bootstrap
   ```

2. **Create virtual environment**
   ```bash
   make venv
   # Or manually: uv venv --python python3.12
   ```

3. **Install dependencies**
   ```bash
   make install
   # Or manually: uv pip install --python .venv/bin/python <dependencies>
   ```

4. **Set environment variables**
   ```bash
   export OPENAI_API_KEY="your-api-key-here"
   # Optional:
   export DEFAULT_GAI_MODEL="gpt-4o-mini"
   export CHAINLIT_PORT=8000
   # To bypass authentication in dev mode:
   export CHAINLIT_NO_LOGIN=1
   ```

5. **Run the application**
   ```bash
   chainlit run app.py
   ```
   The app will be available at `http://localhost:8000`

#### Option 2: Using Docker

1. **Create `.env` file**
   ```bash
   echo "OPENAI_API_KEY=your-api-key-here" > .env
   ```

2. **Build and run**
   ```bash
   make build    # Build Docker image
   make dev      # Run with hot reload
   # Or: docker-compose up
   ```

3. **Access the application**
   - Open `http://localhost:8000` in your browser

### Development Workflow

#### Code Quality
```bash
# Lint code
make lint

# Format code
make format

# Auto-fix issues
make fix
```

#### Testing
```bash
# Run tests
make test

# Note: Create tests/ directory and add pytest tests
```

#### Cleanup
```bash
# Remove build artifacts and caches
make clean
```

### Project Structure

```
chainlit-bootstrap/
├── app.py                 # Main application entry point
├── chainlit.toml          # Chainlit configuration
├── pyproject.toml         # Python project metadata and dependencies
├── Dockerfile             # Docker image definition
├── docker-compose.yml     # Docker Compose configuration
├── Makefile               # Development commands
├── data/                  # Persistent data (database, uploads)
│   └── chainlit.db       # SQLite database (created at runtime)
├── docs/                  # Documentation
│   ├── requirements.md
│   └── technical-design.md
└── tests/                 # Test directory (create as needed)
```

### Configuration Files

- **`chainlit.toml`**: Chainlit UI and feature configuration
  - Authentication settings
  - Feature flags (voice, file upload, etc.)
  - UI customization

- **`pyproject.toml`**: Python project configuration
  - Dependencies
  - Ruff linting/formatting rules
  - Build system configuration

### Environment Variables

Create a `.env` file for local development (or export in shell):

```bash
OPENAI_API_KEY=sk-...
DEFAULT_GAI_MODEL=gpt-4o-mini  # Optional
CHAINLIT_PORT=8000              # Optional
CHAINLIT_HOST=0.0.0.0           # Optional
CHAINLIT_NO_LOGIN=1             # Optional: bypass authentication in dev mode
TAVILY_API_KEY=tvly-...         # Optional: enables `/search` web lookups
```

### Common Development Tasks

#### Adding a New Dependency
1. Add to `pyproject.toml` under `dependencies`
2. Run `make install` to sync
3. Update `Dockerfile` and `Makefile` if needed

#### Modifying Chainlit Configuration
- Edit `chainlit.toml`
- Restart the application for changes to take effect
- Note: `CHAINLIT_NO_LOGIN` environment variable programmatically modifies `chainlit.toml` to disable authentication when set

#### Debugging
- Chainlit provides built-in debugging UI
- Check logs in terminal output
- Use `cl.Message()` for debugging messages

### Troubleshooting

#### Issue: Port already in use
```bash
export CHAINLIT_PORT=8001
# Or change in docker-compose.yml
```

#### Issue: OpenAI API errors
- Verify `OPENAI_API_KEY` is set correctly
- Check API key has sufficient credits
- Verify model name is correct

#### Issue: Docker build fails
- Ensure Docker has sufficient memory (4GB+ recommended)
- Check Python version compatibility (3.12 required)

## Assistant Architecture

The application supports a multi-assistant system where specialized assistants can be registered and discovered automatically.

### Discovery Convention

Assistants are discovered using a convention-based approach:

1. **Directory Structure**: Create a package under `assistants/<assistant-name>/`
2. **Contract**: Each assistant package must export an `ASSISTANT_DESCRIPTOR` in its `__init__.py`
3. **Auto-Discovery**: The registry automatically scans `assistants/` and imports descriptors on startup

### Assistant Contract

Each assistant must implement the `AssistantDescriptor` interface:

```python
from chainlit_bootstrap.assistants import AssistantDescriptor

ASSISTANT_DESCRIPTOR = AssistantDescriptor(
    name="Assistant Name",
    command="command",  # Slash command prefix (e.g., "health")
    description="What this assistant does",
    handle_message=async_function,  # Required: async (message: str, context: dict) -> str
    handle_file=optional_function,  # Optional: custom file handling
    handle_search=optional_function,  # Optional: custom search handling
)
```

### Example: Healthcare Assistant

The healthcare assistant (`assistants/healthcare/`) demonstrates:

- **Parlant-inspired design**: Uses journey-based conversation flows
- **Tool integration**: Implements tools for scheduling and lab results
- **State management**: Maintains conversation state in Chainlit session
- **Guidelines**: Handles edge cases (insurance, urgent requests, off-topic queries)

### Using Assistants

Users can interact with assistants via:

- `/assistant list`: List all available assistants
- `/assistant <name>`: Switch default assistant
- `/<command> <message>`: Use assistant directly (e.g., `/health schedule appointment`)

### Shared Commands

The following commands work across all assistants:

- `/search <query>`: Web search via Tavily
- `/chart <size>`: Generate visualization
- File uploads: Process documents for Q&A

### Adding a New Assistant

1. Create `assistants/<your-assistant>/` directory
2. Implement `__init__.py` with `ASSISTANT_DESCRIPTOR`
3. Implement `handle_message` function (and optionally `handle_file`, `handle_search`)
4. Restart the application - the assistant will be auto-discovered

### LlamaIndex Migration

The application migrated from LangChain to LlamaIndex for:

- **Simpler API**: More straightforward RAG and chat engine setup
- **Better streaming**: Native async streaming support
- **Framework flexibility**: Assistants can use any framework (Parlant, Haystack, etc.)

Key changes:
- `ConversationalRetrievalChain` → `VectorStoreIndex.as_chat_engine()`
- `ChatMessageHistory` → `ChatMemoryBuffer`
- `RecursiveCharacterTextSplitter` → `SentenceSplitter`
- LangChain callbacks → LlamaIndex streaming

### Next Steps for Contributors

1. Review `app.py` to understand the application flow
2. Check `chainlit.toml` for available features
3. Explore LlamaIndex documentation for RAG patterns
4. Review `assistants/healthcare/` as an example assistant implementation
5. Consider implementing TODO items (PDF support, voice integration)

