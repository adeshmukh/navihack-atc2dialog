# Authentication Testing Guide

## Current Setup

Your `.env` file currently has OAuth credentials configured, which means:
- Running containers are in **OAuth mode** (Google authentication)
- To test **local dev mode**, you need to temporarily remove OAuth credentials

## Quick Test Instructions

### Test 1: Verify Current OAuth Mode (make dev-https)

Since OAuth credentials are set, verify the system is working correctly:

```bash
# The containers are already running, so just check the logs
docker logs chainlit-app --tail 50

# Look for this line in the output:
# INFO: Authentication mode: Google OAuth
```

**Access the app**:
- Open https://chainlit.local.ai
- You should be redirected to Google OAuth login
- After login, you should see your Google account identity

### Test 2: Test Local Dev Mode (make dev)

To test auto-login without OAuth:

```bash
# Step 1: Stop current containers
make down

# Step 2: Temporarily remove OAuth credentials
# Create a backup of your .env
cp .env .env.backup

# Step 3: Comment out OAuth credentials in .env
# Edit .env and comment out these lines:
#   OAUTH_GOOGLE_CLIENT_ID=...
#   OAUTH_GOOGLE_CLIENT_SECRET=...
#   OAUTH_REDIRECT_URI=...

# You can do this with sed:
sed -i.bak 's/^OAUTH_GOOGLE_CLIENT_ID=/# OAUTH_GOOGLE_CLIENT_ID=/' .env
sed -i 's/^OAUTH_GOOGLE_CLIENT_SECRET=/# OAUTH_GOOGLE_CLIENT_SECRET=/' .env
sed -i 's/^OAUTH_REDIRECT_URI=/# OAUTH_REDIRECT_URI=/' .env

# Step 4: Start in local dev mode
make dev

# Step 5: Check the logs for confirmation
# Look for this line:
# INFO: Local dev mode enabled. Auto-login as: user@chainlit.local.ai
```

**Access the app**:
- Open http://localhost:8000
- You should be **automatically logged in** as `user@chainlit.local.ai`
- No OAuth redirect should occur
- You should see your user identity in the UI

### Test 3: Restore OAuth Mode

After testing local dev mode, restore OAuth:

```bash
# Step 1: Stop containers
make down

# Step 2: Restore the original .env
cp .env.backup .env

# Step 3: Start in HTTPS mode
make dev-https

# Step 4: Verify OAuth is back
docker logs chainlit-app --tail 20
# Should show: INFO: Authentication mode: Google OAuth
```

## Automated Test Script

Here's a complete test script you can run:

```bash
#!/bin/bash
set -e

echo "=== Authentication Mode Testing ==="
echo

# Backup current .env
cp .env .env.test-backup

echo "TEST 1: OAuth Mode (current setup)"
echo "-----------------------------------"
make down
make dev-https &
HTTPS_PID=$!
sleep 10
echo "Check logs..."
docker logs chainlit-app --tail 20 | grep -i "authentication mode"
echo "✓ OAuth mode active"
echo "   Access: https://chainlit.local.ai"
echo "   Press Enter to continue to next test..."
read

echo
echo "TEST 2: Local Dev Mode"
echo "----------------------"
make down
# Comment out OAuth vars
sed -i.test 's/^OAUTH_GOOGLE_CLIENT_ID=/# OAUTH_GOOGLE_CLIENT_ID=/' .env
sed -i 's/^OAUTH_GOOGLE_CLIENT_SECRET=/# OAUTH_GOOGLE_CLIENT_SECRET=/' .env
sed -i 's/^OAUTH_REDIRECT_URI=/# OAUTH_REDIRECT_URI=/' .env

make dev &
DEV_PID=$!
sleep 10
echo "Check logs..."
docker logs chainlit-app --tail 20 | grep -i "local dev mode"
echo "✓ Local dev mode active"
echo "   Access: http://localhost:8000"
echo "   Press Enter to restore original config..."
read

echo
echo "Restoring original configuration..."
make down
cp .env.test-backup .env
rm -f .env.test .env.test-backup

echo
echo "=== Tests Complete ==="
echo "Run 'make dev-https' to restart in OAuth mode"
```

Save this as `test_auth.sh`, make it executable (`chmod +x test_auth.sh`), and run it.

## Expected Console Output

### Local Dev Mode
```
INFO: Local dev mode enabled. Auto-login as: user@chainlit.local.ai
INFO: To use Google OAuth, set OAUTH_GOOGLE_CLIENT_ID, OAUTH_GOOGLE_CLIENT_SECRET, and OAUTH_REDIRECT_URI
INFO: Authentication configured: enabled=true, provider=header
```

### OAuth Mode
```
INFO: Authentication mode: Google OAuth
INFO: Authentication configured: enabled=true, provider=google
```

### No-Login Mode (if CHAINLIT_NO_LOGIN=1)
```
INFO: No-login mode enabled. Authentication will be disabled.
INFO: Authentication configured: enabled=false, provider=google
```

## Verification Checklist

After implementation, verify:

- [ ] **Local Dev Mode**:
  - [ ] Console shows "Local dev mode enabled"
  - [ ] Auto-login happens without OAuth redirect
  - [ ] User identity matches `LOCAL_USER_ID`
  - [ ] Can access app at http://localhost:8000
  
- [ ] **OAuth Mode**:
  - [ ] Console shows "Authentication mode: Google OAuth"
  - [ ] OAuth redirect to Google occurs
  - [ ] Can authenticate with Google account
  - [ ] Can access app at https://chainlit.local.ai
  
- [ ] **Mode Switching**:
  - [ ] Can switch between modes by changing .env
  - [ ] Changes take effect after container restart
  - [ ] Correct mode is detected and configured

## Troubleshooting

### "Still seeing OAuth redirect in local dev mode"
**Solution**: 
```bash
# Verify OAuth vars are not set:
docker exec chainlit-app printenv | grep OAUTH

# Should show empty values or not exist
# If they still have values, restart containers:
make down
make dev
```

### "Auto-login not working"
**Solution**:
```bash
# Check the logs for the authentication mode:
docker logs chainlit-app | grep -i "authentication"

# Verify LOCAL_USER_ID is set:
docker exec chainlit-app printenv LOCAL_USER_ID

# Should show: user@chainlit.local.ai (or your configured value)
```

### "Changes not taking effect"
**Solution**:
```bash
# Always stop containers before changing .env:
make down

# Then start fresh:
make dev  # or make dev-https
```

## Integration with CI/CD

For automated testing, use `CHAINLIT_NO_LOGIN=1`:

```yaml
# .github/workflows/test.yml
env:
  CHAINLIT_NO_LOGIN: 1
  OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
```

This completely disables authentication for headless testing.

