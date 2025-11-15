"""Google OAuth authentication configuration for Chainlit."""

import os
import secrets

import chainlit as cl


def is_no_login_mode() -> bool:
    """Check if no-login mode is enabled via CHAINLIT_NO_LOGIN environment variable."""
    no_login = os.getenv("CHAINLIT_NO_LOGIN", "").strip().lower()
    return no_login and no_login not in ("0", "false", "no", "")


def is_local_dev_mode() -> bool:
    """
    Check if we're in local dev mode (auto-login without OAuth).

    Local dev mode is enabled when:
    - CHAINLIT_NO_LOGIN is not set (we still want authentication, just automatic)
    - OAuth credentials are not configured

    This allows `make dev` to auto-login, while `make dev-https` uses OAuth.
    """
    if is_no_login_mode():
        return False

    # Check if OAuth credentials are configured
    google_client_id = os.getenv("OAUTH_GOOGLE_CLIENT_ID") or os.getenv("GOOGLE_CLIENT_ID")
    google_client_secret = os.getenv("OAUTH_GOOGLE_CLIENT_SECRET") or os.getenv("GOOGLE_CLIENT_SECRET")
    oauth_redirect_uri = os.getenv("OAUTH_REDIRECT_URI")

    # Local dev mode when OAuth is not configured
    return not (google_client_id and google_client_secret and oauth_redirect_uri)


def get_local_user_id() -> str:
    """Get the local user ID for auto-login in dev mode."""
    return os.getenv("LOCAL_USER_ID", "user@chainlit.local.ai")


def configure_google_oauth():
    """
    Configure Google OAuth environment variables from custom names to Chainlit's expected names.

    Also ensures CHAINLIT_AUTH_SECRET is set, which is required for authentication to work.
    """
    # Skip OAuth configuration if no-login mode is enabled
    if is_no_login_mode():
        print("INFO: No-login mode enabled. Skipping OAuth configuration.")
        return

    # Skip OAuth configuration if local dev mode is enabled
    if is_local_dev_mode():
        local_user = get_local_user_id()
        print(f"INFO: Local dev mode enabled. Auto-login as: {local_user}")
        print("INFO: To use Google OAuth, set OAUTH_GOOGLE_CLIENT_ID, OAUTH_GOOGLE_CLIENT_SECRET, and OAUTH_REDIRECT_URI")
        return

    # Chainlit expects OAUTH_GOOGLE_CLIENT_ID and OAUTH_GOOGLE_CLIENT_SECRET directly
    # Check for Chainlit's expected names first, then fall back to custom names for backward compatibility
    google_client_id = os.getenv("OAUTH_GOOGLE_CLIENT_ID") or os.getenv("GOOGLE_CLIENT_ID")
    google_client_secret = os.getenv("OAUTH_GOOGLE_CLIENT_SECRET") or os.getenv("GOOGLE_CLIENT_SECRET")
    oauth_redirect_uri = os.getenv("OAUTH_REDIRECT_URI")

    has_oauth_creds = bool(google_client_id and google_client_secret and oauth_redirect_uri)

    # Ensure Chainlit's expected environment variables are set
    env_vars = {
        "OAUTH_GOOGLE_CLIENT_ID": google_client_id,
        "OAUTH_GOOGLE_CLIENT_SECRET": google_client_secret,
        "OAUTH_REDIRECT_URI": oauth_redirect_uri,
    }
    for key, value in env_vars.items():
        if value:
            os.environ[key] = value

    # CHAINLIT_AUTH_SECRET is required for authentication to work
    # If not set, generate a random secret (for development only)
    # In production, this should be set explicitly via environment variable
    if not os.getenv("CHAINLIT_AUTH_SECRET"):
        # Generate a secure random secret
        auth_secret = secrets.token_urlsafe(32)
        os.environ["CHAINLIT_AUTH_SECRET"] = auth_secret
        if has_oauth_creds:
            print(
                "WARNING: CHAINLIT_AUTH_SECRET was not set. Generated a random secret. "
                "For production, set CHAINLIT_AUTH_SECRET explicitly."
            )

    # Warn if OAuth credentials are missing but authentication is enabled
    if not has_oauth_creds:
        print(
            "WARNING: Google OAuth credentials (OAUTH_GOOGLE_CLIENT_ID or GOOGLE_CLIENT_ID, "
            "OAUTH_GOOGLE_CLIENT_SECRET or GOOGLE_CLIENT_SECRET, OAUTH_REDIRECT_URI) are not set. "
            "Authentication will not be enforced. Set these environment variables to enable Google OAuth authentication."
        )


# Configure OAuth before the decorator is evaluated
configure_google_oauth()


def oauth_callback(
    provider_id: str,
    token: str,
    raw_user_data: dict[str, str],
    default_user: cl.User,
) -> cl.User | None:
    """
    OAuth callback handler for Google authentication.

    This function is called after a user successfully authenticates with Google.
    By default, it allows all authenticated Google users to access the app.

    Args:
        provider_id: The OAuth provider identifier (e.g., "google")
        token: The OAuth token received from the provider
        raw_user_data: User information returned by the provider
        default_user: A cl.User object created by Chainlit

    Returns:
        A cl.User object if authentication is successful, None otherwise
    """
    if provider_id == "google":
        # Allow all authenticated Google users
        # You can customize this to restrict access, e.g., by domain:
        # if raw_user_data.get("hd") == "example.org":
        #     return default_user
        return default_user
    return None


# Only register OAuth callback if no-login mode is not enabled and not in local dev mode
if not is_no_login_mode() and not is_local_dev_mode():
    oauth_callback = cl.oauth_callback(oauth_callback)


def header_auth_callback(headers: dict) -> cl.User | None:
    """
    Header-based authentication for local development.

    This automatically logs in the user configured via LOCAL_USER_ID when:
    - OAuth credentials are not configured (local dev mode)
    - CHAINLIT_NO_LOGIN is not set (we still want user identity)

    Args:
        headers: HTTP request headers

    Returns:
        A cl.User object for automatic login
    """
    if is_local_dev_mode():
        user_id = get_local_user_id()
        # Extract name from email if possible
        name = user_id.split("@")[0] if "@" in user_id else user_id
        return cl.User(
            identifier=user_id,
            metadata={"email": user_id, "role": "admin", "provider": "local-dev"}
        )
    return None


# Register header auth callback for local dev mode
if is_local_dev_mode():
    header_auth_callback = cl.header_auth_callback(header_auth_callback)
