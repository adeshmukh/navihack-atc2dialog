# Local Development Authentication Setup

## Overview

The authentication system now supports three modes that are automatically detected based on environment variables:

1. **Local Dev Mode** - Auto-login without OAuth (for `make dev`)
2. **OAuth Mode** - Full Google OAuth (for `make dev-https`)
3. **No-Login Mode** - No authentication (for testing only)

## How It Works

### Detection Logic

The application checks environment variables at startup and configures authentication accordingly:

```python
# Local Dev Mode is enabled when:
- OAuth credentials are NOT set (empty or missing)
- CHAINLIT_NO_LOGIN is NOT set

# OAuth Mode is enabled when:
- All OAuth credentials are set:
  - OAUTH_GOOGLE_CLIENT_ID
  - OAUTH_GOOGLE_CLIENT_SECRET
  - OAUTH_REDIRECT_URI

# No-Login Mode is enabled when:
- CHAINLIT_NO_LOGIN is set to any non-empty value
```

### Implementation Details

1. **Authentication Detection** (`chainlit_bootstrap/auth.py`):
   - `is_local_dev_mode()`: Checks if OAuth credentials are missing
   - `get_local_user_id()`: Returns configured user from `LOCAL_USER_ID` env var
   - `header_auth_callback()`: Automatically creates user session in local dev mode

2. **Dynamic Configuration** (`app.py`):
   - `configure_auth_mode()`: Updates `chainlit.toml` at startup
   - Sets `provider = "header"` for local dev
   - Sets `provider = "google"` for OAuth
   - Sets `enabled = false` for no-login mode

3. **Environment Variables** (`docker-compose.yml`):
   - `LOCAL_USER_ID`: Configures the auto-login user identity
   - Default: `user@chainlit.local.ai`

## Usage Scenarios

### Scenario 1: Local Development (make dev)

**Goal**: Quick testing without OAuth setup

**Setup**:
1. Create or edit `.env.local` (for local dev only):
   ```bash
   OPENAI_API_KEY=your_key_here
   LOCAL_USER_ID=your.email@example.com
   
   # Leave OAuth variables unset or comment them out:
   # OAUTH_GOOGLE_CLIENT_ID=
   # OAUTH_GOOGLE_CLIENT_SECRET=
   # OAUTH_REDIRECT_URI=
   ```

2. Use `.env.local`:
   ```bash
   ln -sf .env.local .env
   ```

3. Start the server:
   ```bash
   make dev
   ```

**Expected Behavior**:
- App starts at `http://localhost:8000`
- You are automatically logged in as `LOCAL_USER_ID`
- No OAuth redirect occurs
- Console shows: `INFO: Local dev mode enabled. Auto-login as: your.email@example.com`

### Scenario 2: HTTPS with OAuth (make dev-https)

**Goal**: Production-like testing with full authentication

**Setup**:
1. Create or edit `.env.prod` (for OAuth):
   ```bash
   OPENAI_API_KEY=your_key_here
   
   # OAuth credentials (required):
   OAUTH_GOOGLE_CLIENT_ID=your_client_id
   OAUTH_GOOGLE_CLIENT_SECRET=your_client_secret
   OAUTH_REDIRECT_URI=https://chainlit.local.ai/auth/callback
   CHAINLIT_AUTH_SECRET=your_generated_secret
   
   # LOCAL_USER_ID is ignored when OAuth is configured
   LOCAL_USER_ID=user@chainlit.local.ai
   ```

2. Use `.env.prod`:
   ```bash
   ln -sf .env.prod .env
   ```

3. One-time setup (if not done already):
   ```bash
   make init-dev
   ```

4. Start the HTTPS server:
   ```bash
   make dev-https
   ```

**Expected Behavior**:
- App starts at `https://chainlit.local.ai`
- You are redirected to Google OAuth login
- After authentication, you're logged in with your Google identity
- Console shows: `INFO: Authentication mode: Google OAuth`

### Scenario 3: No Authentication (testing)

**Setup**:
```bash
# In .env:
CHAINLIT_NO_LOGIN=1
```

**Expected Behavior**:
- No authentication required
- App accessible without login
- Console shows: `INFO: No-login mode enabled. Authentication will be disabled.`

## Switching Between Modes

To switch from OAuth mode to local dev mode:

1. **Option A**: Use separate `.env` files (recommended)
   ```bash
   # For local dev
   ln -sf .env.local .env
   make dev
   
   # For OAuth
   ln -sf .env.prod .env
   make dev-https
   ```

2. **Option B**: Comment out OAuth variables
   ```bash
   # Edit .env and comment out these lines:
   # OAUTH_GOOGLE_CLIENT_ID=...
   # OAUTH_GOOGLE_CLIENT_SECRET=...
   # OAUTH_REDIRECT_URI=...
   ```

3. **Restart the server** for changes to take effect

## Troubleshooting

### Issue: "Still being redirected to OAuth even after removing credentials"

**Solution**: 
- Make sure to restart the Docker container
- Check that OAuth variables are truly empty or unset (not just commented in .env)
- Verify console logs show "Local dev mode enabled"

### Issue: "Auto-login not working in local dev mode"

**Solution**:
- Check that `LOCAL_USER_ID` is set correctly
- Verify console shows: `INFO: Local dev mode enabled. Auto-login as: [user]`
- Check that `chainlit.toml` has `provider = "header"`

### Issue: "OAuth not working in dev-https mode"

**Solution**:
- Verify all OAuth environment variables are set
- Check that `OAUTH_REDIRECT_URI` matches Google Cloud Console configuration
- Ensure `chainlit.local.ai` is in `/etc/hosts`
- Verify console shows: `INFO: Authentication mode: Google OAuth`

## Testing Checklist

- [ ] Local dev mode works (`make dev` without OAuth)
- [ ] Auto-login happens automatically
- [ ] Correct user identity is shown in UI
- [ ] OAuth mode works (`make dev-https` with OAuth)
- [ ] OAuth redirect works correctly
- [ ] User can authenticate with Google
- [ ] Can switch between modes by changing `.env`
- [ ] Console logs show correct authentication mode

## Code Changes Summary

**Files Modified**:
1. `chainlit_bootstrap/auth.py`:
   - Added `is_local_dev_mode()` and `get_local_user_id()`
   - Added `header_auth_callback()` for auto-login
   - Updated OAuth callback registration logic

2. `app.py`:
   - Updated `configure_auth_mode()` to support three modes
   - Added dynamic `chainlit.toml` configuration
   - Added imports for local dev mode functions

3. `docker-compose.yml`:
   - Added `LOCAL_USER_ID` environment variable

4. `chainlit.toml`:
   - Updated comments to document dynamic configuration
   - Set default to `provider = "header"` (will be overridden at runtime)

5. `docs/requirements.md`:
   - Updated authentication documentation
   - Added environment variables reference

**Files Created**:
1. `SETUP.md`: User-facing setup guide
2. `docs/LOCAL_DEV_AUTH.md`: Technical documentation (this file)

