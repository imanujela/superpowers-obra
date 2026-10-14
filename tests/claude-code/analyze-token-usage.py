#!/usr/bin/env python3
"""Analyze token usage from Claude Code session transcripts.

Breaks down usage by main session and individual subagents, printing a
per-agent table and aggregate totals with estimated cost.
"""

from __future__ import annotations

import json
import logging
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Cost rates (USD per million tokens).
_INPUT_COST_PER_M = 3.0
_OUTPUT_COST_PER_M = 15.0

_USAGE_FIELDS = (
    "input_tokens",
    "output_tokens",
    "cache_creation",
    "cache_read",
    "messages",
)


def _empty_usage(include_description: bool = False) -> dict[str, Any]:
    """Return a fresh usage dict with all counters zeroed."""
    base: dict[str, Any] = {f: 0 for f in _USAGE_FIELDS}
    if include_description:
        base["description"] = None
    return base


def _accumulate(target: dict[str, Any], usage: dict[str, Any]) -> None:
    """Add *usage* values into *target* in place."""
    for field in _USAGE_FIELDS:
        target[field] += usage.get(field, 0)


def _extract_subagent_description(
    subagent: dict[str, Any], agent_id: str, result: dict[str, Any]
) -> None:
    """Set a subagent's description from the prompt if not already set."""
    if subagent["description"] is not None:
        return
    prompt = result.get("prompt", "")
    first_line = prompt.split("\n")[0] if prompt else f"agent-{agent_id}"
    if first_line.startswith("You are "):
        first_line = first_line[8:]
    subagent["description"] = first_line[:60]


def analyze_main_session(
    filepath: str,
) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    """Analyze a session file and return token usage broken down by agent.

    Args:
        filepath: Path to a JSONL session transcript.

    Returns:
        A ``(main_usage, subagent_usage)`` tuple where *main_usage* is the
        aggregate for the main session and *subagent_usage* maps agent IDs to
        their per-agent usage dicts.
    """
    main_usage = _empty_usage()
    subagent_usage: dict[str, dict[str, Any]] = defaultdict(
        lambda: _empty_usage(include_description=True)
    )

    with open(filepath, encoding="utf-8") as f:
        for line in f:
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                logger.debug(
                    "Skipping malformed JSON line in %s", filepath, exc_info=True
                )
                continue

            # Main session assistant messages.
            if data.get("type") == "assistant" and "message" in data:
                main_usage["messages"] += 1
                msg_usage = data["message"].get("usage", {})
                _accumulate(main_usage, msg_usage)

            # Subagent tool results.
            if data.get("type") == "user" and "toolUseResult" in data:
                result = data["toolUseResult"]
                if "usage" not in result or "agentId" not in result:
                    continue
                agent_id = result["agentId"]
                usage = result["usage"]
                agent = subagent_usage[agent_id]
                _extract_subagent_description(agent, agent_id, result)
                agent["messages"] += 1
                _accumulate(agent, usage)

    return main_usage, dict(subagent_usage)


def format_tokens(n: int) -> str:
    """Format a token count with thousands separators."""
    return f"{n:,}"


def calculate_cost(
    usage: dict[str, Any],
    input_cost_per_m: float = _INPUT_COST_PER_M,
    output_cost_per_m: float = _OUTPUT_COST_PER_M,
) -> float:
    """Calculate estimated cost in dollars.

    Args:
        usage: A usage dict with token counters.
        input_cost_per_m: Cost per million input tokens (including cache).
        output_cost_per_m: Cost per million output tokens.

    Returns:
        Estimated cost in USD.
    """
    total_input = (
        usage["input_tokens"] + usage["cache_creation"] + usage["cache_read"]
    )
    input_cost = total_input * input_cost_per_m / 1_000_000
    output_cost = usage["output_tokens"] * output_cost_per_m / 1_000_000
    return input_cost + output_cost


def _print_agent_row(
    agent_id: str,
    description: str,
    usage: dict[str, Any],
) -> None:
    """Print one table row for an agent."""
    cost = calculate_cost(usage)
    print(
        f"{agent_id:<15} {description:<35} "
        f"{usage['messages']:>5} "
        f"{format_tokens(usage['input_tokens']):>10} "
        f"{format_tokens(usage['output_tokens']):>10} "
        f"{format_tokens(usage['cache_read']):>10} "
        f"${cost:>7.2f}"
    )


def main() -> int:
    """CLI entry point. Returns the exit code."""
    if len(sys.argv) < 2:
        print("Usage: analyze-token-usage.py <session-file.jsonl>")
        return 1

    main_session_file = sys.argv[1]

    if not Path(main_session_file).exists():
        print(f"Error: Session file not found: {main_session_file}")
        return 1

    main_usage, subagent_usage = analyze_main_session(main_session_file)

    print("=" * 100)
    print("TOKEN USAGE ANALYSIS")
    print("=" * 100)
    print()
    print("Usage Breakdown:")
    print("-" * 100)
    print(
        f"{'Agent':<15} {'Description':<35} {'Msgs':>5} "
        f"{'Input':>10} {'Output':>10} {'Cache':>10} {'Cost':>8}"
    )
    print("-" * 100)

    _print_agent_row("main", "Main session (coordinator)", main_usage)

    for agent_id in sorted(subagent_usage):
        usage = subagent_usage[agent_id]
        desc = usage.get("description") or f"agent-{agent_id}"
        _print_agent_row(agent_id, desc, usage)

    print("-" * 100)

    # Aggregate totals.
    total_usage = _empty_usage()
    _accumulate(total_usage, main_usage)
    for usage in subagent_usage.values():
        _accumulate(total_usage, usage)

    total_input = (
        total_usage["input_tokens"]
        + total_usage["cache_creation"]
        + total_usage["cache_read"]
    )
    total_tokens = total_input + total_usage["output_tokens"]
    total_cost = calculate_cost(total_usage)

    print()
    print("TOTALS:")
    print(f"  Total messages:         {format_tokens(total_usage['messages'])}")
    print(f"  Input tokens:           {format_tokens(total_usage['input_tokens'])}")
    print(f"  Output tokens:          {format_tokens(total_usage['output_tokens'])}")
    print(
        f"  Cache creation tokens:  {format_tokens(total_usage['cache_creation'])}"
    )
    print(f"  Cache read tokens:      {format_tokens(total_usage['cache_read'])}")
    print()
    print(f"  Total input (incl cache): {format_tokens(total_input)}")
    print(f"  Total tokens:             {format_tokens(total_tokens)}")
    print()
    print(f"  Estimated cost: ${total_cost:.2f}")
    print(f"  (at ${_INPUT_COST_PER_M}/${_OUTPUT_COST_PER_M} per M tokens for input/output)")
    print()
    print("=" * 100)

    return 0


if __name__ == "__main__":
    sys.exit(main())