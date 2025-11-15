"""Assistant registry and discovery system."""

import importlib
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Awaitable, Callable

logger = logging.getLogger(__name__)


@dataclass
class AssistantDescriptor:
    """Descriptor for an assistant implementation."""

    name: str
    command: str
    description: str
    handle_message: Callable[[str, dict], Awaitable[str]]
    handle_file: Callable[[str, dict], Awaitable[str]] | None = None
    handle_search: Callable[[str, dict], Awaitable[str]] | None = None


class AssistantRegistry:
    """Registry for managing assistant descriptors."""

    def __init__(self) -> None:
        self._assistants: dict[str, AssistantDescriptor] = {}

    def register(self, descriptor: AssistantDescriptor) -> None:
        """Register an assistant descriptor."""
        if descriptor.command in self._assistants:
            logger.warning(
                f"Assistant with command '{descriptor.command}' already registered. "
                f"Overwriting with '{descriptor.name}'."
            )
        self._assistants[descriptor.command] = descriptor
        logger.info(f"Registered assistant: {descriptor.name} (command: /{descriptor.command})")

    def get(self, command: str) -> AssistantDescriptor | None:
        """Get an assistant by command."""
        return self._assistants.get(command)

    def list_all(self) -> list[AssistantDescriptor]:
        """List all registered assistants."""
        return list(self._assistants.values())


def discover_assistants() -> AssistantRegistry:
    """
    Auto-discover assistants from the assistants/ directory.

    Scans for subdirectories under assistants/ and attempts to import
    ASSISTANT_DESCRIPTOR from each package.
    """
    registry = AssistantRegistry()

    # Get the assistants directory path (at project root, same level as chainlit_bootstrap)
    # __file__ is chainlit_bootstrap/assistants/__init__.py
    # We want to go up to project root, then into assistants/
    project_root = Path(__file__).parent.parent.parent
    assistants_dir = project_root / "assistants"
    if not assistants_dir.exists():
        logger.info(f"Assistants directory not found at {assistants_dir}")
        return registry

    # Scan for subdirectories
    for item in assistants_dir.iterdir():
        if not item.is_dir():
            continue
        if item.name.startswith("_") or item.name.startswith("."):
            continue

        assistant_name = item.name
        module_name = f"assistants.{assistant_name}"

        try:
            module = importlib.import_module(module_name)
            descriptor = getattr(module, "ASSISTANT_DESCRIPTOR", None)

            if descriptor is None:
                logger.warning(
                    f"Module {module_name} does not export ASSISTANT_DESCRIPTOR. Skipping."
                )
                continue

            if not isinstance(descriptor, AssistantDescriptor):
                logger.warning(
                    f"ASSISTANT_DESCRIPTOR in {module_name} is not an AssistantDescriptor instance. "
                    f"Got {type(descriptor)}. Skipping."
                )
                continue

            registry.register(descriptor)

        except ImportError as e:
            logger.warning(f"Failed to import {module_name}: {e}. Skipping.")
        except Exception as e:
            logger.warning(f"Error processing assistant {assistant_name}: {e}. Skipping.")

    return registry

