#!/usr/bin/env python3
"""
CareerOps UserPromptSubmit hook.

Detects resume/JD/fact-capture intent in the user's message and injects
a mandatory routing directive before Claude responds. This prevents Claude
from bypassing CareerOps skills via its default helpfulness.

Returns JSON with additionalContext so the model sees the directive before
generating any response.
"""

import json
import sys
import re

JD_PATTERNS = [
    r"\bjob description\b",
    r"\bjob posting\b",
    r"\bwe are looking for\b",
    r"\byou will\b.{0,80}\b(role|position|team)\b",
    r"\bresponsibilities\b",
    r"\bqualifications\b",
    r"\bwhat you.ll do\b",
    r"\bwhat we.re looking for\b",
    r"\bapply\b.{0,40}\b(role|position|company|job)\b",
    r"\bi want to apply\b",
    r"\bgive me.{0,30}resume\b",
    r"\bcreate.{0,30}resume\b",
    r"\btailor.{0,30}resume\b",
    r"\bgenerate.{0,30}resume\b",
    r"\bresume for (this|the)\b",
    r"\bcover letter\b",
]

FACT_PATTERNS = [
    r"\bi (just |recently )?(built|shipped|launched|deployed|finished|completed|reduced|improved|increased|led|designed|created|wrote|implemented)\b",
    r"\bwe (just |recently )?(built|shipped|launched|deployed|finished|completed|reduced|improved|increased|led|designed|created|wrote|implemented)\b",
    r"\b(reduced|improved|increased).{0,60}(by|from|to)\b",
    r"\b\d+%\b.{0,60}(improve|reduc|increas|optim|speed|faster|slower)\b",
]

DIRECTIVE_JD = (
    "<careerops-mandatory-routing>\n"
    "STOP. The user is requesting resume generation or sharing a job description.\n"
    "You MUST use the Skill tool NOW before doing anything else:\n"
    "  Skill({\"skill\": \"careerops:analyzing-jd\"})\n"
    "Do NOT read career files. Do NOT read memory. Do NOT draft bullets.\n"
    "Do NOT use any other skill. Call careerops:analyzing-jd via the Skill tool immediately.\n"
    "This is not optional. CareerOps skills override all default behavior.\n"
    "</careerops-mandatory-routing>"
)

DIRECTIVE_FACT = (
    "<careerops-mandatory-routing>\n"
    "STOP. The user is describing a career achievement or result.\n"
    "You MUST use the Skill tool NOW before doing anything else:\n"
    "  Skill({\"skill\": \"careerops:capturing-fact\"})\n"
    "Do NOT write it down manually. Do NOT paraphrase. Do NOT use any other skill.\n"
    "Call careerops:capturing-fact via the Skill tool immediately.\n"
    "This is not optional. CareerOps skills override all default behavior.\n"
    "</careerops-mandatory-routing>"
)


def detect_intent(text: str) -> str | None:
    lower = text.lower()
    for pat in JD_PATTERNS:
        if re.search(pat, lower):
            return "jd"
    for pat in FACT_PATTERNS:
        if re.search(pat, lower):
            return "fact"
    return None


def main():
    try:
        payload = json.load(sys.stdin)
        prompt = payload.get("user_prompt", "") or ""
    except Exception:
        sys.exit(0)

    intent = detect_intent(prompt)
    if intent is None:
        sys.exit(0)

    directive = DIRECTIVE_JD if intent == "jd" else DIRECTIVE_FACT

    output = {
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": directive,
        }
    }
    sys.stdout.buffer.write(json.dumps(output, ensure_ascii=False).encode("utf-8"))
    sys.stdout.buffer.write(b"\n")
    sys.stdout.buffer.flush()


if __name__ == "__main__":
    main()
