# CareerOps Plugin — Development Workspace

This directory is the **plugin development workspace** for CareerOps, a Claude Code plugin that automates schema-driven, fact-traceable resume and cover-letter generation. Everything here is part of the **plugin** itself. Zero user data lives here.

If you are a new Claude session opening this directory: read this file end to end before touching anything.

---

## Hard Rules (apply to every output from this plugin)

1. **EM-DASHES ARE FORBIDDEN.** Zero tolerance for U+2014 (—), U+2015 (―), U+2E3A (⸺), U+2E3B (⸻). En-dash (–) is allowed only in date/number ranges. Use commas, semicolons, parentheses, or sentence restructuring instead. Enforced at every layer: subagent prompts, Python validator, YAML linter, hooks, auditor scan.
2. **No fabrication.** Every resume bullet must trace to a verified fact embedded in the user's `career/experiences/X-*.yaml` files (under the `facts[]` array in each experience envelope), which live in their data directory, not here. The linter enforces this mechanically.
3. **Dates and employers are immutable.** Schema-locked. Never change a fact's `when:` or `employer:` field, regardless of JD.
4. **Tier 2 reframing only with explicit user opt-in per application.** Subagents default to strict-fact-mode if `user_overrides.yaml` is absent or empty.
5. **Encapsulation requires user approval.** The bullet-composer agent proposes a presentation plan (expand/compress/merge/drop); the user approves before render. Current role is never dropped or below 3 bullets.

---

## Architecture: Plugin vs User Directory

```
P:\CareerOps\                       ← THIS DIRECTORY (plugin only)
├── .claude-plugin/plugin.json
├── skills/                         How Claude does each operation
├── agents/                         Specialized subagents
├── hooks/hooks.json                Event-driven automation
├── scripts/                        Python validators (path-agnostic)
├── schemas/                        JSON schemas (data contracts)
├── config/default-rules.yaml       Default rules (em-dash, page budgets)
├── templates/                      Starter files copied into new user dirs
├── docs/                           Specs, plans, architecture
├── CLAUDE.md                       This file
└── README.md                       Plugin documentation

P:\Resumes\Claude-automations\      ← USER DATA (Kalhar's personal directory)
├── CLAUDE.md                       User's profile, writing preferences
├── career/                         Facts, experiences, projects, applications
├── inbox/                          Raw JDs waiting to be analyzed
├── raw_data/                       Source resumes for seeding
└── Master_Career_Document.md       User's canonical career doc
```

**Rule of thumb:**
- If it tells the system **how** to do something → plugin (here)
- If it is **personal information** or **user-supplied data** → user directory (other)
- If it is **user-specific configuration** (theme choice, rule override, profile) → user directory

A fresh user installs this plugin via `claude --plugin-dir P:\CareerOps` from their own data directory, then runs `/careerops:setting-up` to populate it from `templates/`.

The `using-careerops` skill is injected at every SessionStart via hook and serves as the bootstrap skill, orienting Claude to the plugin structure and user data directory at the start of each session.

---

## Current State (2026-05-13)

**Phase:** Pre-migration. The plugin is being lifted out of `P:\Resumes\Claude-automations\` (the legacy location where plugin code and user data were mixed together).

**What lives here right now:** Only documentation. The actual skills, agents, scripts, schemas, and hooks are still in the legacy location and will be migrated per the plan.

**Active plan:** `docs/superpowers/plans/2026-05-13-careerops-plugin-restructure.md` (11 tasks, ordered for safe migration with rollback at every step)

**Done:**
- Created this directory and docs scaffold
- Wrote the restructure plan
- Investigated and catalogued every user-specific contamination in the legacy plugin code (6 skill files, 2 agent files, 4 Python scripts hardcoded paths, `render_cover_letter.py` had a Kalhar Pandya fallback)
- Confirmed memory directory stays valid (user directory path is unchanged)

**Next:** Execute the restructure plan, task by task. See "Execution" section below.

---

## Plugin Conventions

### File and ID Naming

| Entity | Pattern | Example |
|---|---|---|
| Fact | `F-YYYY-<employer-slug>-<3-word-desc>` | `F-2025-deloitte-1st-50agents` |
| Experience envelope | `X-<employer-slug>-<role-slug>` | `X-oracle-research-coop` |
| Project | `P-<project-slug>` | `P-careerops` |
| Evidence | `E-<fact-id>-<source-slug>` | `E-F-2025-deloitte-1st-cert` |
| Application | `A-YYYY-MM-DD-<company>-<role>` | `A-2026-05-12-procogia-ai-intern` |
| JD analysis | `JD-YYYY-MM-DD-<company>-<role>` | `JD-2026-05-12-procogia-ai-intern` |

### Skill Namespace

All skills are namespaced under the plugin once installed: `/careerops:capturing-fact`, `/careerops:generating-resume`, etc.

### Path Resolution

Python scripts must use `Path.cwd()` (or `CAREEROPS_DATA_DIR` env var) to find the user data directory. **Never hardcode absolute paths.** Helper at `scripts/_paths.py`:

```python
from _paths import data_root, career_dir
```

Hook commands reference plugin files via `${CLAUDE_PLUGIN_ROOT}`:

```json
{ "command": "python \"${CLAUDE_PLUGIN_ROOT}/scripts/lint_yaml.py\" \"$CLAUDE_FILE_PATHS\"" }
```

### Examples in Skills and Agents

When writing examples inside `skills/**/SKILL.md` or `agents/*.md`, use **generic placeholders**, never real personal data:

- `<Your Name>` not `Kalhar Pandya`
- `<your-email@example.com>` not real emails
- `<City, Region>` not `Vancouver, BC`
- `X-<employer-slug>-<role-slug>` not `X-kfin-senior-dev`
- `raw_data/<your-resume>.tex` not the actual filename

If you find a real name leaking into plugin code, treat it as a bug.

---

## Components Built Into This Plugin

| Component | Count | Location | Purpose |
|---|---|---|---|
| Skills | 13 | `skills/` | User-invocable commands |
| Subagents | 5 | `agents/` | Specialized Claude personas |
| Hooks | 4 | `hooks/hooks.json` | PostToolUse (3), SessionStart (1) |
| Python scripts | 6 | `scripts/` | Validators, linters, dashboards |
| JSON schemas | 8 | `schemas/` | Data structure contracts |
| Templates | 6 | `templates/` | Starter files for new users |

### The 13 Skills

| Skill | What it does |
|---|---|
| `/careerops:setting-up` | One-time setup for a new user directory |
| `/careerops:capturing-fact` | Interview to record a new career achievement |
| `/careerops:capturing-evidence` | Attach evidence to an existing fact |
| `/careerops:seeding-career-db` | Bootstrap from Master_Career_Document.md or LaTeX resume |
| `/careerops:analyzing-jd` | Analyze a job description |
| `/careerops:generating-resume` | End-to-end resume generation (includes planning Q&A) |
| `/careerops:auditing-resume` | Re-run semantic auditor |
| `/careerops:humanizing-resume` | Manual AI-marker cleanup |
| `/careerops:logging-outcome` | Record application outcome |
| `/careerops:linting-career` | Schema + ref + em-dash check |
| `/careerops:getting-help` | Full command reference |
| `/careerops:using-careerops` | Bootstrap skill injected at SessionStart via hook |
| `/careerops:rendercv` | External RenderCV skill |

> Note: The DB health summary is no longer a standalone skill; it now runs automatically via the SessionStart hook (`session_start.py`). Pre-generation planning Q&A is absorbed into `/careerops:generating-resume`.

### The 5 Subagents

| Agent | Role |
|---|---|
| `fact-curator` | Interactive interviewer for capturing new facts |
| `jd-analyzer` | Parses JDs into structured YAML with verbatim keywords |
| `bullet-composer` | Proposes presentation plan, composes bullets, writes claim ledger |
| `cover-letter-composer` | Generates tailored cover letters |
| `resume-auditor` | Semantic quality pass, AI-marker scan, verdict |

---

## Technology Decisions (locked)

| Concern | Choice |
|---|---|
| Renderer | RenderCV (Typst). `rendercv render <input.yaml> --output-folder <absolute-path>` |
| Career data | Flat YAML files in user directory. No SQLite. |
| JD analysis | Pure Claude subagent (`jd-analyzer`). No ESCO/SkillNER. |
| Validation | Two-stage: Python validators (8 gates) + Claude semantic auditor |
| Capture | Interactive subagent (`fact-curator`) via `/careerops:capturing-fact` |
| Version registry | One YAML folder per application under `career/applications/` |

---

## Execution

The restructure plan is at `docs/superpowers/plans/2026-05-13-careerops-plugin-restructure.md`.

To execute, use either:
- **Subagent-driven** (`superpowers:subagent-driven-development`): fresh subagent per task with review between tasks (recommended for safety)
- **Inline** (`superpowers:executing-plans`): batch execution in current session with checkpoints

Until the migration is run, the actual plugin code (skills, agents, scripts) still lives at `P:\Resumes\Claude-automations\`. Read from there when investigating; write changes here.

---

## Git

This directory is not yet a git repo. Once initialized:
- Branch naming: `feat/kalhar-<feature>`
- Commit prefix: `Kalhar: <message>`
- Never add Co-Authored-By Claude references.
