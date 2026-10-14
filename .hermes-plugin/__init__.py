"""Superpowers plugin for Hermes Agent.

Registers the stock skills/ tree with Hermes' native skill loader and injects
the using-superpowers bootstrap into the first turn via the pre_llm_call hook.
"""

from __future__ import annotations

import logging
import os
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

BOOTSTRAP_MARKER = "superpowers:using-superpowers bootstrap for hermes"


def _skills_dir() -> str:
    """Locate the stock ``skills/`` tree for either supported install layout.

    Supports two layouts:

    - **git-clone** (``hermes plugins install obra/superpowers``): the plugin
      directory is the repo root, so ``.hermes-plugin/`` and ``skills/`` are
      siblings and this function resolves ``../skills``.
    - **flattened** (plugin files copied to the plugin dir root): ``skills/``
      sits next to this module.

    Raises:
        RuntimeError: if neither layout contains a ``using-superpowers/SKILL.md``.
            A bootstrap that silently skips is how a broken install masquerades
            as a working one.
    """
    here = os.path.dirname(os.path.realpath(__file__))
    candidates = (
        os.path.realpath(os.path.join(here, "..", "skills")),
        os.path.realpath(os.path.join(here, "skills")),
    )
    for cand in candidates:
        if os.path.isfile(os.path.join(cand, "using-superpowers", "SKILL.md")):
            return cand
    raise RuntimeError(
        "superpowers plugin: cannot find the skills/ tree "
        f"(looked at {candidates}). Reinstall with "
        "`hermes plugins install obra/superpowers`."
    )


def _strip_frontmatter(content: str) -> str:
    """Remove YAML frontmatter from *content* and return the stripped body."""
    match = re.match(r"^---\n[\s\S]*?\n---\n([\s\S]*)$", content)
    return (match.group(1) if match else content).strip()


def _frontmatter_value(content: str, key: str) -> str:
    """Return a flat ``key: value`` scalar from a SKILL.md frontmatter block.

    Hermes reads a skill's description from ``register_skill``'s ``description``
    argument, which defaults to ``""``. Registering only the path left every
    stock skill with a blank description in the skill catalogue, so the model
    had nothing to select on. Stock frontmatter is a flat block of single-line
    scalars, so a line scan covers it without a YAML dependency.
    """
    match = re.match(r"^---\n([\s\S]*?)\n---\n", content)
    if not match:
        return ""
    for line in match.group(1).splitlines():
        name, sep, value = line.partition(":")
        if sep and name.strip() == key:
            return value.strip().strip("\"'")
    return ""


def _build_bootstrap(skills_dir: str) -> str:
    """Build the bootstrap context string injected into the first turn.

    Reads the using-superpowers SKILL.md body (frontmatter stripped) and the
    Hermes tool-mapping reference, then wraps them in the EXTREMELY_IMPORTANT
    envelope with the bootstrap marker.

    Args:
        skills_dir: Absolute path to the stock ``skills/`` tree.

    Returns:
        The full bootstrap context string.

    Raises:
        FileNotFoundError: if the using-superpowers SKILL.md or the
            hermes-tools.md reference is missing.
    """
    skill_md_path = os.path.join(skills_dir, "using-superpowers", "SKILL.md")
    with open(skill_md_path, encoding="utf-8") as f:
        body = _strip_frontmatter(f.read())

    tools_path = os.path.join(
        skills_dir, "using-superpowers", "references", "hermes-tools.md"
    )
    with open(tools_path, encoding="utf-8") as f:
        tool_mapping = f.read().strip()

    return (
        f"<EXTREMELY_IMPORTANT>\n"
        f"{BOOTSTRAP_MARKER}\n\n"
        f"You have superpowers.\n\n"
        f"The using-superpowers skill content is included below and is already "
        f"loaded for this Hermes session. Follow it now. "
        f"Do not try to load using-superpowers again.\n\n"
        f"{body}\n\n"
        f"## Loading Superpowers Skills on Hermes\n\n"
        f"Superpowers skills are registered with Hermes' native skill loader: "
        f'invoke one with `skill_view("superpowers:skill-name")` '
        f'(for example `skill_view("superpowers:brainstorming")`). '
        f"If a namespaced lookup returns 'not found', read the skill file "
        f"directly instead:\n"
        f'`read_file("{skills_dir}/skill-name/SKILL.md")`\n\n'
        f"The superpowers skills directory is: `{skills_dir}`\n\n"
        f"{tool_mapping}\n"
        f"</EXTREMELY_IMPORTANT>"
    )


def register(ctx: Any) -> None:
    """Register all stock skills and the pre_llm_call hook with Hermes.

    Walks the ``skills/`` tree, registers every directory containing a
    ``SKILL.md`` with Hermes' native loader (so ``skill_view`` can load them
    on demand), then attaches the ``pre_llm_call`` hook that injects the
    bootstrap into the first turn.

    Args:
        ctx: Hermes plugin context providing ``register_skill`` and
            ``register_hook``.
    """
    skills_dir = _skills_dir()
    bootstrap = _build_bootstrap(skills_dir)

    # Register every stock skill with Hermes' native loader so skill_view can
    # load them on demand. Standard markdown; no conversion (plugin guide).
    # register_skill requires a pathlib.Path — a str raises AttributeError and
    # hermes silently disables the whole plugin (verified 2026-07-23).
    for name in sorted(os.listdir(skills_dir)):
        skill_md = os.path.join(skills_dir, name, "SKILL.md")
        if not os.path.isfile(skill_md):
            continue
        try:
            with open(skill_md, encoding="utf-8") as f:
                description = _frontmatter_value(f.read(), "description")
            ctx.register_skill(name, Path(skill_md), description=description)
        except OSError:
            logger.debug(
                "superpowers: failed to read skill %s at %s",
                name,
                skill_md,
                exc_info=True,
            )
            raise

    # pre_llm_call returning {"context": ...} is the documented injection path
    # (on_session_start return values are ignored, and ctx.inject_message
    # refuses from that hook — verified empirically 2026-07-23). The context is
    # appended to the first turn's user message.
    def pre_llm_call(
        session_id: str | None = None,
        user_message: str | None = None,
        conversation_history: list | None = None,
        is_first_turn: bool | None = None,
        model: str | None = None,
        platform: str | None = None,
        **kwargs: Any,
    ) -> dict[str, str] | None:
        if is_first_turn:
            return {"context": bootstrap}
        return None

    ctx.register_hook("pre_llm_call", pre_llm_call)