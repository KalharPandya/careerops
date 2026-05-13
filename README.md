# CareerOps

**A Claude Code plugin that turns your career history into tailored, ATS-clean resumes — with zero fabrication.**

Every resume bullet traces to a verified fact you captured. A multi-layer pipeline handles relevance scoring, planning, writing, rendering, and validation. You stay in control at every step.

---

## How It Works

1. **Capture** your career achievements once — CareerOps stores them as structured facts
2. **Drop a job description** into your inbox folder
3. **Run the resume pipeline** — it scores your facts against the JD, asks you to approve the plan, writes bullets with full provenance, renders a PDF, and validates the result

---

## Prerequisites

- [Claude Code](https://claude.ai/code) installed and running
- Python 3.10+
- `pip install pyyaml rendercv`

---

## Install

```bash
npx careerops install
```

Then restart Claude Code. That's it — all commands are available under `/careerops:`.

To update later:
```bash
npx careerops update
```

To uninstall:
```bash
npx careerops uninstall
```

---

## Getting Started

**Step 1 — Create your career directory and open Claude inside it**

```bash
mkdir ~/my-career
cd ~/my-career
claude
```

**Step 2 — Run the setup wizard**

```
/careerops:setting-up
```

This scaffolds your directory structure and collects your profile (name, email, links).

**Step 3 — Import your existing resume** *(optional but recommended)*

Drop your current resume into `raw_data/`, then:

```
/careerops:seeding-career-db raw_data/your-resume.tex
```

Supports `.tex` and `.md` formats. CareerOps will extract structured facts from it.

**Step 4 — Capture new achievements as they happen**

```
/careerops:capturing-fact
```

CareerOps interviews you and stores the result as a verified fact.

**Step 5 — Apply to a job**

Drop the job description into `inbox/`, then:

```
/careerops:analyzing-jd
/careerops:generating-resume
```

The pipeline scores your facts against the JD, proposes a presentation plan for your approval, writes the bullets, renders the PDF, and validates it.

---

## All Commands

### Setup
| Command | What it does |
|---|---|
| `/careerops:setting-up` | First-run wizard — scaffolds directories, collects your profile |
| `/careerops:seeding-career-db` | Import an existing resume into your knowledge base |

### Capture
| Command | What it does |
|---|---|
| `/careerops:capturing-fact` | Interview to record a new achievement |
| `/careerops:capturing-evidence` | Attach a URL, PR, or document to an existing fact |

### Apply
| Command | What it does |
|---|---|
| `/careerops:analyzing-jd` | Parse a job description — scores all your facts by relevance |
| `/careerops:generating-resume` | Full pipeline: plan, compose, render PDF, validate, audit |
| `/careerops:auditing-resume` | Re-run the quality auditor on a generated resume |
| `/careerops:humanizing-resume` | Clean up AI-marker patterns in bullets |
| `/careerops:logging-outcome` | Record the result of an application |

### Health
| Command | What it does |
|---|---|
| `/careerops:linting-career` | Schema, reference, and em-dash check across all your data |
| `/careerops:getting-help` | Quick-start guide — add `full` for the complete reference |

---

## Your Data Layout

After setup, your career directory looks like this:

```
~/my-career/
├── career/
│   ├── experiences/        # Your work history + facts
│   ├── applications/       # One folder per job application
│   ├── jd-analysis/        # Parsed job descriptions
│   └── config/             # Theme, rules
├── inbox/                  # Drop JDs here
└── raw_data/               # Source resumes for seeding
```

The plugin lives separately at `~/.claude/plugins/careerops/`. Your data never touches it.

---

## Guarantees

- **No fabrication.** Every bullet traces to a fact ID you captured. The validator enforces this.
- **No em-dashes.** Enforced at every layer — scripts, hooks, and the semantic auditor all scan for them.
- **Dates and employers are immutable.** The schema locks these fields regardless of what a JD asks for.
- **You approve before render.** The pipeline presents a plan (which roles to expand, compress, or drop) and waits for your sign-off.

---

## Tech

- **Renderer:** RenderCV (Typst)
- **Data:** YAML files with JSON Schema validation
- **JD analysis:** Claude subagent with relevance scoring
- **Validation:** Python (8 gates) + Claude semantic auditor

---

## License

MIT
