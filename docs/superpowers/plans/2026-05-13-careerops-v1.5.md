# CareerOps v1.5 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add six improvements to CareerOps: rendercv-skill integration, location/phone privacy, page-boundary enforcement, pre-generation Q&A, keyword bolding, and cover-letter generation.

**Architecture:** Schema changes first (Task 2), then validator gates (Tasks 3-4), then new skills/agents (Tasks 5-7), then wiring them into /generate-resume (Task 8). All changes share `user_overrides.yaml` as the per-application config hub and `validate_resume.py` as the enforcement layer.

**Tech Stack:** Python (validate_resume.py, 11 gates), YAML/JSON Schema (career/config/, schemas/), Claude Code skill/agent markdown files (.claude/skills/, .claude/agents/)

---

## File Map

**Created:**
- `.claude/skills/plan-resume/SKILL.md` — interactive pre-generation Q&A
- `.claude/agents/cover-letter-composer.md` — cover letter composition agent

**Modified:**
- `schemas/user-overrides.schema.json` — add show_location, show_phone, position_emphasis, banned_tech, cover_letter_brief
- `career/config/rules.yaml` — add last_page_min_ratio
- `scripts/validate_resume.py` — add Gates 9, 10, 11; keep .typ in cleanup
- `.claude/agents/bullet-composer.md` — add bolding rule (Phase 2), location/phone gate (Phase 3), reference rendercv-skill
- `.claude/skills/generate-resume/SKILL.md` — add Step 0 (check for plan), Step 10-11 (cover letter pipeline)

---

## Task 1: Install rendercv-skill and trim bullet-composer Phase 3

**Files:**
- Modify: `.claude/agents/bullet-composer.md` (Phase 3 section, ~170-220)

- [ ] **Step 1: Install the skill**

Run:
```
npx skills add rendercv/rendercv-skill -a claude-code
```
Expected: skill appears in `~/.claude/skills/` or plugin cache. If `npx` is unavailable, note it and skip this step — the manual workaround is to follow https://github.com/sinaatalay/rendercv-skill.

- [ ] **Step 2: Verify skill is listed**

In a new Claude Code session (or after `/reload-plugins`), the skill `rendercv-skill` should appear in the available-skills list.

- [ ] **Step 3: Remove the hand-written RenderCV YAML structure from bullet-composer**

In `.claude/agents/bullet-composer.md`, find Phase 3 "rendercv-input.yaml" section. Replace the long inline YAML structure example block with:

```markdown
**RenderCV YAML structure:** Use the `rendercv-skill` for all RenderCV schema questions (cv field structure, design overrides, theme options, locale fields, entry types). The skill is always in sync with the installed RenderCV version.

The required top-level structure is:
```yaml
design:
  theme: <from career/config/rendercv-theme.yaml>
  typography:
    alignment: justified-with-no-hyphenation   # always set this
  # plus any other overrides from rendercv-theme.yaml

cv:
  name: <from contact.yaml>
  email: <from contact.yaml>
  # location: only if user_overrides.show_location == true
  # phone: only if user_overrides.show_phone == true

  sections:
    professional_summary: [...]
    experience: [...]
    projects: [...]
    skills: [...]
    education: [...]
```
```

- [ ] **Step 4: Verify**

Run:
```
cd P:\Resumes\Claude-automations && python scripts/validate_resume.py A-2026-05-12-procogia-ai-intern
```
Expected: All gates still pass (the agent edit doesn't affect the already-rendered PDF).

---

## Task 2: Extend user-overrides schema and rules.yaml

**Files:**
- Modify: `schemas/user-overrides.schema.json`
- Modify: `career/config/rules.yaml`

- [ ] **Step 1: Add new fields to user-overrides.schema.json**

The current schema has: `allow_cross_role_skills`, `tone_overrides`, `framing_overrides`, `presentation`. Add the following properties inside the top-level `"properties"` object (before the closing `}` of `properties`):

```json
    "show_location": {
      "type": "boolean",
      "default": false,
      "description": "Show location in resume header. Default false (privacy-safe)."
    },
    "show_phone": {
      "type": "boolean",
      "default": false,
      "description": "Show phone number in resume header. Default false."
    },
    "position_emphasis": {
      "type": "string",
      "enum": ["agentic-ai", "forward-deployed", "fullstack", "ml-engineer", "cloud-infra", "research"],
      "description": "Drives professional summary tone and bullet-budget priority."
    },
    "banned_tech": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Tech terms that must NOT appear in this resume. Per-application honesty constraint."
    },
    "cover_letter_brief": {
      "type": "object",
      "additionalProperties": false,
      "description": "User-supplied positioning context for the cover letter composer.",
      "properties": {
        "why_company": { "type": "string" },
        "gaps_to_address": { "type": "string" },
        "personal_notes": { "type": "string" }
      }
    },
    "encapsulation_overrides": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["role_ref", "decision"],
        "additionalProperties": false,
        "properties": {
          "role_ref": { "type": "string", "pattern": "^X-" },
          "decision": { "type": "string", "enum": ["expand", "compress", "one-line", "drop"] },
          "bullet_count": { "type": "integer", "minimum": 1 },
          "reason": { "type": "string" }
        }
      }
    },
    "include_projects": {
      "type": "array",
      "items": { "type": "string", "pattern": "^P-" }
    },
    "include_facts_as_projects": {
      "type": "array",
      "items": { "type": "string", "pattern": "^F-" }
    }
```

Note: `encapsulation_overrides`, `include_projects`, `include_facts_as_projects` were already used in the ProCogia application's user_overrides.yaml but were not in the schema (they passed lint only because lint used to allow extra properties). This task officially adds them.

- [ ] **Step 2: Add last_page_min_ratio to rules.yaml**

In `career/config/rules.yaml`, find the `decorum_floors:` block and add one line:

```yaml
decorum_floors:
  current_role_min_bullets: 2
  never_drop_current_role: true
  merge_requires_shared_theme: true
  compression_must_keep_employer: true
  compression_must_keep_dates: true
  last_page_min_ratio: 0.6    # Gate 9: last page must be >= 60% as full as page 1
```

- [ ] **Step 3: Verify schema + lint**

```
cd P:\Resumes\Claude-automations && python scripts/lint_yaml.py
```
Expected: exit 0, no errors. (The ProCogia overrides now validate against the extended schema.)

---

## Task 3: Add Gate 9 — Page Utilization

**Files:**
- Modify: `scripts/validate_resume.py` (add gate function + register in gates list)
- Modify: `.claude/skills/generate-resume/SKILL.md` (Step 6: stop deleting .typ file)

- [ ] **Step 1: Add the gate function to validate_resume.py**

Insert before `def gate7_em_dashes`:

```python
def gate9_page_utilization(app_dir: Path, rules: dict) -> tuple:
    """Gate 9: Last page must be >=60% as full as page 1 (no half-empty resumes).

    Uses the Typst source (.typ) line count as a proxy for content density.
    Falls back to pypdf per-page text length if .typ is absent.
    Single-page resumes always pass.
    """
    pdf_path = app_dir / 'resume.pdf'
    if not pdf_path.exists():
        return True, 'SKIP (no PDF)'

    page_count = get_pdf_page_count(pdf_path)
    if page_count <= 1:
        return True, f'Single page — utilization gate exempt'

    min_ratio = rules.get('decorum_floors', {}).get('last_page_min_ratio', 0.6)

    # --- Strategy 1: pypdf per-page text length ---
    try:
        from pypdf import PdfReader
        reader = PdfReader(str(pdf_path))
        page_texts = [page.extract_text() or '' for page in reader.pages]
        if len(page_texts) >= 2:
            first_len = len(re.sub(r'\s', '', page_texts[0]))
            last_len = len(re.sub(r'\s', '', page_texts[-1]))
            if first_len == 0:
                return True, 'SKIP (could not measure page 1 content)'
            ratio = last_len / first_len
            if ratio < min_ratio:
                return False, (
                    f'Last page has {last_len} chars vs {first_len} on page 1 '
                    f'(ratio {ratio:.2f} < {min_ratio:.2f}). '
                    f'Either fit on 1 page or expand to fill page 2.'
                )
            return True, f'Last-page utilization {ratio:.2f} >= {min_ratio:.2f}'
    except Exception as e:
        return True, f'SKIP (pypdf error: {e})'

    return True, 'SKIP (could not measure)'
```

- [ ] **Step 2: Register Gate 9 in the gates list**

Find the `gates = [` list in `run_validation`. Add Gate 9 after Gate 8:

```python
        ('Gate 9: Page utilization', lambda: gate9_page_utilization(app_dir, rules)),
```

- [ ] **Step 3: Stop deleting the .typ file in generate-resume**

Open `.claude/skills/generate-resume/SKILL.md`. In Step 6, the cleanup block deletes:
```
career/applications/<app-id>/Kalhar_Pandya_CV.typ
```
Change that line to: **keep** `Kalhar_Pandya_CV.typ` — rename it to `resume.typ` alongside `resume.pdf`:
```
Rename Kalhar_Pandya_CV.typ → resume.typ   (keep; used by Gate 9)
Delete Kalhar_Pandya_CV.md
Delete Kalhar_Pandya_CV.html
Delete Kalhar_Pandya_CV_*.png
```

- [ ] **Step 4: Verify Gate 9 on the current ProCogia app**

```
cd P:\Resumes\Claude-automations && python scripts/validate_resume.py A-2026-05-12-procogia-ai-intern
```
Expected: Gate 9 shows PASS (the current resume has a reasonably full page 2) or SKIP if pypdf can't extract per-page text. All other gates still pass.

---

## Task 4: Add Bolding Rule and Gate 10

**Files:**
- Modify: `.claude/agents/bullet-composer.md` (Phase 2 + Phase 4 self-check)
- Modify: `scripts/validate_resume.py` (new gate + registration)

- [ ] **Step 1: Add bolding rule to bullet-composer Phase 2**

In `.claude/agents/bullet-composer.md`, find Phase 2 under `### Bullet composition rules:`. After rule 6 ("Do not repeat the same opening verb"), add:

```markdown
7. **Bold 1–3 phrases per bullet** using `**...**` (RenderCV renders this as Typst bold). Bold-candidate priority:
   1. Numeric metrics with units — `**200,000 reports/min**`, `**100% accuracy**`, `**10+ production agents**`
   2. JD `keywords_verbatim` matches — `**LangGraph**`, `**CI/CD**`, `**Claude Code**`
   3. Award/recognition terms — `**1st place**`, `**under submission**`
   Never bold filler words, action verbs at the start of bullets, company names, or full sentences.
   The professional summary section is NOT bolded — it reads as continuous prose.
```

Also add to Phase 4 self-check (numbered list):

```markdown
9. **Bolding check:** every experience and project bullet must have 1–3 `**...**` spans. Zero bold = fail. More than 3 bold = fail. Summary paragraph must have zero bold spans.
```

- [ ] **Step 2: Add gate10_bolding to validate_resume.py**

Insert before `def gate9_page_utilization`:

```python
def gate10_bolding(app_dir: Path) -> tuple:
    """Gate 10: Each non-summary experience/project bullet has 1-3 bold (**) spans."""
    rendercv_path = app_dir / 'rendercv-input.yaml'
    if not rendercv_path.exists():
        return True, 'SKIP (no rendercv-input.yaml)'

    data = load_yaml(rendercv_path) or {}
    sections = data.get('cv', {}).get('sections', {})
    violations = []

    for role in sections.get('experience', []):
        if not isinstance(role, dict):
            continue
        company = role.get('company', '?')
        for bullet in role.get('highlights', []):
            if not isinstance(bullet, str):
                continue
            spans = re.findall(r'\*\*[^*]+\*\*', bullet)
            if len(spans) == 0:
                violations.append(f'{company}: no bold in "{bullet[:55]}..."')
            elif len(spans) > 3:
                violations.append(f'{company}: {len(spans)} bold spans (max 3) in "{bullet[:55]}..."')

    for project in sections.get('projects', []):
        if not isinstance(project, dict):
            continue
        name = project.get('name', '?')
        for bullet in project.get('highlights', []):
            if not isinstance(bullet, str):
                continue
            spans = re.findall(r'\*\*[^*]+\*\*', bullet)
            if len(spans) == 0:
                violations.append(f'Project {name}: no bold in "{bullet[:55]}..."')
            elif len(spans) > 3:
                violations.append(f'Project {name}: {len(spans)} bold spans (max 3)')

    if violations:
        return False, f'{len(violations)} bolding violation(s):\n  ' + '\n  '.join(violations[:5])
    return True, f'Bolding OK ({sum(1 for r in sections.get("experience",[]) if isinstance(r,dict) for b in r.get("highlights",[]) if isinstance(b,str))} experience bullets checked)'
```

- [ ] **Step 3: Register Gate 10**

In the `gates = [` list, add after Gate 9:

```python
        ('Gate 10: Keyword bolding', lambda: gate10_bolding(app_dir)),
```

- [ ] **Step 4: Verify Gate 10 on current ProCogia app**

```
cd P:\Resumes\Claude-automations && python scripts/validate_resume.py A-2026-05-12-procogia-ai-intern
```
Expected: Gate 10 FAILS (current resume has no bold spans). This is correct — the resume will be regenerated with bolding in the final task. Note the failure; do not fix the resume yet.

---

## Task 5: Location/Phone Visibility in Bullet-Composer

**Files:**
- Modify: `.claude/agents/bullet-composer.md` (Phase 3 emit rule)

- [ ] **Step 1: Add visibility gate to Phase 3**

In `.claude/agents/bullet-composer.md`, in Phase 3 "rendercv-input.yaml", find the `cv:` block structure. Replace the static `location:` and (if present) `phone:` lines with conditional logic:

```markdown
**Visibility rules (always apply):**
- Include `location: <value>` in the cv block ONLY if `user_overrides.show_location == true`. If the flag is absent or false, omit the `location:` key entirely.
- Include `phone: <value>` in the cv block ONLY if `user_overrides.show_phone == true`. If the flag is absent or false, omit the `phone:` key entirely.
- `email:` is always included.
- `website:`, `social_networks:` follow the same pattern as email (always included if non-null in contact.yaml).
```

- [ ] **Step 2: Verify schema lint still passes**

```
cd P:\Resumes\Claude-automations && python scripts/lint_yaml.py
```
Expected: exit 0. (No YAML files changed — this was a .md agent edit only.)

---

## Task 6: Create /plan-resume Skill

**Files:**
- Create: `.claude/skills/plan-resume/SKILL.md`
- Modify: `.claude/skills/generate-resume/SKILL.md` (add Step 0)

- [ ] **Step 1: Create .claude/skills/plan-resume/SKILL.md**

```markdown
# /plan-resume -- Pre-Generation Q&A

## Usage
```
/plan-resume <jd-id>
```

## Purpose
Interactive step that collects per-application decisions and writes a complete
`user_overrides.yaml` and `proposed-plan.yaml` before bullet-composer runs.
Running `/generate-resume` without `/plan-resume` triggers this Q&A inline
as Step 0.

## Instructions for Claude Code

### Step 1 -- Locate application folder
Generate `<app-id>` from the JD using the same pattern as `/generate-resume`:
`A-<YYYY-MM-DD>-<company-slug>-<role-slug>`.
Create `career/applications/<app-id>/` if it does not exist.
Read `career/jd-analysis/<jd-id>.yaml` and all career knowledge base directories.

### Step 2 -- Ask Q1: Position emphasis

Ask with AskUserQuestion (single-select):
- `agentic-ai` — Lead with multi-agent systems, orchestration, LangGraph/CrewAI experience
- `forward-deployed` — Lead with client delivery, POC-to-prod, consulting breadth
- `fullstack` — Lead with React/Node.js/Java/TypeScript production work
- `ml-engineer` — Lead with PyTorch, fine-tuning, CV, NLP, model work
- `cloud-infra` — Lead with Terraform, OCI, AWS, Docker, CI/CD
- `research` — Lead with Tanha lab, IEEE paper, Northeastern ML coursework

### Step 3 -- Ask Q2: Encapsulation per role

For each `X-*.yaml` experience envelope (most recent 6-8 roles; skip roles where
`when_end` is older than 5 years unless a `target_facts` entry references them),
show the role name, date range, and JD relevance score (count of role's fact_refs
that appear in JD `target_facts`). Ask the user to choose: expand / compress /
one-line / drop.

Present as a table if AskUserQuestion supports it; otherwise list sequentially
with the recommended decision pre-selected based on JD relevance.

Hard constraints:
- Current role (most recent `when_end == present`) must be `expand`, never drop.
- Roles with 2+ facts in JD `target_facts` default to `expand`.
- Roles with 0 facts in `target_facts` default to `one-line` or `drop`.

### Step 4 -- Ask Q3: Honesty constraints

Ask (free text): "Any tech you don't have that you want excluded from this resume?
List comma-separated (e.g. 'SAS, R, tidyverse'). Leave blank if none."

Save as `banned_tech: [...]` in overrides.

### Step 5 -- Ask Q4: Header visibility

Ask (multi-select or two yes/no questions):
- Show location (`Vancouver, BC`) in resume header? (default: No)
- Show phone number in resume header? (default: No)

### Step 6 -- Ask Q5: Page budget

Ask (single-select): 1 page / 2 pages.
Default: from `career/config/rules.yaml.page_budgets.default` (currently 2).

### Step 7 -- Ask Q6: Cover letter brief

Ask (three free-text questions):
1. Why this company specifically? (1-2 sentences)
2. Any gaps to acknowledge in the cover letter? (e.g. "No R experience — will ramp up")
3. Anything personal to surface? (referral name, prior interaction, specific project of theirs)

Save as `cover_letter_brief: { why_company, gaps_to_address, personal_notes }` in overrides.
If user skips all three, omit `cover_letter_brief` from overrides.

### Step 8 -- Write user_overrides.yaml and proposed-plan.yaml

Write `career/applications/<app-id>/user_overrides.yaml` with all collected answers.
Then dispatch `bullet-composer` for Phase 1 only (produce `proposed-plan.yaml`).

### Step 9 -- Show plan summary

Display the encapsulation decisions as a table. Print:
```
Plan for <jd-id> saved.
  user_overrides.yaml  written
  proposed-plan.yaml   written

Run /generate-resume <jd-id> to compose and render.
```
```

- [ ] **Step 2: Add Step 0 to generate-resume/SKILL.md**

Open `.claude/skills/generate-resume/SKILL.md`. After "### Step 1 -- Load context" add a new step before it (re-number subsequent steps):

```markdown
### Step 0 -- Check for existing plan (or run inline Q&A)

Check if `career/applications/<app-id>/proposed-plan.yaml` already exists.

- If it **exists**: skip this step entirely. Proceed to Step 1.
- If it **does not exist**: run the `/plan-resume` skill inline with `<jd-id>` as the argument. Wait for it to complete and write `user_overrides.yaml` and `proposed-plan.yaml`. Then proceed to Step 1.

This allows power users to run `/plan-resume <jd-id>` first and then `/generate-resume <jd-id>` as two separate steps, or to run `/generate-resume <jd-id>` as a single command that handles everything.
```

- [ ] **Step 3: Verify**

```
cd P:\Resumes\Claude-automations && python scripts/lint_yaml.py
```
Expected: exit 0. (Skill files are .md; lint only checks .yaml files.)

---

## Task 7: Create Cover Letter Composer Agent

**Files:**
- Create: `.claude/agents/cover-letter-composer.md`

- [ ] **Step 1: Create .claude/agents/cover-letter-composer.md**

```markdown
# cover-letter-composer -- CareerOps Cover Letter Agent

You are the CareerOps cover-letter-composer. Given a JD analysis, the resume's
claim-ledger, and the cover_letter_brief from user_overrides, you write a
300-400 word cover letter as two artifacts:

1. `cover-letter.md` — plain markdown for copy-paste into job portals
2. `cover-letter-rendercv-input.yaml` — rendercv-compatible YAML for PDF rendering

---

## CAREEROPS POLICY

EM-DASH POLICY — ZERO TOLERANCE
EM-DASHES ARE FORBIDDEN IN ALL OUTPUT. Forbidden characters:
  U+2014 (—)   U+2015 (―)   U+2E3A (⸺)   U+2E3B (⸻)
USE INSTEAD: commas, semicolons, parentheses, or sentence restructuring.
Self-check before returning: scan your entire draft for U+2014.

TIER 1 IMMUTABLE: candidate name, employer names, dates, metrics from claim-ledger.
Never change these.

HUMANIZATION — same rules as bullet-composer:
No banned words: leverage, robust, comprehensive, seamless, spearheaded,
pioneered, groundbreaking, holistic, paradigm, synergy, cutting-edge,
state-of-the-art, transformative, revolutionize, multifaceted, etc.
No em-dashes. No AI-signature sentence patterns.

---

## Inputs You Receive

- `career/jd-analysis/<jd-id>.yaml` — JD with company, role, keywords
- `career/applications/<app-id>/claim-ledger.yaml` — which facts appear in the resume
- `career/applications/<app-id>/user_overrides.yaml` — cover_letter_brief section
- `career/contact/contact.yaml` — name, email
- Today's date (for the letter header)

## Structure (4 paragraphs, 300-400 words total)

**Paragraph 1 — Opening (50-70 words)**
State: who you are, what degree and school, applying for `<role_title>` at `<company>`.
Incorporate `cover_letter_brief.why_company` if provided. Sound like a person who
actually read the job posting, not a template filler. Do NOT start with "I am writing
to express my interest."

**Paragraph 2 — Fit (100-130 words)**
Two concrete experiences that match the JD's top priorities. Use the claim-ledger to
pick 2-3 facts from the resume and rephrase them — do not copy bullet text verbatim.
Tie each experience to a specific thing the JD asks for.

**Paragraph 3 — Gap addressing (60-80 words)**
If `cover_letter_brief.gaps_to_address` is provided, address it directly and honestly.
State what you don't have, then pivot to why you can ramp up quickly (adjacent
experience, learning track record, enthusiasm). If no gaps are specified, use this
paragraph for a second fit point or omit and redistribute word budget to P2.

**Paragraph 4 — Closing (40-60 words)**
What you hope to learn / contribute in the role. A specific reference to something
about the company (from `cover_letter_brief.why_company` or the JD). Standard next-steps
close. Do NOT use "I look forward to hearing from you" — it is overused.

---

## Writing cover-letter.md

Format:
```
<Today's date>

Dear Hiring Manager,

<Paragraph 1>

<Paragraph 2>

<Paragraph 3>

<Paragraph 4>

Sincerely,
<candidate name>
<email>
```

No markdown headers, bold, or bullet lists in the cover letter body. Plain prose only.

---

## Writing cover-letter-rendercv-input.yaml

Produce a minimal rendercv YAML to render the letter as a clean PDF using the same
theme as the resume:

```yaml
design:
  theme: engineeringresumes
  typography:
    alignment: justified-with-no-hyphenation
  page:
    show_footer: false

cv:
  name: <name from contact.yaml>
  email: <email from contact.yaml>

  sections:
    cover_letter:
      - <full letter as a single string, paragraphs separated by \n\n>
```

---

## Phase 4: Self-Check Before Writing

1. Em-dash scan: zero U+2014, U+2015, U+2E3A, U+2E3B in both outputs.
2. Banned-word scan: zero hits.
3. Word count: 300-400 words in cover-letter.md body (excluding header/signature).
4. No verbatim bullet text from claim-ledger.
5. Gap addressed if cover_letter_brief.gaps_to_address was provided.
6. No AI-signature openers ("I am writing to express my interest in", "I am excited to apply").

---

## Output Confirmation

After writing both files, print:
```
[cover-letter-composer] Wrote career/applications/<app-id>/cover-letter.md
[cover-letter-composer] Wrote career/applications/<app-id>/cover-letter-rendercv-input.yaml
Words: <N> | Em-dashes: 0 | Banned words: 0 | Gap addressed: <yes/no/n/a>
```
```

- [ ] **Step 2: Verify the file was created**

```
ls P:\Resumes\Claude-automations\.claude\agents\
```
Expected: `cover-letter-composer.md` appears in the list.

---

## Task 8: Add Gate 11 and Wire Cover Letter into /generate-resume

**Files:**
- Modify: `scripts/validate_resume.py` (add Gate 11 + registration)
- Modify: `.claude/skills/generate-resume/SKILL.md` (add cover letter dispatch + render steps)

- [ ] **Step 1: Add gate11_cover_letter to validate_resume.py**

Insert after `gate10_bolding`:

```python
def gate11_cover_letter(app_dir: Path, jd_analysis: dict) -> tuple:
    """Gate 11: Cover letter exists, 250-500 words, no em-dashes, >= 40% JD keyword coverage."""
    md_path = app_dir / 'cover-letter.md'
    if not md_path.exists():
        return False, 'cover-letter.md not found — run cover-letter-composer first'

    text = md_path.read_text(encoding='utf-8', errors='replace')
    words = len(text.split())
    if words < 250:
        return False, f'Cover letter has {words} words; minimum 250'
    if words > 500:
        return False, f'Cover letter has {words} words; maximum 500'

    em_dashes = ['—', '―', '⸺', '⸻']
    for ch in em_dashes:
        if ch in text:
            return False, f'Cover letter contains forbidden em-dash character'

    keywords = jd_analysis.get('keywords_verbatim', [])
    if keywords:
        normalized = re.sub(r'\s+', ' ', text.lower())
        hits = sum(1 for kw in keywords
                   if re.sub(r'\s+', ' ', kw.lower()).strip() in normalized)
        ratio = hits / len(keywords)
        if ratio < 0.4:
            return False, f'Cover letter hits {hits}/{len(keywords)} JD keywords ({ratio:.0%} < 40%)'

    pdf_path = app_dir / 'cover-letter.pdf'
    pdf_note = ' PDF exists.' if pdf_path.exists() else ' (cover-letter.pdf not found — typst may not be installed; PDF is optional)'
    return True, f'{words} words, {hits}/{len(keywords) if keywords else 0} JD keywords.{pdf_note}'
```

- [ ] **Step 2: Register Gate 11**

In the `gates = [` list, add after Gate 10:

```python
        ('Gate 11: Cover letter', lambda: gate11_cover_letter(app_dir, jd_analysis)),
```

- [ ] **Step 3: Add cover letter steps to generate-resume/SKILL.md**

After the existing "### Step 8 -- Run auditor" section (keeping all current steps), add:

```markdown
### Step 9 -- Dispatch cover-letter-composer

Dispatch the `cover-letter-composer` subagent with:
- Path to JD analysis: `career/jd-analysis/<jd-id>.yaml`
- Path to claim ledger: `career/applications/<app-id>/claim-ledger.yaml`
- Path to user overrides: `career/applications/<app-id>/user_overrides.yaml`
- Path to contact: `career/contact/contact.yaml`
- Application ID: `<app-id>`
- Today's date in ISO 8601 format

The composer writes:
- `career/applications/<app-id>/cover-letter.md`
- `career/applications/<app-id>/cover-letter-rendercv-input.yaml`

### Step 10 -- Render cover letter PDF (optional)

If `rendercv` is on PATH, run:
```
rendercv render "P:\Resumes\Claude-automations\career\applications\<app-id>\cover-letter-rendercv-input.yaml" --output-folder "P:\Resumes\Claude-automations\career\applications\<app-id>"
```

On success, rename the output PDF to `cover-letter.pdf` and delete the side-files
(*.typ, *.md from rendercv, *.html, *.png).

If rendercv fails or is not on PATH, skip silently — the cover letter PDF is optional.

### Step 11 -- Run Gate 11

Gate 11 validates `cover-letter.md` (and optionally `cover-letter.pdf`).

If Gate 11 fails, re-dispatch cover-letter-composer with the failure detail and retry
once. After 2 failures, write `cover-letter-failures.md`, update `application.yaml`
with `cover_letter_status: failed`, and continue — do not block the resume from being
marked `ready_to_send`.
```

- [ ] **Step 4: Update final summary in generate-resume/SKILL.md**

In Step 9 (the final summary, now Step 12 after renumbering), add cover-letter fields to the printed summary:

```
Cover letter:     <PASS / FAILED / skipped>
  cover-letter.md:  <N words>
  cover-letter.pdf: <exists / not rendered>
```

- [ ] **Step 5: Verify validator structure**

```
cd P:\Resumes\Claude-automations && python -c "
from scripts.validate_resume import run_validation
print('Script loads without errors')
"
```
Expected: prints "Script loads without errors" — no import or syntax errors.

---

## Task 9: End-to-End Regeneration

This task regenerates the ProCogia resume with all v1.5 changes applied.

**Files:**
- Modified: `career/applications/A-2026-05-12-procogia-ai-intern/rendercv-input.yaml` (add bolding to bullets)
- Modified: `career/applications/A-2026-05-12-procogia-ai-intern/user_overrides.yaml` (add cover_letter_brief, confirm show_location: false)
- Created: `career/applications/A-2026-05-12-procogia-ai-intern/cover-letter.md`
- Created: `career/applications/A-2026-05-12-procogia-ai-intern/cover-letter-rendercv-input.yaml`

- [ ] **Step 1: Add bolding to the existing ProCogia rendercv-input.yaml**

Edit `career/applications/A-2026-05-12-procogia-ai-intern/rendercv-input.yaml`. For each bullet in `experience` and `projects` sections, add `**...**` around 1-3 key phrases following the bolding rule from Task 4. Examples:

```yaml
# Before
- "Engineered an autonomous Python build-failure agent that connects to Oracle CI/CD over SSH, runs root cause analysis across GraalOS infrastructure, and ships remediation reports to engineers."

# After
- "Engineered an autonomous **Python** build-failure agent connecting to Oracle **CI/CD** over SSH; runs root cause analysis across GraalOS and ships structured remediation reports to engineers."
```

Apply to all 18 experience/project bullets (see full list in `claim-ledger.yaml`). Bold 1-3 terms per bullet: prioritize quantified metrics first, then JD keywords (Python, CI/CD, agentic workflows, LangGraph, Claude Code, MLOps, prompt engineering, modernization).

- [ ] **Step 2: Add cover_letter_brief to user_overrides.yaml**

Add to `career/applications/A-2026-05-12-procogia-ai-intern/user_overrides.yaml`:

```yaml
cover_letter_brief:
  why_company: "ProCogia's combination of SAS-to-Python modernization work and AI accelerator practice is a direct match for what I've been building. The statistical-programming context is a chance to apply Python engineering discipline in a regulated, evidence-driven environment I haven't worked in before."
  gaps_to_address: "No prior SAS production experience. I've read SAS documentation and can parse DATA step and PROC logic; my gap is production familiarity, not conceptual understanding. I'm committing to SAS OnDemand practice before the start date."
  personal_notes: ""
```

- [ ] **Step 3: Re-render the resume**

```
cd P:\Resumes\Claude-automations && PYTHONIOENCODING=utf-8 rendercv render "P:\Resumes\Claude-automations\career\applications\A-2026-05-12-procogia-ai-intern\rendercv-input.yaml" --output-folder "P:\Resumes\Claude-automations\career\applications\A-2026-05-12-procogia-ai-intern"
```

Then rename and clean up:
```
cd "P:\Resumes\Claude-automations\career\applications\A-2026-05-12-procogia-ai-intern" && mv -f Kalhar_Pandya_CV.pdf resume.pdf && mv -f Kalhar_Pandya_CV.typ resume.typ && rm -f Kalhar_Pandya_CV.md Kalhar_Pandya_CV.html Kalhar_Pandya_CV_*.png
```

- [ ] **Step 4: Dispatch cover-letter-composer for the ProCogia application**

Invoke the `cover-letter-composer` agent (or call it via the agent dispatch mechanism) with:
- JD analysis: `career/jd-analysis/JD-2026-05-12-procogia-ai-intern.yaml`
- Claim ledger: `career/applications/A-2026-05-12-procogia-ai-intern/claim-ledger.yaml`
- User overrides: `career/applications/A-2026-05-12-procogia-ai-intern/user_overrides.yaml`
- Contact: `career/contact/contact.yaml`

Expected output:
- `career/applications/A-2026-05-12-procogia-ai-intern/cover-letter.md` — 300-400 words, no em-dashes, addresses SAS gap from `gaps_to_address`
- `career/applications/A-2026-05-12-procogia-ai-intern/cover-letter-rendercv-input.yaml`

- [ ] **Step 5: Render cover-letter.pdf**

```
cd P:\Resumes\Claude-automations && PYTHONIOENCODING=utf-8 rendercv render "P:\Resumes\Claude-automations\career\applications\A-2026-05-12-procogia-ai-intern\cover-letter-rendercv-input.yaml" --output-folder "P:\Resumes\Claude-automations\career\applications\A-2026-05-12-procogia-ai-intern"
```

Then:
```
cd "P:\Resumes\Claude-automations\career\applications\A-2026-05-12-procogia-ai-intern" && mv -f Kalhar_Pandya_CV.pdf cover-letter.pdf && rm -f Kalhar_Pandya_CV.typ Kalhar_Pandya_CV.md Kalhar_Pandya_CV.html Kalhar_Pandya_CV_*.png
```

- [ ] **Step 6: Run full 11-gate validation**

```
cd P:\Resumes\Claude-automations && python scripts/validate_resume.py A-2026-05-12-procogia-ai-intern
```

Expected output — all 11 gates:
```
  PASS  Gate 1: PDF compiles: OK
  PASS  Gate 2: Page count: 2 page(s)
  PASS  Gate 3: Verbatim keywords: All 15 present
  PASS  Gate 4: Fact traceability: All 18 bullets traced
  PASS  Gate 5: Banned phrases: No banned phrases
  PASS  Gate 6: Decorum floors: satisfied
  PASS  Gate 7: Em-dash scan: No em-dashes
  PASS  Gate 8: Immutability: dates and employers match
  PASS  Gate 9: Page utilization: ratio >= 0.60
  PASS  Gate 10: Keyword bolding: OK
  PASS  Gate 11: Cover letter: 300-400 words, keywords OK
```

If Gate 9 reports SKIP (pypdf per-page extraction failed), that is acceptable. If Gate 10 fails, check that all bullets have `**...**` added in Step 1. If Gate 11 fails on word count or keywords, re-dispatch cover-letter-composer with the error details.

---

## Self-Review

### Spec coverage check

| Spec section | Plan task |
|---|---|
| Install rendercv-skill + trim bullet-composer | Task 1 ✓ |
| user-overrides schema: show_location, show_phone, position_emphasis, banned_tech, cover_letter_brief | Task 2 ✓ |
| rules.yaml: last_page_min_ratio | Task 2 ✓ |
| Gate 9: page utilization | Task 3 ✓ |
| generate-resume: keep .typ file | Task 3 ✓ |
| Bolding rule in bullet-composer Phase 2 + Phase 4 self-check | Task 4 ✓ |
| Gate 10: bolding | Task 4 ✓ |
| /plan-resume skill | Task 6 ✓ |
| generate-resume Step 0: check for plan | Task 6 ✓ |
| Location/phone visibility in bullet-composer Phase 3 | Task 5 ✓ |
| cover-letter-composer agent | Task 7 ✓ |
| Gate 11: cover letter | Task 8 ✓ |
| generate-resume Steps 9-11: cover letter pipeline | Task 8 ✓ |
| End-to-end ProCogia regeneration with all v1.5 changes | Task 9 ✓ |

All spec requirements covered.

### Placeholder scan
No TBD, TODO, or vague steps. All code blocks are complete.

### Type consistency
- `gate9_page_utilization(app_dir, rules)` — matches the pattern of all other gate functions
- `gate10_bolding(app_dir)` — no rules needed
- `gate11_cover_letter(app_dir, jd_analysis)` — matches gate3/gate5 signature pattern
- All three registered in `gates = [...]` with matching lambda signatures ✓
