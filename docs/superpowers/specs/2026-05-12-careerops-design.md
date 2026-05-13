# CareerOps — Design Spec

**Date:** 2026-05-12
**Owner:** Kalhar Pandya
**Status:** Draft for review
**Project root:** `P:\Resumes\Claude-automations`

---

## 1. Purpose

CareerOps is a local-first, evidence-backed, Claude Code-native resume automation system. It generates job-tailored PDF resumes from a structured career knowledge base in which every resume claim traces to a verified source fact.

The system is not a resume rewriter. It is a CareerOps knowledge OS: capture once, generate many times, never fabricate, always audit.

---

## 2. Hard rules

These rules are enforced at multiple layers (subagent prompts + deterministic code) and cannot be silently bypassed.

1. **Em-dashes are forbidden in all resume output artifacts.** Zero tolerance for U+2014 (—), U+2015 (―), U+2E3A (⸺), U+2E3B (⸻). En-dash (–) is allowed only in date or number ranges. Use commas, semicolons, parentheses, or sentence restructuring instead. **Scope:** applies to `career/applications/**` (output) and the rendered PDF text. Does NOT apply to documentation under `docs/` (which legitimately quotes the rule), source `career/facts/**` files (warned, not blocked, so they get normalized at compose time), or `career/jd-analysis/**` files (preserve verbatim JD content even if the JD itself contains em-dashes).
2. **No fabrication.** Every resume bullet must trace to a verified fact ID in `career/facts/**`.
3. **Dates and employers are immutable.** Schema-locked. The validator rejects any resume in which a role's `when:` or `employer:` differs from its source fact.
4. **Tier 2 reframing requires explicit per-application opt-in.** Subagents default to strict-fact-mode if `user_overrides.yaml` is absent or empty. Reframings are always flagged in the claim ledger, never hidden.
5. **Encapsulation requires user approval.** The composer proposes a presentation plan (expand / compress / merge / drop per role); the user approves before render. Current/most-recent role is never dropped or below two bullets.

---

## 3. Architecture overview

```
                                 ┌────────────────────────┐
                                 │   Career Knowledge DB  │
                                 │   (facts + evidence)   │
                                 └──────────┬─────────────┘
                                            │
   ┌──────────────────┐                     │                    ┌────────────────────┐
   │  JD Ingestion    │─── normalized JD ──>│<── selected facts──│  Resume Renderer   │
   │  (Claude only)   │                     │                    │  (RenderCV/Typst)  │
   └──────────────────┘                     │                    └─────────┬──────────┘
                                            │                              │
                                            │                              ▼
                                            │                    ┌────────────────────┐
                                            └─── claim ledger ──>│ Validation Pipeline│
                                                                 │ (Python + auditor) │
                                                                 └─────────┬──────────┘
                                                                           ▼
                                                                 ┌────────────────────┐
                                                                 │  Version Registry  │
                                                                 │  (sent → outcome)  │
                                                                 └────────────────────┘
```

Five subsystems: knowledge base, JD ingestion, generation (composer + renderer), validation, registry. All local. All file-based.

---

## 4. Locked technology decisions

| Decision | Choice | Rationale |
|---|---|---|
| Renderer | **RenderCV (Typst)** | Inherits ATS-tested PDF output (20-PDF report). YAML input, JSON Schema validation, theme overrides. Build effort goes to provenance layer instead of a custom renderer. |
| Career data layer | **Flat YAML files only** | Career-scale (~100s of facts), human-editable, LLM-greppable, clean git diffs. No SQLite. Linter enforces referential integrity. |
| JD analysis | **Pure Claude subagent** | Research confirmed convergent evidence (ats-resume-agent, resume-tailoring-skill, santifer/career-ops all chose LLM-only). No ESCO/SkillNER. Documented v1.5 upgrade path. |
| Validation | **Two-stage: Python gates + Claude auditor** | Deterministic gates first (cheap, reproducible), semantic auditor second (quality). Both must pass for ready-to-send. |
| Achievement capture | **Interactive subagent (`fact-curator`)** | Ongoing workflow, not just at resume time. Drives `/capture-fact`. |
| Version registry | **Per-application YAML log** | One folder per application under `career/applications/`. Snapshot + ledger + audit + outcome. |

---

## 5. Folder layout

```
P:\Resumes\Claude-automations\
├── CLAUDE.md                              project instructions (hard rules first)
├── docs/superpowers/specs/                this spec + future ones
├── raw_data/                              existing LaTeX resumes (source for migration only)
├── ats-resume-agent/                      cloned reference, not used at runtime
├── career/                                THE CAREER KNOWLEDGE BASE
│   ├── facts/                             one atomic fact per file
│   │   └── F-2025-deloitte-1st-50agents.yaml
│   ├── evidence/                          sources backing facts
│   │   └── E-deloitte-certificate.yaml
│   ├── experiences/                       role envelopes; reference fact IDs
│   │   └── X-oracle-research-coop.yaml
│   ├── projects/                          long-form project descriptions
│   │   └── P-eagle-eye-cv.yaml
│   ├── skills/skills.yaml
│   ├── education/edu.yaml
│   ├── contact/contact.yaml
│   ├── jd-analysis/                       one per ingested JD
│   │   └── JD-2026-05-15-procogia-mle.yaml
│   ├── applications/                      one folder per sent resume
│   │   └── A-2026-05-15-procogia-mle/
│   │       ├── application.yaml           JD ref, generated ref, outcome
│   │       ├── user_overrides.yaml        explicit tier-2 authorizations
│   │       ├── proposed-plan.yaml         composer draft, awaiting approval
│   │       ├── rendercv-input.yaml        exact YAML rendered
│   │       ├── claim-ledger.yaml          bullet → fact ID map
│   │       ├── resume.pdf
│   │       └── audit-report.md
│   └── config/
│       ├── rules.yaml                     banned words, em-dash policy, page budgets
│       └── rendercv-theme.yaml            Typst theme overrides
├── scripts/
│   ├── lint_yaml.py                       schema + ref + em-dash check on YAML
│   ├── check_em_dashes.py                 standalone em-dash scanner
│   ├── validate_resume.py                 6 deterministic gates
│   ├── secret_scan.py                     pre-commit secret check
│   ├── career_status.py                   session-start summary
│   ├── jd_relevance_score.py              shared helper
│   └── extract_pdf_text.py                shared helper (uses pypdf)
├── schemas/                               JSON Schemas
│   ├── fact.schema.json
│   ├── evidence.schema.json
│   ├── experience.schema.json
│   ├── project.schema.json
│   ├── application.schema.json
│   ├── jd-analysis.schema.json
│   ├── user-overrides.schema.json
│   └── claim-ledger.schema.json
└── .claude/
    ├── settings.json                      hooks, model defaults
    ├── settings.local.json                user-specific (gitignored)
    ├── agents/
    │   ├── fact-curator.md
    │   ├── jd-analyzer.md
    │   ├── bullet-composer.md
    │   └── resume-auditor.md
    └── skills/
        ├── capture-fact/SKILL.md
        ├── capture-evidence/SKILL.md
        ├── ingest-jd/SKILL.md
        ├── generate-resume/SKILL.md
        ├── audit-resume/SKILL.md
        ├── humanize-resume/SKILL.md
        ├── log-outcome/SKILL.md
        ├── lint-career/SKILL.md
        ├── career-status/SKILL.md
        └── seed-from-tex/SKILL.md         one-shot migration
```

---

## 6. Data model

### 6.1 Fact

```yaml
# career/facts/F-2025-deloitte-1st-50agents.yaml
id: F-2025-deloitte-1st-50agents
type: achievement                          # achievement | responsibility | skill_use
title: 1st place at Deloitte AI Hackathon with 50+ agent hierarchy
when: 2025-03                              # YYYY or YYYY-MM
employer: Deloitte AI Hackathon            # IMMUTABLE
role_ref: X-northeastern-grad-student      # rolls up to which experience envelope
role_title: Participant                    # IMMUTABLE
impact:
  metric: "1st place"
  quantified: true
  outcome: won_1st_place
tech_actual: [CrewAI, LangGraph, multi-agent, RAG]
metrics:
  - "50+ specialized agents in hierarchical orchestration"
framings:                                  # pre-authored angles (pre-authorized)
  - id: agentic-systems
    angle: "Lead with multi-agent orchestration"
    sample: "Architected 50+ agent hierarchy with CrewAI and LangGraph, winning 1st place."
  - id: ai-leadership
    angle: "Lead with competitive outcome"
    sample: "Won Deloitte AI Hackathon (1st of N) by architecting a multi-agent research system."
evidence:
  - E-deloitte-certificate
  - E-deloitte-team-photo
description: |
  Built a hierarchical system of 50+ specialized AI agents using CrewAI and
  LangGraph to automate complex research, outperforming all other solutions.
tags: [hackathon, agentic-systems, leadership]
status: verified                           # verified | pending-evidence | retired
```

### 6.2 Evidence

```yaml
# career/evidence/E-deloitte-certificate.yaml
id: E-deloitte-certificate
type: certificate                          # certificate | url | file | screenshot | testimonial
source: "file://./assets/deloitte-cert.pdf"
attestation: self-attested                 # self-attested | third-party-verified | public-record
verified_at: 2025-03-20
backs_facts: [F-2025-deloitte-1st-50agents]
```

### 6.3 Experience envelope

```yaml
# career/experiences/X-oracle-research-coop.yaml
id: X-oracle-research-coop
employer: Oracle                           # IMMUTABLE
role_title: Research Assistant CO-OP       # IMMUTABLE
location: Vancouver, BC
when_start: 2025-05                        # IMMUTABLE
when_end: present                          # IMMUTABLE
team: Oracle Cloud Infrastructure - Identity
fact_refs:
  - F-2025-oracle-oauth-terraform
  - F-2025-oracle-react-iam-frontend
```

### 6.4 JD analysis

```yaml
# career/jd-analysis/JD-2026-05-15-procogia-mle.yaml
id: JD-2026-05-15-procogia-mle
ingested_at: 2026-05-15T09:00:00-07:00
source_file: "inbox/procogia-mle-jd.md"
company: Procogia
role: ML Engineer
seniority: mid
required_skills: [Python, ML pipelines, AWS]
preferred_skills: [LangChain, vector DBs]
keywords_verbatim:                         # exact strings from JD text
  - "Python"
  - "machine learning"
  - "AWS"
  - "LangChain"
red_flags: ["5+ years required, you have ~4"]
match_score_hint: 0.78
target_facts: [F-oracle-oauth, F-deloitte-50agents, F-flytbase-perf]
```

### 6.5 User overrides (per-application)

```yaml
# career/applications/A-2026-05-15-procogia-mle/user_overrides.yaml
# Empty = strict-fact mode. Subagents NEVER write here. User-only.
allow_cross_role_skills:
  - in_role_ref: X-oracle-research-coop
    add_terms: [Kubernetes]
    justification: "Used K8s in P-eagle-eye-cv; JD requires it"
tone_overrides:
  - target_fact: F-2025-deloitte-1st-50agents
    tone: aggressive
presentation:
  page_budget: 2
  expand_fully: [X-oracle-research-coop, X-flytbase-fullstack]
  compress:
    - role_ref: X-kfin-senior-dev
      style: two-bullets
    - role_ref: X-iit-research-assistant
      style: one-line
  merge:
    - merged_label: "Earlier Internships (2020–2021)"
      role_refs: [X-spinx-intern, X-zeus-intern, X-asambhav-intern]
      style: paragraph
  drop: [X-undergrad-ta-2017]
```

### 6.6 Claim ledger

```yaml
# career/applications/A-*/claim-ledger.yaml
generated_at: 2026-05-15T14:32:00-07:00
jd_ref: JD-2026-05-15-procogia-mle
target_pages: 2
bullets:
  - bullet_id: B-001
    section: career_highlights
    text: "Architected 50+ agent hierarchy with CrewAI and LangGraph, winning Deloitte AI Hackathon."
    backed_by: [F-2025-deloitte-1st-50agents]
    framing_used: agentic-systems
    framing_override: false
    keywords_hit: [agentic, multi-agent, LangGraph]
  - bullet_id: B-007
    section: experience.oracle
    text: "Engineered OAuth 2.0 + IAM solution leveraging Kubernetes-style orchestration on OCI."
    backed_by: [F-2025-oracle-oauth-terraform]
    framing_used: enterprise-security
    framing_override: true                 # FLAGGED — surfaced in audit report
    override_source: user_overrides.yaml
    override_terms_added: [Kubernetes]
    verified_against: P-eagle-eye-cv
unmatched_keywords: []                     # JD wanted these, no fact supports them
```

### 6.7 Application registry

```yaml
# career/applications/A-*/application.yaml
id: A-2026-05-15-procogia-mle
company: Procogia
role: ML Engineer
jd_ref: JD-2026-05-15-procogia-mle
generated_at: 2026-05-15T14:32:00-07:00
ready_to_send: false                       # flipped to true by validator only if all gates and auditor pass
sent_at: null
outcome:
  state: pending                           # pending | no_response | interview | offer | reject
  at: null
  notes: ""
```

---

## 7. Subagents

Each subagent has its own isolated context window and a system prompt that includes the shared CareerOps policy block plus role-specific instructions.

### 7.1 Shared policy block (in every subagent prompt)

```
# CAREEROPS POLICY

EM-DASH POLICY — ZERO TOLERANCE
EM-DASHES ARE FORBIDDEN IN ALL OUTPUT. Forbidden characters:
  U+2014 (—)   U+2015 (―)   U+2E3A (⸺)   U+2E3B (⸻)
USE INSTEAD: commas, semicolons, parentheses, or sentence restructuring.
EN-DASH (–) is allowed ONLY in date or number ranges.
Self-check before returning: scan your draft for U+2014. Zero hits.
Failed output is rejected by the linter and you will be re-invoked.

TIER 1 IMMUTABLE: never change dates, employers, role titles, what happened,
or numeric metrics. Schema-enforced.

TIER 2 FLEXIBLE: framings, tone, cross-role skill spotlighting only when
authorized in user_overrides.yaml for the current application. Default to
strict-fact-mode if the file is absent or unauthorized.

ENCAPSULATION: roles may be expanded, compressed, merged, or dropped per
presentation plan. Current role is never dropped or below 2 bullets.
Merging requires a shared theme. Plan must be approved by user before render.

EVIDENCE: every claim in the resume must trace to a fact ID. Every fact
should have at least one evidence reference.

FLAG, NEVER HIDE: every framing override and encapsulation choice goes into
claim-ledger.yaml, visible in the audit report.

HUMANIZATION: apply humanize-content principles inline. No banned words
(leverage, robust, comprehensive, seamless, delve, landscape, etc.) unless
the JD verbatim keyword list contains them. Vary sentence rhythm. Be
concrete, not generic.
```

### 7.2 Subagent roles

| Subagent | Job | Inputs | Outputs |
|---|---|---|---|
| `fact-curator` | Interview-style fact capture; suggests framings; identifies evidence to attach | User dialogue, existing facts (for dedup) | `career/facts/F-*.yaml`, optional `career/evidence/E-*.yaml` |
| `jd-analyzer` | Parse JD into structured analysis with verbatim keywords | JD file path | `career/jd-analysis/JD-*.yaml` |
| `bullet-composer` | Propose presentation plan; compose bullets with claim ledger after user approval | JD analysis, all facts, user_overrides.yaml | `proposed-plan.yaml` (pre-approval), then `rendercv-input.yaml` + `claim-ledger.yaml` |
| `resume-auditor` | Semantic pass over generated resume; AI-marker scan; quality verdict | resume.pdf text, claim-ledger, JD analysis | `audit-report.md` |

---

## 8. Skills

| Slash command | Purpose | Invokes |
|---|---|---|
| `/capture-fact` | Record a new achievement | `fact-curator` |
| `/capture-evidence` | Attach source URL/file to existing facts | direct file write |
| `/ingest-jd <path>` | Parse a JD | `jd-analyzer` |
| `/generate-resume <jd-id>` | End-to-end generation with plan-review gate | `bullet-composer` → RenderCV → validator → `resume-auditor` |
| `/audit-resume <app-id>` | Re-run auditor on existing resume | `resume-auditor` |
| `/humanize-resume <app-id>` | Manual humanization touchup on bullets | global `humanize-content` skill |
| `/log-outcome <app-id> <state>` | Record interview/reject/offer | direct file write |
| `/lint-career` | Run YAML linter on whole DB | `lint_yaml.py` |
| `/career-status` | One-line health summary | `career_status.py` |
| `/seed-from-tex <path>` | One-shot migration from existing LaTeX | `fact-curator` (migration mode) |

---

## 9. Hooks

The Claude Code hook matcher is tool-based (e.g. `Write|Edit`). Path-based scoping is implemented inside each script — the script reads `$CLAUDE_FILE_PATHS`, decides whether the path is in scope, and exits 0 (skip) for out-of-scope paths.

**Path scoping convention:**
- `lint_yaml.py` runs on any path matching `career/**/*.yaml`; ignores everything else
- `check_em_dashes.py` runs in strict mode on `career/applications/**`; warn-only on `career/facts/**` and `career/projects/**`; skips `career/jd-analysis/**`, `docs/`, `raw_data/`, `ats-resume-agent/`
- `validate_resume.py` runs only when the modified path is `career/applications/<app-id>/resume.pdf` or `claim-ledger.yaml` is finalized

```json
// .claude/settings.json (excerpt)
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "command": "python scripts/lint_yaml.py \"$CLAUDE_FILE_PATHS\"",
        "blocking": true,
        "description": "Schema + reference check on YAML edits (path-scoped to career/**)"
      },
      {
        "matcher": "Write|Edit",
        "command": "python scripts/check_em_dashes.py \"$CLAUDE_FILE_PATHS\"",
        "blocking": true,
        "description": "Zero-tolerance em-dash scan on output artifacts (path-scoped)"
      },
      {
        "matcher": "Write|Edit",
        "command": "python scripts/validate_resume.py --auto \"$CLAUDE_FILE_PATHS\"",
        "blocking": true,
        "description": "Full resume validation; runs only when resume.pdf or claim-ledger.yaml is written; skips otherwise"
      }
    ],
    "SessionStart": [
      {
        "command": "python scripts/career_status.py",
        "description": "Session-start summary of career DB"
      }
    ],
    "PreCommit": [
      {
        "command": "python scripts/secret_scan.py",
        "blocking": true,
        "description": "Block commits containing secrets in evidence/contact files"
      }
    ]
  }
}
```

---

## 10. Validation pipeline

`scripts/validate_resume.py <app-id>` runs all gates. Exits non-zero if any fail. Hooked to `PostToolUse` after `/generate-resume`. The skill marks `application.yaml.ready_to_send: true` only on exit 0.

| # | Gate | Tool | Failure action |
|---|---|---|---|
| 1 | PDF compiles cleanly | `rendercv render` exit code | Block — surface RenderCV error |
| 2 | Page count matches `page_budget` | `pypdf` page count | Block — propose compression in plan |
| 3 | All `keywords_verbatim` from JD analysis appear in PDF text | regex search on extracted text | Block — composer must re-attempt |
| 4 | Every bullet in `claim-ledger.yaml` maps to a real fact ID | YAML walk | Block — composer hallucination, re-attempt |
| 5 | No banned phrases | regex list from `config/rules.yaml` | Block — composer re-attempt with corrections |
| 6 | Decorum floors satisfied | structural check (current role bullets ≥ 2, no dropped current role, merged groups share theme) | Block — surface decorum violation |
| 7 | Em-dash scan returns zero | `check_em_dashes.py` on output YAML + extracted PDF text | Block — composer re-attempt |
| 8 | Dates and employers match source facts | cross-check `rendercv-input.yaml` against fact files | Block — schema violation |

Auditor (LLM) runs only after gates 1–8 pass. Auditor produces `audit-report.md` with:
- Presentation plan table
- Framing overrides table
- AI-marker scan (em-dash count, banned-word density, rhythm stddev)
- Verdict: PASS / NEEDS-REVIEW

`ready_to_send: true` is set only after Python gates pass AND auditor verdict is PASS or user explicitly accepts NEEDS-REVIEW.

---

## 11. End-to-end workflows

### 11.1 `/generate-resume <jd-id>`

```
1. Load: jd-analysis, all facts, user_overrides.yaml (if exists)
2. bullet-composer: propose plan + selected facts → proposed-plan.yaml
3. PAUSE: print plan; wait for user [approve | edit | abort]
4. bullet-composer (compose mode): produce rendercv-input.yaml + claim-ledger.yaml
5. Shell: rendercv render rendercv-input.yaml → resume.pdf
6. PostToolUse hook: validate_resume.py runs gates 1–8
   - On any gate failure: re-invoke bullet-composer with failure context (max 3 retries)
   - After 3 failed retries: mark `ready_to_send: false`, write `validation-failures.md`, surface to user; do not loop further
7. resume-auditor: semantic pass → audit-report.md
8. Set application.yaml.ready_to_send based on auditor verdict
9. Print summary: PDF path, # bullets, # overrides, verdict, AI-marker counts
```

### 11.2 `/capture-fact`

```
1. fact-curator interviews user (probes for metrics, evidence, framings)
2. Drafts F-*.yaml; user edits/approves
3. Write fact file (PostEditFile hook validates schema)
4. Optionally prompt: "Attach evidence now?" → /capture-evidence
5. Suggest: "Update which experience envelope (X-*) references this fact?"
```

### 11.3 `/seed-from-tex <path>` (one-shot migration)

```
1. fact-curator (migration mode) reads .tex file
2. Extracts each bullet, asks: "Save as fact?" [y/edit/skip]
3. For each yes: creates F-*.yaml with status: pending-evidence
4. Suggests 2-3 framings per fact (based on common JD angles)
5. After all .tex files processed: ~30-50 seeded facts, ~10 role envelopes
6. Self-archives (skill becomes a no-op after first use)
```

---

## 12. Phasing

### v1 MVP (sessions 1–4)

Minimum to start using for real applications. See §13 for build order.

### v1.5 (after first real job hunt batch)

- Hand-curated `data/tech_keywords.yml` — validator catches tech terms `jd-analyzer` missed
- Retrospective skill: `/review-applications` — analyze outcomes, suggest fact gaps
- Better evidence attachment (drag-drop screenshots into evidence folder)
- Cover letter generation (parallel pipeline sharing career DB)

### v2 (only if data demands)

- ESCO HTTP lookups (only if callback rate < 10% after 30+ applications)
- 1-page aggressive / 3-page CV template variants
- LinkedIn/GitHub auto-ingestion for fact capture

### Explicitly deferred — do not build

- Web UI / dashboard
- Multi-user support
- SQLite or any DB engine
- SkillNER / spaCy / heavy NLP
- Cloud sync / collaborative editing

---

## 13. Build order

Four sessions, each independently shippable.

**Session 1 — Foundation (data layer + guardrails)**
- Init project structure (`career/`, `scripts/`, `.claude/`, `schemas/`)
- Write JSON Schemas: fact, evidence, experience, project, application, jd-analysis, user-overrides, claim-ledger
- Write `scripts/lint_yaml.py` with schema + ref resolution + em-dash check
- Write `scripts/check_em_dashes.py` (standalone, includes PDF text extraction mode)
- Write `config/rules.yaml` (banned words, em-dash policy, page budgets)
- Wire hooks in `.claude/settings.json`
- Test: hand-write 3 facts, confirm linter catches em-dashes and dangling refs

**Session 2 — Capture pipeline**
- Write `fact-curator.md` subagent (policy block + interview prompts)
- Write `/capture-fact` skill
- Write `/seed-from-tex` one-shot migration skill
- Run `/seed-from-tex raw_data/Kalhar-Resume-September-2025.tex`
- Manually review/clean seeded facts (~30-50 facts expected)
- Write `/capture-evidence` skill
- Attach evidence to high-value facts (Deloitte cert, Oracle PR, FlytBase metrics)

**Session 3 — Generation pipeline**
- Write `jd-analyzer.md` subagent + `/ingest-jd` skill
- Test on a real JD from your pipeline
- Write `bullet-composer.md` subagent (large policy-heavy prompt)
- Write `/generate-resume` skill with plan-review pause gate
- Install RenderCV; pick a starting theme close to two-page sourcesanspro look
- End-to-end test: real JD → real PDF
- Manually verify claim ledger maps to facts correctly

**Session 4 — Validation + auditor + ship**
- Write `scripts/validate_resume.py` (8 gates)
- Wire as PostToolUse hook on `/generate-resume`
- Write `resume-auditor.md` subagent + `/audit-resume` skill
- Write `/log-outcome`, `/career-status`, `/lint-career` convenience skills
- Write `/humanize-resume` skill (delegates to global `humanize-content`)
- Customize RenderCV theme to match Kalhar's two-page Impact / Credibility layout
- Dry run on 3 real JDs from your pipeline
- Ship — start using for actual applications

---

## 14. Open items for implementation plan

These are intentionally deferred until the writing-plans phase, not part of this design:

- Exact JSON Schema field-level definitions (this spec gives examples; schemas formalize them)
- Exact RenderCV theme TOML/YAML overrides to match the two-page layout
- Exact prompts for each subagent (policy block defined; role-specific instructions written during implementation)
- Test fixtures (sample fact + sample JD + expected output for each gate)
- Migration of all six existing `.tex` files vs just the September 2025 master (decision at Session 2 time)

---

## 15. Non-goals

- This is a personal tool. No multi-user, no shared career DB.
- The system does not auto-apply to jobs. It generates the artifact; sending is manual.
- The system does not scrape job boards. JDs are pasted or dropped into `inbox/`.
- The system does not generate cover letters in v1. Deferred to v1.5 as a parallel pipeline.
- The system does not produce non-PDF formats in v1. RenderCV can output HTML and other formats; not needed.
