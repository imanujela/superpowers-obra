# Superpowers

> **Upgraded fork** by [imanujela](https://github.com/imanujela) — originally built by [Jesse Vincent (obra)](https://github.com/obra). This fork hardens the Python plugin (type hints, logging with `exc_info=True`, narrowed exceptions), tightens shell script safety (`set -euo pipefail` everywhere), and sharpens the Hermes Agent integration. All credit for the methodology and skills design belongs to the original author.

Superpowers is a complete software development methodology for your coding agents, built on top of a set of composable skills and some initial instructions that make sure your agent uses them.

## Installation

### Hermes Agent (primary target for this fork)

```bash
hermes plugins install imanujela/superpowers-obra --enable --force
```

Restart any active Hermes sessions after installing. Note: Hermes has no
post-compaction hook, so a very long session that compacts over its first
turn loses the bootstrap — start a fresh session if skills stop triggering.

### Other harnesses

Installation differs by harness. If you use more than one, install Superpowers separately for each one.

#### Claude Code

Superpowers is available via the [official Claude plugin marketplace](https://claude.com/plugins/superpowers)

##### Official Marketplace

- Install the plugin from Anthropic's official marketplace:

  ```bash
  /plugin install superpowers@claude-plugins-official
  ```

##### Superpowers Marketplace

The Superpowers marketplace provides Superpowers and some other related plugins for Claude Code.

- Register the marketplace:

  ```bash
  /plugin marketplace add obra/superpowers-marketplace
  ```

- Install the plugin from this marketplace:

  ```bash
  /plugin install superpowers@superpowers-marketplace
  ```

#### Antigravity

Install Superpowers as a plugin from this repository:

```bash
agy plugin install https://github.com/imanujela/superpowers-obra
```

Antigravity lists each installed skill's description, and the description of
the `using-superpowers` skill prompts the model to load that skill at the start
of a conversation. Reinstall with the same command to update.

#### Codex App

Superpowers is available via the [official Codex plugin marketplace](https://github.com/openai/plugins).

- In the Codex app, click on Plugins in the sidebar.
- You should see `Superpowers` in the Coding section.
- Click the `+` next to Superpowers and follow the prompts.

#### Codex CLI

Superpowers is available via the [official Codex plugin marketplace](https://github.com/openai/plugins).

- Open the plugin search interface:

  ```bash
  /plugins
  ```

- Search for Superpowers:

  ```bash
  superpowers
  ```

- Select `Install Plugin`.

#### Cursor

- In Cursor Agent chat, install from marketplace:

  ```text
  /add-plugin superpowers
  ```

- Or search for "superpowers" in the plugin marketplace.

#### Devin CLI

- Install the plugin from this repository:

  ```bash
  devin plugins install imanujela/superpowers-obra
  ```

- Update to the latest version with:

  ```bash
  devin plugins update superpowers
  ```

#### Factory Droid

- Register the marketplace:

  ```bash
  droid plugin marketplace add https://github.com/imanujela/superpowers-obra
  ```

- Install the plugin:

  ```bash
  droid plugin install superpowers@superpowers
  ```

#### Gemini CLI

- Install the extension:

  ```bash
  gemini extensions install https://github.com/imanujela/superpowers-obra
  ```

- Update later:

  ```bash
  gemini extensions update superpowers
  ```

#### GitHub Copilot CLI

- Register the marketplace:

  ```bash
  copilot plugin marketplace add obra/superpowers-marketplace
  ```

- Install the plugin:

  ```bash
  copilot plugin install superpowers@superpowers-marketplace
  ```

#### Grok Build CLI

Superpowers is available via the [official Grok plugin marketplace](https://github.com/xai-org/plugin-marketplace).

- Install the plugin from xAI's official marketplace:

  ```bash
  grok plugin install superpowers@xai-official --trust
  ```

- Or open the marketplace in the TUI, search for Superpowers, and install it:

  ```text
  /marketplace
  ```

#### Kimi Code

Superpowers is available in Kimi Code's plugin marketplace.

- Open Kimi Code's plugin manager:

  ```text
  /plugins
  ```

- Go to `Marketplace` > `Superpowers` and install it.

- Or install directly from this repository:

  ```text
  /plugins install https://github.com/imanujela/superpowers-obra
  ```

- Detailed docs: [docs/README.kimi.md](docs/README.kimi.md)

#### OpenCode

OpenCode uses its own plugin install; install Superpowers separately even if you
already use it in another harness.

- Tell OpenCode:

  ```
  Fetch and follow instructions from https://raw.githubusercontent.com/imanujela/superpowers-obra/refs/heads/main/.opencode/INSTALL.md
  ```

- Detailed docs: [docs/README.opencode.md](docs/README.opencode.md)

#### Pi

Install Superpowers as a Pi package from this repository:

```bash
pi install git:github.com/imanujela/superpowers-obra
```

For local development, run Pi with this checkout loaded as a temporary package:

```bash
pi -e /path/to/superpowers-obra
```

The Pi package loads the Superpowers skills and a small extension that injects the `using-superpowers` bootstrap at session startup and again after compaction. Pi has native skills, so no compatibility `Skill` tool is required. Subagent and task-list tools remain optional Pi companion packages.

#### Qwen Code

Qwen Code installs plugins from Claude Code marketplaces directly.

- Install the plugin from this repository, and pick `superpowers` when prompted:

  ```bash
  qwen extensions install imanujela/superpowers-obra
  ```

- Update later:

  ```bash
  qwen extensions update superpowers
  ```

#### Muse

Superpowers is available as a native Muse plugin — same repo, same skills, all harnesses. The `using-superpowers` bootstrap is injected via the native `SessionStart` hook alongside Claude Code, Codex, Cursor, Gemini, Pi, and the rest — no per-session opt-in.

- Install from a local checkout:

  ```bash
  muse plugins install ./
  muse plugins approve superpowers
  ```

  Or clone and install:

  ```bash
  git clone https://github.com/imanujela/superpowers-obra.git
  muse plugins install ./superpowers-obra
  muse plugins approve superpowers
  ```

- Update later:

  ```bash
  muse plugins update superpowers
  ```

Restart any active Muse sessions after installing so the `SessionStart` hook takes effect — skills are active immediately, hooks require approval on first install. To verify, start a fresh session and send `Let's make a react todo list` — a working install auto-triggers `brainstorming` before any code is written. Version is tracked in `.version-bump.json` so `scripts/bump-version.sh` keeps it in sync.

---

## What Changed in This Fork (v8.0.0)

**12 files changed, 418 insertions, 217 deletions** vs upstream v7.0.0.

### Python Plugin (`.hermes-plugin/__init__.py`)

The Hermes plugin bootstrap that registers all 15 skills and injects the `using-superpowers` context on the first turn.

- **Type hints** on every function: `str | None`, `dict[str, str] | None`, `list | None`, `bool | None`, `Any` for the context object
- **Logging module** added (`logger = logging.getLogger(__name__)`) with `logger.debug(exc_info=True)` on skill read failures instead of silent propagation
- **Google-style docstrings** on all functions (`_skills_dir`, `_strip_frontmatter`, `_frontmatter_value`, `_build_bootstrap`, `register`, `pre_llm_call`)
- **Defensive `continue`** guard before attempting to read a SKILL.md that may not exist
- **`from __future__ import annotations`** for clean union type syntax on Python 3.9+

### Token Usage Analyzer (`tests/claude-code/analyze-token-usage.py`)

- **Narrowed** bare `except Exception: pass` → `except json.JSONDecodeError` with `logger.debug(exc_info=True)` — malformed JSON lines are now logged, not silently swallowed
- **Extracted helpers**: `_empty_usage()`, `_accumulate()`, `_extract_subagent_description()`, `_print_agent_row()` — removed copy-paste accumulation logic
- **Module-level constants**: `_INPUT_COST_PER_M`, `_OUTPUT_COST_PER_M`, `_USAGE_FIELDS` — no more magic numbers inline
- **Type hints** throughout
- **`main()` returns exit code** instead of calling `sys.exit()` directly — testable

### Test Suite (`tests/hermes/`)

- Type hints on all test methods and fixtures across `conftest.py`, `test_bootstrap.py`, `test_plugin.py`
- Improved docstrings on conftest fixtures and test classes
- Defensive `assert spec is not None` and `assert spec.loader is not None` on importlib calls

### Shell Scripts

| File | Change |
|------|--------|
| `skills/brainstorming/scripts/start-server.sh` | Added `set -euo pipefail` |
| `skills/brainstorming/scripts/stop-server.sh` | Added `set -euo pipefail`, defaulted `SESSION_DIR="${1:-}"` |
| `skills/systematic-debugging/find-polluter.sh` | Upgraded `set -e` → `set -euo pipefail` |

### Bootstrap Skill (`skills/using-superpowers/SKILL.md`)

- Tightened prose throughout (removed redundant "Superpowers'" prefix from skill references)
- Added `SOUL.md` to the User Instructions list alongside `CLAUDE.md`, `AGENTS.md`, `GEMINI.md`

### Hermes Tools Reference (`skills/using-superpowers/references/hermes-tools.md`)

This file is injected verbatim into the first-turn bootstrap for Hermes sessions.

- Added `skills_list()`, `skill_manage`, `memory`, `browser_exec` mappings
- Changed "Find files by name" from `terminal with find` → `search_files with target='files'` (native Hermes tool)
- Cleaned up `delegate_task` signature

### Fork Metadata

- `README.md`: fork notice with attribution to obra, all URLs updated to `imanujela/superpowers-obra`
- `plugin.yaml`: version `7.0.0` → `8.0.0`, author updated

### Files Changed

1. `.hermes-plugin/__init__.py`
2. `.hermes-plugin/plugin.yaml`
3. `README.md`
4. `skills/brainstorming/scripts/start-server.sh`
5. `skills/brainstorming/scripts/stop-server.sh`
6. `skills/systematic-debugging/find-polluter.sh`
7. `skills/using-superpowers/SKILL.md`
8. `skills/using-superpowers/references/hermes-tools.md`
9. `tests/claude-code/analyze-token-usage.py`
10. `tests/hermes/conftest.py`
11. `tests/hermes/test_bootstrap.py`
12. `tests/hermes/test_plugin.py`

---

## How it works

It starts from the moment you fire up your coding agent. As soon as it sees that you're building something, it *doesn't* just jump into trying to write code. Instead, it steps back and asks you what you're really trying to do. 

Once it's teased a spec out of the conversation, it shows it to you in chunks short enough to actually read and digest. 

After you've signed off on the design, your agent puts together an implementation plan that's clear enough for an enthusiastic junior engineer with poor taste, no judgement, no project context, and an aversion to testing to follow. It emphasizes true red/green TDD, YAGNI (You Aren't Gonna Need It), and DRY. 

Next up, once you say "go", it launches a *subagent-driven-development* process, having agents work through each engineering task, inspecting and reviewing their work, and continuing forward. It's not uncommon for your agent to work autonomously for a couple hours at a time without deviating from the plan you put together.

There's a bunch more to it, but that's the core of the system. And because the skills trigger automatically, you don't need to do anything special. Your coding agent just has Superpowers.

## The Basic Workflow

1. **brainstorming** - Activates before building anything. Draws out what you actually want, and why, through questions that get you describing it, then plays its understanding back for correction. Small changes get agreed in chat; projects get a written design document a builder could plan from.

2. **using-git-worktrees** - Activates after design approval. Creates isolated workspace on new branch, runs project setup, verifies clean test baseline.

3. **writing-plans** - Activates with approved design. Breaks work into bite-sized tasks (2-5 minutes each). Every task has exact file paths, complete code, verification steps.

4. **subagent-driven-development** or **executing-plans** - Activates with plan. Either dispatches a fresh subagent per task with a review after each (most thorough), or implements every task inline in the current session with one fresh review of the whole branch at the end (cheapest).

5. **test-driven-development** - Activates during implementation. Enforces RED-GREEN-REFACTOR: write failing test, watch it fail, write minimal code, watch it pass, commit. Deletes code written before tests.

6. **requesting-code-review** - Activates between tasks. Reviews against plan, reports issues by severity. Critical issues block progress.

7. **finishing-a-development-branch** - Activates when tasks complete. Verifies tests, presents options (merge/PR/keep/discard), cleans up worktree.

**The agent checks for relevant skills before any task.** Mandatory workflows, not suggestions.

## When Something Goes Wrong

Sometimes a session misbehaves: a skill fires when it shouldn't, stays silent when it should, or the agent ignores its plan, repeats work, or burns more tokens than you'd expect. Ask your coding agent to "figure out what went wrong with superpowers in this session" and it will invoke the **diagnosing-superpowers** skill. To examine an earlier session, name it: "figure out what went wrong with superpowers in session `<id>`".

The skill reads the session transcript, reports what happened with line-level evidence, and, if you want, packages a scrubbed bundle for a bug report.

## Community

Superpowers is built by [Jesse Vincent](https://blog.fsck.com) and the rest of the folks at [Prime Radiant](https://primeradiant.com).

- **Discord**: [Join us](https://discord.gg/35wsABTejz) for community support, questions, and sharing what you're building with Superpowers
- **Issues**: https://github.com/imanujela/superpowers-obra/issues
- **Release announcements**: [Sign up](https://primeradiant.com/superpowers/) to get notified about new versions

## What's Inside

### Skills Library

**Testing**
- **test-driven-development** - RED-GREEN-REFACTOR cycle (includes testing anti-patterns reference)

**Debugging**
- **systematic-debugging** - 4-phase root cause process (includes root-cause-tracing, defense-in-depth, condition-based-waiting techniques)
- **verification-before-completion** - Ensure it's actually fixed
- **diagnosing-superpowers** - Work out what went wrong in a session, with evidence; export a scrubbed bundle or file an issue

**Collaboration** 
- **brainstorming** - Drawing out intent before building
- **writing-plans** - Detailed implementation plans
- **executing-plans** - Inline plan execution: one context, one final review
- **dispatching-parallel-agents** - Concurrent subagent workflows
- **requesting-code-review** - Pre-review checklist
- **receiving-code-review** - Responding to feedback
- **using-git-worktrees** - Parallel development branches
- **finishing-a-development-branch** - Merge/PR decision workflow
- **subagent-driven-development** - Fast iteration with two-stage review (spec compliance, then code quality)

**Meta**
- **writing-skills** - Create new skills following best practices (includes testing methodology)
- **using-superpowers** - Introduction to the skills system

## Philosophy

- **Test-Driven Development** - Write tests first, always
- **Systematic over ad-hoc** - Process over guessing
- **Complexity reduction** - Simplicity as primary goal
- **Evidence over claims** - Verify before declaring success

Read [the original release announcement](https://blog.fsck.com/2025/10/09/superpowers/).

## Contributing

The general contribution process for Superpowers is below. Keep in mind that we don't generally accept contributions of new skills and that any updates to skills must work across all of the coding agents we support.

1. Fork the repository
2. Switch to the 'dev' branch
3. Create a branch for your work
4. Follow the `writing-skills` skill for creating and testing new and modified skills
5. Submit a PR, being sure to fill in the pull request template.

Skill-behavior tests use the drill eval harness from [superpowers-evals](https://github.com/prime-radiant-inc/superpowers-evals/), cloned into `evals/` — see `evals/README.md` for setup. Plugin-infrastructure tests live at `tests/` and run via the relevant `run-*.sh` or `npm test`.

See `skills/writing-skills/SKILL.md` for the complete guide.

## Updating

Superpowers updates are somewhat coding-agent dependent, but are often automatic.

## License

MIT License - see LICENSE file for details

## Visual companion telemetry

Because skills and plugins don't provide any feedback to creators, we have no idea how many of you are using Superpowers. By default, the Prime Radiant logo on brainstorming's optional visual companion feature is loaded from our website. It includes the version of Superpowers in use. It does not include any details about your project, prompt, or coding agent. We don't see your clicks or anything about what you're building. This helps us have a rough idea of how many folks are using Superpowers and which version of Superpowers they're using. It's 100% optional. To disable this, set the environment variable `SUPERPOWERS_DISABLE_TELEMETRY` to any true value. Superpowers also honors Claude Code's `DISABLE_TELEMETRY` and `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` opt-outs.
