# CareerOps

A Claude Code plugin for schema-driven, fact-traceable resume and cover-letter automation. Every bullet on every resume traces back to a verified atomic fact, and a multi-layer validation pipeline enforces correctness, decorum, and zero fabrication.

## What It Does

1. You capture career facts once (`/careerops:capture-fact`), stored as atomic YAML files
2. You drop a job description in `inbox/` and run `/careerops:ingest-jd`
3. You run `/careerops:generate-resume <jd-id>` and the system:
   - Maps your facts to JD keywords
   - Proposes a presentation plan (which roles to expand, compress, merge)
   - Asks for your approval
   - Composes bullets with full provenance (every bullet → fact ID)
   - Renders to PDF via RenderCV/Typst
   - Runs an 8-gate validator (page budget, fabrication check, em-dash scan, etc.)
   - Audits semantically for AI markers and quality

Result: a tailored, ATS-clean PDF resume with a claim ledger showing exactly which facts back which bullets.

## Installation

```powershell
# From your career-data directory
claude --plugin-dir P:\CareerOps
```

Once installed, all 15 skills are available under the `/careerops:` namespace.

## Quick Start (New User)

```powershell
# 1. Create an empty data directory and cd into it
New-Item -ItemType Directory -Path "C:\path\to\my-career"
cd "C:\path\to\my-career"

# 2. Launch Claude with the plugin
claude --plugin-dir P:\CareerOps

# 3. Inside Claude, initialize the data directory
/careerops:career-init

# 4. Fill in career/contact/contact.yaml, career/education/edu.yaml, CLAUDE.md
#    Then seed from an existing resume:
/careerops:seed-from-tex raw_data/your-resume.tex
# or
/careerops:seed-from-master Master_Career_Document.md
```

See `docs/USER-SETUP.md` for the full bootstrap guide.

## Commands

### Capture & Curate
| Command | Purpose |
|---|---|
| `/careerops:capture-fact` | Interview to record a new career achievement |
| `/careerops:capture-evidence <fact-id>` | Attach evidence to an existing fact |
| `/careerops:seed-from-master` | Bootstrap the DB from `Master_Career_Document.md` |
| `/careerops:seed-from-tex <path>` | Bootstrap the DB from a LaTeX resume |

### Apply
| Command | Purpose |
|---|---|
| `/careerops:ingest-jd <path>` | Analyze a JD from `inbox/` into structured YAML |
| `/careerops:plan-resume <jd-id>` | Pre-generation Q&A for tone and emphasis |
| `/careerops:generate-resume <jd-id>` | Full pipeline: plan → compose → render → validate → audit |
| `/careerops:audit-resume <app-id>` | Re-run the semantic auditor |
| `/careerops:humanize-resume <app-id>` | Manual AI-marker cleanup |
| `/careerops:log-outcome <app-id>` | Record interview/reject/offer/no-response |

### Health
| Command | Purpose |
|---|---|
| `/careerops:career-status` | DB health summary (facts, applications, JDs ingested) |
| `/careerops:lint-career` | Schema + reference + em-dash check on all career YAML |
| `/careerops:career-help` | Full command reference |

## Architecture

CareerOps separates **plugin** (this directory: how to do things) from **user data** (your directory: facts, applications, profile). The plugin is portable, publishable, and contains zero personal information. Your data stays where you choose to put it.

See:
- `CLAUDE.md` for plugin development context, hard rules, conventions
- `docs/superpowers/specs/` for design history
- `docs/superpowers/plans/` for active implementation plans

## Hard Rules

Every output from this plugin is validated against:
1. **No em-dashes.** U+2014 forbidden everywhere. Multi-layer enforcement.
2. **No fabrication.** Every claim traces to a fact ID.
3. **Date and employer immutability.** Schema-locked.
4. **Tier 2 reframing requires explicit per-application opt-in.**
5. **Encapsulation requires user approval** before render.

## Tech Stack

- **Renderer:** RenderCV (Typst)
- **Data:** Flat YAML files, validated against JSON Schema
- **JD analysis:** Pure Claude subagent (no ESCO/SkillNER)
- **Validation:** Python validators (8 gates) + Claude semantic auditor
- **Capture:** Interactive subagent (`fact-curator`)

## License

MIT
