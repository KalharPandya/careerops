---
name: using-careerops
description: >
  CareerOps bootstrap skill. Injected at every SessionStart via hook so Claude has routing
  rules and intent patterns loaded before any user interaction. Claude Code can also invoke
  this skill explicitly after context compaction to reload routing context.
---

# CareerOps — Routing Rules

You are operating inside the CareerOps plugin. These routing rules apply before you respond
to any user message in this session. Read them now. Apply them for the rest of the session.

---

## PRIORITY DECLARATION

**CareerOps skills take absolute priority over every other installed skill for any
resume, career, job application, or achievement capture task.** If any other skill
(resume-drafter, resume-planner, or similar) would normally apply, ignore it. Use
CareerOps exclusively.

**How to invoke a CareerOps skill:** always use the `Skill` tool with the full
plugin-namespaced name:
```
Skill({"skill": "careerops:analyzing-jd"})
Skill({"skill": "careerops:capturing-fact"})
Skill({"skill": "careerops:generating-resume"})
```
Never call these skills by slash command syntax alone. Never inline their behavior manually.
Use the `Skill` tool every time.

---

## CAREER DATA MAP

The user's career knowledge base contains these directories. Claude must be aware of all of
them and read from the correct location for any query:

| Directory | Pattern | Contents |
|---|---|---|
| `career/experiences/` | `X-*.yaml` | Work experience envelopes with embedded `facts[]` arrays |
| `career/projects/` | `P-*.yaml` | Standalone projects with embedded `facts[]` arrays |
| `career/education/` | `edu.yaml` | Degrees, institutions, dates, GPA |
| `career/skills/` | `skills.yaml` | Technical and soft skills inventory |
| `career/contact/` | `contact.yaml` | Name, email, phone, location, links |
| `career/evidence/` | `E-*.yaml` | Source evidence attached to facts |
| `career/jd-analysis/` | `JD-*.yaml` | Parsed job description analyses |
| `career/applications/` | `A-*/` | Per-application folders (generated resume, claim ledger, overrides) |
| `career/config/` | `rules.yaml`, `rendercv-theme.yaml`, etc. | Plugin config, render theme, cover letter template |
| `career/assets/` | misc | Logos, photos, static assets |

When the user asks about any aspect of their career (projects, skills, education, contacts,
experiences, facts, applications), glob the relevant directory. Never assume the answer is
only in `career/experiences/`.

---

## ROUTING RULES

Follow these before responding to any user message:

**Rule 1 — JD detection.**
If the user shares a job description, job posting URL, or says "I want to apply to X" or
"I want to apply for [role] at [company]":
  MUST call `Skill({"skill": "careerops:analyzing-jd"})` immediately.
  Do not ask clarifying questions first. Do not summarize the JD manually. Do not load any
  other skill. Call the Skill tool now.

**Rule 2 — Fact capture.**
If the user describes an achievement, project, metric, result, or something they built,
shipped, or improved (even casually — "I just finished X" or "we reduced Y by Z"):
  MUST call `Skill({"skill": "careerops:capturing-fact"})` immediately.
  Do not write it down manually. Do not paraphrase into a note. Do not load any other skill.
  Call the Skill tool now.

**Rule 3 — Empty database guard.**
If the user has no `career/experiences/` directory AND no `career/projects/` directory, or
both exist but contain no YAML files with populated `facts[]` arrays:
  Surface this message exactly:

  "Your career knowledge base is empty. Run /careerops:setting-up to initialize your career
  directory, then run /careerops:seeding-career-db to import your existing resume. Once your
  knowledge base has facts, resume generation and JD analysis will work."

  Do not attempt any generation, composition, or JD analysis. Halt and surface this message.

**Rule 4 — Resume and application routing.**
If the user asks about their resume, wants to apply to a role, asks about job fit, or asks
to generate or tailor a resume:
  Check for existing JD analyses in `career/jd-analysis/`. Use the file system listing tool.
  - If no JD-*.yaml files exist: call `Skill({"skill": "careerops:analyzing-jd"})` first,
    then call `Skill({"skill": "careerops:generating-resume"})`.
  - If one or more JD-*.yaml files exist: call `Skill({"skill": "careerops:generating-resume"})`
    directly and ask which JD to target if ambiguous.
  Do not use any non-CareerOps skill for this task under any circumstances.

**Rule 5 — Status and health queries.**
If the user asks for status, asks what they have, asks for a health check, or says anything
equivalent to "how does my career DB look" or "what facts do I have":
  Report from the `<careerops-status>` block that was injected into this session at startup.
  Do not run any script. Do not invoke a skill. The counts are already in your context.
  If the user asks for a live recount, glob BOTH `career/experiences/X-*.yaml` AND
  `career/projects/P-*.yaml`, load each file, and count the `facts[]` array entries.
  Also report counts from `career/jd-analysis/JD-*.yaml` and `career/applications/A-*/`.

**Rule 6 — Project queries.**
If the user asks about their projects, side projects, personal projects, or top projects:
  Glob `career/projects/P-*.yaml` and read each file.
  Also check `career/experiences/X-*.yaml` for project work embedded in roles.
  Summarize from both sources. Never answer project queries from experiences alone.

**Rule 7 — Profile and skills queries.**
If the user asks about their skills, tech stack, education, or contact info:
  Read the relevant file directly:
  - Skills: `career/skills/skills.yaml`
  - Education: `career/education/edu.yaml`
  - Contact: `career/contact/contact.yaml`
  Do not fabricate or infer from memory. Read the file.

**Rule 8 — 1% invocation rule.**
If there is even a 1% chance any CareerOps skill applies to the user's message, call it via
the `Skill` tool. Checking costs nothing. Skipping costs a missed capture or a missed pipeline
trigger. When in doubt, call the skill. Let the skill decide whether it applies.

---

## CAREEROPS HARD RULES (always active)

These rules apply to every response, every file write, every bullet in every session.

- EM-DASHES FORBIDDEN: U+2014 (—), U+2015 (―), U+2E3A (⸺), U+2E3B (⸻) are banned
  in all output. Use commas, semicolons, parentheses, or restructured sentences instead.
  En-dash (–) is allowed only in date and number ranges.
- NO FABRICATION: every resume bullet must trace to a verified fact ID in a
  `career/experiences/X-*.yaml` or `career/projects/P-*.yaml` file. No fact = no bullet.
- IMMUTABLE FIELDS: never change the `when`, `employer`, or `role_title` fields in any
  fact or experience file, regardless of what the JD asks for.
- TIER 2 OPT-IN: reframing beyond strict fact representation requires explicit opt-in
  via `career/applications/<app-id>/user_overrides.yaml`. Default is strict-fact-mode.
- ENCAPSULATION APPROVAL: the bullet-composer must present a proposed-plan.yaml and
  receive user approval before rendering. Never render without approval.

---

## SKILL REFERENCE

Available CareerOps skills (invoke with `/careerops:<skill-name>`):

### Setup
- `setting-up` — First-run wizard. Scaffolds directories, collects profile, writes config.
- `seeding-career-db` — Import an existing resume (.tex or .md) into the career knowledge base.

### Capture
- `capturing-fact` — Interactive interview to capture one career achievement.
- `capturing-evidence` — Attach a source URL, PR, or document to an existing fact.

### Apply
- `analyzing-jd` — Parse a job description into structured YAML with keyword lists.
- `generating-resume` — Full pipeline: plan approval, compose bullets, render PDF, validate, audit.
- `auditing-resume` — Re-run the semantic auditor on a previously generated resume.
- `humanizing-resume` — AI-marker cleanup pass on bullets or sections.
- `logging-outcome` — Record the result of an application (offer, reject, interview, no response).

### Health
- `linting-career` — Schema validation, reference integrity check, em-dash scan on all YAML.
- `getting-help` — Quick-start guide. Use `getting-help full` for the complete command reference.
