"""Chainlit application entry point."""

import logging
import os
import re
from pathlib import Path

from chainlit_bootstrap.auth import is_no_login_mode, is_local_dev_mode


class SuppressReactDevtoolsFilter(logging.Filter):
    """Drop noisy react-devtools websocket messages from logs."""

    noisy_tokens = ("window_message", '"react-devtools')

    def filter(self, record):
        msg = record.getMessage()
        return not any(token in msg for token in self.noisy_tokens)


def configure_logging():
    """
    Configure logging to suppress DEBUG level messages, especially react-devtools noise.
    """
    log_level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, log_level_name, None)
    if level is None or not isinstance(level, int):
        print(
            f"WARNING: Unknown LOG_LEVEL '{log_level_name}'. "
            "Defaulting to INFO."
        )
        level = logging.INFO

    logging.basicConfig(level=level, force=True)

    spam_filter = SuppressReactDevtoolsFilter()
    logging.getLogger().addFilter(spam_filter)

    # Specifically suppress DEBUG logs from socketio/websocket libraries
    socketio_logger = logging.getLogger("socketio")
    socketio_logger.setLevel(logging.WARNING)
    socketio_logger.addFilter(spam_filter)

    engineio_logger = logging.getLogger("engineio")
    engineio_logger.setLevel(logging.WARNING)
    engineio_logger.addFilter(spam_filter)

    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)


configure_logging()


def configure_auth_mode():
    """
    Configure authentication mode based on environment variables.

    Three modes are supported:
    1. No-login mode (CHAINLIT_NO_LOGIN=1): Disables authentication completely
    2. Local dev mode (no OAuth credentials): Enables header-based auto-login
    3. OAuth mode (OAuth credentials set): Enables Google OAuth
    """
    chainlit_toml_path = Path(__file__).parent / "chainlit.toml"
    if not chainlit_toml_path.exists():
        print(
            f"WARNING: chainlit.toml not found at {chainlit_toml_path}. "
            "Cannot configure authentication."
        )
        return

    content = chainlit_toml_path.read_text(encoding="utf-8")

    # Determine authentication mode
    if is_no_login_mode():
        # Mode 1: No authentication at all
        print("INFO: No-login mode enabled. Authentication will be disabled.")
        enabled_value = "false"
        provider_value = "google"  # doesn't matter when disabled
    elif is_local_dev_mode():
        # Mode 2: Local dev mode with header-based auto-login
        from chainlit_bootstrap.auth import get_local_user_id
        local_user = get_local_user_id()
        print(f"INFO: Local dev mode enabled. Header-based auto-login as: {local_user}")
        enabled_value = "true"
        provider_value = "header"
    else:
        # Mode 3: OAuth mode
        print("INFO: Authentication mode: Google OAuth")
        enabled_value = "true"
        provider_value = "google"

    # Update enabled setting
    pattern = r"(\[features\.authentication\]\s*#.*?\n.*?# Enable authentication\s*\n)enabled\s*=\s*(true|false)"
    modified_content = re.sub(pattern, rf"\1enabled = {enabled_value}", content, flags=re.MULTILINE)

    # Fallback: line-by-line parsing if regex didn't match
    if modified_content == content:
        lines = content.split("\n")
        in_auth_section = False
        modified_lines = []

        for line in lines:
            if line.strip().startswith("[features.authentication]"):
                in_auth_section = True
                modified_lines.append(line)
            elif in_auth_section and line.strip().startswith("enabled"):
                modified_lines.append(f"enabled = {enabled_value}")
                in_auth_section = False
            elif in_auth_section and line.strip().startswith("["):
                in_auth_section = False
                modified_lines.append(line)
            else:
                modified_lines.append(line)

        modified_content = "\n".join(modified_lines)

    # Update provider setting
    provider_pattern = r"(provider\s*=\s*\")(\w+)(\")"
    modified_content = re.sub(provider_pattern, rf"\1{provider_value}\3", modified_content)

    chainlit_toml_path.write_text(modified_content, encoding="utf-8")
    print(f"INFO: Authentication configured: enabled={enabled_value}, provider={provider_value}")


configure_auth_mode()


def configure_audio_feature():
    """
    Ensure audio feature is enabled in chainlit.toml before Chainlit loads the configuration.

    This function modifies the TOML file directly (similar to configure_auth_mode) to ensure
    the audio feature is enabled before Chainlit reads the config. This is necessary because
    Chainlit loads config at import time and the config object may be immutable.

    Checks both chainlit.toml (root) and .chainlit/config.toml (Chainlit may prefer this).
    """
    project_root = Path(__file__).parent

    # Chainlit may prefer .chainlit/config.toml over chainlit.toml
    # Check both locations, but prioritize .chainlit/config.toml if it exists
    chainlit_dir_config = project_root / ".chainlit" / "config.toml"
    root_config = project_root / "chainlit.toml"

    # Determine which config file to use
    if chainlit_dir_config.exists():
        chainlit_toml_path = chainlit_dir_config
        print(f"INFO: Using Chainlit config at {chainlit_toml_path}")
    elif root_config.exists():
        chainlit_toml_path = root_config
        print(f"INFO: Using Chainlit config at {chainlit_toml_path}")
    else:
        # Neither exists - try to create/update root config
        chainlit_toml_path = root_config
        print(
            f"WARNING: No chainlit.toml found. Will create/update {chainlit_toml_path}"
        )

    # Read existing content if file exists, otherwise start with empty
    if chainlit_toml_path.exists():
        content = chainlit_toml_path.read_text(encoding="utf-8")
    else:
        # Create basic config structure
        content = """[project]
enable_telemetry = false

[features.audio]
enabled = true
"""

    original_content = content

    # Check if audio section exists and what its current value is
    audio_section_pattern = r"\[features\.audio\]"
    has_audio_section = bool(re.search(audio_section_pattern, content))

    if not has_audio_section:
        # Add audio section after [features.persistent_sessions] or before [UI]
        # Find insertion point
        if "[UI]" in content:
            # Insert before [UI] section
            content = re.sub(
                r"(\[UI\])",
                r"[features.audio]\nenabled = true\n\n\1",
                content,
                1
            )
        elif "[features.persistent_sessions]" in content:
            # Insert after persistent_sessions section
            content = re.sub(
                r"(\[features\.persistent_sessions\]\s*enabled\s*=\s*true)",
                r"\1\n\n# Allow users to use the microphone\n[features.audio]\nenabled = true",
                content,
                1
            )
        else:
            # Fallback: add before [UI] or at end
            if "[UI]" in content:
                content = re.sub(r"(\[UI\])", r"[features.audio]\nenabled = true\n\n\1", content, 1)
            else:
                content += "\n\n# Allow users to use the microphone\n[features.audio]\nenabled = true\n"
    else:
        # Audio section exists - ensure enabled = true
        # Pattern to match [features.audio] section and enabled line
        # Handle various formats: enabled = true, enabled=true, enabled = false, etc.
        # Match: [features.audio] followed by optional comments/newlines, then enabled = value
        audio_enabled_pattern = r"(\[features\.audio\]\s*(?:#[^\n]*\n)?\s*)enabled\s*=\s*(true|false)"

        if re.search(audio_enabled_pattern, content, re.MULTILINE):
            # Replace enabled = false with enabled = true, or ensure it's true
            def replace_enabled(match):
                prefix = match.group(1)
                value = match.group(2).lower()
                if value == "false":
                    return f"{prefix}enabled = true"
                else:
                    return match.group(0)  # Already true, keep as is

            content = re.sub(audio_enabled_pattern, replace_enabled, content, flags=re.MULTILINE)
        else:
            # Audio section exists but no enabled line - add it after the section header
            # Handle case where there's a comment after [features.audio]
            content = re.sub(
                r"(\[features\.audio\]\s*(?:#[^\n]*)?)\n",
                r"\1\nenabled = true\n",
                content,
                1
            )

    # Only write if content changed
    if content != original_content:
        # Ensure parent directory exists (for .chainlit/config.toml)
        chainlit_toml_path.parent.mkdir(parents=True, exist_ok=True)
        chainlit_toml_path.write_text(content, encoding="utf-8")
        print(f"INFO: Audio feature enabled in {chainlit_toml_path.name}")
    else:
        # Verify the current value
        enabled_match = re.search(
            r"\[features\.audio\].*?enabled\s*=\s*(true|false)",
            content,
            re.DOTALL | re.IGNORECASE
        )
        if enabled_match:
            enabled_value = enabled_match.group(1).lower()
            if enabled_value == "true":
                print("INFO: Audio feature is already enabled in chainlit.toml")
            else:
                print(f"WARNING: Audio feature is set to {enabled_value} in chainlit.toml")
        else:
            print("WARNING: Could not verify audio feature setting in chainlit.toml")


configure_audio_feature()

import chainlit as cl

# Verify audio config after Chainlit import (for debugging)
def verify_audio_config():
    """Verify audio configuration after Chainlit loads it."""
    try:
        import chainlit.config as cfg
        if hasattr(cfg.config, 'features') and hasattr(cfg.config.features, 'audio'):
            current_enabled = cfg.config.features.audio.enabled
            print(f"INFO: Chainlit loaded audio.enabled = {current_enabled}")
            if not current_enabled:
                print(
                    "WARNING: Audio feature is disabled in Chainlit config despite TOML setting. "
                    "This may indicate a Chainlit bug or config loading issue."
                )
        else:
            print("WARNING: Audio feature config not found in Chainlit config object")
    except Exception as e:
        print(f"WARNING: Could not verify audio config: {e}")


# Verify after import
verify_audio_config()
from chainlit.data.sql_alchemy import SQLAlchemyDataLayer
from chainlit.data.storage_clients.base import BaseStorageClient
from typing import Dict, Any, Union
import asyncio
from urllib.parse import quote

_data_layer = None


class LocalFileStorageClient(BaseStorageClient):
    """Local file-based storage client for blob storage."""

    def __init__(self, base_path: Path):
        """Initialize local file storage client.

        Args:
            base_path: Base directory path for storing files
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    async def upload_file(
        self,
        object_key: str,
        data: Union[bytes, str],
        mime: str = "application/octet-stream",
        overwrite: bool = True,
        content_disposition: str | None = None,
    ) -> Dict[str, Any]:
        """Upload a file to local storage."""
        file_path = self.base_path / object_key

        if isinstance(data, str):
            data_bytes = data.encode("utf-8")
        else:
            data_bytes = data

        def _write_file():
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_bytes(data_bytes)

        await asyncio.to_thread(_write_file)

        return {
            "path": str(file_path),
            "size": len(data_bytes),
            "mime": mime,
        }

    async def delete_file(self, object_key: str) -> bool:
        """Delete a file from local storage."""
        file_path = self.base_path / object_key

        def _delete_file():
            if file_path.exists():
                file_path.unlink()
                return True
            return False

        try:
            return await asyncio.to_thread(_delete_file)
        except Exception:
            return False

    async def get_read_url(self, object_key: str) -> str:
        """Get a URL to read the file (returns a file:// URL for local storage)."""
        file_path = self.base_path / object_key
        # Return a relative path that can be served by Chainlit
        return f"/files/{quote(object_key)}"

    async def close(self) -> None:
        """Close the storage client (no-op for local storage)."""
        pass


def _initialize_database_tables(conninfo: str) -> None:
    """Initialize database tables synchronously before async operations."""
    try:
        from sqlalchemy import create_engine

        sync_conninfo = conninfo.replace("sqlite+aiosqlite:///", "sqlite:///")
        sync_engine = create_engine(sync_conninfo, echo=False)

        try:
            from chainlit.data.sql_alchemy import Base
            Base.metadata.create_all(sync_engine)
            print("INFO: Database tables initialized successfully")
        except ImportError:
            print("INFO: Database initialization will happen on first access")

        sync_engine.dispose()
    except Exception as e:
        print(f"INFO: Database initialization deferred: {type(e).__name__}")


@cl.data_layer
def get_data_layer():
    """Get or create the data layer instance."""
    global _data_layer

    if _data_layer is None:
        data_dir = Path(__file__).parent / "data"
        data_dir.mkdir(exist_ok=True)

        db_path = data_dir / "chainlit.db"
        conninfo = f"sqlite+aiosqlite:///{db_path}"

        # Configure blob storage for file uploads
        blob_storage_dir = Path(__file__).parent / ".local" / "data" / "blobs"
        blob_storage_client = LocalFileStorageClient(blob_storage_dir)

        _data_layer = SQLAlchemyDataLayer(
            conninfo=conninfo,
            storage_provider=blob_storage_client,
        )
        _initialize_database_tables(conninfo)

    return _data_layer




from chainlit_bootstrap import handlers  # noqa: F401
from chainlit_bootstrap.auth import oauth_callback  # noqa: F401

# Final verification after all imports
verify_audio_config()
