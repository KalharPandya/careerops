---
name: capturing-evidence
description: Attach an evidence source (URL, certificate, file) to an existing career fact by its ID.
---

# /capturing-evidence -- Attach Evidence to a Fact

## When to Use
Run this after capturing a fact to attach a source document, URL, screenshot, certificate, PR link, or other verifiable evidence. Evidence upgrades a fact's status from `pending-evidence` to `verified`.

## Usage
```
/careerops:capturing-evidence <fact-id>
```
Example:
```
/careerops:capturing-evidence F-2025-deloitte-1st-50agents
```

## What This Skill Does
1. Locates the specified fact by scanning `facts[]` arrays inside `career/experiences/X-*.yaml` files (and `career/projects/P-*.yaml`)
2. Prompts you for the evidence source (URL, file path, or description)
3. Creates a new `career/evidence/E-*.yaml` file
4. Updates the fact's `evidence` list and sets `status: verified`

## Evidence Types Supported
- `certificate` -- award certificate, diploma, completion cert
- `url` -- public URL (GitHub PR, LinkedIn post, article, leaderboard)
- `file` -- local file (place in `career/assets/`)
- `screenshot` -- screenshot of result (place in `career/assets/`)
- `testimonial` -- reference letter or recommendation text
- `pr` -- GitHub PR link
- `commit` -- GitHub commit link
- `email` -- email confirmation (redact personal info before saving)

## Instructions for Claude Code

When this skill is invoked:

1. Parse the fact ID from the argument. If missing, ask: "Which fact ID? (e.g. F-2025-deloitte-1st-50agents)"
2. Scan all `career/experiences/X-*.yaml` and `career/projects/P-*.yaml` files for a fact with `id: <fact-id>`. If not found, print an error and stop.
3. Ask: "What type of evidence? (certificate / url / file / screenshot / pr / commit / email / testimonial)"
4. Ask: "Provide the source (URL, file path, or description):"
5. Ask: "When was this verified? (YYYY-MM-DD):"
6. Generate evidence ID: `E-<employer-slug>-<description>` (e.g. `E-deloitte-certificate`)
7. Write `career/evidence/<evidence-id>.yaml`:

```yaml
id: <evidence-id>
type: <type>
source: "<source>"
attestation: self-attested
verified_at: <YYYY-MM-DD>
backs_facts:
  - <fact-id>
```

8. Locate the fact entry inside its parent experience or project file. Update it:
   - Add the evidence ID to the `evidence` list
   - Change `status` from `pending-evidence` to `verified`

9. Confirm: "Evidence attached. Fact <fact-id> is now verified."
10. Run lint: invoke `python scripts/lint_yaml.py` on the updated experience file and the new evidence file
