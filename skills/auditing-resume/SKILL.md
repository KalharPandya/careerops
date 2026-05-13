---
name: auditing-resume
description: Re-run the semantic auditor on an existing application to check AI markers, quality, and JD fit.
---

# /auditing-resume -- Re-run Semantic Auditor on a Resume

## Usage
```
/careerops:auditing-resume <app-id>
```
Example:
```
/careerops:auditing-resume A-2026-05-15-procogia-mle
```

Optional flag to accept a NEEDS-REVIEW verdict:
```
/careerops:auditing-resume A-2026-05-15-procogia-mle --accept
```

## What This Skill Does
Dispatches the `resume-auditor` subagent to re-run the semantic quality pass on an already-generated resume. Use this to:
- Re-audit after manually editing `rendercv-input.yaml`
- Get a fresh verdict after humanizing specific bullets
- Accept a NEEDS-REVIEW verdict explicitly

## Instructions for Claude Code

1. Parse the app-id from arguments.
2. Verify `career/applications/<app-id>/rendercv-input.yaml` exists. If not, print an error.
3. Read `career/applications/<app-id>/application.yaml` to get the `jd_ref`.
4. If `--accept` flag is present and there is an existing audit report:
   - Set `validation_summary.auditor_verdict: PASS` (user-accepted)
   - Ask: "Mark ready_to_send: true as well? [y/n]"
   - If yes: set `ready_to_send: true` in `application.yaml`
   - Print: "NEEDS-REVIEW verdict accepted by user. Application marked ready_to_send."
   - Stop (skip re-running the auditor).
5. Otherwise dispatch the `resume-auditor` subagent with:
   - `rendercv-input.yaml` path
   - `claim-ledger.yaml` path
   - JD analysis yaml path
   - `proposed-plan.yaml` path
6. After the report is written, display the verdict and the AI Marker Scan table.
7. If verdict is PASS, ask: "Mark ready_to_send: true? [y/n]"
