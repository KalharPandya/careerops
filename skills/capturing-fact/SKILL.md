---
name: capturing-fact
description: Interview to record a new career achievement as an atomic fact with metrics, framings, and evidence prompts.
---

# /capturing-fact -- Record a New Career Achievement

## When to Use
Run this skill whenever you want to record a new achievement, responsibility, or skill use to your career knowledge base. Run it right after completing something notable -- while details are fresh.

## What This Skill Does
Invokes the `fact-curator` subagent, which will interview you one question at a time to capture a new atomic fact. The fact is written as an entry in the `facts[]` array of the matching `career/experiences/X-*.yaml` file (or as a standalone fact in `career/projects/P-*.yaml` for project work). You are prompted to attach evidence after capture.

## How to Invoke
In Claude Code, type:
```
/careerops:capturing-fact
```

Optional: provide a brief description to skip the first interview question:
```
/careerops:capturing-fact Won the AI Hackathon with a 50-agent hierarchy
```

## Steps This Skill Executes
1. Load the `fact-curator` subagent
2. If a description was provided as an argument, pass it as the starting context
3. The subagent interviews you for: what happened, when, which role/employer, impact metric, technologies used, evidence available
4. You review and approve the draft fact YAML
5. The fact is appended to the `facts[]` array inside the matching `career/experiences/X-*.yaml`
6. You are prompted to attach evidence (`/careerops:capturing-evidence`) if none is available yet

## After Capturing
- Run `/careerops:linting-career` to verify the updated experience file passes schema validation
- Run `/careerops:capturing-evidence <fact-id>` to attach a source document
- The fact will have `status: pending-evidence` until evidence is attached

## Instructions for Claude Code

When this skill is invoked:

1. Announce: "Starting fact capture. I'll ask you a few questions one at a time."
2. Dispatch the `fact-curator` subagent with this context:
   - Working directory: the user's career data directory (wherever Claude Code is running from)
   - Any text provided after `/careerops:capturing-fact` as the initial description
   - Instruction: follow the fact-curator interview protocol; append result to matching experience file's `facts[]` array
3. After the subagent writes the fact, confirm the experience file path and the new fact ID to the user
4. Ask: "Attach evidence now? Run `/careerops:capturing-evidence <fact-id>` when ready."
5. Ask: "Should I update any other related experience or project file for this achievement?"
