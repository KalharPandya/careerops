# CareerOps v2 — Plugin Architecture Design

**Date:** 2026-05-13
**Status:** Approved for implementation

---

## Goal

Redesign the CareerOps Claude Code plugin from a collection of 15 manually-invoked skills into a proactive assistant that routes itself based on user intent. A user pastes a JD — the pipeline starts. A user describes an achievement — it gets captured. No slash commands required unless the user wants explicit control.

---

## Architecture Overview

Three layers work together:

1. **Bootstrap layer** — a `using-careerops` skill injected at SessionStart via hook. Primes Claude with routing rules, intent patterns, and state-awareness checks before any user interaction. Mirrors the superpowers `using-superpowers` mechanism exactly.

2. **Skill layer** — 11 user-invocable skills organized into 4 groups (Setup, Capture, Apply, Health). Renamed to verb-first gerund convention. Three skills removed vs. v1 (`career-status` → hook, `plan-resume` → absorbed into `generating-resume`, `seed-from-tex` + `seed-from-master` → unified `seeding-career-db`).

3. **Subagent layer** — 6 specialized agents (5 existing + 1 new `setup-guide`). JD analyzer gains relevance-ranking output; bullet composer reads ranked shortlist instead of all facts.

---

## Bootstrap: `using-careerops`

**Mechanism:** The SessionStart hook reads `skills/using-careerops/SKILL.md` and injects its full content as `additionalContext` JSON output. This means Claude reads the routing rules before the user says anything — no skill invocation needed.

**Content of the bootstrap skill:**

```
ROUTING RULES — follow before responding to any user message:

1. User shares a job description, job posting URL, or says "I want to apply to X":
   → MUST invoke analyzing-jd immediately. Do not ask clarifying questions first.

2. User describes an achievement, project, metric, or thing they built/shipped:
   → MUST invoke capturing-fact. Do not write it down manually.

3. User has no career/facts/ directory or facts/ is empty:
   → Surface: "Your career knowledge base is empty. Run /careerops:setting-up
     to initialize, then /careerops:seeding-career-db to import your resume."
     Do not attempt any generation or analysis.

4. User asks about resume, application, or job fit:
   → Check for existing JD analyses in career/jd-analysis/. If none, invoke
     analyzing-jd first. If one exists, proceed to generating-resume.

5. User asks for status, health, or "what do I have":
   → Run career_status.py and display the output inline. Do not invoke a skill.

6. If there is even a 1% chance any CareerOps skill applies — invoke it.
   Checking costs nothing. Skipping costs a missed capture.
```

**State checks injected at SessionStart:**

The hook also checks:
- `career/facts/` empty or missing → inject setup reminder as `<important-reminder>` block
- `career/contact/contact.yaml` missing → inject contact-setup reminder
- If both present → inject normal status dashboard output from `career_status.py`

---

## Skill Map

### BOOTSTRAP

| Skill | Trigger | What it does |
|---|---|---|
| `using-careerops` | SessionStart hook (auto-injected, also Claude-invocable) | Routing rules, intent patterns, state-awareness. Injected automatically at session start via hook. Claude Code can also invoke it explicitly when needed (e.g., after context compaction to reload routing rules). No `disable-model-invocation` restriction. |

### SETUP

| Skill | Replaces | What it does |
|---|---|---|
| `setting-up` | `career-init` | Full first-run wizard driven by `setup-guide` subagent. Detects new vs. returning user. New: scaffolds full directory tree, copies templates, collects profile, prompts to seed. Returning: shows current config as defaults, only re-asks what is unset. |

### CAPTURE

| Skill | Replaces | What it does |
|---|---|---|
| `capturing-fact` | `capture-fact` | Invokes `fact-curator` subagent. Unchanged behavior. |
| `capturing-evidence` | `capture-evidence` | Attaches evidence source to a fact. Unchanged behavior. |
| `seeding-career-db` | `seed-from-tex` + `seed-from-master` | Unified seeding skill. Auto-detects file type: `.tex` → LaTeX parser, `.md` → master doc parser, anything else → error with supported formats list. Single entry point replaces two skills. |

### APPLY

| Skill | Replaces | What it does |
|---|---|---|
| `analyzing-jd` | `ingest-jd` | Invokes updated `jd-analyzer` subagent. Outputs JD-*.yaml with `ranked_facts[]` section (fact IDs scored by relevance). |
| `generating-resume` | `generate-resume` + `plan-resume` | Full pipeline. Step 0 (previously `plan-resume`) is now an inline Q&A before composition, not a separate skill. Reads ranked_facts from JD analysis to give composer a pre-sorted shortlist. |
| `auditing-resume` | `audit-resume` | Standalone re-run of auditor. Unchanged behavior. |
| `humanizing-resume` | `humanize-resume` | AI-marker cleanup. Unchanged behavior. |
| `logging-outcome` | `log-outcome` | Record application result. Unchanged behavior. |

### HEALTH

| Skill | Replaces | What it does |
|---|---|---|
| `linting-career` | `lint-career` | Schema + reference + em-dash validation. Unchanged behavior. |
| `getting-help` | `career-help` | Default: shows 3-command quickstart. `/careerops:getting-help full` shows the complete reference. |

### REMOVED (not replaced by skills)

| Removed skill | Where it went |
|---|---|
| `career-status` | SessionStart hook output + bootstrap routing rule #5 |
| `plan-resume` | Absorbed as step 0 of `generating-resume` |
| `seed-from-tex` | Merged into `seeding-career-db` |
| `seed-from-master` | Merged into `seeding-career-db` |

---

## Subagent Map

| Agent | Change from v1 |
|---|---|
| `fact-curator` | None |
| `jd-analyzer` | Updated: scores each known fact against the JD using keyword overlap + semantic proximity. Outputs `ranked_facts[]` array in JD-*.yaml. |
| `bullet-composer` | Updated: reads ALL facts from `career/facts/` into context. Uses `ranked_facts[]` from JD analysis as a sort-order hint only — higher-scored facts are composed first, but nothing is excluded. Every fact is available for selection. No RAG-based filtering. |
| `cover-letter-composer` | None |
| `resume-auditor` | None |
| `setup-guide` | **New.** Drives the `setting-up` wizard interactively. Detects existing state (reads contact.yaml, config, facts count), presents sensible defaults, scaffolds missing directories, copies templates, writes config files. |

---

## Hook Map

| Hook | Event | Change from v1 |
|---|---|---|
| `inject-bootstrap` | SessionStart | **New.** Reads `skills/using-careerops/SKILL.md`, injects as `additionalContext`. Also runs `career_status.py` and injects output. Checks for empty facts/ and missing contact.yaml, injects appropriate `<important-reminder>` blocks. Replaces the simple `career_status.py` SessionStart hook. |
| `lint-yaml` | PostToolUse Write/Edit | None |
| `check-em-dashes` | PostToolUse Write/Edit | None |
| `validate-resume` | PostToolUse Write/Edit | None |

**Updated `hooks/hooks.json`:**

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [{
          "type": "command",
          "command": "python \"${CLAUDE_PLUGIN_ROOT}/scripts/session_start.py\""
        }]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          { "type": "command", "command": "python \"${CLAUDE_PLUGIN_ROOT}/scripts/lint_yaml.py\" \"$CLAUDE_FILE_PATHS\"" },
          { "type": "command", "command": "python \"${CLAUDE_PLUGIN_ROOT}/scripts/check_em_dashes.py\" \"$CLAUDE_FILE_PATHS\"" },
          { "type": "command", "command": "python \"${CLAUDE_PLUGIN_ROOT}/scripts/validate_resume.py\" --auto \"$CLAUDE_FILE_PATHS\"" }
        ]
      }
    ]
  }
}
```

The old `career_status.py` SessionStart hook is replaced by `session_start.py`, which handles bootstrap injection + state detection + status display in one script. The script outputs JSON with `hookSpecificOutput.additionalContext` containing the bootstrap skill content and any state-detected reminders, so Claude receives them as injected context rather than as stdout.

---

## Data Model Changes

### JD Analysis — `ranked_facts[]` (new field)

The `jd-analyzer` subagent appends a `ranked_facts` array to JD-*.yaml output:

```yaml
# JD-YYYY-MM-DD-company-role.yaml
id: JD-2026-05-13-acme-swe
company: Acme Corp
role: Software Engineer
...
keywords:
  required: [Python, LLM, RAG, agentic]
  preferred: [LangGraph, TypeScript]
ranked_facts:
  - fact_id: F-2025-oracle-rag-pipeline
    score: 0.94
    matched_keywords: [RAG, LLM, pipeline]
  - fact_id: F-2025-deloitte-1st-place
    score: 0.88
    matched_keywords: [agentic, LangGraph, orchestration]
  - fact_id: F-2025-vaultai-10-agents
    score: 0.81
    matched_keywords: [agentic, LLM, production]
```

**Scoring logic (in `jd-analyzer` agent prompt):**
- 1.0 = fact tech stack overlaps 3+ required keywords AND impact metric is strong
- 0.8–0.99 = 2+ required keyword matches
- 0.6–0.79 = 1 required or 2+ preferred keyword matches
- Below 0.6 = low relevance, included in ranked list but sorted to the bottom

All facts are scored and included regardless of score. The ranked list is a sort-order hint for the composer — no fact is excluded. The composer reads all facts from `career/facts/` directly; `ranked_facts[]` is advisory only.

**Schema change:** `jd-analysis.schema.json` gains an optional `ranked_facts` array. Existing JD files without it remain valid (linter does not require it).

### Facts Consolidated Into Experience Files

**Motivation:** The bullet-composer reads all facts into context on every generation. With facts in 61 separate files plus 14 experience envelope files, every generation requires 75 file reads. Since selective loading no longer happens, the per-file atomicity provides no benefit — only overhead. Consolidating facts into their parent experience file reduces reads to 14 (one per company/role) and organizes context the way Claude and humans both think about a resume: by employer.

**New structure — facts embedded in `X-*.yaml`:**

```yaml
# career/experiences/X-oracle-research-coop.yaml
id: X-oracle-research-coop
employer: Oracle
role: Research Assistant CO-OP
role_title: Research Assistant CO-OP
when: "2025-05 to present"
location: Burnaby, BC
facts:
  - id: F-2025-oracle-rag-pipeline
    type: achievement
    title: Built production RAG pipeline for document retrieval
    when: "2025-06"
    impact:
      metric: latency reduced 40%
      quantified: true
      outcome: shipped to production
    tech_actual: [Python, LangChain, Pinecone]
    metrics: ["40% latency reduction", "shipped to 3 internal teams"]
    tags: [RAG, LLM, backend]
    status: verified
  - id: F-2025-oracle-agent-orchestration
    ...
```

**What stays unchanged:**
- Fact IDs (`F-*.yaml` naming pattern) — still referenced by the claim ledger
- Evidence files (`E-*.yaml`) — still reference fact IDs, still live in `career/evidence/`
- All hard rules (immutable dates/employers, no fabrication)
- The `ranked_facts[]` in JD analysis still references fact IDs by the same IDs

**What changes:**
- `career/facts/` directory is eliminated. Facts live inside `career/experiences/X-*.yaml`
- The `role_ref` field is removed from each fact (redundant — the fact is inside its parent)
- `lint_yaml.py` walks `experience.facts[]` arrays instead of a flat `facts/` directory
- `fact-curator` appends to the matching experience file instead of creating a new `F-*.yaml`
- `jd-analyzer` scans `career/experiences/*.yaml` and extracts all `facts[].id` for scoring
- `bullet-composer` reads `career/experiences/*.yaml` — all facts arrive organized by employer
- `validate_resume.py` resolves fact IDs by scanning `experience.facts[].id` across all experience files

**Schema changes:**

`experience.schema.json` — add `facts` array:
```json
"facts": {
  "type": "array",
  "items": { "$ref": "embedded-fact.schema.json" }
}
```

`embedded-fact.schema.json` — new schema, same fields as current `fact.schema.json` minus `role_ref` and `employer` (inherited from parent experience):
```json
{
  "required": ["id", "type", "title", "when", "impact"],
  "properties": {
    "id":         { "type": "string", "pattern": "^F-" },
    "type":       { "enum": ["achievement", "responsibility", "skill_use"] },
    "title":      { "type": "string", "minLength": 5 },
    "when":       { "type": "string", "pattern": "^[0-9]{4}(-[0-9]{2})?$" },
    "impact":     { "$ref": "#/definitions/impact" },
    "tech_actual":{ "type": "array", "items": { "type": "string" } },
    "metrics":    { "type": "array", "items": { "type": "string" } },
    "framings":   { "type": "array", "items": { "$ref": "#/definitions/framing" } },
    "evidence":   { "type": "array", "items": { "type": "string", "pattern": "^E-" } },
    "tags":       { "type": "array", "items": { "type": "string" } },
    "status":     { "enum": ["verified", "pending-evidence", "retired"] }
  }
}
```

**Data migration — one-time, not a runtime concern:**

A migration script `scripts/migrate_facts.py` reads every `F-*.yaml` from `career/facts/`, looks up the matching experience via `role_ref`, appends the fact to that experience's `facts[]` array, then deletes the source file. Run once; idempotent (skips facts already present by ID). After migration, `career/facts/` directory is removed.

**Projects** (`P-*.yaml`) keep their own facts inline — they have no experience envelope. No change needed there.

**Evidence** (`E-*.yaml`) reference `fact_id: F-*` — the ID format is unchanged so evidence files need no modification.

---

## `setting-up` Wizard — New Behavior

The `setup-guide` subagent drives the wizard interactively. Behavior depends on detected state:

**New user (no career/ directory or empty facts/):**
1. Scaffold full directory tree:
   ```
   career/facts/        career/experiences/    career/projects/
   career/evidence/     career/applications/   career/jd-analysis/
   career/contact/      career/education/      career/skills/
   career/config/       inbox/                 raw_data/
   ```
2. Copy all templates from `${CLAUDE_PLUGIN_ROOT}/templates/` into appropriate directories
3. Ask Q1–Q4 (theme, header visibility, page budget, contact info) via AskUserQuestion
4. Write config files
5. Prompt: "Drop an existing resume in raw_data/ and run `/careerops:seeding-career-db` to import it, or run `/careerops:capturing-fact` to start adding achievements manually."

**Returning user (facts/ exists and is non-empty):**
1. Show current config values as defaults
2. Only ask about fields that are unset
3. Skip directory scaffolding entirely
4. End with summary of what changed

**Error guard:** If `setting-up` is invoked mid-session while facts exist, confirm before overwriting any config (never touch facts, experiences, applications, or JD analyses).

---

## `getting-help` — Tiered Output

Default (no arguments):

```
CareerOps — Quick Start

  New here?
    /careerops:setting-up              Initialize your career directory
    /careerops:seeding-career-db       Import an existing resume
    /careerops:capturing-fact          Add a new career achievement

  Applying for a job?
    /careerops:analyzing-jd            Analyze a job description
    /careerops:generating-resume       Generate a tailored resume PDF

  /careerops:getting-help full         Show all commands
```

Full (with "full" argument):

Complete command reference with all 11 skills, descriptions, and arguments.

---

## Naming Conventions

All skills use verb-first gerund form: `verb-ing-noun`.

| v1 name | v2 name |
|---|---|
| `career-init` | `setting-up` |
| `capture-fact` | `capturing-fact` |
| `capture-evidence` | `capturing-evidence` |
| `seed-from-tex` + `seed-from-master` | `seeding-career-db` |
| `ingest-jd` | `analyzing-jd` |
| `generate-resume` | `generating-resume` |
| `audit-resume` | `auditing-resume` |
| `humanize-resume` | `humanizing-resume` |
| `log-outcome` | `logging-outcome` |
| `lint-career` | `linting-career` |
| `career-help` | `getting-help` |
| `career-status` | (removed — SessionStart hook) |
| `plan-resume` | (removed — step 0 of generating-resume) |

---

## File Changes Summary

### New files
- `schemas/embedded-fact.schema.json` — fact schema without role_ref/employer (for embedding inside experiences)
- `scripts/migrate_facts.py` — one-time migration: merges career/facts/F-*.yaml into parent X-*.yaml files
- `skills/using-careerops/SKILL.md` — bootstrap skill
- `skills/setting-up/SKILL.md` — replaces career-init
- `skills/seeding-career-db/SKILL.md` — replaces seed-from-tex + seed-from-master
- `skills/analyzing-jd/SKILL.md` — replaces ingest-jd
- `skills/generating-resume/SKILL.md` — replaces generate-resume (absorbs plan-resume)
- `skills/capturing-fact/SKILL.md` — replaces capture-fact
- `skills/capturing-evidence/SKILL.md` — replaces capture-evidence
- `skills/auditing-resume/SKILL.md` — replaces audit-resume
- `skills/humanizing-resume/SKILL.md` — replaces humanize-resume
- `skills/logging-outcome/SKILL.md` — replaces log-outcome
- `skills/linting-career/SKILL.md` — replaces lint-career
- `skills/getting-help/SKILL.md` — replaces career-help
- `agents/setup-guide.md` — new wizard agent
- `scripts/session_start.py` — new SessionStart script (bootstrap inject + state check + status)

### Modified files
- `agents/jd-analyzer.md` — scan experiences/*.yaml for fact IDs; add relevance scoring
- `agents/bullet-composer.md` — read experiences/*.yaml; use ranked_facts as sort hint
- `agents/fact-curator.md` — append to matching experience file instead of creating F-*.yaml
- `hooks/hooks.json` — replace SessionStart command with session_start.py
- `schemas/experience.schema.json` — add optional facts[] array
- `schemas/jd-analysis.schema.json` — add optional ranked_facts array
- `scripts/lint_yaml.py` — walk experience.facts[] arrays; retire facts/ directory scanning
- `scripts/validate_resume.py` — resolve fact IDs from experience.facts[].id
- `scripts/career_status.py` — count facts by summing experience.facts[] lengths
- `.claude-plugin/plugin.json` — bump version to 2.0.0
- `CLAUDE.md` — update skill names and data model description

### Deleted files
- `skills/career-init/` — replaced by `skills/setting-up/`
- `skills/career-status/` — replaced by SessionStart hook
- `skills/career-help/` — replaced by `skills/getting-help/`
- `skills/capture-fact/` — replaced by `skills/capturing-fact/`
- `skills/capture-evidence/` — replaced by `skills/capturing-evidence/`
- `skills/seed-from-tex/` — replaced by `skills/seeding-career-db/`
- `skills/seed-from-master/` — replaced by `skills/seeding-career-db/`
- `skills/ingest-jd/` — replaced by `skills/analyzing-jd/`
- `skills/generate-resume/` — replaced by `skills/generating-resume/`
- `skills/plan-resume/` — absorbed into `skills/generating-resume/`
- `skills/audit-resume/` — replaced by `skills/auditing-resume/`
- `skills/humanize-resume/` — replaced by `skills/humanizing-resume/`
- `skills/log-outcome/` — replaced by `skills/logging-outcome/`
- `skills/lint-career/` — replaced by `skills/linting-career/`
- `scripts/career_status.py` — logic absorbed into session_start.py
- `schemas/fact.schema.json` — replaced by embedded-fact.schema.json (facts now live inside experiences)

---

## Hard Rules (unchanged from v1)

1. Em-dashes forbidden everywhere (U+2014, U+2015, U+2E3A, U+2E3B)
2. No fabrication — every bullet traces to a verified fact ID
3. Dates and employers are immutable in facts
4. Tier 2 reframing requires explicit per-application opt-in via user_overrides.yaml
5. Encapsulation requires user approval before render
