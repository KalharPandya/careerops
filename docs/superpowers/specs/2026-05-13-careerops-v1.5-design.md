# CareerOps v1.5 — Design Spec

**Status:** Design approved 2026-05-13. Implementation plan to follow.
**Owner:** Kalhar Pandya
**Date drafted:** 2026-05-13

---

## Goal

Make CareerOps generate ATS-correct, recruiter-scannable, page-disciplined resumes plus matching cover letters, with all per-application decisions captured up-front through an interactive planning skill. Plug into the official `rendercv-skill` so RenderCV knowledge stays current as upstream evolves.

## Scope

Six changes, tightly coupled (they all share `user_overrides.yaml`, the `bullet-composer` agent, and the resume validator pipeline). One implementation plan covers all six.

1. Install the official `rendercv-skill` and trim hand-written RenderCV knowledge in `bullet-composer.md`.
2. Strict page-boundary validator gate (Gate 9).
3. Location and phone hidden by default; visibility chosen per application in `/plan-resume`.
4. New `/plan-resume` skill for pre-generation Q&A (optional; falls back to inline Q&A inside `/generate-resume`).
5. Keyword bolding in bullets (composer rule + new Gate 10).
6. Cover letter bundled into `/generate-resume` (new `cover-letter-composer` agent + cover-letter pipeline + Gate 11).

## Out of scope

- Plugin packaging (separate plan at `docs/plugin-packaging-plan.md`)
- Multi-language / non-English locale support
- Resume A/B variant tracking across applications
- Auto-submission to job portals
- Real-time ATS-scoring estimation (we ship correct keyword coverage and page discipline; we don't simulate ATS rank)

## Background — what already shipped today (pre-v1.5)

These items are part of the same conversation but landed before the spec was written. Listed for context, not redoing:

- **RenderCV theme is now configurable.** `career/config/rendercv-theme.yaml` is the runtime source of truth; `bullet-composer` reads it and emits the top-level `design:` block. Kalhar's pick: `engineeringresumes`.
- **`/career-init` skill created.** Interactive first-run setup that writes the theme config, contact info, and the `presentation` block in `rules.yaml`. Idempotent.
- **Soft hyphenation fixed at source.** `design.typography.alignment: justified-with-no-hyphenation`. ATS parsers built on pypdf or pdfminer do not dehyphenate, so soft hyphens at line ends break keyword search; we eliminate them in the PDF rather than patching the validator.
- **Memory: `feedback_verify_claims.md`.** Don't invent "real systems handle X" justifications to soften a fix; verify or flag.

---

## Architecture overview

```
                                   ┌────────────────────────────────┐
                                   │ career/config/rendercv-theme   │
                                   │  + career/config/rules.yaml    │
                                   │  (presentation defaults)       │
                                   └───────────────┬────────────────┘
                                                   │
inbox/<jd.md> ─▶ /ingest-jd ─▶ career/jd-analysis/JD-*.yaml
                                                   │
                              ┌────────────────────┴───────────────────┐
                              ▼                                        │
                     /plan-resume (optional)                            │
                              │ asks user Q&A                           │
                              ▼                                        │
                   career/applications/<app-id>/                       │
                     user_overrides.yaml                               │
                     proposed-plan.yaml                                │
                              │                                        │
                              ▼                                        │
                     /generate-resume <jd-id>                          │
                              │                                        │
                              ├── (if no proposed-plan) ────────────────┘
                              │   fall through to inline Q&A
                              │
                              ├── dispatch bullet-composer
                              │     emits rendercv-input.yaml
                              │                          + claim-ledger.yaml
                              ├── dispatch cover-letter-composer
                              │     emits cover-letter.md
                              │                  + cover-letter-typst-input.yaml
                              ├── rendercv render both PDFs
                              ├── validate_resume.py (11 gates)
                              └── audit-resume.md (semantic pass)

Outputs in career/applications/<app-id>/:
  resume.pdf
  cover-letter.md
  cover-letter.pdf
  claim-ledger.yaml
  audit-report.md
```

---

## Change 1 — Install official rendercv-skill

### Motivation
`bullet-composer.md` currently contains hand-written RenderCV YAML schema (Phase 3, ~80 lines). It will drift as RenderCV releases. The official `rendercv-skill` is auto-generated from RenderCV's Pydantic source and validated against RenderCV's own pipeline.

### Design
1. Run `npx skills add rendercv/rendercv-skill -a claude-code` once. The skill installs to `~/.claude/skills/rendercv-skill/` (or the plugin equivalent).
2. Edit `.claude/agents/bullet-composer.md` Phase 3:
   - Remove the inline RenderCV YAML structure example.
   - Add: "For all RenderCV YAML schema questions (cv fields, design overrides, theme-specific options, locale fields), use the `rendercv-skill`. Honor the `design:` block from `career/config/rendercv-theme.yaml` as before."
3. Keep the CareerOps-specific parts: reading the theme config, writing `claim-ledger.yaml`, applying framing overrides, the em-dash and banned-phrase rules.

### Files touched
- `.claude/agents/bullet-composer.md`

### Acceptance criteria
- `rendercv-skill` is listed in `Skill` tool's available skills after install.
- Bullet-composer's Phase 3 section is shorter and references the skill instead of duplicating schema.
- Re-running `/generate-resume` on the existing ProCogia application still passes all gates.

---

## Change 2 — Strict page-boundary validator (Gate 9)

### Motivation
Today a resume can be 1.3 pages — content runs onto page 2 but page 2 is mostly empty. That looks unprofessional. The fix is to fail the validator unless the resume is either fully 1 page or page 2 is meaningfully full.

### Design
- Update `scripts/validate_resume.py` to add `gate9_page_utilization`.
- Algorithm:
  1. Read the `.typ` source rendercv emits during render. (Today we delete it as cleanup — change `/generate-resume` Step 6 to keep `<name>.typ` next to `resume.pdf`.)
  2. Count `#line` and content blocks per logical page using Typst's `pagebreak` markers and content line counts.
  3. If page count == 1: PASS.
  4. If page count > 1 and last-page line count < 60% of first-page line count: FAIL with detail "Page N has K lines, page 1 has M; ratio R below 0.6 threshold."
- Hook into the existing composer retry loop: a Gate 9 failure triggers re-composition with the instruction "either fit on 1 page (drop weakest bullet) or expand to fill page 2 to >=75% (add back a compressed bullet)."

### Edge cases
- Single-page resumes always pass Gate 9.
- If `.typ` source is missing (older runs), Gate 9 skips with a warning rather than failing.
- The 60% threshold is configurable in `rules.yaml` under `decorum_floors.last_page_min_ratio`.

### Files touched
- `scripts/validate_resume.py` (new gate function + registration)
- `.claude/skills/generate-resume/SKILL.md` (stop deleting `.typ`; pass it through to validation)
- `career/config/rules.yaml` (add `last_page_min_ratio: 0.6`)

### Acceptance criteria
- A deliberately under-filled 1.2-page resume fails Gate 9.
- Composer retry produces either a 1-page or page-2-mostly-full version on retry.
- Single-page resumes still pass cleanly.

---

## Change 3 — Location and phone hidden by default

### Motivation
ProCogia rejected applicants who appear distant. Kalhar lives in Vancouver and is hybrid-eligible; surfacing a city can trigger geographic auto-filtering when the candidate would actually take the role. Privacy default: hide; show only when explicitly chosen per application.

### Design
- Schema change `schemas/user-overrides.schema.json`:
  ```json
  "show_location": { "type": "boolean", "default": false },
  "show_phone":    { "type": "boolean", "default": false }
  ```
- `career/contact/contact.yaml` keeps all fields (always stored locally).
- `bullet-composer` Phase 3 emit rule:
  - Include `location:` in the cv block only if `user_overrides.show_location == true`.
  - Include `phone:` only if `user_overrides.show_phone == true`.
- `/plan-resume` Q&A asks these two questions explicitly every run.

### Files touched
- `schemas/user-overrides.schema.json`
- `.claude/agents/bullet-composer.md` (Phase 3 emit rule)
- `.claude/skills/plan-resume/SKILL.md` (new — see Change 4)

### Acceptance criteria
- A fresh application with no `user_overrides.yaml` produces a resume with no city and no phone in the header.
- Setting `show_location: true` in overrides re-adds the city.
- Existing applications (ProCogia) keep their current visibility — no silent change to past output.

---

## Change 4 — `/plan-resume` skill (interactive Q&A)

### Motivation
Today the composer is asked to choose encapsulation, framings, position emphasis, banned-tech list, and a half-dozen other decisions inside one dispatch. The user only sees the result. This change pulls decisions out of the composer's head and into an explicit pre-generation step the user can edit before bullets are written.

### Design
New skill `.claude/skills/plan-resume/SKILL.md`.

Inputs: `<jd-id>` argument. Loads:
- `career/jd-analysis/<jd-id>.yaml`
- All `career/facts/`, `career/experiences/`, `career/projects/`
- Current `career/config/rendercv-theme.yaml` and `rules.yaml.presentation` defaults
- Existing `career/applications/<app-id>/user_overrides.yaml` if present

Q&A flow (uses `AskUserQuestion` where the option set is finite):

1. **Position emphasis** — single-select: Agentic AI / Forward Deployed / Full-Stack / ML Engineer / Cloud-Infra / Research-Leaning. Drives the professional-summary tone and which roles get bullet-budget priority.
2. **Encapsulation per role** — for each `X-*.yaml` envelope (skipping those whose `when_end` is older than 5 years unless `target_facts` references them), ask: expand / compress / one-line / drop. Show recommended default based on JD target_facts overlap. Multi-select within a single AskUserQuestion call where feasible (otherwise sequential).
3. **Framing overrides** — for each fact in `target_facts` that has multiple available framings, show the framings and ask which one to use. Default = master-doc Agent Note guidance.
4. **Honesty constraints (banned tech)** — free-text list of tech the candidate does not have and that must not appear (e.g., `SAS, R, tidyverse` for ProCogia). Saved as `banned_tech` in overrides. Validator already supports banned-phrases enforcement.
5. **Page budget** — 1 or 2 (defaults to `rules.yaml.presentation.page_budget_default`).
6. **Location / phone visibility** — always asked, regardless of defaults, per change 3.
7. **Cover letter brief** — free text plus three follow-ups:
   - Why this company specifically?
   - Any gaps to acknowledge (and how)?
   - Anything personal worth surfacing (referral, prior interaction, specific portfolio piece)?

Output: writes the complete `user_overrides.yaml` and the `proposed-plan.yaml` (mirroring the composer's Phase 1 output). Prints a summary.

`/generate-resume` flow change:
- Step 0 (new): if `<app-id>/proposed-plan.yaml` does not exist, invoke `/plan-resume <jd-id>` inline. Otherwise skip Q&A and proceed to bullet composition with the existing overrides.

### Files touched
- New: `.claude/skills/plan-resume/SKILL.md`
- Modified: `.claude/skills/generate-resume/SKILL.md` (add Step 0 fallback)
- Modified: `schemas/user-overrides.schema.json` (add `position_emphasis`, `banned_tech`, `cover_letter_brief`)

### Acceptance criteria
- Running `/plan-resume <jd-id>` for the ProCogia JD produces the same overrides we hand-wrote, given matching answers.
- Running `/generate-resume <jd-id>` with no prior `/plan-resume` triggers the Q&A inline.
- Running `/generate-resume <jd-id>` with an existing `proposed-plan.yaml` skips the Q&A.
- `banned_tech` entries flow through to validator Gate 5 (banned-phrase scan) for that application only.

---

## Change 5 — Keyword bolding

### Motivation
Recruiters skim. A bullet with no bold runs together; a bullet with one bolded metric is read first. Bolded keywords also signal "this resume was written for this JD" without the candidate saying so.

### Design
Composer rule added to `.claude/agents/bullet-composer.md` Phase 2:

> For every experience and project bullet, surround 1 to 3 phrases with `**...**` (RenderCV passes through to Typst bold). Bold-candidate priority:
> 1. Numeric metrics with units ("**200,000 reports/min**", "**100% accuracy**", "**10+ production Python agents**")
> 2. JD `keywords_verbatim` matches ("**LangGraph**", "**CI/CD**", "**Claude Code**")
> 3. Award or recognition terms ("**1st place**", "**under submission**")
>
> Do not bold filler words ("the", "with", "and"), full sentences, action verbs at the start of bullets, or company names. Never bold inside the professional summary — that section reads as continuous prose.

New `gate10_bolding(app_dir)` in `validate_resume.py`:
1. Load `rendercv-input.yaml`.
2. For each bullet in `experience.<role>.highlights` and `projects.<project>.highlights`, count `**...**` spans.
3. FAIL if any such bullet has 0 spans or > 3 spans. PASS otherwise.
4. Summary paragraph and skills section are not checked.

### Files touched
- `.claude/agents/bullet-composer.md` (Phase 2 + Phase 4 self-check rules)
- `scripts/validate_resume.py` (new gate)

### Acceptance criteria
- Regenerated ProCogia resume has 1–3 bold phrases per experience/project bullet.
- Numeric metrics and JD keywords get priority for the bold treatment.
- Summary paragraph remains unbolded.
- An intentionally over-bolded bullet (4+ spans) fails Gate 10 in test.

---

## Change 6 — Cover letter bundled with `/generate-resume`

### Motivation
Resume and cover letter share most of their inputs (JD, facts, overrides, voice). Producing them separately doubles the user's interaction cost. Bundling — with cover-letter-specific Q&A inline during `/generate-resume` — is the cleanest UX.

### Design
- New subagent `.claude/agents/cover-letter-composer.md`.
  - Inputs: JD analysis, full career knowledge base, `user_overrides.yaml.cover_letter_brief`, the bullet-composer's `claim-ledger.yaml` (so the letter doesn't repeat resume bullets verbatim).
  - Structure: 4 paragraphs, 300-400 words total.
    1. Opening — name, current MS CS context, the specific role and why it caught attention. Uses `cover_letter_brief.why_company`.
    2. Fit — two concrete experience examples (not resume bullets verbatim; rephrased and tied to JD priorities).
    3. Gap-addressing — honest, brief acknowledgement of any banned-tech gaps from `user_overrides.banned_tech`, plus a credible learning plan. Uses `cover_letter_brief.gaps_to_address`.
    4. Closing — what the candidate is hoping to learn, light specific reference to the company, next-steps cordiality.
  - Same em-dash zero-tolerance and banned-phrase rules as the resume composer.
  - Outputs:
    - `cover-letter.md` — plain markdown, ready to paste into Workday/Greenhouse/Lever portals.
    - `cover-letter-typst-input.yaml` — minimal YAML for the cover-letter PDF render. Includes name, contact, date, JD-referenced role title, four paragraph blocks.

- `cover-letter-template.typ` — minimal Typst template for rendering the PDF. Reuses theme colors / fonts from `career/config/rendercv-theme.yaml` for consistency with the resume.

- `/generate-resume` flow extension:
  - After the resume pipeline succeeds (validation passes), dispatch `cover-letter-composer`.
  - Render `cover-letter.pdf` from the Typst template.
  - New Gate 11: cover-letter validation.

- New `gate11_cover_letter(app_dir)`:
  - `cover-letter.md` exists and has 250 to 500 words (target 300–400 with buffer).
  - Em-dash scan: zero hits.
  - Banned-phrase scan: zero hits.
  - JD `keywords_verbatim` coverage: at least 40% of resume's keyword set appears in the cover letter too.
  - `cover-letter.pdf` exists and is non-empty.

### Files touched
- New: `.claude/agents/cover-letter-composer.md`
- New: `cover-letter-template.typ` (project-root level or under `career/config/`)
- Modified: `.claude/skills/generate-resume/SKILL.md` (add Step 10 cover-letter dispatch + Step 11 cover-letter validation)
- Modified: `scripts/validate_resume.py` (Gate 11)
- Modified: `schemas/user-overrides.schema.json` (add `cover_letter_brief` sub-schema with `why_company`, `gaps_to_address`, `personal_notes`)

### Acceptance criteria
- Running `/generate-resume JD-2026-05-12-procogia-ai-intern` regenerates the resume AND produces both cover-letter outputs.
- Cover letter avoids verbatim bullet repetition from the resume.
- Cover letter cleanly addresses the SAS gap (the test case Kalhar specified).
- Both PDFs pass all validation gates.

---

## Risks and open issues

1. **`.typ` source format may change between rendercv versions.** Gate 9's line counting depends on parsing `#pagebreak()` and content blocks. Mitigation: encapsulate the count logic in a small function with version probes; fall back to PDF text-length ratio if the Typst parse fails.
2. **Bolding policy is subjective.** A composer may bold awkwardly. Mitigation: Gate 10 enforces 1-3 spans per bullet but cannot enforce quality. The semantic auditor can flag bad bolding in its pass.
3. **Cover-letter pdf rendering** — RenderCV does not natively render arbitrary Typst input outside its CV schema. We need a small custom Typst compile step (call `typst compile <template>.typ <output>.pdf` directly). Adds Typst CLI as a dependency. Mitigation: document the dependency; check at the start of the cover-letter render step; if `typst` is not on PATH, produce `cover-letter.md` only, log a clear warning, and let Gate 11 still pass on the `.md` so the overall pipeline doesn't fail just because the optional PDF is missing.
4. **Banned-tech list bleed across applications.** `banned_tech` lives in per-app overrides; no cross-application persistence. Acceptable: each JD is different and the candidate's gaps relative to that JD differ.
5. **Q&A friction.** `/plan-resume` asks 7 question groups; for some applications the user may want to skip. Acceptable for v1.5; if friction is real after a few applications, add a `--skip-questions` flag in v1.6 that uses sensible defaults from `rules.yaml.presentation`.

## Implementation order (informs the plan)

1. RenderCV skill install (smallest, independent)
2. `user-overrides.schema.json` updates (foundation for plan-resume and cover-letter)
3. `/plan-resume` skill (builds on schema)
4. Location/phone bullet-composer changes (small, depends on schema)
5. Bolding rule + Gate 10 (composer + validator)
6. Gate 9 page-utilization (independent)
7. Cover-letter-composer agent + template + Gate 11 (biggest, depends on plan-resume for `cover_letter_brief`)
8. `/generate-resume` skill rewrite to chain everything

## Acceptance — overall

- Regenerating ProCogia application with the full v1.5 pipeline produces:
  - resume.pdf — engineeringresumes theme, no hyphenation, 1–3 bold spans per bullet, header has no location/phone (Kalhar's pick for distance-sensitive applications), page-2 utilization ≥ 60%, 11/11 gates pass.
  - cover-letter.md — 300–400 words, addresses the SAS gap explicitly per `cover_letter_brief.gaps_to_address`.
  - cover-letter.pdf — typst-rendered, same fonts/colors as resume.
- `/plan-resume` runs cleanly for at least 2 distinct JDs (ProCogia + one other) and produces the right overrides.
- Bullet-composer agent no longer contains a long RenderCV schema dump; it cites the `rendercv-skill` instead.
- Validator passes all 11 gates on the regenerated ProCogia application.
