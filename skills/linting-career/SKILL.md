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
