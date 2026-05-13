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
