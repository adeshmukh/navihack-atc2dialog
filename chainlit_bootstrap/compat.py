"""Runtime compatibility helpers for third-party integrations."""

from __future__ import annotations

import importlib
import sys
import types
from typing import Optional

_LANGCHAIN_COMPAT_ALIASES = [
    ("langchain.callbacks.tracers.schemas", "langchain_core.tracers.schemas"),
    ("langchain.load", "langchain_core.load"),
    ("langchain.load.dump", "langchain_core.load.dump"),
    ("langchain.load.load", "langchain_core.load.load"),
    ("langchain.load.mapping", "langchain_core.load.mapping"),
    ("langchain.load.serializable", "langchain_core.load.serializable"),
    ("langchain.schema", "langchain_core.messages"),
]


def _ensure_package(module_name: str) -> Optional[types.ModuleType]:
    if not module_name:
        return None

    existing = sys.modules.get(module_name)
    if existing is not None:
        return existing

    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError:
        module = types.ModuleType(module_name)
        module.__path__ = []  # type: ignore[attr-defined]
        sys.modules[module_name] = module
        parent_name, _, attr = module_name.rpartition(".")
        parent_module = _ensure_package(parent_name)
        if parent_module is not None and attr:
            setattr(parent_module, attr, module)

    return module


def _alias_module(legacy: str, target: str) -> None:
    if legacy in sys.modules:
        return

    try:
        importlib.import_module(legacy)
        return
    except ModuleNotFoundError:
        pass

    target_module = importlib.import_module(target)
    sys.modules[legacy] = target_module

    parent_name, _, attr = legacy.rpartition(".")
    parent_module = _ensure_package(parent_name)
    if parent_module is not None and attr:
        setattr(parent_module, attr, target_module)


def ensure_langchain_compat() -> None:
    """
    Ensure modules that moved during the LangChain v1 re-architecture remain importable.
    """

    for legacy, target in _LANGCHAIN_COMPAT_ALIASES:
        _alias_module(legacy, target)


ensure_langchain_compat()

