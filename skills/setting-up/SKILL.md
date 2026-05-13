---
name: setting-up
description: First-run wizard that scaffolds your career directory, collects config, and prepares the knowledge base for use. Safe to re-run -- detects new vs. returning user and adjusts accordingly.
---

# /setting-up -- CareerOps Setup Wizard

## Purpose
Run once after installing the CareerOps plugin (or any time you want to change your defaults). The skill detects whether you are a new or returning user and adjusts its behavior accordingly.

## Usage
```
/careerops:setting-up
```

Idempotent: re-running shows existing values as defaults. Existing facts, experiences, applications, and JD analyses are never touched.

## User Detection Logic

**New user:** `career/experiences/` does not exist or is empty.
**Returning user:** `career/experiences/` exists and contains at least one `X-*.yaml` file.

The `setup-guide` subagent handles both flows interactively.

## What This Skill Does

### New user flow
1. Scaffold the full directory tree:
   ```
   career/experiences/    career/projects/
   career/evidence/       career/applications/   career/jd-analysis/
   career/contact/        career/education/      career/skills/
   career/config/         inbox/                 raw_data/
   ```
2. Copy all templates from `${CLAUDE_PLUGIN_ROOT}/templates/` into appropriate directories
3. Ask Q1-Q4 (theme, header visibility, page budget, contact info) interactively
4. Write config files
5. Prompt: "Drop an existing resume in `raw_data/` and run `/careerops:seeding-career-db <path>` to import it, or run `/careerops:capturing-fact` to start adding achievements manually."

### Returning user flow
1. Show current config values as defaults
2. Ask only about fields that are unset
3. Skip directory scaffolding entirely
4. End with a summary of what changed (or "No changes made" if nothing was updated)

## Questions Asked (Q1-Q4)

**Q1: RenderCV theme**
Options:
- `engineeringresumes` -- densest, inline dates, no right column, no color
- `classic` -- centered name, icon bar, right-aligned dates, blue accent
- `sb2nov` -- horizontal-rule section headers, two-line role headers
- `moderncv` -- colored sidebar, more graphical
- `engineeringclassic` -- hybrid: classic header + engineeringresumes body

If the user is unsure, offer to render all 5 themes against their current resume data into a `previews/` folder for visual comparison.

**Q2: Header visibility**
- Show location: yes / no / per-application
- Show phone: yes / no / per-application
- Show email: yes (default, required) / no

**Q3: Default page budget**
- 1 page (typical for intern, junior, or career-change applications)
- 2 pages (recommended default for mid-to-senior)

**Q4: Contact info** (only fields that are currently unset)
- Name
- Email
- Location string (e.g. `<City, Region>`)
- Phone (optional)
- LinkedIn username (optional)
- GitHub username (optional)
- Personal website (optional)

## Config Files Written

```yaml
# career/config/rendercv-theme.yaml
theme: <chosen-theme>
```

```yaml
# career/contact/contact.yaml
name: <name>
email: <email>
location: <location string>
phone: <phone or null>
linkedin: <username or null>
github: <username or null>
website: <url or null>
```

```yaml
# career/config/rules.yaml (presentation block only -- other fields untouched)
presentation:
  show_location_default: <true|false|per_application>
  show_phone_default:    <true|false|per_application>
  page_budget_default:   <1|2>
```

## Instructions for Claude Code

When this skill is invoked:

1. Check whether `career/experiences/` exists and contains at least one `X-*.yaml` file.
   - If no: this is a new user. Proceed with new user flow.
   - If yes: this is a returning user. Proceed with returning user flow.

2. Dispatch the `setup-guide` subagent with:
   - Detected user state: `new` or `returning`
   - Paths to existing config files (if any)
   - List of directories that are missing and must be created
   - Instruction to follow the Q1-Q4 interview protocol

3. After the subagent completes, confirm to the user which files were written.

4. If new user: print the seed prompt (see new user flow step 5 above).

5. If returning user: print a diff of what changed (or "No changes made").

## Error Guard

If `setting-up` is invoked when facts exist, confirm before overwriting any config file. Never touch `career/facts[]` arrays inside experience files, `career/applications/`, or `career/jd-analysis/` under any circumstances.

## Rules

- Never delete career facts, experiences, projects, applications, or JD analyses during setup. This skill only touches config and contact files.
- Always show the current value as the default so the user can keep it by pressing enter.
- Preserve all other top-level fields in `rules.yaml` -- only add or update the `presentation` block.
