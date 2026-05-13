# CareerOps

**The resume engine that never makes things up.**

[![npm version](https://img.shields.io/npm/v/careerops)](https://www.npmjs.com/package/careerops)
[![license](https://img.shields.io/npm/l/careerops)](LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-plugin-blue)](https://claude.ai/code)

CareerOps is a Claude Code plugin that turns your real career history into tailored, ATS-ready resumes — automatically, repeatably, and without fabricating a single word.

**If you find it useful, [star the repo](https://github.com/KalharPandya/careerops) — it helps others find it.**

---

## The Problem with AI Resumes

Every AI resume tool has the same flaw: it invents. It dresses up your experience with metrics you never hit, skills you never used, and bullet points that sound great but aren't true. That works until the interview — then it fails badly.

CareerOps takes a different approach. It treats your resume as an **output of a database**, not a document written from scratch each time.

---

## How It Works

**Step 1 — Build your fact database once**

You capture career achievements interactively. CareerOps stores each one as a structured fact: what you did, the metric, the context, the employer, the date. Locked in. Immutable.

**Step 2 — Drop in a job description**

CareerOps parses the JD and scores every fact in your database against it — relevance, keyword match, experience level.

**Step 3 — Approve the plan, get the resume**

CareerOps proposes which roles to expand, compress, or drop based on relevance. You approve the plan. It then writes bullets with full provenance (every bullet cites the fact it came from), renders a PDF via RenderCV/Typst, and runs an 8-gate validator before handing it to you.

---

## Why CareerOps

| | Manual writing | Generic AI tools | CareerOps |
|---|---|---|---|
| Fabrication risk | Low | High | None — validator enforces it |
| Tailored to each JD | Only if you rewrite | Yes, but generic | Yes, from your real facts |
| Repeatable | No | No | Yes — same facts, different weights |
| Provenance | None | None | Every bullet cites a fact ID |
| ATS-safe output | Depends | Usually | Yes — validated, em-dash-free |
| You own your data | Yes | Depends | Yes — local YAML files, no cloud |

---

## Use Cases

- **Active job search** — apply to 10 roles with 10 tailored resumes, each grounded in real facts
- **Career journaling** — capture achievements as they happen, never scramble to remember them later
- **Senior engineers** — too much experience to fit one page; CareerOps scores and ranks what matters for each role
- **Career changers** — surface transferable skills from your history that align with the target JD
- **Anyone who hates writing about themselves** — describe what you built; CareerOps handles the framing

---

## Prerequisites

- [Claude Code](https://claude.ai/code) installed
- Python 3.10+
- `pip install pyyaml rendercv`

---

## Install

```bash
npx careerops install
```

Restart Claude Code. Done — all commands are live under `/careerops:`.

```bash
npx careerops update     # pull the latest version
npx careerops uninstall  # remove cleanly
```

---

## Getting Started

**1. Create your career directory and open Claude**

```bash
mkdir ~/my-career && cd ~/my-career
claude
```

**2. Run the setup wizard**

```
/careerops:setting-up
```

Scaffolds your folders, collects your name, email, and links. Takes two minutes.

**3. Import your existing resume** *(optional but recommended)*

```
/careerops:seeding-career-db raw_data/your-resume.tex
```

Supports `.tex` and `.md`. CareerOps extracts structured facts from it so you start with a populated database.

**4. Capture new achievements as they happen**

```
/careerops:capturing-fact
```

CareerOps interviews you and stores the result. Run this any time you ship something worth remembering.

**5. Apply to a job**

Drop the job description into `inbox/`, then:

```
/careerops:analyzing-jd
/careerops:generating-resume
```

Approve the plan, get the PDF.

---

## Commands

### Setup
| Command | What it does |
|---|---|
| `/careerops:setting-up` | First-run wizard — scaffold directories, collect your profile |
| `/careerops:seeding-career-db` | Import an existing resume into your knowledge base |

### Capture
| Command | What it does |
|---|---|
| `/careerops:capturing-fact` | Interview to record a new career achievement |
| `/careerops:capturing-evidence` | Attach a URL, PR, or document to an existing fact |

### Apply
| Command | What it does |
|---|---|
| `/careerops:analyzing-jd` | Parse a JD — scores all your facts by relevance |
| `/careerops:generating-resume` | Full pipeline: plan, compose, render PDF, validate, audit |
| `/careerops:auditing-resume` | Re-run the quality auditor on a generated resume |
| `/careerops:humanizing-resume` | Clean up AI-marker patterns in bullets |
| `/careerops:logging-outcome` | Record the result of an application |

### Health
| Command | What it does |
|---|---|
| `/careerops:linting-career` | Schema, reference, and em-dash check on all your data |
| `/careerops:getting-help` | Quick-start guide — add `full` for the complete reference |

---

## Your Data

```
~/my-career/
├── career/
│   ├── experiences/        Your work history and facts
│   ├── applications/       One folder per application
│   ├── jd-analysis/        Parsed job descriptions
│   └── config/             Theme, rules
├── inbox/                  Drop JDs here
└── raw_data/               Source resumes for seeding
```

The plugin lives at `~/.claude/plugins/careerops/`. Your data never touches it. No cloud sync, no accounts, no data leaving your machine.

---

## Guarantees

- **No fabrication.** Every bullet traces to a fact ID you captured. The 8-gate validator enforces this mechanically.
- **No em-dashes.** Banned at every layer — Python scripts, hooks, and the semantic auditor all scan for them (ATS systems often choke on them).
- **Immutable facts.** Dates and employers are schema-locked. The pipeline cannot change what you actually did.
- **You approve before render.** CareerOps proposes a presentation plan and waits for your sign-off before writing a single bullet.

---

## Tech

- **Renderer:** RenderCV (Typst) — produces clean, ATS-safe PDFs
- **Data:** Local YAML files with JSON Schema validation
- **JD analysis:** Claude subagent with relevance scoring
- **Validation:** Python (8 gates) + Claude semantic auditor

---

## Contributing

Issues and PRs welcome. See `CLAUDE.md` for plugin architecture, conventions, and hard rules.

**[Star the repo](https://github.com/KalharPandya/careerops) if CareerOps saves you time.**

---

## License

MIT
