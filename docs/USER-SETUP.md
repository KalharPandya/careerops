# CareerOps User Setup Guide

This guide walks a new user through setting up their own career data directory with the CareerOps plugin.

## Prerequisites

- Claude Code CLI installed
- Python 3.9+ on PATH
- RenderCV installed: `pip install rendercv`

## Step 1: Install the Plugin

Inside any Claude Code session:

```
/plugin marketplace add KalharPandya/careerops
/plugin install careerops@careerops
```

The plugin is now available in every future session automatically.

## Step 2: Create Your Career Data Directory

```bash
mkdir -p ~/my-career
cd ~/my-career
```

This directory holds all your personal career data. It is completely separate from the plugin.

## Step 3: Launch Claude and Run Setup

```bash
claude
```

Then inside Claude:

```
/careerops:setting-up
```

This runs the first-time wizard which:
1. Detects you are a new user (no existing data)
2. Scaffolds the full directory structure:
   ```
   career/experiences/    career/projects/       career/evidence/
   career/applications/   career/jd-analysis/    career/contact/
   career/education/      career/skills/         career/config/
   inbox/                 raw_data/
   ```
3. Copies starter templates from the plugin
4. Asks 8 questions (name, email, location, LinkedIn, GitHub, website, theme, page budget)
5. Writes your config files and tells you what to do next

## Step 4: Seed Your Knowledge Base

Drop an existing resume into `raw_data/` then run:

```
/careerops:seeding-career-db raw_data/your-resume.tex
```

Or for a Markdown career document:

```
/careerops:seeding-career-db Master_Career_Document.md
```

This populates `career/experiences/` with your roles and embedded facts from your existing resume.

## Step 5: Apply for a Job

1. Drop the job description into `inbox/` as a `.md` or `.txt` file
2. Run `/careerops:analyzing-jd inbox/company-role.md`
3. Run `/careerops:generating-resume JD-YYYY-MM-DD-company-role`
4. Review and approve the proposed presentation plan
5. The system renders, validates, and audits your resume
6. Find the output at `career/applications/A-YYYY-MM-DD-company-role/resume.pdf`

## Ongoing Usage

```
/careerops:capturing-fact       Add a new career achievement any time
/careerops:linting-career       Validate all career YAML files
/careerops:logging-outcome      Record interview/offer/reject outcome
/careerops:getting-help         Quick-start guide (add "full" for complete reference)
```

## Validation Rules

The plugin enforces several rules automatically on every file write:

- **No em-dashes** (U+2014 and variants) — use commas, semicolons, or parentheses instead
- **No fabrication** — every resume bullet must trace to a fact ID
- **Dates and employers are immutable** in facts
- **Page budget** — resumes default to max 2 pages
