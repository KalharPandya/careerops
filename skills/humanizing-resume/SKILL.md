---
name: humanizing-resume
description: Remove AI markers and improve bullet tone in an existing application resume using the humanize-content skill.
---

# /humanizing-resume -- Manual Humanization Touchup

## Usage
```
/careerops:humanizing-resume <app-id>
```
Or target a specific section:
```
/careerops:humanizing-resume <app-id> --section professional_summary
/careerops:humanizing-resume <app-id> --bullet B-007
```

## What This Skill Does
Applies humanization rules to bullets or sections in a generated resume, without regenerating the whole thing. Delegates to the `humanize-content` skill (a separate external skill, not part of careerops -- invoke it directly as `/humanize-content`) for the actual rules. Updates `rendercv-input.yaml` in place. Re-runs the auditor after changes.

## The humanize-content rules (condensed for resume context)

No banned words: leverage, robust, comprehensive, seamless, delve, landscape,
paradigm, synergy, holistic, cutting-edge, state-of-the-art, spearheaded,
pioneered, harnessed, fostered, facilitated, streamlined, successfully.

No em-dashes. Never. Use commas, semicolons, or restructure the sentence.

Vary sentence openings: not every bullet starts with "Developed" or "Built".
Mix short punchy bullets with slightly longer contextual ones.

Be concrete: name the technology, name the metric, name the outcome.
Replace vague generics ("improved performance") with specific claims ("cut P99 latency from 800ms to 120ms").

Sound like a technical professional, not an AI assistant.

## Instructions for Claude Code

1. Parse app-id and optional `--section` or `--bullet` flags.

2. Read `career/applications/<app-id>/rendercv-input.yaml`.

3. Also read `career/applications/<app-id>/claim-ledger.yaml` to understand which facts back each bullet. Do not change the facts -- only surface phrasing.

4. If `--bullet B-NNN` specified:
   - Find the bullet in `rendercv-input.yaml` by matching its text against `claim-ledger.yaml` bullet_id
   - Apply humanization to that single bullet
   - Show before/after and ask: "Use this version? [y/n/edit]"

5. If `--section professional_summary` specified:
   - Apply humanization to the summary paragraph
   - Show before/after and ask: "Use this version? [y/n/edit]"

6. If no section/bullet specified:
   - Scan all bullets and the summary for AI markers (banned words, em-dashes, uniform rhythm)
   - Show a list of flagged bullets with suggested rewrites
   - Ask: "Apply all fixes? [y/n/select]"

7. For each accepted change:
   - Update `rendercv-input.yaml`
   - Verify the new text does not contain em-dashes
   - The backed_by facts in claim-ledger.yaml must still be traceable to the new text (same meaning, different words)

8. After changes, re-run the em-dash check:
   ```
   python scripts/check_em_dashes.py career/applications/<app-id>/rendercv-input.yaml
   ```

9. Ask: "Re-run the auditor? [y/n]" (suggest yes)

## Hard constraints

- Never change numeric metrics (these trace to Tier 1 immutable facts)
- Never change employer names or dates
- The claim must still be traceable to the backed_by fact after rewording
- If you cannot humanize a bullet without changing its factual claim, flag it and skip
