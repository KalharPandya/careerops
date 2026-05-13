#!/usr/bin/env python3
"""
CareerOps SessionStart hook script.

Outputs a single JSON object to stdout with hookSpecificOutput.additionalContext
containing the bootstrap routing rules (from using-careerops/SKILL.md) plus
career DB state (fact counts, empty-state warnings, missing contact warning).

Used by hooks/hooks.json SessionStart event.
Format: {"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": "..."}}
"""

import json
import os
import sys
import yaml
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from _paths import career_dir, data_root

BANNER = (
    " ██████╗ █████╗ ██████╗ ███████╗███████╗██████╗  ██████╗ ██████╗ ███████╗\n"
    "██╔════╝██╔══██╗██╔══██╗██╔════╝██╔════╝██╔══██╗██╔═══██╗██╔══██╗██╔════╝\n"
    "██║     ███████║██████╔╝█████╗  █████╗  ██████╔╝██║   ██║██████╔╝███████╗\n"
    "██║     ██╔══██║██╔══██╗██╔══╝  ██╔══╝  ██╔══██╗██║   ██║██╔═══╝ ╚════██║\n"
    "╚██████╗██║  ██║██║  ██║███████╗███████╗██║  ██║╚██████╔╝██║     ███████║\n"
    " ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚═╝     ╚══════╝\n"
    "  Your career, recorded. Your resume, generated. Zero fabrication.\n"
    "                                                        — by Kalhar Pandya"
)


def plugin_root() -> Path:
    env = os.environ.get("CLAUDE_PLUGIN_ROOT")
    if env:
        return Path(env).resolve()
    return Path(__file__).resolve().parent.parent


def bootstrap_skill_path() -> Path:
    return plugin_root() / "skills" / "using-careerops" / "SKILL.md"


def count_facts(career: Path) -> tuple:
    v2_facts = 0
    v2_experiences = 0
    experiences_dir = career / "experiences"

    if experiences_dir.exists():
        for exp_path in sorted(experiences_dir.glob("X-*.yaml")):
            try:
                with open(exp_path, encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                if data and isinstance(data.get("facts"), list):
                    v2_facts += len(data["facts"])
                    v2_experiences += 1
            except Exception:
                pass

    v1_facts = 0
    facts_dir = career / "facts"
    if facts_dir.exists():
        v1_facts = len(list(facts_dir.glob("F-*.yaml")))

    total = v2_facts + v1_facts

    if v2_facts > 0 and v1_facts == 0:
        desc = f"{v2_facts} facts across {v2_experiences} experience file(s)"
    elif v1_facts > 0 and v2_facts == 0:
        desc = f"{v1_facts} standalone fact file(s) in career/facts/"
    elif v2_facts > 0 and v1_facts > 0:
        desc = (
            f"{v2_facts} embedded fact(s) in experience files + "
            f"{v1_facts} standalone fact file(s) (migration in progress)"
        )
    else:
        desc = "0 facts"

    return total, desc


def count_applications(career: Path) -> int:
    apps_dir = career / "applications"
    if not apps_dir.exists():
        return 0
    return len([d for d in apps_dir.iterdir() if d.is_dir() and d.name.startswith("A-")])


def count_jd_analyses(career: Path) -> int:
    jd_dir = career / "jd-analysis"
    if not jd_dir.exists():
        return 0
    return len(list(jd_dir.glob("JD-*.yaml")))


def contact_exists(career: Path) -> bool:
    return (career / "contact" / "contact.yaml").exists()


def build_additional_context(career: Path) -> str:
    parts = []

    skill_path = bootstrap_skill_path()
    if skill_path.exists():
        try:
            skill_content = skill_path.read_text(encoding="utf-8")
            parts.append(
                "<careerops-routing-rules>\n"
                + skill_content.strip()
                + "\n</careerops-routing-rules>"
            )
        except Exception as e:
            parts.append(
                f"<careerops-routing-rules>\n"
                f"[ERROR: could not read SKILL.md: {e}]\n"
                f"</careerops-routing-rules>"
            )
    else:
        parts.append(
            "<careerops-routing-rules>\n"
            "CareerOps bootstrap skill not yet installed "
            f"(expected at {skill_path}). "
            "If the user shares a JD, analyze it. "
            "If they describe an achievement, capture it. "
            "If they ask for a resume, run the generation pipeline.\n"
            "</careerops-routing-rules>"
        )

    total_facts, facts_desc = count_facts(career)
    apps = count_applications(career)
    jds = count_jd_analyses(career)

    status_lines = [
        "<careerops-status>",
        f"  Facts      : {facts_desc}",
        f"  Applications: {apps}",
        f"  JDs analyzed: {jds}",
        "</careerops-status>",
    ]
    parts.append("\n".join(status_lines))

    reminders = []

    if total_facts == 0:
        reminders.append(
            "<important-reminder>\n"
            "Your CareerOps career knowledge base is empty. "
            "Run /careerops:setting-up to initialize, then "
            "/careerops:seeding-career-db to import your existing resume. "
            "Do not attempt resume generation or JD analysis until facts exist.\n"
            "</important-reminder>"
        )

    if not contact_exists(career):
        reminders.append(
            "<important-reminder>\n"
            "career/contact/contact.yaml is missing. "
            "Run /careerops:setting-up to set up your contact information. "
            "Resume generation will fail without it.\n"
            "</important-reminder>"
        )

    parts.extend(reminders)

    return "\n\n".join(parts)


def main():
    career = career_dir()
    additional_context = build_additional_context(career)
    output = {
        "systemMessage": BANNER,
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": additional_context,
        },
    }
    sys.stdout.buffer.write(json.dumps(output, ensure_ascii=False).encode("utf-8"))
    sys.stdout.buffer.write(b"\n")
    sys.stdout.buffer.flush()


if __name__ == "__main__":
    main()
