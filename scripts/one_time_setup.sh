#!/bin/bash
# One-time setup script for HTTPS development environment
# This script sets up /etc/hosts entry and generates SSL certificates

set -eo pipefail

HOSTNAME="chainlit.local.ai"
HOSTS_FILE="/etc/hosts"
CERTS_DIR=".certs"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CERTS_PATH="$PROJECT_ROOT/$CERTS_DIR"

echo "🔧 Running one-time HTTPS development setup..."

# Step 1: Check and update /etc/hosts
echo ""
echo "📝 Checking /etc/hosts for $HOSTNAME..."
if grep -q "$HOSTNAME" "$HOSTS_FILE" 2>/dev/null; then
    echo "✓ $HOSTNAME already exists in /etc/hosts"
else
    echo "Adding $HOSTNAME to /etc/hosts (requires sudo)..."
    if sudo sh -c "echo '127.0.0.1 $HOSTNAME' >> $HOSTS_FILE"; then
        echo "✓ Added $HOSTNAME to /etc/hosts"
    else
        echo "✗ Failed to update /etc/hosts. Please add '127.0.0.1 $HOSTNAME' manually."
        exit 1
    fi
fi

# Step 1b: Check and update Windows hosts file (for WSL)
WINDOWS_HOSTS="/mnt/c/Windows/System32/drivers/etc/hosts"
if [ -f "$WINDOWS_HOSTS" ]; then
    echo ""
    echo "📝 Checking Windows hosts file for $HOSTNAME..."
    if grep -qi "$HOSTNAME" "$WINDOWS_HOSTS" 2>/dev/null; then
        echo "✓ $HOSTNAME already exists in Windows hosts file"
    else
        echo "⚠ Windows hosts file found but requires manual editing (admin privileges needed)"
        echo "  Please add this line to: $WINDOWS_HOSTS"
        echo "    127.0.0.1 $HOSTNAME"
        echo ""
        echo "  You can edit it by running in PowerShell (as Administrator):"
        echo "    notepad C:\\Windows\\System32\\drivers\\etc\\hosts"
        echo ""
        echo "  Or use this command in PowerShell (as Administrator):"
        echo "    Add-Content -Path C:\\Windows\\System32\\drivers\\etc\\hosts -Value \"127.0.0.1 $HOSTNAME\""
        echo ""
        echo "  ⚠ IMPORTANT: Browsers on Windows will not resolve $HOSTNAME until this is added!"
    fi
fi

# Step 2: Create certs directory
echo ""
echo "📁 Creating certificates directory..."
mkdir -p "$CERTS_PATH"
echo "✓ Certificates directory ready: $CERTS_PATH"

# Step 3: Check for locally installed mkcert
echo ""
echo "🔍 Checking for mkcert installation..."
if ! command -v mkcert &> /dev/null; then
    echo "✗ mkcert is not installed locally"
    echo ""
    echo "Please install mkcert first:"
    echo "  macOS: brew install mkcert"
    echo "  Linux: See https://github.com/FiloSottile/mkcert#linux"
    echo "  Windows: choco install mkcert"
    exit 1
fi

MKCERT_VERSION=$(mkcert -version 2>/dev/null || echo "unknown")
echo "✓ Found mkcert: $MKCERT_VERSION"

# Step 4: Install mkcert CA (idempotent - safe to run multiple times)
echo ""
echo "🔐 Installing mkcert root CA (requires sudo)..."
if mkcert -install 2>/dev/null; then
    echo "✓ mkcert root CA installed"
else
    echo "⚠ mkcert CA installation may have failed or was already installed"
    echo "  This is usually fine if you've run this script before"
fi

# Step 5: Generate certificates
echo ""
echo "🎫 Generating SSL certificates..."
cd "$PROJECT_ROOT"

if mkcert \
    -key-file "$CERTS_PATH/chainlit-dev.key" \
    -cert-file "$CERTS_PATH/chainlit-dev.crt" \
    "$HOSTNAME" localhost 127.0.0.1 ::1; then
    echo "✓ Certificates generated successfully"
    echo "  Certificate: $CERTS_PATH/chainlit-dev.crt"
    echo "  Private key: $CERTS_PATH/chainlit-dev.key"
else
    echo "✗ Failed to generate certificates"
    exit 1
fi

echo ""
echo "✅ One-time setup completed successfully!"
echo ""
echo "Next steps:"
echo "  1. Run 'make dev-https' to start the application with HTTPS"
echo "  2. Open https://$HOSTNAME in your browser"
echo "  3. The microphone should now be available in the Chainlit UI"

