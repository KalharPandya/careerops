# CareerOps

**Your career, recorded. Your resume, generated. Zero fabrication.**

[![npm version](https://img.shields.io/npm/v/careerops)](https://www.npmjs.com/package/careerops)
[![license](https://img.shields.io/npm/l/careerops)](LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-plugin-blue)](https://claude.ai/code)

CareerOps is a Claude Code plugin — a personal career knowledge base that turns your real history into tailored, ATS-ready resumes on demand, without fabricating a single word.

**If this saves you time, [star the repo](https://github.com/KalharPandya/careerops) — it helps others find it.**

---

## Sound Familiar?

> *"I just got promoted. How do I capture this properly so I remember it in two years?"*

> *"I shipped something big last quarter. I know it was impressive — I just can't remember the exact numbers anymore."*

> *"I won an award. Got a great performance review. Finished a project I'm proud of. Where do I put all of this?"*

> *"I'm applying to ten jobs. My resume says the same thing for all of them. I know some of this experience is more relevant than others — I just don't know how to show that."*

> *"It's been three years. I open a blank doc. I stare at it. I genuinely cannot remember everything I've done."*

This is the problem CareerOps solves. Not just resume generation — **career memory**.

Most people have no system for recording what they do. Achievements get forgotten. Promotions don't make it into resumes with the right framing. Side projects disappear into GitHub. When a great opportunity appears, you're scrambling to reconstruct years of work from memory, Slack messages, and old PRs.

CareerOps is the system you never had. **Capture once. Apply everywhere.**

---

## The Problem with AI Resumes

The other problem: every AI resume tool invents things. It dresses up your experience with metrics you never hit, skills you never used, and bullet points that sound impressive but aren't true. That works until the interview — then it fails badly.

CareerOps treats your resume as an **output of your fact database**, not a document generated from scratch. If you didn't capture it, it doesn't appear. Every bullet on every resume traces to something you actually did.

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

**You just shipped something big.**
Run `/careerops:capturing-fact`. CareerOps interviews you — what did you build, what was the impact, what's the metric. Stored, structured, permanently recorded. You'll have it word-for-word when you need it two years from now.

**You got promoted or won an award.**
Same flow. Capture it now, while you remember the details. Your fact database grows with your career.

**You're in a job search.**
Drop in a job description. CareerOps scores every fact in your database against it, surfaces the most relevant experience, proposes a presentation plan, and generates a tailored resume grounded entirely in your real history.

**You're applying to 10 different roles.**
Not 10 different resumes written by hand. One database, 10 different fact weightings. Each resume is specific to its JD.

**You have too much experience for one page.**
CareerOps knows what you've done. It decides what to expand, compress, or drop based on what the role actually asks for — and asks for your sign-off before writing a word.

**You haven't updated your resume in three years.**
Import your old resume and seed your database from it. Then start capturing forward. You'll never start from a blank page again.

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
