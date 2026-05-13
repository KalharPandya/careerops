# CareerOps User Setup Guide

This guide walks a new user through setting up their own career data directory with the CareerOps plugin.

## Prerequisites

- Claude Code CLI installed
- CareerOps plugin at a local path (e.g., `P:\CareerOps`) or installed via marketplace
- Python 3.9+ on PATH
- RenderCV installed: `pip install rendercv`

## Step 1: Create Your Data Directory

```powershell
New-Item -ItemType Directory -Path "C:\path\to\my-career"
cd "C:\path\to\my-career"
```

This directory will hold all your career data. It is separate from the plugin and contains only your personal information.

## Step 2: Start Claude with the Plugin

```powershell
claude --plugin-dir P:\CareerOps
```

All CareerOps skills are now available under the `/careerops:` namespace.

## Step 3: Initialize the Data Directory

```
/careerops:career-init
```

This copies starter templates from the plugin into your data directory, creating:

```
my-career/
├── CLAUDE.md                      Your profile and preferences (fill this in)
├── career/
│   ├── contact/contact.yaml       Your contact info
│   ├── education/edu.yaml         Your degrees
│   ├── skills/skills.yaml         Your skills by category
│   ├── facts/                     Will hold F-*.yaml atomic facts
│   ├── experiences/               Will hold X-*.yaml role envelopes
│   ├── projects/                  Will hold P-*.yaml project entries
│   ├── evidence/                  Will hold E-*.yaml evidence sources
│   ├── applications/              One folder per sent resume
│   ├── jd-analysis/               Analyzed job descriptions
│   └── config/
│       ├── rules.yaml             Validation rules (inherits plugin defaults)
│       └── rendercv-theme.yaml    Your theme choice
├── inbox/                         Drop raw JDs here
└── raw_data/                      Drop source resumes here
```

## Step 4: Fill In Your Profile

Edit the generated files with your real information:

**`CLAUDE.md`** — Your name, email, target roles, experience summary, writing preferences. This is what Claude reads every session to know who you are.

**`career/contact/contact.yaml`** — Name, email, phone, location, website, LinkedIn, GitHub.

**`career/education/edu.yaml`** — Your degrees, institutions, GPAs, dates.

**`career/skills/skills.yaml`** — Your skills organized by category (languages, frameworks, tools, etc.).

## Step 5: Seed Your Career Knowledge Base

If you have an existing LaTeX resume:

```
/careerops:seed-from-tex raw_data/your-resume.tex
```

If you have a Markdown career document:

```
/careerops:seed-from-master Master_Career_Document.md
```

Both commands populate `career/facts/` and `career/experiences/` from your existing material.

## Step 6: Apply for a Job

1. Drop the job description into `inbox/` as a `.md` or `.txt` file
2. Run `/careerops:ingest-jd inbox/company-role.md`
3. Run `/careerops:generate-resume JD-YYYY-MM-DD-company-role`
4. Review the proposed presentation plan and approve
5. The system renders, validates, and audits your resume
6. Find the output at `career/applications/A-YYYY-MM-DD-company-role/resume.pdf`

## Ongoing Usage

```
/careerops:capture-fact        Add a new career achievement any time
/careerops:career-status       Check DB health (fact count, applications)
/careerops:lint-career         Validate all career YAML files
/careerops:log-outcome <id>    Record interview/offer/reject
```

## Validation Rules

The plugin enforces several rules on every file write:

- **No em-dashes** (U+2014 and variants) — use commas, semicolons, or parentheses instead
- **No fabrication** — every resume bullet must trace to a fact ID
- **Dates and employers are immutable** in facts
- **Page budget** — resumes default to max 2 pages

These are enforced automatically via hooks whenever you edit YAML or resume files.
