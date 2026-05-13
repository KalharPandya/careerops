# CareerOps

A Claude Code plugin for schema-driven, fact-traceable resume and cover-letter automation. Every bullet on every resume traces back to a verified atomic fact, and a multi-layer validation pipeline enforces correctness, decorum, and zero fabrication.

## What It Does

1. You capture career facts once (`/careerops:capturing-fact`), stored inside experience files
2. You drop a job description in `inbox/` and run `/careerops:analyzing-jd`
3. You run `/careerops:generating-resume <jd-id>` and the system:
   - Scores all your facts against the JD and ranks them by relevance
   - Asks you to approve the presentation plan (which roles to expand, compress, merge)
   - Composes bullets with full provenance (every bullet traces to a fact ID)
   - Renders to PDF via RenderCV/Typst
   - Runs an 8-gate validator (page budget, fabrication check, em-dash scan, etc.)
   - Audits semantically for AI markers and quality

Result: a tailored, ATS-clean PDF resume with a claim ledger showing exactly which facts back which bullets.

## Installation

```bash
npx careerops install
```

This copies the plugin to `~/.claude/plugins/careerops/` and registers it in your Claude Code settings. Restart Claude Code afterward.

**Requirements:**
- Python 3.10+
- `pip install pyyaml`
- `pip install rendercv` (for PDF output)

All CareerOps skills are then available under the `/careerops:` namespace.

## Quick Start (New User)

```bash
# 1. Create an empty career data directory and cd into it
mkdir -p ~/my-career
cd ~/my-career

# 2. Launch Claude
claude

# 3. Inside Claude, run the first-time setup wizard
/careerops:setting-up

# 4. Drop an existing resume into raw_data/ and seed your knowledge base
/careerops:seeding-career-db raw_data/your-resume.tex
```

Run `/careerops:getting-help full` inside Claude for the complete command reference.

## Commands

### Setup
| Command | Purpose |
|---|---|
| `/careerops:setting-up` | First-run wizard: scaffold directories, collect profile, write config |
| `/careerops:seeding-career-db <path>` | Import a resume (.tex or .md) into the career knowledge base |

### Capture
| Command | Purpose |
|---|---|
| `/careerops:capturing-fact` | Interview to record a new career achievement |
| `/careerops:capturing-evidence <fact-id>` | Attach evidence to an existing fact |

### Apply
| Command | Purpose |
|---|---|
| `/careerops:analyzing-jd <path>` | Analyze a JD from `inbox/` — scores all facts by relevance |
| `/careerops:generating-resume <jd-id>` | Full pipeline: plan approval, compose, render, validate, audit |
| `/careerops:auditing-resume <app-id>` | Re-run the semantic auditor |
| `/careerops:humanizing-resume <app-id>` | Manual AI-marker cleanup |
| `/careerops:logging-outcome <app-id>` | Record interview/reject/offer/no-response |

### Health
| Command | Purpose |
|---|---|
| `/careerops:linting-career` | Schema + reference + em-dash check on all career YAML |
| `/careerops:getting-help` | Quick-start guide. Add `full` for complete command reference |

## Architecture

CareerOps separates **plugin** (this repo: how to do things) from **user data** (your directory: facts, applications, profile). The plugin is portable, publishable, and contains zero personal information. Your data stays where you choose to put it.

**Data model:** Facts are embedded inside experience files (`career/experiences/X-*.yaml`) rather than stored as individual files. Every JD analysis scores all your facts by relevance, giving the composer a ranked shortlist while keeping all facts available for selection.

See:
- `CLAUDE.md` for plugin development context, hard rules, conventions
- `docs/USER-SETUP.md` for the new-user bootstrap guide
- `docs/superpowers/specs/` for design history

## Hard Rules

Every output from this plugin is validated against:
1. **No em-dashes.** U+2014 and variants forbidden everywhere. Multi-layer enforcement.
2. **No fabrication.** Every resume bullet traces to a verified fact ID.
3. **Date and employer immutability.** Schema-locked fields.
4. **Tier 2 reframing requires explicit per-application opt-in.**
5. **Encapsulation requires user approval** before render.

## Tech Stack

- **Renderer:** RenderCV (Typst)
- **Data:** YAML files with JSON Schema validation; facts embedded in experience envelopes
- **JD analysis:** Pure Claude subagent with relevance scoring (no ESCO/SkillNER)
- **Validation:** Python validators (8 gates) + Claude semantic auditor
- **Bootstrap:** `using-careerops` skill injected at every SessionStart via hook

## License

MIT
