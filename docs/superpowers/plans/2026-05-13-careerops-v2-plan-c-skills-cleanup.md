# CareerOps v2 -- Plan C: Skills + Cleanup

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create 11 new verb-first skills, delete 14 old skills, and update the manifest.

**Architecture:** Each new skill is a direct replacement for one or two old skills. Behavior is carried forward with renames, namespace fixes, and v2 data model references. Three skills have new or expanded behavior (setting-up, seeding-career-db, generating-resume).

**Tech Stack:** Claude Code skills (Markdown with YAML frontmatter).

---

## Prerequisites

- Plan A (foundation) and Plan B (bootstrap + agents) must be complete before this plan executes.
- `P:\CareerOps\skills\` directory exists (confirmed).
- `P:\CareerOps\.claude-plugin\plugin.json` exists.
- `P:\CareerOps\CLAUDE.md` exists.

---

## Task 1 -- Create `capturing-fact/SKILL.md`

Verb-first rename of `capture-fact`. Behavior identical. All cross-skill references updated to `/careerops:` namespace.

- [ ] Create directory `P:\CareerOps\skills\capturing-fact\`
- [ ] Write `P:\CareerOps\skills\capturing-fact\SKILL.md` with the content below
- [ ] Verify: `head -4 P:/CareerOps/skills/capturing-fact/SKILL.md` shows correct frontmatter

**File content:**

```markdown
---
name: capturing-fact
description: Interview to record a new career achievement as an atomic fact with metrics, framings, and evidence prompts.
---

# /capturing-fact -- Record a New Career Achievement

## When to Use
Run this skill whenever you want to record a new achievement, responsibility, or skill use to your career knowledge base. Run it right after completing something notable -- while details are fresh.

## What This Skill Does
Invokes the `fact-curator` subagent, which will interview you one question at a time to capture a new atomic fact. The fact is written as an entry in the `facts[]` array of the matching `career/experiences/X-*.yaml` file (or as a standalone fact in `career/projects/P-*.yaml` for project work). You are prompted to attach evidence after capture.

## How to Invoke
In Claude Code, type:
```
/careerops:capturing-fact
```

Optional: provide a brief description to skip the first interview question:
```
/careerops:capturing-fact Won the AI Hackathon with a 50-agent hierarchy
```

## Steps This Skill Executes
1. Load the `fact-curator` subagent
2. If a description was provided as an argument, pass it as the starting context
3. The subagent interviews you for: what happened, when, which role/employer, impact metric, technologies used, evidence available
4. You review and approve the draft fact YAML
5. The fact is appended to the `facts[]` array inside the matching `career/experiences/X-*.yaml`
6. You are prompted to attach evidence (`/careerops:capturing-evidence`) if none is available yet

## After Capturing
- Run `/careerops:linting-career` to verify the updated experience file passes schema validation
- Run `/careerops:capturing-evidence <fact-id>` to attach a source document
- The fact will have `status: pending-evidence` until evidence is attached

## Instructions for Claude Code

When this skill is invoked:

1. Announce: "Starting fact capture. I'll ask you a few questions one at a time."
2. Dispatch the `fact-curator` subagent with this context:
   - Working directory: the user's career data directory (wherever Claude Code is running from)
   - Any text provided after `/careerops:capturing-fact` as the initial description
   - Instruction: follow the fact-curator interview protocol; append result to matching experience file's `facts[]` array
3. After the subagent writes the fact, confirm the experience file path and the new fact ID to the user
4. Ask: "Attach evidence now? Run `/careerops:capturing-evidence <fact-id>` when ready."
5. Ask: "Should I update any other related experience or project file for this achievement?"
```

---

## Task 2 -- Create `capturing-evidence/SKILL.md`

Verb-first rename of `capture-evidence`. Behavior identical. References updated to v2 data model (facts live inside experience files).

- [ ] Create directory `P:\CareerOps\skills\capturing-evidence\`
- [ ] Write `P:\CareerOps\skills\capturing-evidence\SKILL.md` with the content below
- [ ] Verify: `head -4 P:/CareerOps/skills/capturing-evidence/SKILL.md` shows correct frontmatter

**File content:**

```markdown
---
name: capturing-evidence
description: Attach an evidence source (URL, certificate, file) to an existing career fact by its ID.
---

# /capturing-evidence -- Attach Evidence to a Fact

## When to Use
Run this after capturing a fact to attach a source document, URL, screenshot, certificate, PR link, or other verifiable evidence. Evidence upgrades a fact's status from `pending-evidence` to `verified`.

## Usage
```
/careerops:capturing-evidence <fact-id>
```
Example:
```
/careerops:capturing-evidence F-2025-deloitte-1st-50agents
```

## What This Skill Does
1. Locates the specified fact by scanning `facts[]` arrays inside `career/experiences/X-*.yaml` files (and `career/projects/P-*.yaml`)
2. Prompts you for the evidence source (URL, file path, or description)
3. Creates a new `career/evidence/E-*.yaml` file
4. Updates the fact's `evidence` list and sets `status: verified`

## Evidence Types Supported
- `certificate` -- award certificate, diploma, completion cert
- `url` -- public URL (GitHub PR, LinkedIn post, article, leaderboard)
- `file` -- local file (place in `career/assets/`)
- `screenshot` -- screenshot of result (place in `career/assets/`)
- `testimonial` -- reference letter or recommendation text
- `pr` -- GitHub PR link
- `commit` -- GitHub commit link
- `email` -- email confirmation (redact personal info before saving)

## Instructions for Claude Code

When this skill is invoked:

1. Parse the fact ID from the argument. If missing, ask: "Which fact ID? (e.g. F-2025-deloitte-1st-50agents)"
2. Scan all `career/experiences/X-*.yaml` and `career/projects/P-*.yaml` files for a fact with `id: <fact-id>`. If not found, print an error and stop.
3. Ask: "What type of evidence? (certificate / url / file / screenshot / pr / commit / email / testimonial)"
4. Ask: "Provide the source (URL, file path, or description):"
5. Ask: "When was this verified? (YYYY-MM-DD):"
6. Generate evidence ID: `E-<employer-slug>-<description>` (e.g. `E-deloitte-certificate`)
7. Write `career/evidence/<evidence-id>.yaml`:

```yaml
id: <evidence-id>
type: <type>
source: "<source>"
attestation: self-attested
verified_at: <YYYY-MM-DD>
backs_facts:
  - <fact-id>
```

8. Locate the fact entry inside its parent experience or project file. Update it:
   - Add the evidence ID to the `evidence` list
   - Change `status` from `pending-evidence` to `verified`

9. Confirm: "Evidence attached. Fact <fact-id> is now verified."
10. Run lint: invoke `python scripts/lint_yaml.py` on the updated experience file and the new evidence file
```

---

## Task 3 -- Create `setting-up/SKILL.md`

Replaces `career-init`. Invokes the new `setup-guide` subagent. Full directory scaffold for new users. Smart detection for returning users.

- [ ] Create directory `P:\CareerOps\skills\setting-up\`
- [ ] Write `P:\CareerOps\skills\setting-up\SKILL.md` with the content below
- [ ] Verify: `head -4 P:/CareerOps/skills/setting-up/SKILL.md` shows correct frontmatter

**File content:**

```markdown
---
name: setting-up
description: First-run wizard that scaffolds your career directory, collects config, and prepares the knowledge base for use. Safe to re-run -- detects new vs. returning user and adjusts accordingly.
---

# /setting-up -- CareerOps Setup Wizard

## Purpose
Run once after installing the CareerOps plugin (or any time you want to change your defaults). The skill detects whether you are a new or returning user and adjusts its behavior accordingly.

## Usage
```
/careerops:setting-up
```

Idempotent: re-running shows existing values as defaults. Existing facts, experiences, applications, and JD analyses are never touched.

## User Detection Logic

**New user:** `career/experiences/` does not exist or is empty.
**Returning user:** `career/experiences/` exists and contains at least one `X-*.yaml` file.

The `setup-guide` subagent handles both flows interactively.

## What This Skill Does

### New user flow
1. Scaffold the full directory tree:
   ```
   career/experiences/    career/projects/
   career/evidence/       career/applications/   career/jd-analysis/
   career/contact/        career/education/      career/skills/
   career/config/         inbox/                 raw_data/
   ```
2. Copy all templates from `${CLAUDE_PLUGIN_ROOT}/templates/` into appropriate directories
3. Ask Q1-Q4 (theme, header visibility, page budget, contact info) interactively
4. Write config files
5. Prompt: "Drop an existing resume in `raw_data/` and run `/careerops:seeding-career-db <path>` to import it, or run `/careerops:capturing-fact` to start adding achievements manually."

### Returning user flow
1. Show current config values as defaults
2. Ask only about fields that are unset
3. Skip directory scaffolding entirely
4. End with a summary of what changed (or "No changes made" if nothing was updated)

## Questions Asked (Q1-Q4)

**Q1: RenderCV theme**
Options:
- `engineeringresumes` -- densest, inline dates, no right column, no color
- `classic` -- centered name, icon bar, right-aligned dates, blue accent
- `sb2nov` -- horizontal-rule section headers, two-line role headers
- `moderncv` -- colored sidebar, more graphical
- `engineeringclassic` -- hybrid: classic header + engineeringresumes body

If the user is unsure, offer to render all 5 themes against their current resume data into a `previews/` folder for visual comparison.

**Q2: Header visibility**
- Show location: yes / no / per-application
- Show phone: yes / no / per-application
- Show email: yes (default, required) / no

**Q3: Default page budget**
- 1 page (typical for intern, junior, or career-change applications)
- 2 pages (recommended default for mid-to-senior)

**Q4: Contact info** (only fields that are currently unset)
- Name
- Email
- Location string (e.g. `<City, Region>`)
- Phone (optional)
- LinkedIn username (optional)
- GitHub username (optional)
- Personal website (optional)

## Config Files Written

```yaml
# career/config/rendercv-theme.yaml
theme: <chosen-theme>
```

```yaml
# career/contact/contact.yaml
name: <name>
email: <email>
location: <location string>
phone: <phone or null>
linkedin: <username or null>
github: <username or null>
website: <url or null>
```

```yaml
# career/config/rules.yaml (presentation block only -- other fields untouched)
presentation:
  show_location_default: <true|false|per_application>
  show_phone_default:    <true|false|per_application>
  page_budget_default:   <1|2>
```

## Instructions for Claude Code

When this skill is invoked:

1. Check whether `career/experiences/` exists and contains at least one `X-*.yaml` file.
   - If no: this is a new user. Proceed with new user flow.
   - If yes: this is a returning user. Proceed with returning user flow.

2. Dispatch the `setup-guide` subagent with:
   - Detected user state: `new` or `returning`
   - Paths to existing config files (if any)
   - List of directories that are missing and must be created
   - Instruction to follow the Q1-Q4 interview protocol

3. After the subagent completes, confirm to the user which files were written.

4. If new user: print the seed prompt (see new user flow step 5 above).

5. If returning user: print a diff of what changed (or "No changes made").

## Error Guard

If `setting-up` is invoked when facts exist, confirm before overwriting any config file. Never touch `career/facts[]` arrays inside experience files, `career/applications/`, or `career/jd-analysis/` under any circumstances.

## Rules

- Never delete career facts, experiences, projects, applications, or JD analyses during setup. This skill only touches config and contact files.
- Always show the current value as the default so the user can keep it by pressing enter.
- Preserve all other top-level fields in `rules.yaml` -- only add or update the `presentation` block.
```

---

## Task 4 -- Create `seeding-career-db/SKILL.md`

Unified replacement for `seed-from-tex` and `seed-from-master`. Auto-detects `.tex` vs `.md`. Facts are written as embedded arrays inside experience files (v2 data model).

- [ ] Create directory `P:\CareerOps\skills\seeding-career-db\`
- [ ] Write `P:\CareerOps\skills\seeding-career-db\SKILL.md` with the content below
- [ ] Verify: `head -4 P:/CareerOps/skills/seeding-career-db/SKILL.md` shows correct frontmatter

**File content:**

```markdown
---
name: seeding-career-db
description: One-shot migration skill. Reads an existing resume file and populates career/experiences/ with experience envelopes and embedded facts. Supports .tex (LaTeX) and .md (Master Career Document) formats.
---

# /seeding-career-db -- Seed Career Knowledge Base from Existing Resume

## Purpose
One-shot migration skill. Reads a `.tex` or `.md` resume file, extracts every role and bullet, and creates `career/experiences/X-*.yaml` files (with facts embedded as `facts[]` arrays) and `career/projects/P-*.yaml` files. Run once per source file.

## Usage
```
/careerops:seeding-career-db <path-to-file>
```
Examples:
```
/careerops:seeding-career-db raw_data/my-resume.tex
/careerops:seeding-career-db raw_data/Master_Career_Document.md
```

## Auto-Detection Logic

The skill reads the file extension from the argument:
- `.tex` -- calls the LaTeX resume parser (logic from `seed-from-tex`)
- `.md` -- calls the Master Career Document parser (logic from `seed-from-master`)
- Any other extension -- print error:
  ```
  Unsupported file type: <extension>
  Supported formats: .tex (LaTeX resume), .md (Master Career Document)
  ```
  Then stop.

## What This Skill Does (both formats)
1. Reads the source file
2. Extracts all experience sections (employer, role, dates) and their bullet points
3. For each bullet, asks interactively: Save as fact? [y / edit / skip / quit]
4. Creates one `career/experiences/X-*.yaml` per role, with approved bullets embedded as `facts[]` entries
5. For `.md` format: also creates `career/projects/P-*.yaml` for standalone project highlights
6. All facts get `status: pending-evidence` -- mark as `verified` after attaching evidence

## LaTeX Parsing (.tex)

Read the file at the provided path. Extract:
- Each section that looks like a job role (`cventry`, `cvevent`, `job`, `experience` environments; `\textbf{}` for names; date patterns `MM/YYYY`, `YYYY`, `Month YYYY`, `Present`)
- Employer name, role title, start date, end date (YYYY-MM format)
- All `\item` bullets per role

If the format is ambiguous, print the raw section and ask: "What is the employer and role for this section?"

Strip all LaTeX markup (`\textbf{}`, `\emph{}`, `%` comments, `\\`, etc.) from fact titles and descriptions.

## Master Career Document Parsing (.md)

Parse the document structure:
- For each `### <Employer> -- <Role Title>` block under `## Work Experience`: extract date line, employer slug, role slug
- For each `-` bullet under the role: create a fact entry
- For each `> **Agent Note:**` callout near a bullet: capture the guidance in the fact's `description` and add appropriate tags. Never drop or silently ignore an Agent Note.
- For each section under `## Technical Project Highlights` that is not already modelled as an employment role: create a `P-*.yaml`

## Experience File Format (v2 -- facts embedded)

```yaml
id: X-<employer-slug>-<role-slug>
employer: <exact employer name>
role_title: <exact role title>
location: <city, region if known>
when_start: YYYY-MM
when_end: YYYY-MM | present
facts:
  - id: F-<YYYY>-<employer-slug>-<2-3-word-slug>
    type: achievement | responsibility | skill_use
    title: <clean one-line summary, no markup, no em-dashes>
    when: YYYY-MM
    impact:
      metric: <verbatim number+unit if present, else "qualitative">
      quantified: <true if a number is present, false otherwise>
      outcome: <short outcome slug>
    tech_actual: [<tech mentioned>]
    metrics: ["<verbatim metric strings>"]
    framings:
      - id: <suggested-angle>
        angle: "<what this framing leads with>"
        sample: "<example bullet>"
    tags: []
    status: pending-evidence
```

Note: `role_ref` and `employer` fields are NOT written inside embedded facts -- they are inherited from the parent experience envelope.

## Interactive Bullet Review

For each bullet:
```
Bullet: "<extracted bullet text>"
Save as fact? [y / edit / skip / quit]:
```
- `y` -- generate a fact draft and embed it
- `edit` -- show the draft YAML and let the user modify before saving
- `skip` -- move to next bullet
- `quit` -- stop processing, report what was saved so far

## Project File Format (P-*.yaml, .md source only)

```yaml
id: P-<slug>
name: <verbatim project name>
url: <if present>
when_start: YYYY-MM
when_end: YYYY-MM | present
tech: [<tech list>]
description: |
  <2-4 sentence narrative>
facts:
  - id: F-<YYYY>-<project-slug>-<2-3-word-slug>
    ...
tags: []
```

## Duplicate Guard

Before writing any file, check if `career/experiences/<id>.yaml` or `career/projects/<id>.yaml` already exists. If it does, skip it and print a notice. Never overwrite existing data.

## Summary Report

After processing all roles, print:
```
=== seeding-career-db complete ===
Source:           <filename> (<.tex|.md>)
Experiences:      N written  (career/experiences/)
Facts embedded:   N total
Projects:         N written  (career/projects/)  [.md source only]
Skipped:          N bullets

All facts marked status: pending-evidence.

Next steps:
  1. /careerops:linting-career           -- verify schema + refs
  2. /careerops:capturing-evidence <id>  -- attach evidence to key facts
```

## Hard Rules

- Never invent metrics not present in the original source file
- Never change employer names or dates extracted from the source
- If a date cannot be parsed, show it raw and ask the user
- Zero em-dashes (U+2014, U+2015, U+2E3A, U+2E3B) in any field
- Never overwrite existing `X-*.yaml` or `P-*.yaml` files
- Strip markup from titles and descriptions; preserve all punctuation and numbers exactly
- If a bullet contains multiple distinct claims, split into multiple fact entries
```

---

## Task 5 -- Create `analyzing-jd/SKILL.md`

Replaces `ingest-jd`. Invokes `jd-analyzer` subagent. Output JD-*.yaml now includes `ranked_facts[]` with relevance scores for all known facts.

- [ ] Create directory `P:\CareerOps\skills\analyzing-jd\`
- [ ] Write `P:\CareerOps\skills\analyzing-jd\SKILL.md` with the content below
- [ ] Verify: `head -4 P:/CareerOps/skills/analyzing-jd/SKILL.md` shows correct frontmatter

**File content:**

```markdown
---
name: analyzing-jd
description: Analyze a job description file and extract structured keywords, requirements, role signals, and a ranked list of relevant career facts into a JD YAML.
---

# /analyzing-jd -- Analyze a Job Description

## Usage
```
/careerops:analyzing-jd <path-to-jd-file>
```
Example:
```
/careerops:analyzing-jd inbox/company-role-jd.md
```

JD files go in `inbox/`. Supported formats: `.md`, `.txt`, `.pdf` (text-extractable).

## What This Skill Does
Dispatches the `jd-analyzer` subagent to read the JD file and produce a structured `career/jd-analysis/JD-*.yaml`. The analysis includes verbatim keywords (used for validation Gate 3), a match-score hint, and a `ranked_facts[]` array that scores every known fact by relevance to this JD.

## ranked_facts[] Output

The `jd-analyzer` subagent scans all `career/experiences/X-*.yaml` files and extracts every `facts[].id`. It then scores each fact against the JD:

- Score 1.0: fact tech stack overlaps 3+ required keywords AND impact metric is strong
- Score 0.8-0.99: 2+ required keyword matches
- Score 0.6-0.79: 1 required keyword or 2+ preferred keyword matches
- Below 0.6: low relevance (still included, sorted to the bottom)

All facts are scored and included. The ranked list is a sort-order hint for the bullet composer -- no fact is excluded from composition consideration.

Example output in JD-*.yaml:
```yaml
ranked_facts:
  - fact_id: F-2025-oracle-rag-pipeline
    score: 0.94
    matched_keywords: [RAG, LLM, pipeline]
  - fact_id: F-2025-deloitte-1st-place
    score: 0.88
    matched_keywords: [agentic, LangGraph, orchestration]
```

## Instructions for Claude Code

1. Parse the file path from the argument. If missing, ask: "Path to JD file? (e.g. inbox/company-role-jd.md)"
2. Verify the file exists. If not, print an error and stop.
3. Dispatch the `jd-analyzer` subagent with:
   - The JD file path
   - Today's date (for the output file ID)
   - Paths to all `career/experiences/X-*.yaml` files (for fact ID extraction and relevance scoring)
   - Instruction to produce `ranked_facts[]` covering every fact found across all experience files
4. After the subagent writes the JD analysis file, print:
   ```
   JD analyzed: career/jd-analysis/<id>.yaml
   Match score: <score>
   Keywords:    <count> verbatim terms extracted
   Facts ranked: <count> facts scored by relevance
   Red flags:   <list or "none">
   Ready for:   /careerops:generating-resume <jd-id>
   ```
5. Suggest next step: `/careerops:generating-resume <jd-id>`
```

---

## Task 6 -- Create `generating-resume/SKILL.md`

Replaces `generate-resume` and absorbs `plan-resume` as Step 0 inline Q&A. References `ranked_facts[]` from JD analysis. Facts sourced from `career/experiences/X-*.yaml` embedded arrays. All cross-skill references use `/careerops:` namespace.

- [ ] Create directory `P:\CareerOps\skills\generating-resume\`
- [ ] Write `P:\CareerOps\skills\generating-resume\SKILL.md` with the content below
- [ ] Verify: `head -4 P:/CareerOps/skills/generating-resume/SKILL.md` shows correct frontmatter

**File content:**

```markdown
---
name: generating-resume
description: End-to-end resume generation from a job description ID. Inline planning Q&A (Step 0), bullet composition using ranked facts, PDF rendering, 8-gate validation, semantic audit, and cover letter generation.
---

# /generating-resume -- End-to-End Resume Generation

## Usage
```
/careerops:generating-resume <jd-id>
```
Example:
```
/careerops:generating-resume JD-2026-05-15-procogia-mle
```

## Prerequisites
- JD must be analyzed first: `/careerops:analyzing-jd inbox/<jd-file>`
- Career knowledge base must exist: run `/careerops:linting-career` to check

## What This Skill Does
Orchestrates the full generation pipeline:
0. Inline planning Q&A (tone, emphasis, overrides) -- replaces the standalone plan-resume skill
1. Bullet-composer proposes a presentation plan
2. You approve (or edit) the plan
3. Bullet-composer composes bullets using `ranked_facts[]` as a priority hint; reads all facts from `career/experiences/*.yaml`
4. RenderCV renders the PDF
5. Validator runs 8 deterministic gates
6. Resume-auditor does a semantic pass
7. Cover-letter-composer writes `cover-letter.md`; `render_cover_letter.py` compiles the PDF
8. `application.yaml` is updated with the final result

---

## Instructions for Claude Code

### Step 0 -- Inline planning Q&A

Check if `career/applications/<app-id>/proposed-plan.yaml` already exists.

- If it **exists** (user ran a separate planning session): skip to Step 1.
- If it **does not exist**: run the planning Q&A inline now.

Ask the following questions before dispatching the bullet-composer:

**Q1: Tone**
"How would you describe the tone for this application?"
Options: `concise-technical` (default) | `narrative-driven` | `leadership-forward`

**Q2: Emphasis**
"Is there anything you want to emphasize or de-emphasize for this specific role?"
Free text, optional. Example: "Emphasize LLM work; downplay frontend."

**Q3: Tier 2 opt-in**
"Any reframings you want to authorize for this application? (Leave blank for strict-fact-mode.)"
If the user provides opt-ins, write them to `career/applications/<app-id>/user_overrides.yaml`.

Collect answers before continuing. Do not skip the Q&A even if the JD seems clear.

### Step 1 -- Load context

Read these files:
- `career/jd-analysis/<jd-id>.yaml` (includes `ranked_facts[]` from v2 jd-analyzer)
- `career/config/rules.yaml`
- All `career/experiences/X-*.yaml` files (facts are embedded in `facts[]` arrays)
- All `career/projects/P-*.yaml` files
- `career/skills/skills.yaml`
- `career/education/edu.yaml`
- `career/contact/contact.yaml`

If `career/jd-analysis/<jd-id>.yaml` does not exist, print:
```
JD not found. Run `/careerops:analyzing-jd <path>` first.
```
and stop.

If `career/config/rules.yaml` does not exist, use defaults: `page_budget: 2`, `max_bullet_chars: 200`.

### Step 2 -- Create application folder

Generate application ID: `A-<YYYY-MM-DD>-<company-slug>-<role-slug>`

Create `career/applications/<app-id>/` and write `application.yaml`:
```yaml
id: <app-id>
company: <from jd-analysis: company>
role: <from jd-analysis: role_title>
jd_ref: <jd-id>
generated_at: <ISO 8601 timestamp>
ready_to_send: false
sent_at: null
outcome:
  state: pending
  at: null
  notes: ""
generation_attempts: 0
validation_status: not_run
audit_status: not_run
```

If `user_overrides.yaml` does not already exist, write the blank template with commented examples (see v1 generate-resume for template content).

### Step 3 -- Dispatch bullet-composer (plan phase)

Dispatch the `bullet-composer` subagent with:
- Path to JD analysis: `career/jd-analysis/<jd-id>.yaml` (the `ranked_facts[]` array inside this file serves as the composition priority hint -- higher-scored facts are composed first, but all facts remain available)
- Paths to all `career/experiences/X-*.yaml` files (facts are read from embedded `facts[]` arrays)
- Paths to all `career/projects/P-*.yaml` files
- Application ID: `<app-id>`
- Path to user overrides: `career/applications/<app-id>/user_overrides.yaml`
- Tone and emphasis from Step 0 Q&A
- Instruction: **produce proposed-plan.yaml only (Phase 1). Do not compose bullets yet.**

The composer reads all facts from experience files directly. `ranked_facts[]` is advisory sort order only -- no fact is excluded.

### Step 4 -- PAUSE: show plan to user

After bullet-composer writes `proposed-plan.yaml`, display it in readable format. Ask:
```
Does this presentation plan look right?
  [approve]           -- continue to bullet composition
  [edit overrides]    -- edit user_overrides.yaml and re-plan
  [abort]             -- cancel and delete this application folder
```

Handle responses:
- **approve**: continue to Step 5
- **edit overrides**: open `user_overrides.yaml` for editing, re-dispatch Phase 1, show revised plan, pause again. Repeat until approved or aborted.
- **abort**: delete `career/applications/<app-id>/` and print "Generation cancelled. Application folder removed." Then stop.

### Step 5 -- Dispatch bullet-composer (compose phase)

Re-dispatch with the same context as Step 3, plus:
- Path to approved plan: `career/applications/<app-id>/proposed-plan.yaml`
- Instruction: **Phase 2-3: compose bullets, write rendercv-input.yaml and claim-ledger.yaml.**

Increment `generation_attempts` in `application.yaml` on each dispatch.

Note: the claim-ledger must reference fact IDs that exist inside experience or project files (not standalone `career/facts/F-*.yaml`, which no longer exists in v2).

### Step 6 -- Render PDF

IMPORTANT: RenderCV resolves `--output-folder` relative to the input YAML file's directory, not the working directory. Always use absolute paths.

Resolve the project root:
```
python -c "from pathlib import Path; print(Path.cwd().resolve())"
```

Run:
```
rendercv render "<absolute-path>\career\applications\<app-id>\rendercv-input.yaml" --output-folder "<absolute-path>\career\applications\<app-id>"
```

If `rendercv` is not installed, print installation instructions and stop.

On success, rename outputs:
- `<Name>_CV.pdf` -> `resume.pdf` (keep)
- `<Name>_CV.typ` -> `resume.typ` (keep, used by page-utilization check)
- Delete: `<Name>_CV.md`, `<Name>_CV.html`, `<Name>_CV_*.png`

### Step 7 -- Run validation

Run:
```
python scripts/validate_resume.py <app-id>
```

The validator checks 8 gates:
1. PDF compiled (file exists and is non-empty)
2. Page count is within `page_budget` from `career/config/rules.yaml`
3. Every verbatim keyword from jd-analysis `keywords_verbatim` appears at least once in the resume text
4. Every bullet in claim-ledger.yaml has at least one `backed_by` fact ID that resolves inside a `career/experiences/X-*.yaml` or `career/projects/P-*.yaml` `facts[]` array
5. No em-dashes (U+2014, U+2015, U+2E3A, U+2E3B) in the resume text
6. No banned phrases from the humanization banned-word list
7. No dangling fact references (every fact ID cited exists in an experience or project file)
8. The current role has at least 3 bullets

On gate failure: print which gate(s) failed, re-dispatch bullet-composer with failure context, increment `generation_attempts`. Retry up to 3 times. After 3 failures, write `validation-failures.md`, update `application.yaml` with `validation_status: failed`, and stop.

On success, update `application.yaml`: `validation_status: passed`.

### Step 8 -- Run auditor

Dispatch `resume-auditor` subagent with paths to `resume.pdf`, `claim-ledger.yaml`, JD analysis, and application ID. The auditor writes `audit-report.md`.

Update `application.yaml`:
```yaml
audit_status: <PASS or NEEDS-REVIEW>
```

If verdict is PASS, set `ready_to_send: true`. If NEEDS-REVIEW, leave `ready_to_send: false` and surface the auditor's concerns.

### Step 9 -- Dispatch cover-letter-composer

Dispatch `cover-letter-composer` with JD analysis path, claim ledger, user overrides, contact file, application ID, and today's date.

The composer writes `career/applications/<app-id>/cover-letter.md`.

### Step 10 -- Render cover letter PDF

Run:
```
python scripts/render_cover_letter.py <app-id>
```

Reads `cover-letter.md`, fills `career/config/cover-letter-template.typ`, compiles via the `typst` package, writes `cover-letter.pdf`. If the script fails, print the error and continue -- Gate 11 still passes on `.md` alone.

### Step 11 -- Validate cover letter (Gate 11)

Gate 11 runs inside `validate_resume.py`. On failure, re-dispatch `cover-letter-composer` with failure details and retry once. After 2 failures, write `cover-letter-failures.md` and continue without blocking `ready_to_send`.

### Step 12 -- Final summary

Print:
```
Resume generated: career/applications/<app-id>/resume.pdf

  Bullets:           <N> total
  Facts used:        <N distinct fact IDs>
  Overrides flagged: <N>
  Unmatched keywords: <comma-separated list or "none">

  Validation:    PASS (<N> gates) | <generation_attempts> attempt(s)
  Auditor:       <PASS / NEEDS-REVIEW>

  Em-dashes:     0
  Banned words:  <N from auditor report>
  Page count:    <N>

  ready_to_send: <true / false>
```

If `ready_to_send: true`, print:
```
When you send this application, run:
  /careerops:logging-outcome <app-id>
to record the outcome.
```

If `ready_to_send: false` and audit verdict is NEEDS-REVIEW, print the auditor's concerns directly below the summary table.
```

---

## Task 7 -- Create `auditing-resume/SKILL.md`

Verb-first rename of `audit-resume`. Behavior identical.

- [ ] Create directory `P:\CareerOps\skills\auditing-resume\`
- [ ] Write `P:\CareerOps\skills\auditing-resume\SKILL.md` with the content below
- [ ] Verify: `head -4 P:/CareerOps/skills/auditing-resume/SKILL.md` shows correct frontmatter

**File content:**

```markdown
---
name: auditing-resume
description: Re-run the semantic auditor on an existing application to check AI markers, quality, and JD fit.
---

# /auditing-resume -- Re-run Semantic Auditor on a Resume

## Usage
```
/careerops:auditing-resume <app-id>
```
Example:
```
/careerops:auditing-resume A-2026-05-15-procogia-mle
```

Optional flag to accept a NEEDS-REVIEW verdict:
```
/careerops:auditing-resume A-2026-05-15-procogia-mle --accept
```

## What This Skill Does
Dispatches the `resume-auditor` subagent to re-run the semantic quality pass on an already-generated resume. Use this to:
- Re-audit after manually editing `rendercv-input.yaml`
- Get a fresh verdict after humanizing specific bullets
- Accept a NEEDS-REVIEW verdict explicitly

## Instructions for Claude Code

1. Parse the app-id from arguments.
2. Verify `career/applications/<app-id>/rendercv-input.yaml` exists. If not, print an error.
3. Read `career/applications/<app-id>/application.yaml` to get the `jd_ref`.
4. If `--accept` flag is present and there is an existing audit report:
   - Set `validation_summary.auditor_verdict: PASS` (user-accepted)
   - Ask: "Mark ready_to_send: true as well? [y/n]"
   - If yes: set `ready_to_send: true` in `application.yaml`
   - Print: "NEEDS-REVIEW verdict accepted by user. Application marked ready_to_send."
   - Stop (skip re-running the auditor).
5. Otherwise dispatch the `resume-auditor` subagent with:
   - `rendercv-input.yaml` path
   - `claim-ledger.yaml` path
   - JD analysis yaml path
   - `proposed-plan.yaml` path
6. After the report is written, display the verdict and the AI Marker Scan table.
7. If verdict is PASS, ask: "Mark ready_to_send: true? [y/n]"
```

---

## Task 8 -- Create `humanizing-resume/SKILL.md`

Verb-first rename of `humanize-resume`. Behavior identical.

- [ ] Create directory `P:\CareerOps\skills\humanizing-resume\`
- [ ] Write `P:\CareerOps\skills\humanizing-resume\SKILL.md` with the content below
- [ ] Verify: `head -4 P:/CareerOps/skills/humanizing-resume/SKILL.md` shows correct frontmatter

**File content:**

```markdown
---
name: humanizing-resume
description: Remove AI markers and improve bullet tone in an existing application resume using the humanize-content skill.
---

# /humanizing-resume -- Manual Humanization Touchup

## Usage
```
/careerops:humanizing-resume <app-id>
```
Or target a specific section:
```
/careerops:humanizing-resume <app-id> --section professional_summary
/careerops:humanizing-resume <app-id> --bullet B-007
```

## What This Skill Does
Applies humanization rules to bullets or sections in a generated resume, without regenerating the whole thing. Delegates to the `humanize-content` skill (a separate external skill, not part of careerops -- invoke it directly as `/humanize-content`) for the actual rules. Updates `rendercv-input.yaml` in place. Re-runs the auditor after changes.

## The humanize-content rules (condensed for resume context)

No banned words: leverage, robust, comprehensive, seamless, delve, landscape,
paradigm, synergy, holistic, cutting-edge, state-of-the-art, spearheaded,
pioneered, harnessed, fostered, facilitated, streamlined, successfully.

No em-dashes. Never. Use commas, semicolons, or restructure the sentence.

Vary sentence openings: not every bullet starts with "Developed" or "Built".
Mix short punchy bullets with slightly longer contextual ones.

Be concrete: name the technology, name the metric, name the outcome.
Replace vague generics ("improved performance") with specific claims ("cut P99 latency from 800ms to 120ms").

Sound like a technical professional, not an AI assistant.

## Instructions for Claude Code

1. Parse app-id and optional `--section` or `--bullet` flags.

2. Read `career/applications/<app-id>/rendercv-input.yaml`.

3. Also read `career/applications/<app-id>/claim-ledger.yaml` to understand which facts back each bullet. Do not change the facts -- only surface phrasing.

4. If `--bullet B-NNN` specified:
   - Find the bullet in `rendercv-input.yaml` by matching its text against `claim-ledger.yaml` bullet_id
   - Apply humanization to that single bullet
   - Show before/after and ask: "Use this version? [y/n/edit]"

5. If `--section professional_summary` specified:
   - Apply humanization to the summary paragraph
   - Show before/after and ask: "Use this version? [y/n/edit]"

6. If no section/bullet specified:
   - Scan all bullets and the summary for AI markers (banned words, em-dashes, uniform rhythm)
   - Show a list of flagged bullets with suggested rewrites
   - Ask: "Apply all fixes? [y/n/select]"

7. For each accepted change:
   - Update `rendercv-input.yaml`
   - Verify the new text does not contain em-dashes
   - The backed_by facts in claim-ledger.yaml must still be traceable to the new text (same meaning, different words)

8. After changes, re-run the em-dash check:
   ```
   python scripts/check_em_dashes.py career/applications/<app-id>/rendercv-input.yaml
   ```

9. Ask: "Re-run the auditor? [y/n]" (suggest yes)

## Hard constraints

- Never change numeric metrics (these trace to Tier 1 immutable facts)
- Never change employer names or dates
- The claim must still be traceable to the backed_by fact after rewording
- If you cannot humanize a bullet without changing its factual claim, flag it and skip
```

---

## Task 9 -- Create `logging-outcome/SKILL.md`

Verb-first rename of `log-outcome`. Behavior identical. Cross-skill references updated to `/careerops:` namespace.

- [ ] Create directory `P:\CareerOps\skills\logging-outcome\`
- [ ] Write `P:\CareerOps\skills\logging-outcome\SKILL.md` with the content below
- [ ] Verify: `head -4 P:/CareerOps/skills/logging-outcome/SKILL.md` shows correct frontmatter

**File content:**

```markdown
---
name: logging-outcome
description: Record the outcome of a job application as interview, offer, reject, or no-response in the application registry.
---

# /logging-outcome -- Record Application Outcome

## Usage
```
/careerops:logging-outcome <app-id> <state>
```
States: `interview`, `reject`, `offer`, `no_response`

Examples:
```
/careerops:logging-outcome A-2026-05-15-procogia-mle interview
/careerops:logging-outcome A-2026-05-15-procogia-mle reject
```

## What This Skill Does
Records the outcome of a job application in `career/applications/<app-id>/application.yaml`.

## Instructions for Claude Code

1. Parse `app-id` and `state` from arguments. If either is missing, ask for them.
2. Validate `state` is one of: `interview`, `reject`, `offer`, `no_response`.
3. Read `career/applications/<app-id>/application.yaml`.
4. Update:
   ```yaml
   outcome:
     state: <state>
     at: <ISO 8601 now>
     notes: ""
   ```
5. Ask: "Any notes to add? (press Enter to skip)"
6. If notes provided, add to `outcome.notes`.
7. Write the updated file.
8. Print:
   ```
   [logging-outcome] <app-id>: outcome recorded as <state> at <date>
   ```
9. If state is `interview`: print "Next step: prepare for interview. Review your audit-report.md for talking points."
10. If state is `reject`: print "Logged. Run a career status check to review your pipeline."
```

---

## Task 10 -- Create `linting-career/SKILL.md`

Verb-first rename of `lint-career`. Updated to note it validates embedded `facts[]` arrays inside experience files (v2 data model).

- [ ] Create directory `P:\CareerOps\skills\linting-career\`
- [ ] Write `P:\CareerOps\skills\linting-career\SKILL.md` with the content below
- [ ] Verify: `head -4 P:/CareerOps/skills/linting-career/SKILL.md` shows correct frontmatter

**File content:**

```markdown
---
name: linting-career
description: Validate all career YAML files for schema compliance, referential integrity, and em-dash policy violations. In v2, also validates embedded facts[] arrays inside experience files.
---

# /linting-career -- Run YAML Linter on Career Knowledge Base

## Usage
```
/careerops:linting-career
```
Or lint a specific subdirectory:
```
/careerops:linting-career experiences
/careerops:linting-career applications/A-2026-05-15-procogia-mle
```

## What This Skill Does
Runs `scripts/lint_yaml.py` against all YAML files in the career knowledge base (or a specific subdirectory). Checks:
- Schema validation against JSON schemas in `schemas/`
- Referential integrity (fact IDs referenced in claim ledgers must exist inside experience or project `facts[]` arrays)
- Em-dash policy (U+2014, U+2015, U+2E3A, U+2E3B forbidden everywhere)
- Embedded `facts[]` arrays inside `career/experiences/X-*.yaml` and `career/projects/P-*.yaml` are validated against `embedded-fact.schema.json`

## v2 Data Model Note

In CareerOps v2, facts are embedded inside experience files as `facts[]` arrays rather than living in a separate `career/facts/` directory. The linter walks `experience.facts[]` arrays for all schema and reference checks. There is no `career/facts/` directory to scan.

## Instructions for Claude Code

1. Determine the target path:
   - No argument: scan all of `career/`
   - `experiences` / `evidence` / `applications` etc.: scan that subdirectory
   - A full path like `applications/A-xyz`: scan that specific folder

2. Build the file list:
   ```
   python scripts/lint_yaml.py <space-separated list of matching .yaml files>
   ```
   Use glob to find all `*.yaml` files in the target directory recursively.

3. Run the lint command. Stream the output.

4. After completion, print a summary:
   ```
   Linted: N files
   OK: N | Schema errors: N | Ref errors: N | Em-dash violations: N
   ```

5. If any errors were found, list the files with errors and suggest how to fix them.

6. If all clean: print "[linting-career] All career YAML files are valid."
```

---

## Task 11 -- Create `getting-help/SKILL.md`

Replaces `career-help`. Default output: 3-command quickstart plus apply section. Full output when `$ARGUMENTS` contains "full". All commands use `/careerops:` namespace.

- [ ] Create directory `P:\CareerOps\skills\getting-help\`
- [ ] Write `P:\CareerOps\skills\getting-help\SKILL.md` with the content below
- [ ] Verify: `head -4 P:/CareerOps/skills/getting-help/SKILL.md` shows correct frontmatter

**File content:**

```markdown
---
name: getting-help
description: Print the CareerOps command reference. Default shows a 3-command quickstart. Pass "full" to see all 11 skills with descriptions and arguments.
---

# /getting-help -- CareerOps Command Reference

## Usage
```
/careerops:getting-help
/careerops:getting-help full
```

## Instructions for Claude Code

### Default output (no argument or argument does not contain "full")

Print the following:

```
CareerOps -- Quick Start

  New here?
    /careerops:setting-up              Initialize your career directory
    /careerops:seeding-career-db       Import an existing resume
    /careerops:capturing-fact          Add a new career achievement

  Applying for a job?
    /careerops:analyzing-jd            Analyze a job description
    /careerops:generating-resume       Generate a tailored resume PDF

  /careerops:getting-help full         Show all commands
```

### Full output (argument contains "full")

Print the following:

```
========================================
 CareerOps v2 -- Full Command Reference
========================================

SETUP
  /careerops:setting-up
    First-run wizard. Scaffolds directory tree, collects config,
    writes rendercv-theme.yaml + contact.yaml + rules.yaml.
    Safe to re-run; detects new vs. returning user.

CAPTURE
  /careerops:capturing-fact
    Interactive interview to record a new career achievement.
    Facts are embedded in career/experiences/X-*.yaml.
    Optional: provide a brief description as argument.

  /careerops:capturing-evidence <fact-id>
    Attach a URL, certificate, PR, or file to a fact.
    Sets fact status from pending-evidence to verified.

  /careerops:seeding-career-db <path>
    One-shot import from an existing resume.
    .tex: LaTeX resume parser
    .md:  Master Career Document parser
    Other extensions: error with supported formats listed.

APPLY
  /careerops:analyzing-jd <path>
    Analyze a JD file from inbox/.
    Outputs JD-*.yaml with verbatim keywords and ranked_facts[]
    (all known facts scored by relevance to this JD).
    Example: /careerops:analyzing-jd inbox/company-role.md

  /careerops:generating-resume <jd-id>
    Full pipeline: inline planning Q&A, compose bullets (ranked_facts
    used as priority hint), render PDF, validate (8 gates), audit,
    generate cover letter.
    Example: /careerops:generating-resume JD-2026-05-15-procogia-mle

  /careerops:auditing-resume <app-id>
    Re-run semantic auditor on a generated resume.
    Add --accept to accept a NEEDS-REVIEW verdict and mark ready.

  /careerops:humanizing-resume <app-id>
    Surgical AI-marker cleanup on bullets or sections.
    Flags: --section <name>, --bullet <B-NNN>

  /careerops:logging-outcome <app-id> <state>
    Record result: interview / reject / offer / no_response

HEALTH
  /careerops:linting-career
    Schema + referential integrity + em-dash check on all career YAML.
    Also validates embedded facts[] arrays inside experience files.
    Optionally pass a subdirectory name to scope the scan.

  /careerops:getting-help full
    Show this reference.

========================================
 TYPICAL WORKFLOW
========================================

  1. First time setup:
       /careerops:setting-up
       /careerops:seeding-career-db raw_data/<your-resume>.tex

  2. Capture achievements (ongoing):
       /careerops:capturing-fact
       /careerops:capturing-evidence <fact-id>

  3. For each job application:
       a. Drop JD into inbox/
       b. /careerops:analyzing-jd inbox/<jd-file>
       c. /careerops:generating-resume <jd-id>
          -- inline planning Q&A (tone, emphasis, overrides)
          -- review presentation plan, approve
          -- PDF is generated + validated + audited
          -- cover letter generated
       d. If NEEDS-REVIEW: /careerops:humanizing-resume <app-id>
          then: /careerops:auditing-resume <app-id> --accept
       e. Send the resume manually
       f. /careerops:logging-outcome <app-id> interview|reject|offer|no_response

  4. Maintenance:
       /careerops:linting-career        (run anytime to check DB health)

========================================
 KEY FILE LOCATIONS (v2)
========================================

  career/experiences/   X-*.yaml    Experience envelopes with embedded facts[]
  career/projects/      P-*.yaml    Side projects with embedded facts[]
  career/evidence/      E-*.yaml    Sources backing facts (reference fact IDs)
  career/jd-analysis/   JD-*.yaml   Analyzed job descriptions (includes ranked_facts[])
  career/applications/  A-*/        One folder per application
    application.yaml                Registry entry + outcome
    rendercv-input.yaml             Exact YAML rendered to PDF
    claim-ledger.yaml               Every bullet -> fact ID map
    audit-report.md                 Auditor verdict
    resume.pdf                      The generated resume
    cover-letter.pdf                The generated cover letter
  career/contact/       contact.yaml
  career/config/        rules.yaml, rendercv-theme.yaml
  inbox/                Drop JD files here before /analyzing-jd
  schemas/              JSON Schemas for all data files

========================================
 HARD RULES (enforced by code)
========================================

  * No em-dashes in any resume output. Ever. Code blocks writes.
  * Every bullet must trace to a fact ID. No fact = no bullet.
  * Dates and employers are immutable. Schema-locked.
  * Tier 2 reframings require explicit user opt-in per application.
  * Current/most-recent role: never dropped, minimum 3 bullets.

========================================
```

After printing the full reference, run `python "${CLAUDE_PLUGIN_ROOT}/scripts/career_status.py"` (if available) and append the output at the bottom.
```

---

## Task 12 -- Delete old skill directories

Remove all v1 skill directories that have been replaced or absorbed. The `rendercv` skill directory is NOT in this list -- it is unrelated to this plan.

- [ ] Delete `P:\CareerOps\skills\career-init\`
- [ ] Delete `P:\CareerOps\skills\career-status\`
- [ ] Delete `P:\CareerOps\skills\career-help\`
- [ ] Delete `P:\CareerOps\skills\capture-fact\`
- [ ] Delete `P:\CareerOps\skills\capture-evidence\`
- [ ] Delete `P:\CareerOps\skills\seed-from-tex\`
- [ ] Delete `P:\CareerOps\skills\seed-from-master\`
- [ ] Delete `P:\CareerOps\skills\ingest-jd\`
- [ ] Delete `P:\CareerOps\skills\generate-resume\`
- [ ] Delete `P:\CareerOps\skills\plan-resume\`
- [ ] Delete `P:\CareerOps\skills\audit-resume\`
- [ ] Delete `P:\CareerOps\skills\humanize-resume\`
- [ ] Delete `P:\CareerOps\skills\log-outcome\`
- [ ] Delete `P:\CareerOps\skills\lint-career\`

**Verification:** After deletes, `ls P:\CareerOps\skills\` should show only: `capturing-fact`, `capturing-evidence`, `setting-up`, `seeding-career-db`, `analyzing-jd`, `generating-resume`, `auditing-resume`, `humanizing-resume`, `logging-outcome`, `linting-career`, `getting-help`, `rendercv`, and the new bootstrap skill directory `using-careerops` (created in Plan B).

---

## Task 13 -- Update `plugin.json` to version 2.0.0

- [ ] Read `P:\CareerOps\.claude-plugin\plugin.json`
- [ ] Update the `version` field to `"2.0.0"`
- [ ] Update the `skills` list to reflect the 11 new skill names (remove all old skill names)
- [ ] Write the updated file
- [ ] Verify: the file contains `"version": "2.0.0"` and all 11 new skill names

The skills list in `plugin.json` should reference:
```
using-careerops
setting-up
capturing-fact
capturing-evidence
seeding-career-db
analyzing-jd
generating-resume
auditing-resume
humanizing-resume
logging-outcome
linting-career
getting-help
```

---

## Task 14 -- Update `CLAUDE.md` skill names table and data model description

- [ ] Read `P:\CareerOps\CLAUDE.md`
- [ ] Replace the skills table under "What Is Built" to list v2 skill names with `/careerops:` prefix
- [ ] Update the data model description to reflect v2: facts embedded in experience files, no standalone `career/facts/` directory
- [ ] Write the updated file
- [ ] Verify: `CLAUDE.md` no longer mentions old skill names like `capture-fact`, `ingest-jd`, `generate-resume`

### Updated skills table (replace existing `/skills/` section)

```
### Skills (`.claude/skills/`)
/careerops:setting-up               First-run wizard (new or returning user)
/careerops:capturing-fact           Record a new achievement (interactive)
/careerops:capturing-evidence <id>  Attach evidence source to a fact
/careerops:seeding-career-db <path> Import from .tex or .md resume file
/careerops:analyzing-jd <path>      Analyze a JD; outputs ranked_facts[]
/careerops:generating-resume <jd-id> Full pipeline: plan Q&A, compose, render, validate, audit
/careerops:auditing-resume <app-id> Re-run semantic auditor
/careerops:humanizing-resume <app-id> Surgical AI-marker cleanup
/careerops:logging-outcome <app-id> Record application result
/careerops:linting-career           Schema + ref + em-dash check
/careerops:getting-help             Command reference (add "full" for complete list)
```

### Updated data model description (replace existing `career/` tree description)

```
career/
  experiences/   X-*.yaml    Experience envelopes; facts[] array embedded inside each file
  projects/      P-*.yaml    Side projects; facts[] array embedded inside each file
  evidence/      E-*.yaml    Sources backing facts (reference fact IDs)
  applications/  A-*/        One folder per sent resume
    application.yaml         Registry + outcome
    rendercv-input.yaml      Exact YAML rendered to PDF
    claim-ledger.yaml        Bullet -> fact ID provenance map
    user_overrides.yaml      Per-application Tier 2 opt-ins (user-only)
    proposed-plan.yaml       Composer draft, awaiting approval
    audit-report.md          Auditor verdict + AI marker scan
    resume.pdf               The generated resume
    cover-letter.pdf         The generated cover letter
  jd-analysis/   JD-*.yaml   Analyzed job descriptions; includes ranked_facts[]
  contact/       contact.yaml
  education/     edu.yaml
  skills/        skills.yaml
  config/
    rules.yaml               Banned words, em-dash policy, page budgets
    rendercv-theme.yaml      Typst theme overrides

Note: career/facts/ no longer exists. Facts are embedded as facts[] arrays
inside career/experiences/X-*.yaml and career/projects/P-*.yaml.
```

---

## Execution Order

Tasks must be executed in this order:

1. Tasks 1-11 (create new skills) -- can be parallelized
2. Task 12 (delete old skills) -- only after all new skills are written and verified
3. Task 13 (update plugin.json) -- after Task 12
4. Task 14 (update CLAUDE.md) -- after Task 13

---

## Verification Checklist

After all tasks complete, verify:

- [ ] `ls P:\CareerOps\skills\` shows exactly: `using-careerops`, `setting-up`, `capturing-fact`, `capturing-evidence`, `seeding-career-db`, `analyzing-jd`, `generating-resume`, `auditing-resume`, `humanizing-resume`, `logging-outcome`, `linting-career`, `getting-help`, `rendercv`
- [ ] Each new SKILL.md starts with `---` YAML frontmatter containing `name:` and `description:`
- [ ] No SKILL.md contains em-dashes (U+2014)
- [ ] No SKILL.md contains hardcoded personal data (names, email addresses, organization names, file paths specific to any one user)
- [ ] All cross-skill invocations use `/careerops:` namespace
- [ ] `P:\CareerOps\.claude-plugin\plugin.json` contains `"version": "2.0.0"`
- [ ] `P:\CareerOps\CLAUDE.md` references v2 skill names only; no mention of `capture-fact`, `ingest-jd`, `generate-resume`, `lint-career`, `log-outcome`, `audit-resume`, `humanize-resume`, `career-init`, `career-help`, `seed-from-tex`, `seed-from-master`
- [ ] `P:\CareerOps\CLAUDE.md` data model section no longer references `career/facts/` as a standalone directory

---

## Self-Review Notes

- `setting-up` correctly implements both new-user and returning-user flows from the spec, driven by detection of `career/experiences/` content, not `career/facts/` (which is removed in v2).
- `seeding-career-db` writes facts as embedded `facts[]` arrays inside experience files, not as standalone `F-*.yaml` files. The `role_ref` and `employer` fields are explicitly excluded from embedded facts.
- `generating-resume` Step 0 is the inline planning Q&A that replaces the standalone `plan-resume` skill. It still allows power users to skip it by pre-creating `proposed-plan.yaml`.
- `generating-resume` Step 3 explicitly notes that `ranked_facts[]` is advisory sort order only and that all facts remain available to the composer via direct experience file reads.
- `generating-resume` Step 7 Gate 4 is updated to resolve fact IDs through experience/project `facts[]` arrays, not a flat `career/facts/` directory.
- `linting-career` explicitly notes the v2 data model shift and that the linter walks `experience.facts[]` arrays.
- `getting-help` default output matches the spec exactly, including the two-section layout (new here / applying for a job).
- No SKILL.md contains any personal name, email, employer, location, or filesystem path specific to any individual user.
- No em-dashes present in any task description or SKILL.md content.
