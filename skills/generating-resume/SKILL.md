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
- All `career/experiences/X-*.yaml` files (facts are read from embedded `facts[]` arrays)
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

Note: the claim-ledger must reference fact IDs that exist inside experience or project files (not standalone fact files, which no longer exist in v2).

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
