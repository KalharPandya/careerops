---
name: logging-outcome
description: Record the outcome of a job application as interview, offer, reject, or no-response in the application registry.
---

# /logging-outcome -- Record Application Outcome

## Usage
```
/careerops:logging-outcome <app-id> <state>
```
States: `interview`, `reject`, `offer`, `no_response`

Examples:
```
/careerops:logging-outcome A-2026-05-15-procogia-mle interview
/careerops:logging-outcome A-2026-05-15-procogia-mle reject
```

## What This Skill Does
Records the outcome of a job application in `career/applications/<app-id>/application.yaml`.

## Instructions for Claude Code

1. Parse `app-id` and `state` from arguments. If either is missing, ask for them.
2. Validate `state` is one of: `interview`, `reject`, `offer`, `no_response`.
3. Read `career/applications/<app-id>/application.yaml`.
4. Update:
   ```yaml
   outcome:
     state: <state>
     at: <ISO 8601 now>
     notes: ""
   ```
5. Ask: "Any notes to add? (press Enter to skip)"
6. If notes provided, add to `outcome.notes`.
7. Write the updated file.
8. Print:
   ```
   [logging-outcome] <app-id>: outcome recorded as <state> at <date>
   ```
9. If state is `interview`: print "Next step: prepare for interview. Review your audit-report.md for talking points."
10. If state is `reject`: print "Logged. Run a career status check to review your pipeline."
