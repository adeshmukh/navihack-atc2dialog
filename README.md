# Chainlit Bootstrap

A Chainlit-based conversational AI application with document QA, voice input capabilities, and PII security features.

## Features

- **Document Question-Answering**: Upload text documents and ask questions using RAG (Retrieval-Augmented Generation)
- **Voice Input**: Real-time microphone input support (requires HTTPS for browser access)
- **PII Detection**: Automatic detection and anonymization of personally identifiable information
- **Web Search**: Live Tavily-powered web search via `/search` command
- **Persistent Sessions**: SQLite-backed conversation history

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.12+ (for local development)
- `OPENAI_API_KEY` environment variable
- `mkcert` (for HTTPS development setup)
  - macOS: `brew install mkcert`
  - Linux: See [mkcert installation guide](https://github.com/FiloSottile/mkcert#linux)
  - Windows: `choco install mkcert`

### HTTPS Development Setup (Recommended for Voice Input)

The microphone feature requires HTTPS. Follow these steps for a repeatable HTTPS development environment:

1. **One-time setup** (run once per workstation):
   ```bash
   make init-dev
   ```
   This will:
   - Check for locally installed `mkcert` (install it first if missing)
   - Add `chainlit.local.ai` to `/etc/hosts` (if not already present)
   - **WSL users**: Also add to Windows hosts file (script will prompt with instructions)
   - Install mkcert root CA for trusted local certificates (requires sudo)
   - Generate SSL certificates in `.certs/` directory

2. **Start the application with HTTPS**:
   ```bash
   make dev-https
   ```

3. **Access the application**:
   - Open `https://chainlit.local.ai` in your browser
   - The microphone icon should now be visible in the UI

### Standard Development Setup (HTTP)

For development without voice input:

```bash
make dev
```

Access at `http://localhost:8000`

## Development

### Environment Variables

Create a `.env` file with:

```bash
OPENAI_API_KEY=sk-...
DEFAULT_GAI_MODEL=gpt-4o-mini  # Optional
CHAINLIT_PORT=8000              # Optional
CHAINLIT_HOST=0.0.0.0           # Optional
CHAINLIT_NO_LOGIN=1             # Optional: bypass authentication in dev mode
TAVILY_API_KEY=tvly-...         # Optional: enables `/search` web lookups
```

### Make Targets

- `make init-dev` - One-time HTTPS dev setup (hosts entry + certificates)
- `make dev-https` - Start dev container with HTTPS (requires init-dev)
- `make dev` - Start dev container with hot reload (HTTP)
- `make up` - Start services in detached mode
- `make down` - Stop services
- `make build` - Build Docker image
- `make rebuild` - Rebuild Docker image without cache
- `make install` - Create venv and install dependencies
- `make lint` - Run ruff linter
- `make format` - Format code with ruff
- `make test` - Run tests
- `make clean` - Clean build artifacts

### Troubleshooting

#### Microphone not appearing in UI

- Ensure you're accessing via HTTPS (`https://chainlit.local.ai`)
- Verify certificates exist: `ls -la .certs/`
- Check browser console for permission errors
- Ensure `/etc/hosts` contains `127.0.0.1 chainlit.local.ai`
- **WSL users**: Also ensure Windows hosts file (`C:\Windows\System32\drivers\etc\hosts`) contains the entry, as browsers on Windows bypass Linux `/etc/hosts`

#### Certificate errors

- Run `make init-dev` to regenerate certificates
- Ensure mkcert CA is installed (the script handles this automatically)
- Clear browser cache and reload

#### Port conflicts

- Change `CHAINLIT_PORT` in `.env` or `docker-compose.yml`
- Ensure ports 80/443 are available for HTTPS mode

## Project Structure

```
chainlit-bootstrap/
├── app.py                 # Main application entry point
├── chainlit.toml          # Chainlit configuration
├── docker-compose.yml     # Docker Compose configuration
├── docker-compose.https.yml  # HTTPS overlay configuration
├── Dockerfile             # Docker image definition
├── Makefile               # Development commands
├── scripts/               # Utility scripts
│   ├── init_db.py        # Database initialization
│   └── one_time_setup.sh # HTTPS dev setup script
├── ops/https/            # HTTPS configuration
│   └── Caddyfile         # Caddy reverse proxy config
└── chainlit_bootstrap/    # Application package
```

## Documentation

- [Requirements](docs/requirements.md) - Feature requirements and status
- [Technical Design](docs/technical-design.md) - Architecture and implementation details

## License

See LICENSE file for details.

