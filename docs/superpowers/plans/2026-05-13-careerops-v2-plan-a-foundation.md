# CareerOps v2: Plan A - Foundation (Schemas + Scripts)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Update schemas and scripts to support the v2 embedded-facts data model and new session_start hook mechanism.

**Architecture:** Three schema changes define the new data contracts. Five script changes implement the new runtime behavior. All changes maintain backward compatibility with old F-*.yaml structure during the migration window.

**Tech Stack:** Python 3, JSON Schema (draft 2020-12), existing _paths.py helper.

---

## Task Index

| # | Deliverable | File |
|---|---|---|
| A1 | Create embedded-fact schema | `schemas/embedded-fact.schema.json` |
| A2 | Update experience schema | `schemas/experience.schema.json` |
| A3 | Update jd-analysis schema | `schemas/jd-analysis.schema.json` |
| A4 | Create session_start.py | `scripts/session_start.py` |
| A5 | Update lint_yaml.py | `scripts/lint_yaml.py` |
| A6 | Update validate_resume.py | `scripts/validate_resume.py` |
| A7 | Create migrate_facts.py | `scripts/migrate_facts.py` |

---

## A1: Create `schemas/embedded-fact.schema.json`

**What:** New JSON Schema for facts embedded inside `X-*.yaml` experience files. Identical to `fact.schema.json` except `role_ref` and `employer` are removed (those fields are inherited from the parent experience envelope). The `role_title` field is also removed for the same reason.

**Why:** The `experience.schema.json` `facts[]` array needs a `$ref` target that does not duplicate employer/role_ref on every child object. Keeping a distinct schema preserves `additionalProperties: false` strictness.

**File to create:** `P:\CareerOps\schemas\embedded-fact.schema.json`

- [ ] Write the file with this exact content:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "embedded-fact.schema.json",
  "title": "CareerOps Embedded Fact",
  "description": "An atomic career fact embedded inside its parent experience envelope. Employer, role_ref, and role_title are inherited from the parent X-*.yaml and must not be repeated here.",
  "type": "object",
  "required": ["id", "type", "title", "when", "impact"],
  "additionalProperties": false,
  "properties": {
    "id": {
      "type": "string",
      "pattern": "^F-",
      "description": "Unique fact identifier, e.g. F-2025-oracle-rag-pipeline. Must be globally unique across all experience files."
    },
    "type": {
      "type": "string",
      "enum": ["achievement", "responsibility", "skill_use"]
    },
    "title": {
      "type": "string",
      "minLength": 5
    },
    "when": {
      "type": "string",
      "pattern": "^[0-9]{4}(-[0-9]{2})?$",
      "description": "YYYY or YYYY-MM -- IMMUTABLE"
    },
    "impact": {
      "type": "object",
      "required": ["metric", "quantified", "outcome"],
      "additionalProperties": false,
      "properties": {
        "metric": { "type": "string" },
        "quantified": { "type": "boolean" },
        "outcome": { "type": "string" }
      }
    },
    "tech_actual": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Technologies actually used -- verbatim, no embellishment"
    },
    "metrics": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Concrete, measurable claims"
    },
    "framings": {
      "type": "array",
      "description": "Pre-authored angles for composing bullets",
      "items": {
        "type": "object",
        "required": ["id", "angle", "sample"],
        "additionalProperties": false,
        "properties": {
          "id": { "type": "string" },
          "angle": { "type": "string" },
          "sample": { "type": "string" }
        }
      }
    },
    "evidence": {
      "type": "array",
      "items": {
        "type": "string",
        "pattern": "^E-"
      },
      "description": "Evidence IDs that back this fact"
    },
    "description": { "type": "string" },
    "tags": {
      "type": "array",
      "items": { "type": "string" }
    },
    "status": {
      "type": "string",
      "enum": ["verified", "pending-evidence", "retired"],
      "default": "pending-evidence"
    }
  }
}
```

- [ ] Verify: `python -c "import json; json.load(open('schemas/embedded-fact.schema.json'))"` exits 0 (from the CareerOps project root).

**Expected output:** No errors, file parses as valid JSON.

---

## A2: Update `schemas/experience.schema.json`

**What:** Add an optional `facts` array whose items conform to `embedded-fact.schema.json`. The existing `fact_refs` array is kept (backward compat) but deprecated. `additionalProperties: false` is maintained.

**Current file:** `P:\CareerOps\schemas\experience.schema.json`

**Exact change:** Add the `facts` property inside `"properties"` and `"$defs"` block. The full replacement content is below.

- [ ] Replace the entire file with:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "experience.schema.json",
  "title": "CareerOps Experience Envelope",
  "description": "A role/job that groups related facts. In v2, facts are embedded directly in the facts[] array. The legacy fact_refs[] array is kept for backward compatibility during migration.",
  "type": "object",
  "required": ["id", "employer", "role_title", "when_start", "when_end"],
  "additionalProperties": false,
  "properties": {
    "id": {
      "type": "string",
      "pattern": "^X-"
    },
    "employer": {
      "type": "string",
      "description": "IMMUTABLE"
    },
    "role_title": {
      "type": "string",
      "description": "IMMUTABLE"
    },
    "location": { "type": "string" },
    "when_start": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}$",
      "description": "YYYY-MM -- IMMUTABLE"
    },
    "when_end": {
      "oneOf": [
        { "type": "string", "pattern": "^[0-9]{4}-[0-9]{2}$" },
        { "type": "string", "enum": ["present"] }
      ],
      "description": "YYYY-MM or 'present' -- IMMUTABLE"
    },
    "team": { "type": "string" },
    "fact_refs": {
      "type": "array",
      "items": { "type": "string", "pattern": "^F-" },
      "description": "DEPRECATED (v1). References to standalone F-*.yaml files. Kept for backward compatibility. Migrate to facts[] embedded array."
    },
    "facts": {
      "type": "array",
      "description": "v2: Embedded fact objects. Replaces the standalone career/facts/ F-*.yaml files.",
      "items": {
        "type": "object",
        "required": ["id", "type", "title", "when", "impact"],
        "additionalProperties": false,
        "properties": {
          "id": {
            "type": "string",
            "pattern": "^F-",
            "description": "Globally unique fact ID"
          },
          "type": {
            "type": "string",
            "enum": ["achievement", "responsibility", "skill_use"]
          },
          "title": { "type": "string", "minLength": 5 },
          "when": {
            "type": "string",
            "pattern": "^[0-9]{4}(-[0-9]{2})?$",
            "description": "YYYY or YYYY-MM -- IMMUTABLE"
          },
          "impact": {
            "type": "object",
            "required": ["metric", "quantified", "outcome"],
            "additionalProperties": false,
            "properties": {
              "metric": { "type": "string" },
              "quantified": { "type": "boolean" },
              "outcome": { "type": "string" }
            }
          },
          "tech_actual": {
            "type": "array",
            "items": { "type": "string" }
          },
          "metrics": {
            "type": "array",
            "items": { "type": "string" }
          },
          "framings": {
            "type": "array",
            "items": {
              "type": "object",
              "required": ["id", "angle", "sample"],
              "additionalProperties": false,
              "properties": {
                "id": { "type": "string" },
                "angle": { "type": "string" },
                "sample": { "type": "string" }
              }
            }
          },
          "evidence": {
            "type": "array",
            "items": { "type": "string", "pattern": "^E-" }
          },
          "description": { "type": "string" },
          "tags": {
            "type": "array",
            "items": { "type": "string" }
          },
          "status": {
            "type": "string",
            "enum": ["verified", "pending-evidence", "retired"],
            "default": "pending-evidence"
          }
        }
      }
    },
    "display_order": {
      "type": "integer",
      "description": "Lower = shown earlier on resume"
    }
  }
}
```

**Note on `$ref` vs inline:** jsonschema validators that do not resolve relative `$ref` paths across files will reject `{ "$ref": "embedded-fact.schema.json" }` unless a resolver is configured. Inlining the fact object schema inside `experience.schema.json` avoids that dependency while keeping the same constraints. `embedded-fact.schema.json` continues to exist as the standalone contract for documentation and for use by the fact-curator subagent when writing isolated facts.

- [ ] Verify: `python -c "import json; json.load(open('schemas/experience.schema.json'))"` exits 0.
- [ ] Verify (backward compat): create a temp YAML with only `fact_refs` (no `facts` key) and run `lint_yaml.py` against it -- must pass schema validation. Example temp file:

```yaml
id: X-test-backward-compat
employer: TestCorp
role_title: Engineer
when_start: "2024-01"
when_end: present
fact_refs: []
```

- [ ] Verify (new structure): create a temp YAML with a `facts[]` array and run `lint_yaml.py` -- must pass schema validation. Example temp file:

```yaml
id: X-test-v2
employer: TestCorp
role_title: Engineer
when_start: "2024-01"
when_end: present
facts:
  - id: F-2024-test-thing
    type: achievement
    title: Built a test thing that works
    when: "2024-06"
    impact:
      metric: reduced latency 30%
      quantified: true
      outcome: shipped to production
    status: verified
```

**Expected output for both:** `[CAREEROPS LINT OK]` (no SCHEMA ERROR lines).

---

## A3: Update `schemas/jd-analysis.schema.json`

**What:** Add an optional `ranked_facts` array. Each item has a `fact_id` (string matching `^F-`), a `score` (number 0.0--1.0), and a `matched_keywords` array of strings. Existing JD files without `ranked_facts` remain valid; the field is not added to `required`.

**Current file:** `P:\CareerOps\schemas\jd-analysis.schema.json`

- [ ] Replace the entire file with:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "jd-analysis.schema.json",
  "title": "CareerOps JD Analysis",
  "description": "Structured analysis of a job description produced by jd-analyzer subagent",
  "type": "object",
  "required": ["id", "ingested_at", "source_file", "company", "role", "keywords_verbatim"],
  "additionalProperties": false,
  "properties": {
    "id": {
      "type": "string",
      "pattern": "^JD-"
    },
    "ingested_at": {
      "type": "string",
      "format": "date-time"
    },
    "source_file": { "type": "string" },
    "company": { "type": "string" },
    "role": { "type": "string" },
    "seniority": {
      "type": "string",
      "enum": ["junior", "mid", "senior", "staff", "principal", "unknown"]
    },
    "required_skills": {
      "type": "array",
      "items": { "type": "string" }
    },
    "preferred_skills": {
      "type": "array",
      "items": { "type": "string" }
    },
    "keywords_verbatim": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Exact strings lifted from JD text -- used in Gate 3 keyword check"
    },
    "red_flags": {
      "type": "array",
      "items": { "type": "string" }
    },
    "match_score_hint": {
      "type": "number",
      "minimum": 0,
      "maximum": 1
    },
    "target_facts": {
      "type": "array",
      "items": { "type": "string", "pattern": "^F-" },
      "description": "v1: Fact IDs the jd-analyzer recommends featuring. Superseded by ranked_facts[] in v2 but kept for backward compatibility."
    },
    "ranked_facts": {
      "type": "array",
      "description": "v2: All known facts scored by relevance to this JD. Higher score = more relevant. Advisory only -- bullet-composer reads all facts regardless. Sorted descending by score.",
      "items": {
        "type": "object",
        "required": ["fact_id", "score", "matched_keywords"],
        "additionalProperties": false,
        "properties": {
          "fact_id": {
            "type": "string",
            "pattern": "^F-",
            "description": "Fact ID -- references a fact embedded in career/experiences/X-*.yaml"
          },
          "score": {
            "type": "number",
            "minimum": 0,
            "maximum": 1,
            "description": "Relevance score: 1.0 = 3+ required keyword matches with strong metric; 0.8-0.99 = 2+ required; 0.6-0.79 = 1 required or 2+ preferred; <0.6 = low relevance"
          },
          "matched_keywords": {
            "type": "array",
            "items": { "type": "string" },
            "description": "Verbatim JD keywords that matched this fact"
          }
        }
      }
    },
    "role_type": {
      "type": "string",
      "enum": ["software-engineer", "ml-engineer", "ai-engineer", "devops", "data-engineer", "other"]
    },
    "notes": { "type": "string" }
  }
}
```

- [ ] Verify: `python -c "import json; json.load(open('schemas/jd-analysis.schema.json'))"` exits 0.
- [ ] Verify (backward compat): run `lint_yaml.py` against any existing `career/jd-analysis/JD-*.yaml` file that lacks `ranked_facts` -- must show `[CAREEROPS LINT OK]`.
- [ ] Verify (new field): validate a JD YAML that contains `ranked_facts` by running `lint_yaml.py` -- must show `[CAREEROPS LINT OK]`. Example addition to any JD YAML:

```yaml
ranked_facts:
  - fact_id: F-2025-oracle-rag-pipeline
    score: 0.94
    matched_keywords: [RAG, LLM, pipeline]
  - fact_id: F-2025-deloitte-1st-place
    score: 0.88
    matched_keywords: [agentic, LangGraph]
```

**Expected output:** No `SCHEMA ERROR` lines for either backward-compat or new-field test.

---

## A4: Create `scripts/session_start.py`

**What:** Replaces `career_status.py` as the SessionStart hook script. Outputs JSON to stdout in the format the Claude Code hook system expects for injecting `additionalContext`. Performs three jobs in one pass:

1. Reads `${CLAUDE_PLUGIN_ROOT}/skills/using-careerops/SKILL.md` and includes its content as the bootstrap routing rules (falls back gracefully if file missing -- Plan B creates it).
2. Detects career DB state: counts facts from embedded experience files (v2) and standalone F-*.yaml files (v1 backward compat); detects missing contact.yaml; checks for empty state.
3. Builds the `additionalContext` string and emits a single JSON object to stdout.

**Output format (single JSON object, one stdout write):**

```json
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "<full context string injected into Claude's system prompt>"
  }
}
```

The `additionalContext` value is a plain string containing:
- The bootstrap skill content (if SKILL.md found), wrapped in a `<careerops-routing-rules>` tag
- A `<careerops-status>` block with counts (facts, experiences, applications, JDs)
- Zero or more `<important-reminder>` blocks if empty state or missing contact is detected

**File to create:** `P:\CareerOps\scripts\session_start.py`

- [ ] Write the file with this exact content:

```python
#!/usr/bin/env python3
"""
CareerOps SessionStart hook script.

Outputs a single JSON object to stdout with hookSpecificOutput.additionalContext
containing the bootstrap routing rules (from using-careerops/SKILL.md) plus
career DB state (fact counts, empty-state warnings, missing contact warning).

Used by hooks/hooks.json SessionStart event.
Format: {"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": "..."}}
"""

import json
import os
import sys
import yaml
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from _paths import career_dir, data_root


# ---------------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------------

def plugin_root() -> Path:
    """
    Resolve the plugin root directory.
    Checks CLAUDE_PLUGIN_ROOT env var first, then falls back to the
    directory two levels above this script (scripts/ -> plugin root).
    """
    env = os.environ.get("CLAUDE_PLUGIN_ROOT")
    if env:
        return Path(env).resolve()
    # scripts/session_start.py -> scripts/ -> plugin root
    return Path(__file__).resolve().parent.parent


def bootstrap_skill_path() -> Path:
    return plugin_root() / "skills" / "using-careerops" / "SKILL.md"


# ---------------------------------------------------------------------------
# Fact counting -- handles both v1 (facts/ dir) and v2 (experience.facts[])
# ---------------------------------------------------------------------------

def count_facts(career: Path) -> tuple:
    """
    Returns (total_facts, source_description).
    Counts embedded facts from experience files (v2) first.
    Falls back to standalone F-*.yaml files (v1) if experiences/ has no embedded facts.
    Reports both if both are present (transition state).
    """
    v2_facts = 0
    v2_experiences = 0
    experiences_dir = career / "experiences"

    if experiences_dir.exists():
        for exp_path in sorted(experiences_dir.glob("X-*.yaml")):
            try:
                with open(exp_path, encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                if data and isinstance(data.get("facts"), list):
                    v2_facts += len(data["facts"])
                    v2_experiences += 1
            except Exception:
                pass

    v1_facts = 0
    facts_dir = career / "facts"
    if facts_dir.exists():
        v1_facts = len(list(facts_dir.glob("F-*.yaml")))

    total = v2_facts + v1_facts

    if v2_facts > 0 and v1_facts == 0:
        desc = f"{v2_facts} facts across {v2_experiences} experience file(s)"
    elif v1_facts > 0 and v2_facts == 0:
        desc = f"{v1_facts} standalone fact file(s) in career/facts/"
    elif v2_facts > 0 and v1_facts > 0:
        desc = (
            f"{v2_facts} embedded fact(s) in experience files + "
            f"{v1_facts} standalone fact file(s) (migration in progress)"
        )
    else:
        desc = "0 facts"

    return total, desc


def count_applications(career: Path) -> int:
    apps_dir = career / "applications"
    if not apps_dir.exists():
        return 0
    return len([d for d in apps_dir.iterdir() if d.is_dir() and d.name.startswith("A-")])


def count_jd_analyses(career: Path) -> int:
    jd_dir = career / "jd-analysis"
    if not jd_dir.exists():
        return 0
    return len(list(jd_dir.glob("JD-*.yaml")))


def contact_exists(career: Path) -> bool:
    return (career / "contact" / "contact.yaml").exists()


# ---------------------------------------------------------------------------
# Context assembly
# ---------------------------------------------------------------------------

def build_additional_context(career: Path) -> str:
    """Assemble the full additionalContext string."""
    parts = []

    # --- Bootstrap routing rules ---
    skill_path = bootstrap_skill_path()
    if skill_path.exists():
        try:
            skill_content = skill_path.read_text(encoding="utf-8")
            parts.append(
                "<careerops-routing-rules>\n"
                + skill_content.strip()
                + "\n</careerops-routing-rules>"
            )
        except Exception as e:
            parts.append(
                f"<careerops-routing-rules>\n"
                f"[ERROR: could not read SKILL.md: {e}]\n"
                f"</careerops-routing-rules>"
            )
    else:
        # Plan B has not been implemented yet; emit a minimal inline reminder
        parts.append(
            "<careerops-routing-rules>\n"
            "CareerOps bootstrap skill not yet installed "
            f"(expected at {skill_path}). "
            "Plan B (skills layer) will create it. "
            "Until then: if the user shares a JD, analyze it. "
            "If they describe an achievement, capture it. "
            "If they ask for a resume, run the generation pipeline.\n"
            "</careerops-routing-rules>"
        )

    # --- Career DB status ---
    total_facts, facts_desc = count_facts(career)
    apps = count_applications(career)
    jds = count_jd_analyses(career)

    status_lines = [
        "<careerops-status>",
        f"  Facts      : {facts_desc}",
        f"  Applications: {apps}",
        f"  JDs analyzed: {jds}",
        "</careerops-status>",
    ]
    parts.append("\n".join(status_lines))

    # --- State-based important reminders ---
    reminders = []

    if total_facts == 0:
        reminders.append(
            "<important-reminder>\n"
            "Your CareerOps career knowledge base is empty. "
            "Run /careerops:setting-up to initialize, then "
            "/careerops:seeding-career-db to import your existing resume. "
            "Do not attempt resume generation or JD analysis until facts exist.\n"
            "</important-reminder>"
        )

    if not contact_exists(career):
        reminders.append(
            "<important-reminder>\n"
            "career/contact/contact.yaml is missing. "
            "Run /careerops:setting-up to set up your contact information. "
            "Resume generation will fail without it.\n"
            "</important-reminder>"
        )

    parts.extend(reminders)

    return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    career = career_dir()

    additional_context = build_additional_context(career)

    output = {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": additional_context,
        }
    }

    # Single write to stdout -- the hook system reads this JSON
    print(json.dumps(output, ensure_ascii=False))


if __name__ == "__main__":
    main()
```

- [ ] Verify (SKILL.md absent): `python scripts/session_start.py` outputs valid JSON (pipe to `python -m json.tool` to confirm). The `additionalContext` must contain `<careerops-routing-rules>` and `<careerops-status>`.
- [ ] Verify (JSON structure): `python scripts/session_start.py | python -c "import json,sys; d=json.load(sys.stdin); assert 'hookSpecificOutput' in d; assert d['hookSpecificOutput']['hookEventName'] == 'SessionStart'; print('JSON OK')"` prints `JSON OK`.
- [ ] Verify (empty career): Run with `CAREEROPS_DATA_DIR` pointing to a temp dir with no `career/` subdirectory. The output JSON must include an `<important-reminder>` block about the empty knowledge base.
- [ ] Verify (SKILL.md present): Create `skills/using-careerops/SKILL.md` with dummy content, then run `session_start.py`. The `additionalContext` must include that content inside `<careerops-routing-rules>`.

**Expected stdout:** A single-line JSON object (no other text). Any errors from this script must be on stderr, not stdout, to avoid corrupting the hook JSON output.

---

## A5: Update `scripts/lint_yaml.py`

**What:** The linter must validate experience files that contain embedded `facts[]` arrays (v2) while keeping backward compat for the v1 structure (`fact_refs`, standalone `facts/` dir). Specific changes:

1. `check_refs` for `experiences` subdir: if the experience file has a `facts[]` array, validate each embedded fact's `evidence[]` references against `career/evidence/`. Also validate each embedded fact's `id` starts with `F-`. Keep the existing `fact_refs` check for v1 backward compat.
2. `check_refs` for `evidence` subdir: the `backs_facts` check currently looks for `F-*.yaml` in `career/facts/`. Add a fallback that also searches embedded `facts[].id` across all `X-*.yaml` files when the standalone file is not found.
3. The `SCHEMA_MAP` entry for `facts` stays in place (v1 backward compat). Do not remove it.

**File to modify:** `P:\CareerOps\scripts\lint_yaml.py`

- [ ] Add a helper function `collect_all_embedded_fact_ids` immediately after the `id_exists` function (before `check_refs`):

```python
def collect_all_embedded_fact_ids() -> set:
    """Collect all fact IDs embedded in career/experiences/X-*.yaml files (v2 structure)."""
    ids = set()
    experiences_dir = CAREER_DIR / 'experiences'
    if not experiences_dir.exists():
        return ids
    for exp_path in experiences_dir.glob('X-*.yaml'):
        try:
            with open(exp_path, encoding='utf-8') as f:
                data = yaml.safe_load(f)
            if data and isinstance(data.get('facts'), list):
                for fact in data['facts']:
                    if isinstance(fact, dict) and fact.get('id'):
                        ids.add(fact['id'])
        except Exception:
            pass
    return ids
```

- [ ] Replace the `check_refs` function with this updated version that handles both v1 and v2:

```python
def check_refs(data: dict, subdir: str, path: Path) -> list:
    errors = []

    if subdir == 'facts':
        # v1: standalone F-*.yaml files
        role_ref = data.get('role_ref')
        if role_ref and not id_exists(role_ref, 'experiences'):
            errors.append(f"role_ref {role_ref} not found in career/experiences/")
        for ev_id in (data.get('evidence') or []):
            if not id_exists(ev_id, 'evidence'):
                errors.append(f"evidence ref {ev_id} not found in career/evidence/")

    elif subdir == 'evidence':
        for fact_id in (data.get('backs_facts') or []):
            # Check v1 standalone file first, then v2 embedded
            if not id_exists(fact_id, 'facts'):
                embedded_ids = collect_all_embedded_fact_ids()
                if fact_id not in embedded_ids:
                    errors.append(
                        f"backs_facts ref {fact_id} not found in career/facts/ "
                        f"or embedded in any career/experiences/X-*.yaml"
                    )

    elif subdir in ('experiences', 'projects'):
        # v1: fact_refs pointing to standalone F-*.yaml
        for fact_id in (data.get('fact_refs') or []):
            if not id_exists(fact_id, 'facts'):
                errors.append(f"fact_refs ref {fact_id} not found in career/facts/")

        # v2: embedded facts[] array
        embedded_facts = data.get('facts') or []
        seen_ids = set()
        for i, fact in enumerate(embedded_facts):
            if not isinstance(fact, dict):
                errors.append(f"facts[{i}] is not a mapping")
                continue
            fact_id = fact.get('id', '')
            if not fact_id.startswith('F-'):
                errors.append(f"facts[{i}].id '{fact_id}' does not start with 'F-'")
            if fact_id in seen_ids:
                errors.append(f"facts[{i}].id '{fact_id}' is duplicated within this file")
            seen_ids.add(fact_id)
            for ev_id in (fact.get('evidence') or []):
                if not id_exists(ev_id, 'evidence'):
                    errors.append(
                        f"facts[{i}] ({fact_id}): evidence ref {ev_id} not found in career/evidence/"
                    )

    elif subdir == 'applications':
        fname = path.name
        if fname == 'claim-ledger.yaml':
            jd_ref = data.get('jd_ref')
            if jd_ref and not id_exists(jd_ref, 'jd-analysis'):
                errors.append(f"jd_ref {jd_ref} not found in career/jd-analysis/")
            # Resolve fact IDs from both v1 (facts/ dir) and v2 (embedded in experiences)
            embedded_ids = collect_all_embedded_fact_ids()
            for bullet in (data.get('bullets') or []):
                for fact_id in (bullet.get('backed_by') or []):
                    if not id_exists(fact_id, 'facts') and fact_id not in embedded_ids:
                        errors.append(
                            f"bullet {bullet.get('bullet_id','?')}: backed_by {fact_id} "
                            f"not found in career/facts/ or embedded in any X-*.yaml"
                        )
        elif fname == 'application.yaml':
            jd_ref = data.get('jd_ref')
            if jd_ref and not id_exists(jd_ref, 'jd-analysis'):
                errors.append(f"jd_ref {jd_ref} not found in career/jd-analysis/")

    return errors
```

- [ ] Verify (v1 backward compat): lint an existing `X-*.yaml` with only `fact_refs` (no `facts` key). Must output `[CAREEROPS LINT OK]` (no errors).
- [ ] Verify (v2 embedded facts): lint the test file from A2 verification (the one with `facts[]` array). Must output `[CAREEROPS LINT OK]`.
- [ ] Verify (bad evidence ref in embedded fact): create a temp experience YAML with an embedded fact that has `evidence: [E-nonexistent]`. Lint must output `[CAREEROPS LINT REF ERROR]` for that evidence reference.
- [ ] Verify (duplicate fact ID): create a temp experience YAML with two embedded facts sharing the same `id`. Lint must output `[CAREEROPS LINT REF ERROR]` reporting the duplicate.

**Expected behavior:** All existing v1 YAML files continue to pass. New v2 files with embedded facts pass. Invalid embedded facts produce clear REF ERROR messages.

---

## A6: Update `scripts/validate_resume.py`

**What:** Gate 4 (`gate4_fact_traceability`) currently resolves fact IDs by checking `career/facts/F-{id}.yaml`. In v2, facts live inside `career/experiences/X-*.yaml` under the `facts[]` array. The `fact_exists` helper must check both locations.

**File to modify:** `P:\CareerOps\scripts\validate_resume.py`

- [ ] Replace the `fact_exists` helper function (lines 80--81 in current file) with this expanded version:

```python
def collect_all_fact_ids() -> set:
    """
    Collect all known fact IDs from both storage locations:
    - v1: career/facts/F-*.yaml (standalone files, stem = fact ID)
    - v2: career/experiences/X-*.yaml (embedded in facts[] array)
    Returns a set of all fact ID strings found.
    """
    ids = set()

    # v1: standalone fact files
    facts_dir = CAREER_DIR / 'facts'
    if facts_dir.exists():
        for p in facts_dir.glob('F-*.yaml'):
            ids.add(p.stem)

    # v2: embedded facts inside experience envelopes
    experiences_dir = CAREER_DIR / 'experiences'
    if experiences_dir.exists():
        for exp_path in experiences_dir.glob('X-*.yaml'):
            try:
                exp_data = load_yaml(exp_path)
                if exp_data and isinstance(exp_data.get('facts'), list):
                    for fact in exp_data['facts']:
                        if isinstance(fact, dict) and fact.get('id'):
                            ids.add(fact['id'])
            except Exception:
                pass

    return ids


def fact_exists(fact_id: str) -> bool:
    """Check if a fact ID exists in either the v1 facts/ directory or v2 embedded in experiences."""
    # Fast path: v1 standalone file
    if (CAREER_DIR / 'facts' / f'{fact_id}.yaml').exists():
        return True
    # Slower path: scan experience files for embedded fact
    experiences_dir = CAREER_DIR / 'experiences'
    if not experiences_dir.exists():
        return False
    for exp_path in experiences_dir.glob('X-*.yaml'):
        try:
            exp_data = load_yaml(exp_path)
            if exp_data and isinstance(exp_data.get('facts'), list):
                for fact in exp_data['facts']:
                    if isinstance(fact, dict) and fact.get('id') == fact_id:
                        return True
        except Exception:
            pass
    return False
```

- [ ] Also update `gate4_fact_traceability` to use `collect_all_fact_ids()` for the full ledger scan (more efficient than one `fact_exists` call per bullet when there are many bullets). Replace the function body:

```python
def gate4_fact_traceability(app_dir: Path) -> tuple:
    """Gate 4: Every bullet in claim-ledger maps to a real fact ID (v1 or v2 storage)."""
    ledger_path = app_dir / 'claim-ledger.yaml'
    if not ledger_path.exists():
        return False, 'claim-ledger.yaml not found'
    ledger = load_yaml(ledger_path) or {}
    bullets = ledger.get('bullets', [])
    if not bullets:
        return True, 'No bullets in claim-ledger (skip)'

    # Build the full fact ID set once (covers both v1 and v2 storage)
    known_ids = collect_all_fact_ids()

    dangling = []
    for bullet in bullets:
        for fact_id in (bullet.get('backed_by') or []):
            if fact_id not in known_ids:
                dangling.append(f"Bullet {bullet.get('bullet_id', '?')}: {fact_id} not found")
    if dangling:
        return False, f'{len(dangling)} dangling fact ref(s):\n  ' + '\n  '.join(dangling)
    return True, f'All {len(bullets)} bullets traced to valid facts'
```

- [ ] Verify (v1 mode): run `validate_resume.py <existing-app-id>` where the facts are still in `career/facts/`. Gate 4 must PASS.
- [ ] Verify (v2 mode): move one fact to an experience file's `facts[]` array, remove the standalone file, rerun validation. Gate 4 must still PASS.
- [ ] Verify (dangling ref): add a fake fact ID to a bullet's `backed_by` list in a test claim-ledger. Gate 4 must FAIL with that ID listed as dangling.

**Expected behavior:** Gate 4 passes regardless of whether facts live in v1 or v2 storage. The `collect_all_fact_ids()` helper is efficient because it builds the full set once per validation run.

---

## A7: Create `scripts/migrate_facts.py`

**What:** One-time migration utility. Reads every `F-*.yaml` from `career/facts/`, finds the matching experience file via the fact's `role_ref` field, appends the fact (minus `role_ref`, `employer`, `role_title` -- those are inherited) to that experience's `facts[]` array, then deletes the source file. Idempotent: skips any fact whose `id` is already present in the target experience's `facts[]`. After all facts are migrated, removes the empty `career/facts/` directory.

**File to create:** `P:\CareerOps\scripts\migrate_facts.py`

- [ ] Write the file with this exact content:

```python
#!/usr/bin/env python3
"""
CareerOps v2 migration utility.

Moves standalone F-*.yaml fact files from career/facts/ into their parent
X-*.yaml experience files under the facts[] array.

Usage:
  python scripts/migrate_facts.py              # dry run (no writes)
  python scripts/migrate_facts.py --apply      # execute migration
  python scripts/migrate_facts.py --apply --verbose  # show each fact moved

This script is NOT run automatically. Run it once after upgrading to v2.
It is idempotent: re-running after a partial migration skips already-moved facts.

After a successful --apply run, career/facts/ will be empty and removed.
Evidence files (E-*.yaml) are NOT modified -- they reference fact IDs by string,
which are unchanged.
"""

import argparse
import os
import sys
import yaml
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from _paths import career_dir


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_yaml(path: Path):
    with open(path, encoding='utf-8') as f:
        return yaml.safe_load(f)


def dump_yaml(data: dict, path: Path):
    with open(path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)


def strip_inherited_fields(fact: dict) -> dict:
    """
    Remove fields that are inherited from the parent experience envelope:
    role_ref, employer, role_title.
    These are redundant inside X-*.yaml and not present in embedded-fact.schema.json.
    """
    stripped = dict(fact)
    for field in ('role_ref', 'employer', 'role_title'):
        stripped.pop(field, None)
    return stripped


def find_experience_for_fact(fact: dict, experiences_dir: Path) -> tuple:
    """
    Find the X-*.yaml file that should contain this fact.
    Uses fact['role_ref'] (e.g. 'X-oracle-research-coop') to locate the file.
    Returns (exp_path, exp_data) or (None, None) if not found.
    """
    role_ref = fact.get('role_ref')
    if not role_ref:
        return None, None
    exp_path = experiences_dir / f'{role_ref}.yaml'
    if not exp_path.exists():
        return None, None
    try:
        exp_data = load_yaml(exp_path)
    except Exception as e:
        print(f'  [ERROR] Could not load {exp_path}: {e}')
        return None, None
    return exp_path, exp_data


def fact_already_embedded(fact_id: str, exp_data: dict) -> bool:
    """Return True if a fact with this ID is already in exp_data['facts']."""
    existing_facts = exp_data.get('facts') or []
    return any(
        isinstance(f, dict) and f.get('id') == fact_id
        for f in existing_facts
    )


# ---------------------------------------------------------------------------
# Migration logic
# ---------------------------------------------------------------------------

def migrate(career: Path, apply: bool, verbose: bool) -> int:
    """
    Perform (or dry-run) the migration.
    Returns the number of facts that would be (or were) migrated.
    """
    facts_dir = career / 'facts'
    experiences_dir = career / 'experiences'

    if not facts_dir.exists():
        print('[migrate_facts] career/facts/ does not exist -- nothing to migrate.')
        return 0

    if not experiences_dir.exists():
        print('[migrate_facts] career/experiences/ does not exist -- cannot migrate.')
        return 0

    fact_files = sorted(facts_dir.glob('F-*.yaml'))
    if not fact_files:
        print('[migrate_facts] career/facts/ is empty -- nothing to migrate.')
        return 0

    print(f'[migrate_facts] Found {len(fact_files)} fact file(s) in career/facts/')
    if not apply:
        print('[migrate_facts] DRY RUN -- pass --apply to execute changes.')
    print()

    migrated = 0
    skipped_already_present = 0
    skipped_no_role_ref = 0
    skipped_no_experience = 0
    errors = 0

    # Track which experience files need to be written (path -> updated data)
    pending_writes: dict[Path, dict] = {}

    for fact_path in fact_files:
        try:
            fact = load_yaml(fact_path)
        except Exception as e:
            print(f'  [ERROR] Could not load {fact_path.name}: {e}')
            errors += 1
            continue

        if not fact or not isinstance(fact, dict):
            print(f'  [SKIP] {fact_path.name}: empty or not a mapping')
            skipped_no_role_ref += 1
            continue

        fact_id = fact.get('id', fact_path.stem)
        role_ref = fact.get('role_ref')

        if not role_ref:
            print(f'  [SKIP] {fact_id}: no role_ref -- cannot determine parent experience')
            skipped_no_role_ref += 1
            continue

        exp_path, exp_data = find_experience_for_fact(fact, experiences_dir)

        if exp_path is None:
            print(f'  [SKIP] {fact_id}: role_ref {role_ref} not found in experiences/')
            skipped_no_experience += 1
            continue

        # Use the pending write buffer so multiple facts to the same file
        # are batched into one write
        working_data = pending_writes.get(exp_path, exp_data)

        if fact_already_embedded(fact_id, working_data):
            if verbose:
                print(f'  [SKIP] {fact_id}: already embedded in {exp_path.name}')
            skipped_already_present += 1
            continue

        # Append the stripped fact to the experience's facts[] array
        if 'facts' not in working_data or working_data['facts'] is None:
            working_data['facts'] = []

        stripped = strip_inherited_fields(fact)
        working_data['facts'].append(stripped)
        pending_writes[exp_path] = working_data

        action = 'MIGRATE' if apply else 'WOULD MIGRATE'
        print(f'  [{action}] {fact_id} -> {exp_path.name}')
        if verbose:
            print(f'           title: {fact.get("title", "?")}')
        migrated += 1

    print()

    # --- Write updated experience files ---
    if apply and pending_writes:
        for exp_path, updated_data in pending_writes.items():
            try:
                dump_yaml(updated_data, exp_path)
                print(f'  [WRITTEN] {exp_path.name}')
            except Exception as e:
                print(f'  [ERROR] Could not write {exp_path.name}: {e}')
                errors += 1

        # Delete the source fact files for successfully migrated facts
        for fact_path in fact_files:
            try:
                fact = load_yaml(fact_path)
                if not fact:
                    continue
                fact_id = fact.get('id', fact_path.stem)
                role_ref = fact.get('role_ref')
                if not role_ref:
                    continue
                exp_path = experiences_dir / f'{role_ref}.yaml'
                if not exp_path.exists():
                    continue
                # Re-read to confirm the fact is now present before deleting
                written_data = load_yaml(exp_path)
                if fact_already_embedded(fact_id, written_data or {}):
                    fact_path.unlink()
                    if verbose:
                        print(f'  [DELETED] {fact_path.name}')
            except Exception as e:
                print(f'  [ERROR] Could not delete {fact_path.name}: {e}')
                errors += 1

        # Remove career/facts/ if it is now empty
        remaining = list(facts_dir.glob('F-*.yaml'))
        if not remaining:
            try:
                # Remove any leftover non-YAML files first, then the dir
                for leftover in facts_dir.iterdir():
                    leftover.unlink()
                facts_dir.rmdir()
                print('\n  [DONE] career/facts/ directory removed (all facts migrated).')
            except Exception as e:
                print(f'\n  [WARN] Could not remove career/facts/ directory: {e}')
        else:
            print(
                f'\n  [WARN] {len(remaining)} fact file(s) remain in career/facts/ '
                f'(could not be migrated). Review manually.'
            )

    # --- Summary ---
    print()
    print('[migrate_facts] Summary:')
    print(f'  Migrated              : {migrated}')
    print(f'  Already embedded      : {skipped_already_present}')
    print(f'  No role_ref (skipped) : {skipped_no_role_ref}')
    print(f'  No experience found   : {skipped_no_experience}')
    print(f'  Errors                : {errors}')

    if not apply and migrated > 0:
        print()
        print(f'[migrate_facts] Re-run with --apply to execute {migrated} migration(s).')

    return migrated


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description=(
            'CareerOps v2 migration: move F-*.yaml facts into parent X-*.yaml experience files.'
        )
    )
    parser.add_argument(
        '--apply',
        action='store_true',
        help='Execute the migration (default is dry run)',
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Print additional detail for each fact',
    )
    args = parser.parse_args()

    career = career_dir()
    migrate(career, apply=args.apply, verbose=args.verbose)


if __name__ == '__main__':
    main()
```

- [ ] Verify (dry run): `python scripts/migrate_facts.py` with facts in `career/facts/` outputs `WOULD MIGRATE` lines and the summary, but does NOT modify any files.
- [ ] Verify (--apply): `python scripts/migrate_facts.py --apply` moves facts into experience files, deletes source F-*.yaml files, and removes `career/facts/` if empty. Re-running immediately after outputs `Already embedded: N, Migrated: 0`.
- [ ] Verify (idempotent): run `--apply` twice in a row. Second run must report `Migrated: 0, Already embedded: N`.
- [ ] Verify (no role_ref): add a test fact file without `role_ref`. The script must skip it and report `No role_ref (skipped): 1` without crashing.
- [ ] Verify (missing experience): add a test fact file with `role_ref: X-nonexistent`. The script must skip it and report `No experience found: 1`.

**Expected behavior:** Migration is safe (dry run by default), idempotent (skips already-moved facts), and leaves the career DB in a consistent state where all facts are queryable via `collect_all_fact_ids()` from both lint_yaml.py and validate_resume.py.

---

## Self-Review Checklist

Before marking this plan complete, verify:

- [ ] **A1 (embedded-fact schema):** Every field from `fact.schema.json` is present except `role_ref`, `employer`, `role_title`. The `additionalProperties: false` constraint is preserved. The `id` pattern `^F-` is preserved.
- [ ] **A2 (experience schema):** `fact_refs` is still present (backward compat). `facts` array is added as optional. `required` does NOT include `facts` or `fact_refs` (both optional). The inline fact object definition matches embedded-fact.schema.json field-for-field.
- [ ] **A3 (jd-analysis schema):** `ranked_facts` is in `properties` but NOT in `required`. Each `ranked_facts` item has `fact_id` (^F- pattern), `score` (0--1), `matched_keywords` (array of strings). Old `target_facts` field is preserved.
- [ ] **A4 (session_start.py):** Outputs valid JSON on stdout only. All other output (warnings, errors) goes to stderr. SKILL.md absence is a graceful fallback, not an error. Both v1 and v2 fact counts are surfaced. The `hookEventName` value is exactly `"SessionStart"`.
- [ ] **A5 (lint_yaml.py):** `collect_all_embedded_fact_ids()` is added before `check_refs`. Evidence refs inside embedded facts are validated. Duplicate fact IDs within one experience file are detected. The v1 `fact_refs` check is preserved unmodified.
- [ ] **A6 (validate_resume.py):** `collect_all_fact_ids()` returns IDs from both `career/facts/` and `experiences/X-*.yaml`. `fact_exists()` checks both locations. `gate4_fact_traceability` calls `collect_all_fact_ids()` once rather than `fact_exists()` per bullet.
- [ ] **A7 (migrate_facts.py):** Dry run is the default (no `--apply` = no writes). `strip_inherited_fields` removes exactly `role_ref`, `employer`, `role_title`. Idempotency uses `fact_already_embedded` by ID. The facts directory is removed only when empty after migration.
- [ ] **No TBD/TODO/placeholder lines** in any code block above.
- [ ] **Function names are consistent:** `collect_all_embedded_fact_ids` in lint_yaml.py; `collect_all_fact_ids` in validate_resume.py (broader scope -- includes v1 files, hence different name). `fact_exists` is kept in validate_resume.py as the per-ID lookup. `count_facts` is session_start.py only.
- [ ] **Em-dash rule:** no em-dash characters (U+2014, U+2015, U+2E3A, U+2E3B) appear anywhere in this document or the code blocks above.

---

## Dependency Order

Tasks are independent of each other EXCEPT:

- A5 depends on A1 and A2 existing (lint needs the schemas to validate against)
- A6 does not depend on any schema (it uses Python dict inspection, not schema validation)
- A4 depends on nothing in this plan (reads SKILL.md path only, which Plan B creates)
- A7 depends on A2 (the experience schema must accept `facts[]` before migration writes to it)

Recommended execution order: **A1 -> A2 -> A3 -> A4 -> A5 -> A6 -> A7**

All seven tasks can be verified independently after writing.
