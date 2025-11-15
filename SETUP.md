# Setup Guide

This guide explains how to set up and run the Chainlit application in different modes.

## Quick Start

### Option 1: Local Development (No OAuth Setup Required)

Perfect for quick testing and local development. The app automatically logs you in without requiring Google OAuth.

1. **Create a `.env` file** with minimal configuration:
   ```bash
   OPENAI_API_KEY=your_openai_api_key_here
   # Optional: Set your local user identity
   LOCAL_USER_ID=your.email@example.com
   ```

2. **Start the development server**:
   ```bash
   make dev
   ```

3. **Access the app**:
   - Open http://localhost:8000
   - You'll be automatically logged in as the configured `LOCAL_USER_ID`
   - No Google authentication required!

### Option 2: HTTPS with Google OAuth

For production-like testing with full OAuth authentication.

1. **Set up OAuth credentials** (one-time):
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create OAuth 2.0 credentials
   - Set authorized redirect URI to: `https://chainlit.local.ai/auth/callback`

2. **Create a `.env` file** with OAuth configuration:
   ```bash
   OPENAI_API_KEY=your_openai_api_key_here
   
   # Google OAuth Configuration
   OAUTH_GOOGLE_CLIENT_ID=your_client_id_here
   OAUTH_GOOGLE_CLIENT_SECRET=your_client_secret_here
   OAUTH_REDIRECT_URI=https://chainlit.local.ai/auth/callback
   
   # Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"
   CHAINLIT_AUTH_SECRET=your_generated_secret_here
   ```

3. **One-time HTTPS setup**:
   ```bash
   make init-dev
   ```
   This sets up:
   - Local SSL certificates
   - `/etc/hosts` entry for `chainlit.local.ai`

4. **Start the HTTPS server**:
   ```bash
   make dev-https
   ```

5. **Access the app**:
   - Open https://chainlit.local.ai
   - You'll be prompted to log in with Google
   - Full OAuth authentication flow

## Environment Variables Reference

### Required (All Modes)
- `OPENAI_API_KEY`: Your OpenAI API key

### Local Dev Mode (make dev)
- `LOCAL_USER_ID`: Email/identifier for auto-login (default: `user@chainlit.local.ai`)

### OAuth Mode (make dev-https)
- `OAUTH_GOOGLE_CLIENT_ID`: Google OAuth client ID
- `OAUTH_GOOGLE_CLIENT_SECRET`: Google OAuth client secret
- `OAUTH_REDIRECT_URI`: OAuth callback URL (use `https://chainlit.local.ai/auth/callback`)
- `CHAINLIT_AUTH_SECRET`: Secret for signing auth tokens

### Optional
- `DEFAULT_GAI_MODEL`: LLM model to use (default: `gpt-4o-mini`)
- `CHAINLIT_PORT`: Server port (default: `8000`)
- `TAVILY_API_KEY`: For web search functionality
- `CHAINLIT_NO_LOGIN`: Set to `1` to disable all authentication (testing only)

## Authentication Modes Explained

The application automatically detects which authentication mode to use:

1. **Local Dev Mode**: Enabled when OAuth credentials are NOT set
   - Header-based automatic login
   - No OAuth redirect required
   - Perfect for local development

2. **OAuth Mode**: Enabled when ALL OAuth credentials are set
   - Full Google OAuth flow
   - Requires valid redirect URI
   - Production-ready authentication

3. **No-Login Mode**: Enabled when `CHAINLIT_NO_LOGIN=1`
   - Completely disables authentication
   - For automated testing only

## Troubleshooting

### "OAuth callback failed" error
- Make sure all OAuth environment variables are set correctly
- Check that the redirect URI matches exactly in both .env and Google Cloud Console

### Can't access https://chainlit.local.ai
- Run `make init-dev` to set up SSL certificates and hosts file
- Check that `/etc/hosts` contains: `127.0.0.1 chainlit.local.ai`

### Want to switch between modes?
- For local dev: Unset or comment out OAuth variables in `.env`
- For OAuth: Set all OAuth variables in `.env`
- Restart the server after changing `.env`

## Additional Commands

- `make help` - Show all available commands
- `make down` - Stop running containers
- `make clean` - Clean up build artifacts
- `make lint` - Run code linting
- `make test` - Run tests

