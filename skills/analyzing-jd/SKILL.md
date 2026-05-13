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
