# CareerOps Plugin — Development Workspace

This directory is the **plugin source** for CareerOps, a Claude Code plugin that automates schema-driven, fact-traceable resume and cover-letter generation. Everything here is part of the **plugin** itself. Zero user data lives here.

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
careerops/                          ← THIS DIRECTORY (plugin only)
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

~/my-career/                        ← USER DATA (user's own directory)
├── CLAUDE.md                       User's profile, writing preferences
├── career/                         Facts, experiences, projects, applications
├── inbox/                          Raw JDs waiting to be analyzed
└── raw_data/                       Source resumes for seeding
```

**Rule of thumb:**
- If it tells the system **how** to do something → plugin (here)
- If it is **personal information** or **user-supplied data** → user directory
- If it is **user-specific configuration** (theme choice, rule override, profile) → user directory

A new user installs this plugin via `npx careerops install`, then runs `/careerops:setting-up` from their own data directory to populate it from `templates/`.

The `using-careerops` skill is injected at every SessionStart via hook and serves as the bootstrap skill, orienting Claude to the plugin structure and user data directory at the start of each session.

---

## Plugin Conventions

### File and ID Naming

| Entity | Pattern | Example |
|---|---|---|
| Fact | `F-YYYY-<employer-slug>-<3-word-desc>` | `F-2025-acme-1st-50agents` |
| Experience envelope | `X-<employer-slug>-<role-slug>` | `X-acme-senior-dev` |
| Project | `P-<project-slug>` | `P-careerops` |
| Evidence | `E-<fact-id>-<source-slug>` | `E-F-2025-acme-1st-cert` |
| Application | `A-YYYY-MM-DD-<company>-<role>` | `A-2026-01-15-acme-swe` |
| JD analysis | `JD-YYYY-MM-DD-<company>-<role>` | `JD-2026-01-15-acme-swe` |

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

- `<Your Name>` not a real person's name
- `<your-email@example.com>` not real emails
- `<City, Region>` not a real city
- `X-<employer-slug>-<role-slug>` for experience IDs
- `raw_data/<your-resume>.tex` for file paths

If you find real personal data leaking into plugin code, treat it as a bug.

---

## Components Built Into This Plugin

| Component | Count | Location | Purpose |
|---|---|---|---|
| Skills | 13 | `skills/` | User-invocable commands |
| Subagents | 5 | `agents/` | Specialized Claude personas |
| Hooks | 4 | `hooks/hooks.json` | PostToolUse (3), SessionStart (1), UserPromptSubmit (1) |
| Python scripts | 8 | `scripts/` | Validators, linters, status, routing guard |
| JSON schemas | 8 | `schemas/` | Data structure contracts |
| Templates | 6 | `templates/` | Starter files for new users |

### The 13 Skills

| Skill | What it does |
|---|---|
| `/careerops:setting-up` | One-time setup for a new user directory |
| `/careerops:capturing-fact` | Interview to record a new career achievement |
| `/careerops:capturing-evidence` | Attach evidence to an existing fact |
| `/careerops:seeding-career-db` | Bootstrap from a resume or career document |
| `/careerops:analyzing-jd` | Analyze a job description |
| `/careerops:generating-resume` | End-to-end resume generation (includes planning Q&A) |
| `/careerops:auditing-resume` | Re-run semantic auditor |
| `/careerops:humanizing-resume` | Manual AI-marker cleanup |
| `/careerops:logging-outcome` | Record application outcome |
| `/careerops:linting-career` | Schema + ref + em-dash check |
| `/careerops:getting-help` | Full command reference |
| `/careerops:using-careerops` | Bootstrap skill injected at SessionStart via hook |
| `/careerops:rendercv` | External RenderCV skill |

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

## Git

- Branch naming: `feat/<feature-name>`
- Never add Co-Authored-By Claude references in commits.
