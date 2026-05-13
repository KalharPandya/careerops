# CareerOps — Plugin Packaging Plan

**Status:** Deferred. Pick this back up when ready to share publicly.
**Date drafted:** 2026-05-12

---

## Goal

Separate the reusable architecture (agents, skills, scripts, hooks, schemas) from Kalhar's personal career data so the system can be shared publicly. Use Claude Code's plugin system as the distribution mechanism.

---

## What we know about Claude Code plugins

A plugin is a self-contained directory with a manifest (`.claude-plugin/plugin.json`). It can bundle:

- **Subagents** — `agents/*.md`
- **Skills** — `skills/<name>/SKILL.md` (commands become namespaced: `/careerops:capture-fact`)
- **Hooks** — `hooks/hooks.json` (PostToolUse, SessionStart, etc.)
- **Scripts** — `scripts/*.py` referenced from hooks via relative paths
- **Schemas / static files** — anywhere in the plugin tree
- **MCP servers, LSPs, executables in `bin/`** — also supported but not needed here

**Install flow for a new user:**

```
/plugin marketplace add kalhar/careerops          # one-time, adds the marketplace JSON
/plugin install careerops@kalhar-careerops        # installs the plugin
/reload-plugins                                    # activates
```

After install, the user creates their own `career/` directory in their project and copies a template `config/rules.yaml`. Commands are namespaced as `/careerops:capture-fact`, `/careerops:generate-resume`, etc.

**Path rule (critical):** Plugin files live in `~/.claude/plugins/cache/<plugin-name>/`. Hardcoded absolute paths like `P:/Resumes/Claude-automations` will fail. All scripts and skills must use paths relative to the user's project root (cwd).

**Distribution:** Either a public GitHub repo with `marketplace.json` at `.claude-plugin/marketplace.json`, or submit to the official Anthropic marketplace at `platform.claude.com/plugins/submit`.

---

## Personal-info inventory (what needs to be scrubbed before public release)

### 1. Hardcoded paths — 10 occurrences across 5 files
Replace `P:/Resumes/Claude-automations` with dynamic project root detection (e.g. `Path.cwd()` or env var):

- `scripts/validate_resume.py` (line 31)
- `scripts/check_em_dashes.py` (line 23)
- `scripts/lint_yaml.py` (lines 14-15)
- `scripts/career_status.py` (line 9)
- `.claude/skills/generate-resume/SKILL.md` (lines 107, 151-153, 166)
- `.claude/skills/capture-fact/SKILL.md` (line 40)
- `.claude/agents/bullet-composer.md` (line 219)
- `docs/superpowers/specs/2026-05-12-careerops-design.md` (line 75)

### 2. Name references — "Kalhar" / "Kalhar Pandya" — 6 files
Genericize to `<candidate-name>` placeholder or read from `career/contact/contact.yaml`:

- `.claude/agents/resume-auditor.md` (3 refs in instructions and examples)
- `.claude/agents/bullet-composer.md` (cv.name hardcoded in template, examples)
- `.claude/skills/generate-resume/SKILL.md` (output filename `Kalhar_Pandya_CV.pdf`)
- `CLAUDE.md` (personal profile block)
- `docs/superpowers/specs/2026-05-12-careerops-design.md` (owner field)
- `README.md` (resume file path examples)

### 3. Employer/school references in examples
Genericize Oracle, KFin, FlytBase, Northeastern, IIT Delhi, Deloitte, VaultAI to `<company>`, `<role>` placeholders in:

- `CLAUDE.md`
- `.claude/agents/bullet-composer.md` (VaultAI example)
- Subagent example bullets

### 4. Files to move into `career/` (not shareable)
- `ats-resume-agent/examples/Master_Career_Document.md` — actually contains real personal data, not the cloned reference example. Verify and move.

### 5. Already-private (no action needed)
- `career/` subdirectories (facts, evidence, experiences, projects, contact, skills, education, applications, jd-analysis)
- `raw_data/`
- `inbox/`
- `ats-resume-agent/` (cloned reference)

---

## Three packaging options considered

| | A. Claude Code Plugin | B. Template repo | C. Hybrid |
|---|---|---|---|
| What ships | Plugin with agents/skills/scripts/hooks/schemas | GitHub template repo users fork | Plugin (logic) + template repo (data skeleton) |
| New user install | `/plugin marketplace add` then `/plugin install` | "Use this template" on GitHub | Both |
| Command form | `/careerops:capture-fact` (namespaced) | `/capture-fact` (root namespace) | Namespaced + bootstrap script |
| Auto-updates | Yes | No (manual git pull) | Plugin yes, template no |
| Effort | ~2 hours | ~45 min | ~3 hours |

**Recommended:** Option A (plugin). The path-fixing and name-scrubbing work is needed for any of the three; the marginal extra cost for the plugin is just adding the manifest and marketplace JSON, and the payoff is the official Anthropic mechanism plus auto-updates.

---

## Proposed plugin folder structure

```
careerops-plugin/                       (public, shareable repo on GitHub)
├── .claude-plugin/
│   ├── plugin.json                     manifest: name, version, author, description
│   └── marketplace.json                marketplace catalog entry
├── agents/
│   ├── fact-curator.md
│   ├── jd-analyzer.md
│   ├── bullet-composer.md              (paths + names parameterized)
│   └── resume-auditor.md               (names parameterized)
├── skills/
│   ├── capture-fact/SKILL.md
│   ├── capture-evidence/SKILL.md
│   ├── ingest-jd/SKILL.md
│   ├── generate-resume/SKILL.md        (paths fixed)
│   ├── audit-resume/SKILL.md
│   ├── humanize-resume/SKILL.md
│   ├── log-outcome/SKILL.md
│   ├── lint-career/SKILL.md
│   ├── career-status/SKILL.md
│   ├── career-help/SKILL.md
│   └── seed-from-tex/SKILL.md
├── hooks/
│   └── hooks.json                      (extracted from .claude/settings.json)
├── scripts/
│   ├── lint_yaml.py                    (paths parameterized)
│   ├── check_em_dashes.py              (paths parameterized)
│   ├── validate_resume.py              (paths parameterized)
│   ├── career_status.py                (paths parameterized)
│   └── secret_scan.py
├── schemas/                            (8 JSON Schemas, already clean)
├── config-template/
│   └── rules.yaml                      user copies into their career/config/
├── README.md                           install + usage docs
└── LICENSE

User's own project (private):
├── career/                             user's career data
│   ├── facts/, evidence/, experiences/, projects/
│   ├── applications/, jd-analysis/
│   ├── contact/contact.yaml            user fills in their info
│   └── config/rules.yaml               copied from plugin's config-template/
├── inbox/                              user drops JDs here
└── raw_data/                           user's existing resumes (optional)
```

---

## Open decisions to make when we resume

1. **Option A / B / C?** Recommendation is A.
2. **Where to build:** sibling folder (`P:\Resumes\careerops-plugin\`), subfolder of current repo, or fresh git repo immediately?
3. **Plugin namespace:** `careerops` is the obvious one. Confirm.
4. **GitHub repo name:** `kalhar/careerops` or `kalhar/careerops-plugin` or something else?
5. **License:** MIT? Apache 2.0?
6. **Submit to Anthropic marketplace, or self-host only?**
7. **Project root resolution strategy in scripts** — three options to pick from:
   - `Path.cwd()` (simple but breaks if user runs script from a subdirectory)
   - Walk up from script location looking for `career/` or a marker file like `.careerops`
   - Environment variable `$CAREEROPS_ROOT` (explicit, requires user setup)

---

## Order of operations when we resume

1. Decide on options 1-7 above
2. Create the new plugin folder/repo
3. Copy files from `P:\Resumes\Claude-automations\.claude\agents\`, `.claude\skills\`, `scripts\`, `schemas\` into the plugin structure
4. Run search-and-replace to fix all 10 hardcoded paths
5. Run search-and-replace to genericize "Kalhar" / "Kalhar Pandya" references in shared files
6. Write `.claude-plugin/plugin.json` manifest
7. Write `.claude-plugin/marketplace.json`
8. Write plugin README with install instructions
9. Test install locally (`/plugin marketplace add file:///P:/Resumes/careerops-plugin`)
10. Test the full workflow end-to-end with a clean fake user project
11. Push to GitHub, optionally submit to Anthropic marketplace

---

## What stays in the current repo

This repo (`P:\Resumes\Claude-automations`) becomes your **personal CareerOps instance**:
- Your `career/` data (facts, evidence, experiences, applications)
- Your `raw_data/` and `inbox/`
- A CLAUDE.md that documents this is your personal instance
- A pointer to the plugin repo for getting updates

Once the plugin is published, you'd uninstall the local `.claude/agents/` and `.claude/skills/` from this repo and replace them with the installed plugin — single source of truth, no drift.
