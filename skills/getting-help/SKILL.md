---
name: getting-help
description: Print the CareerOps command reference. Default shows a 3-command quickstart. Pass "full" to see all 11 skills with descriptions and arguments.
---

# /getting-help -- CareerOps Command Reference

## Usage
```
/careerops:getting-help
/careerops:getting-help full
```

## Instructions for Claude Code

### Default output (no argument or argument does not contain "full")

Print the following:

```
CareerOps -- Quick Start

  New here?
    /careerops:setting-up              Initialize your career directory
    /careerops:seeding-career-db       Import an existing resume
    /careerops:capturing-fact          Add a new career achievement

  Applying for a job?
    /careerops:analyzing-jd            Analyze a job description
    /careerops:generating-resume       Generate a tailored resume PDF

  /careerops:getting-help full         Show all commands
```

### Full output (argument contains "full")

Print the following:

```
========================================
 CareerOps v2 -- Full Command Reference
========================================

SETUP
  /careerops:setting-up
    First-run wizard. Scaffolds directory tree, collects config,
    writes rendercv-theme.yaml + contact.yaml + rules.yaml.
    Safe to re-run; detects new vs. returning user.

CAPTURE
  /careerops:capturing-fact
    Interactive interview to record a new career achievement.
    Facts are embedded in career/experiences/X-*.yaml.
    Optional: provide a brief description as argument.

  /careerops:capturing-evidence <fact-id>
    Attach a URL, certificate, PR, or file to a fact.
    Sets fact status from pending-evidence to verified.

  /careerops:seeding-career-db <path>
    One-shot import from an existing resume.
    .tex: LaTeX resume parser
    .md:  Master Career Document parser
    Other extensions: error with supported formats listed.

APPLY
  /careerops:analyzing-jd <path>
    Analyze a JD file from inbox/.
    Outputs JD-*.yaml with verbatim keywords and ranked_facts[]
    (all known facts scored by relevance to this JD).
    Example: /careerops:analyzing-jd inbox/company-role.md

  /careerops:generating-resume <jd-id>
    Full pipeline: inline planning Q&A, compose bullets (ranked_facts
    used as priority hint), render PDF, validate (8 gates), audit,
    generate cover letter.
    Example: /careerops:generating-resume JD-2026-05-15-procogia-mle

  /careerops:auditing-resume <app-id>
    Re-run semantic auditor on a generated resume.
    Add --accept to accept a NEEDS-REVIEW verdict and mark ready.

  /careerops:humanizing-resume <app-id>
    Surgical AI-marker cleanup on bullets or sections.
    Flags: --section <name>, --bullet <B-NNN>

  /careerops:logging-outcome <app-id> <state>
    Record result: interview / reject / offer / no_response

HEALTH
  /careerops:linting-career
    Schema + referential integrity + em-dash check on all career YAML.
    Also validates embedded facts[] arrays inside experience files.
    Optionally pass a subdirectory name to scope the scan.

  /careerops:getting-help full
    Show this reference.

========================================
 TYPICAL WORKFLOW
========================================

  1. First time setup:
       /careerops:setting-up
       /careerops:seeding-career-db raw_data/<your-resume>.tex

  2. Capture achievements (ongoing):
       /careerops:capturing-fact
       /careerops:capturing-evidence <fact-id>

  3. For each job application:
       a. Drop JD into inbox/
       b. /careerops:analyzing-jd inbox/<jd-file>
       c. /careerops:generating-resume <jd-id>
          -- inline planning Q&A (tone, emphasis, overrides)
          -- review presentation plan, approve
          -- PDF is generated + validated + audited
          -- cover letter generated
       d. If NEEDS-REVIEW: /careerops:humanizing-resume <app-id>
          then: /careerops:auditing-resume <app-id> --accept
       e. Send the resume manually
       f. /careerops:logging-outcome <app-id> interview|reject|offer|no_response

  4. Maintenance:
       /careerops:linting-career        (run anytime to check DB health)

========================================
 KEY FILE LOCATIONS (v2)
========================================

  career/experiences/   X-*.yaml    Experience envelopes with embedded facts[]
  career/projects/      P-*.yaml    Side projects with embedded facts[]
  career/evidence/      E-*.yaml    Sources backing facts (reference fact IDs)
  career/jd-analysis/   JD-*.yaml   Analyzed job descriptions (includes ranked_facts[])
  career/applications/  A-*/        One folder per application
    application.yaml                Registry entry + outcome
    rendercv-input.yaml             Exact YAML rendered to PDF
    claim-ledger.yaml               Every bullet -> fact ID map
    audit-report.md                 Auditor verdict
    resume.pdf                      The generated resume
    cover-letter.pdf                The generated cover letter
  career/contact/       contact.yaml
  career/config/        rules.yaml, rendercv-theme.yaml
  inbox/                Drop JD files here before /analyzing-jd
  schemas/              JSON Schemas for all data files

========================================
 HARD RULES (enforced by code)
========================================

  * No em-dashes in any resume output. Ever. Code blocks writes.
  * Every bullet must trace to a fact ID. No fact = no bullet.
  * Dates and employers are immutable. Schema-locked.
  * Tier 2 reframings require explicit user opt-in per application.
  * Current/most-recent role: never dropped, minimum 3 bullets.

========================================
```

After printing the full reference, run `python "${CLAUDE_PLUGIN_ROOT}/scripts/career_status.py"` (if available) and append the output at the bottom.
