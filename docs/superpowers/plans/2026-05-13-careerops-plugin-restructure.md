# CareerOps Plugin Restructure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restructure CareerOps from a mixed standalone project into a clean Claude Code plugin at `P:\CareerOps\` plus a user data directory at `P:\Resumes\Claude-automations\` (its current location, with plugin pieces stripped out). Zero user information lives inside the plugin; no plugin instructions live inside the user directory.

**Architecture:** Two completely separate top-level folders. The **plugin** (`P:\CareerOps\`) holds all behavior (skills, agents, hooks, scripts, schemas, conventions) and is its own publishable artifact. The **user directory** (`P:\Resumes\Claude-automations\`) holds only personal data (`career/`, `inbox/`, `raw_data/`, `Master_Career_Document.md`), user overrides (`career/config/`), and a personal CLAUDE.md with profile/preferences only. The plugin is installed via `claude --plugin-dir P:\CareerOps` from the user directory and skills are invoked with namespace `/careerops:<name>`. Python scripts read paths from `cwd` (the user directory) rather than hardcoded absolute paths.

**Tech Stack:** Claude Code plugin system, Python 3 (validators), RenderCV/Typst (rendering), YAML (data), JSON Schema (validation).

---

## Target Directory Structure

### Plugin (`P:\CareerOps\` — new, populated from current dir)

```
P:\CareerOps\
├── .claude-plugin/
│   └── plugin.json                 Plugin manifest
├── skills/                         15 skills, examples genericized
│   ├── capture-fact/SKILL.md
│   ├── capture-evidence/SKILL.md
│   ├── career-help/SKILL.md
│   ├── career-init/SKILL.md
│   ├── career-status/SKILL.md
│   ├── generate-resume/SKILL.md
│   ├── humanize-resume/SKILL.md
│   ├── ingest-jd/SKILL.md
│   ├── lint-career/SKILL.md
│   ├── log-outcome/SKILL.md
│   ├── plan-resume/SKILL.md
│   ├── audit-resume/SKILL.md
│   ├── seed-from-master/SKILL.md
│   ├── seed-from-tex/SKILL.md
│   └── rendercv/                   External skill, untouched
├── agents/                         5 agents, names genericized
│   ├── bullet-composer.md
│   ├── cover-letter-composer.md
│   ├── fact-curator.md
│   ├── jd-analyzer.md
│   └── resume-auditor.md
├── hooks/
│   └── hooks.json                  Migrated from .claude/settings.json
├── scripts/                        Path-agnostic Python validators
│   ├── career_status.py
│   ├── check_em_dashes.py
│   ├── lint_yaml.py
│   ├── render_cover_letter.py
│   ├── secret_scan.py
│   └── validate_resume.py
├── schemas/                        8 JSON schemas (unchanged)
├── config/
│   └── default-rules.yaml          Default plugin rules (em-dash policy etc.)
├── templates/                      Starter files copied by /career-init
│   ├── contact.yaml.example
│   ├── edu.yaml.example
│   ├── skills.yaml.example
│   ├── rules.yaml.example
│   ├── rendercv-theme.yaml.example
│   └── user-CLAUDE.md.template
├── docs/                           Plugin documentation
├── CLAUDE.md                       Plugin-internal policy (em-dash, no fabrication, etc.)
└── README.md                       Plugin installation + usage
```

### User Directory (`P:\Resumes\Claude-automations\` — current location, plugin pieces removed)

```
P:\Resumes\Claude-automations\
├── CLAUDE.md                       Kalhar's profile + writing prefs ONLY (no how-to)
├── career/                         All user data
│   ├── facts/                      F-*.yaml (61 files)
│   ├── experiences/                X-*.yaml (14 files)
│   ├── projects/                   P-*.yaml (3 files)
│   ├── evidence/                   E-*.yaml (empty for now)
│   ├── contact/contact.yaml
│   ├── education/edu.yaml
│   ├── skills/skills.yaml
│   ├── applications/               A-* folders (1 application so far)
│   ├── jd-analysis/                JD-*.yaml (1 file)
│   └── config/
│       ├── rules.yaml              Overrides plugin defaults if desired
│       ├── rendercv-theme.yaml     Theme choice (engineeringresumes)
│       └── cover-letter-template.typ
├── inbox/                          User-supplied JDs
├── raw_data/                       LaTeX source resumes
└── Master_Career_Document.md       Kalhar's canonical doc
```

---

## Path Resolution Strategy

All Python scripts use `Path.cwd()` as the user-data root. Claude Code invokes hooks from the project working directory, so when the user runs Claude from `my-career/`, scripts resolve `career/`, `inbox/` etc. relative to that. The plugin's own files are resolved via `${CLAUDE_PLUGIN_ROOT}` in `hooks/hooks.json`.

Optional override: a `CAREEROPS_DATA_DIR` env var, used only if set.

---

## Task 1: Create the Plugin Manifest

**Files:**
- Create: `.claude-plugin/plugin.json`

- [ ] **Step 1: Create `.claude-plugin/` directory and manifest**

Write `.claude-plugin/plugin.json`:

```json
{
  "name": "careerops",
  "description": "Schema-driven, fact-traceable resume and cover-letter automation",
  "version": "1.0.0",
  "author": {
    "name": "Kalhar Pandya"
  },
  "homepage": "https://github.com/KalharPandya/careerops",
  "license": "MIT"
}
```

- [ ] **Step 2: Verify**

Run: `Test-Path .claude-plugin/plugin.json`
Expected: `True`

---

## Task 2: Make Python Scripts Path-Agnostic

**Files:**
- Modify: `scripts/career_status.py:9`
- Modify: `scripts/lint_yaml.py:14`
- Modify: `scripts/validate_resume.py:31`
- Modify: `scripts/check_em_dashes.py:23`
- Modify: `scripts/render_cover_letter.py:18,95`

Each script currently hardcodes `Path('P:/Resumes/Claude-automations')`. Replace with a helper that reads from `cwd` or `CAREEROPS_DATA_DIR`.

- [ ] **Step 1: Create a shared path helper**

Create `scripts/_paths.py`:

```python
"""Shared path resolution for CareerOps scripts.

The user-data directory is wherever Claude Code is invoked from (cwd),
unless CAREEROPS_DATA_DIR is set explicitly.
"""
from pathlib import Path
import os

def data_root() -> Path:
    env = os.environ.get("CAREEROPS_DATA_DIR")
    if env:
        return Path(env).resolve()
    return Path.cwd().resolve()

def career_dir() -> Path:
    return data_root() / "career"
```

- [ ] **Step 2: Update `scripts/career_status.py`**

Replace line 9:

```python
# OLD: CAREER_DIR = Path('P:/Resumes/Claude-automations/career')
from _paths import career_dir
CAREER_DIR = career_dir()
```

- [ ] **Step 3: Update `scripts/lint_yaml.py`**

Replace line 14:

```python
# OLD: PROJECT_ROOT = Path('P:/Resumes/Claude-automations')
from _paths import data_root
PROJECT_ROOT = data_root()
```

- [ ] **Step 4: Update `scripts/validate_resume.py`**

Replace line 31:

```python
# OLD: PROJECT_ROOT = Path('P:/Resumes/Claude-automations')
from _paths import data_root
PROJECT_ROOT = data_root()
```

- [ ] **Step 5: Update `scripts/check_em_dashes.py`**

Replace line 23 inside `report_path`:

```python
# OLD: rel = path.relative_to(Path('P:/Resumes/Claude-automations'))
from _paths import data_root
rel = path.relative_to(data_root())
```

- [ ] **Step 6: Update `scripts/render_cover_letter.py`**

Replace line 18:

```python
# OLD: PROJECT_ROOT = Path('P:/Resumes/Claude-automations')
from _paths import data_root
PROJECT_ROOT = data_root()
```

And line 95 — remove the `'Kalhar Pandya'` fallback (force read from contact.yaml):

```python
# OLD: name = contact.get('name', 'Kalhar Pandya')
name = contact.get('name')
if not name:
    raise ValueError("contact.yaml missing required 'name' field")
```

- [ ] **Step 7: Smoke-test the scripts from the project root**

Run: `python scripts/career_status.py`
Expected: Same dashboard output as before, no hardcoded-path errors.

Run: `python scripts/lint_yaml.py career/facts/F-2025-deloitte-1st-50agents.yaml`
Expected: passes (or expected warning) for a known-good file.

---

## Task 3: De-contaminate Skill Files

Remove every Kalhar-specific reference from skills, replacing with placeholders or generic examples.

**Files (8 skills with contamination):**
- Modify: `.claude/skills/career-init/SKILL.md:74,77`
- Modify: `.claude/skills/career-help/SKILL.md:40`
- Modify: `.claude/skills/generate-resume/SKILL.md:100,175,177,182,187,188,189`
- Modify: `.claude/skills/seed-from-master/SKILL.md:47,133`
- Modify: `.claude/skills/seed-from-tex/SKILL.md:12,136`
- Modify: `.claude/skills/plan-resume/SKILL.md:52`

- [ ] **Step 1: `career-init/SKILL.md` — generalize examples**

Line 74: change `"Vancouver, BC"` to `"<City, Region>"`.
Line 77: change `KalharPandya` to `<your-github-handle>`.

- [ ] **Step 2: `career-help/SKILL.md` — generic example path**

Line 40: change `Example: /seed-from-tex raw_data/Kalhar-Resume-September-2025.tex` to `Example: /seed-from-tex raw_data/your-resume.tex`.

- [ ] **Step 3: `generate-resume/SKILL.md` — RenderCV output naming**

Line 100: change `X-kfin-senior-dev` example to `X-<employer-slug>-<role-slug>`.

Lines 175-189 reference `Kalhar_Pandya_CV.pdf` (RenderCV's output filename derived from `cv.name`). Generalize:

```
On success, RenderCV writes `<Name>_CV.pdf` (named from `cv.name`). Rename it:
career/applications/<app-id>/<Name>_CV.pdf  →  career/applications/<app-id>/resume.pdf
career/applications/<app-id>/<Name>_CV.typ  →  career/applications/<app-id>/resume.typ
```

- [ ] **Step 4: `seed-from-master/SKILL.md` — generic role examples**

Line 47: change `Oracle Labs` → `<Company Name>` and `Research Assistant CO-OP` → `<Role Title>` in slugging examples.
Line 133: change `Oracle CO-OP + ConsentKeys` → `two concurrent roles`.

- [ ] **Step 5: `seed-from-tex/SKILL.md` — generic filenames**

Line 12: change `raw_data/Kalhar-Resume-September-2025.tex` → `raw_data/<your-resume>.tex`.
Line 136: change comment template to `<!-- Migrated: raw_data/<your-resume>.tex on YYYY-MM-DD -->`.

- [ ] **Step 6: `plan-resume/SKILL.md` — generic research example**

Line 52: change `'research' — Tanha lab, IEEE paper, Northeastern ML coursework` to `'research' — academic or industry research positions`.

- [ ] **Step 7: Verify**

Run: `Select-String -Path .claude/skills/**/SKILL.md -Pattern "Kalhar|pandyakalhar|Vancouver|Northeastern|Oracle|KalharPandya|kfin|VaultAI|FlytBase"`
Expected: no matches (or only matches inside code blocks that document generic syntax).

---

## Task 4: De-contaminate Agent Files

**Files (3 agents with contamination):**
- Modify: `.claude/agents/bullet-composer.md:97,186`
- Modify: `.claude/agents/resume-auditor.md:91`

- [ ] **Step 1: `bullet-composer.md` — strip Kalhar from examples**

Line 97: change `role_ref: X-kfin-senior-dev` example to `role_ref: X-<employer-slug>-<role-slug>`.
Line 186: change `name: Kalhar Pandya` to `name: <read from career/contact/contact.yaml>`.

- [ ] **Step 2: `resume-auditor.md` — generic candidate reference**

Line 91: change `does this resume present Kalhar as a strong candidate` to `does this resume present the candidate as a strong fit`.

- [ ] **Step 3: Verify**

Run: `Select-String -Path .claude/agents/*.md -Pattern "Kalhar|pandyakalhar"`
Expected: no matches.

---

## Task 5: Split CLAUDE.md into Plugin and User Versions

The current root `CLAUDE.md` mixes plugin policy (em-dash ban, no fabrication, schema rules) with Kalhar's profile (name, email, target roles, experience list). Split into two files.

**Files:**
- Modify: `CLAUDE.md` (becomes plugin policy only)
- Create: `templates/user-CLAUDE.md.template` (template for user dir)

- [ ] **Step 1: Identify split lines**

Read current `CLAUDE.md`. Sections to keep in plugin CLAUDE.md:
- Hard Rules (em-dash ban, no fabrication, dates immutable, Tier 2 opt-in, encapsulation approval)
- What Is Built (architecture overview)
- Technology Decisions (RenderCV, flat YAML, JD subagent, etc.)

Sections to move out:
- "Kalhar's Profile" section (lines 21-29) — name, email, location, target roles, experience list, education, highlights
- "Current Phase" section — references Kalhar's specific seed file
- Final "Git" section that references Kalhar's branch naming convention

- [ ] **Step 2: Rewrite root `CLAUDE.md` as plugin policy only**

Strip the "Kalhar's Profile" and "Current Phase" sections. Keep all hard rules and architecture docs, but use generic placeholders where needed.

- [ ] **Step 3: Create `templates/user-CLAUDE.md.template`**

```markdown
# <Your Name> — Career Project

## Profile
- **Name:** <Your Full Name>
- **Email (resume):** <your-email>
- **Location:** <City, Region>
- **Target roles:** <Role 1, Role 2, Role 3>
- **Key experience:** <Company 1, Company 2, ...>
- **Education:** <Highest degree, institution>
- **Highlights:** <Top 1-3 differentiators>

## Writing Preferences
<Optional: tone, voice, words to avoid, words to favor>

## Project Notes
<Optional: ongoing job-search context, deadlines, target companies>
```

- [ ] **Step 4: Verify**

Run: `Select-String -Path CLAUDE.md -Pattern "Kalhar|pandyakalhar|Vancouver|Oracle"`
Expected: no matches in CLAUDE.md.

---

## Task 6: Create Template Files for User Bootstrap

**Files:**
- Create: `templates/contact.yaml.example`
- Create: `templates/edu.yaml.example`
- Create: `templates/skills.yaml.example`
- Create: `templates/rules.yaml.example`
- Create: `templates/rendercv-theme.yaml.example`

- [ ] **Step 1: Copy existing user files as templates with values genericized**

Read `career/contact/contact.yaml`, write `templates/contact.yaml.example` with placeholders:

```yaml
name: <Your Full Name>
location: <City, Region>
email: <your-email@example.com>
phone: <+1-555-555-5555>
website: <https://your-website.com>
linkedin: <your-linkedin-handle>
github: <your-github-handle>
```

Repeat for `edu.yaml`, `skills.yaml`, `rules.yaml`, `rendercv-theme.yaml` — strip values, keep schema-valid structure with placeholder strings.

- [ ] **Step 2: Update `/career-init` skill to copy templates**

Modify `.claude/skills/career-init/SKILL.md` so that when invoked on an empty user directory, it copies all `templates/*.example` files into the appropriate `career/` subdirectories (renamed without `.example`).

- [ ] **Step 3: Verify**

Confirm template files exist and are syntactically valid YAML.

Run: `python -c "import yaml; yaml.safe_load(open('templates/contact.yaml.example'))"`
Expected: no exception.

---

## Task 7: Migrate Hooks to Plugin Convention

**Files:**
- Create: `hooks/hooks.json`
- Modify or remove: `.claude/settings.json`

In a plugin, hooks live at `<plugin-root>/hooks/hooks.json` and use `${CLAUDE_PLUGIN_ROOT}` to reference plugin files.

- [ ] **Step 1: Create `hooks/hooks.json`**

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          { "type": "command", "command": "python \"${CLAUDE_PLUGIN_ROOT}/scripts/lint_yaml.py\" \"$CLAUDE_FILE_PATHS\"" },
          { "type": "command", "command": "python \"${CLAUDE_PLUGIN_ROOT}/scripts/check_em_dashes.py\" \"$CLAUDE_FILE_PATHS\"" },
          { "type": "command", "command": "python \"${CLAUDE_PLUGIN_ROOT}/scripts/validate_resume.py\" --auto \"$CLAUDE_FILE_PATHS\"" }
        ]
      }
    ],
    "SessionStart": [
      {
        "hooks": [
          { "type": "command", "command": "python \"${CLAUDE_PLUGIN_ROOT}/scripts/career_status.py\"" }
        ]
      }
    ]
  }
}
```

- [ ] **Step 2: Delete or empty the old `.claude/settings.json`**

Move it aside as `.claude/settings.json.pre-plugin.bak` for safety, or delete after verification.

- [ ] **Step 3: Verify**

After Task 9 (when running from user dir), trigger a Write on a YAML file and confirm the hook fires.

---

## Task 8: Reorganize Plugin Layout

Move `.claude/skills/` → `skills/` and `.claude/agents/` → `agents/` at plugin root (per Claude Code plugin convention).

**Files:**
- Move all of `.claude/skills/` to `skills/`
- Move all of `.claude/agents/` to `agents/`
- Remove `.claude/` from plugin root (or leave empty for plugin-internal use)

- [ ] **Step 1: Move skills directory**

Run: `Move-Item .claude/skills skills`

- [ ] **Step 2: Move agents directory**

Run: `Move-Item .claude/agents agents`

- [ ] **Step 3: Update any internal references**

Skills and agents may reference each other by path. Run:

`Select-String -Path skills/**/SKILL.md,agents/*.md -Pattern "\.claude/"`

Update any `.claude/skills/...` → `skills/...` and `.claude/agents/...` → `agents/...`.

- [ ] **Step 4: Verify**

Plugin tree should now match the target layout in the header.

---

## Task 9: Migrate Plugin Pieces Out and Clean User Directory

User data stays at `P:\Resumes\Claude-automations\`. We strip plugin pieces from it (they've already been built into `P:\CareerOps\` by earlier tasks). What remains in the user directory is pure user data.

**Files moved or removed from `P:\Resumes\Claude-automations\`:**
- `.claude/skills/` → already lifted into `P:\CareerOps\skills\` (Task 8); delete original
- `.claude/agents/` → already lifted into `P:\CareerOps\agents\` (Task 8); delete original
- `.claude/settings.json` → replaced by `P:\CareerOps\hooks\hooks.json` (Task 7); delete original
- `scripts/` → already lifted into `P:\CareerOps\scripts\` (Task 2); delete original
- `schemas/` → already lifted into `P:\CareerOps\schemas\` (Task 1 area); delete original
- `docs/` → already lifted into `P:\CareerOps\docs\`; delete original
- `README.md` → replaced by user-facing one (Task 11); delete or rewrite
- `research-output.md` → orphan research notes; move to `P:\CareerOps\docs\research-notes.md`
- `skills-lock.json` → plugin concern; move to `P:\CareerOps\skills-lock.json`

**Files that stay in `P:\Resumes\Claude-automations\`:**
- `career/`
- `inbox/`
- `raw_data/`
- `Master_Career_Document.md`
- `CLAUDE.md` (now user-only, after Task 5 split)

- [ ] **Step 1: Sanity-check that all plugin pieces are present in `P:\CareerOps\`**

Run: `Get-ChildItem P:\CareerOps`
Expected: `.claude-plugin/`, `skills/`, `agents/`, `hooks/`, `scripts/`, `schemas/`, `config/`, `templates/`, `docs/`, `CLAUDE.md`, `README.md`.

- [ ] **Step 2: Delete plugin pieces from user directory**

```powershell
Remove-Item -Recurse -Force "P:\Resumes\Claude-automations\.claude"
Remove-Item -Recurse -Force "P:\Resumes\Claude-automations\scripts"
Remove-Item -Recurse -Force "P:\Resumes\Claude-automations\schemas"
Remove-Item -Recurse -Force "P:\Resumes\Claude-automations\docs"
Remove-Item -Force "P:\Resumes\Claude-automations\skills-lock.json"
Remove-Item -Force "P:\Resumes\Claude-automations\research-output.md"
Remove-Item -Force "P:\Resumes\Claude-automations\README.md"
```

- [ ] **Step 3: Replace CLAUDE.md with the user-only version**

After Task 5 split, replace `P:\Resumes\Claude-automations\CLAUDE.md` with the user-only version filled in for Kalhar (name, email, location, target roles, experience list, education, highlights pulled from `career/contact/contact.yaml` and `career/education/edu.yaml`).

- [ ] **Step 4: Verify both directories**

Run: `Get-ChildItem P:\Resumes\Claude-automations`
Expected: only `career/`, `inbox/`, `raw_data/`, `CLAUDE.md`, `Master_Career_Document.md`. Nothing else.

Run: `Get-ChildItem P:\CareerOps`
Expected: only plugin files. No `career/`, no `inbox/`, no `raw_data/`, no `Master_Career_Document.md`.

---

## Task 10: Smoke-Test End-to-End

- [ ] **Step 1: Start Claude from user directory with plugin loaded**

```powershell
cd P:\Resumes\Claude-automations
claude --plugin-dir P:\CareerOps
```

- [ ] **Step 2: Verify SessionStart hook fires**

Expected: `[CareerOps] Facts: 61 | Applications: 1 | JDs ingested: 1` appears in session start banner.

- [ ] **Step 3: Run `/careerops:career-status`**

Expected: Same dashboard output as before. Confirms `career_status.py` resolves paths via cwd correctly.

- [ ] **Step 4: Run `/careerops:lint-career`**

Expected: passes for all 61 facts + 14 experiences + 3 projects.

- [ ] **Step 5: Trigger a PostToolUse hook**

Edit any YAML file in `career/facts/` (e.g., add a harmless comment).
Expected: lint_yaml, check_em_dashes, validate_resume all run and pass.

- [ ] **Step 6: Trigger an em-dash failure**

Add an em-dash character (—) to a fact file.
Expected: `check_em_dashes.py` blocks with strict-mode error if inside `career/applications/`, warns otherwise.

---

## Task 11: Update Documentation

**Files:**
- Modify: `README.md` (plugin install + user setup instructions)
- Modify: `CLAUDE.md` (plugin policy, point to user dir for personal info)
- Create: `docs/USER-SETUP.md` (how to set up a new user data directory)

- [ ] **Step 1: Rewrite `README.md` as plugin documentation**

Sections:
- What CareerOps does (one paragraph)
- Installation (`claude --plugin-dir <path>` or marketplace)
- Quick start (run `/careerops:career-init` in an empty directory)
- Command reference (all 15 skills)
- Architecture overview (link to design spec)

- [ ] **Step 2: Add `docs/USER-SETUP.md`**

Step-by-step for a brand new user:
1. Create an empty directory
2. cd into it
3. Run `claude --plugin-dir <plugin-path>`
4. Run `/careerops:career-init` — copies templates from plugin
5. Fill in `career/contact/contact.yaml`, `career/education/edu.yaml`, `CLAUDE.md`
6. Drop a resume in `raw_data/` and run `/careerops:seed-from-tex` (or `/careerops:seed-from-master` for Markdown)

- [ ] **Step 3: Verify**

README is readable end-to-end; no references to Kalhar; no references to `P:/Resumes/`.

---

## Self-Review

**Spec coverage:** Every user goal from the request is covered:
- "Zero user information inside plugin" — Tasks 2-6 strip all references
- "Everything about how, when, what" stays in plugin — Tasks 7-8 reorganize plugin layout
- "No instructions in user dir, personal info only" — Task 5 splits CLAUDE.md, Task 9 moves data
- "User overrides + memory + CLAUDE.md outside" — `career/config/` and CLAUDE.md remain in user dir; memory already lives in `~/.claude/projects/...`

**Placeholder scan:** Every step contains concrete file paths, exact commands, and code blocks. No "TBD" or "implement appropriately" instructions.

**Type/path consistency:** Plugin path resolution (`${CLAUDE_PLUGIN_ROOT}`) used consistently in hooks.json. Script path resolution (`Path.cwd()` via `_paths.py`) used consistently across all 6 Python scripts. Skill namespace (`/careerops:<name>`) used consistently in smoke tests.

**Known risks:**
- RenderCV's output filename (`<Name>_CV.pdf`) depends on `cv.name` field — the skill instructions need to be robust to any name, not just Kalhar's.
- The `templates/` approach requires `/career-init` to be re-implemented (currently it may assume seed-from-tex flow). Verify or expand Task 6 if needed.
- The user directory keeps its current path (`P:\Resumes\Claude-automations\`), so the existing auto-memory at `~/.claude/projects/P--Resumes-Claude-automations/memory/` stays valid and continues to load. No memory migration needed.
- Plugin pieces are first copied into `P:\CareerOps\`, then deleted from the user directory (Task 9 Step 2). Do not run Step 2 until verification in Task 10 passes — keeping the originals intact lets you roll back if anything fails.

---
