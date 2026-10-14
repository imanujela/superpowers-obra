"""Shared pytest fixtures for the Hermes plugin test suite."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_ctx() -> Any:
    """Return a MagicMock simulating the Hermes plugin context.

    Mimics ``register_hook`` and ``register_skill`` with the same fidelity
    constraints as the real Hermes API:

    - ``register_skill`` calls ``path.exists()`` internally, which breaks on a
      bare ``str`` (the bug that silently disabled the whole plugin,
      2026-07-23). Keeping that fidelity means a regression to ``str`` paths
      fails these tests instead of failing silently inside Hermes.
    """
    ctx = MagicMock()
    ctx._hooks: dict[str, Any] = {}
    ctx._skills: dict[str, Path] = {}
    ctx._descriptions: dict[str, str] = {}

    def register_hook(event: str, fn: Any) -> None:
        ctx._hooks[event] = fn

    def register_skill(
        name: str,
        path: Path,
        description: str = "",
        frontmatter: Any = None,
    ) -> None:
        if not isinstance(path, Path):
            raise AttributeError(
                f"register_skill requires a pathlib.Path, got {type(path).__name__}"
            )
        ctx._skills[name] = path
        ctx._descriptions[name] = description

    ctx.register_hook.side_effect = register_hook
    ctx.register_skill.side_effect = register_skill
    return ctx