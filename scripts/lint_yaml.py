#!/usr/bin/env python3
"""
CareerOps YAML linter.
Invoked by Claude Code PostToolUse hook on Write|Edit tool calls to career/**/*.yaml.
Performs: schema validation, referential integrity check, em-dash check.
Exit 1 on any blocking violation; exit 0 otherwise.
"""

import os
import sys
import yaml
from pathlib import Path
sys.path.insert(0, os.path.dirname(__file__))
from _paths import data_root

PROJECT_ROOT = data_root()
SCHEMAS_DIR = PROJECT_ROOT / 'schemas'
CAREER_DIR = PROJECT_ROOT / 'career'

EM_DASH_CHARS = {
    '—': 'U+2014 EM DASH',
    '―': 'U+2015 HORIZONTAL BAR',
    '⸺': 'U+2E3A TWO-EM DASH',
    '⸻': 'U+2E3B THREE-EM DASH',
}

SCHEMA_MAP = {
    'facts': 'fact.schema.json',
    'evidence': 'evidence.schema.json',
    'experiences': 'experience.schema.json',
    'projects': 'project.schema.json',
    'jd-analysis': 'jd-analysis.schema.json',
}

APPLICATION_SCHEMA_MAP = {
    'application.yaml': 'application.schema.json',
    'user_overrides.yaml': 'user-overrides.schema.json',
    'claim-ledger.yaml': 'claim-ledger.schema.json',
}

EM_DASH_MODE = {
    'applications': 'strict',
    'facts': 'warn',
    'evidence': 'warn',
    'experiences': 'warn',
    'projects': 'warn',
    'skills': 'warn',
    'education': 'warn',
    'contact': 'warn',
    'config': 'warn',
    'jd-analysis': 'skip',
}


def try_import_jsonschema():
    try:
        import jsonschema
        return jsonschema
    except ImportError:
        print('[CAREEROPS LINT WARNING] jsonschema not installed; schema validation skipped.')
        print('  Install with: pip install jsonschema')
        return None


def load_schema(schema_file: str):
    import json
    path = SCHEMAS_DIR / schema_file
    if not path.exists():
        return None
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def get_career_subdir(path: Path):
    """Return the career subdirectory name for a path, or None if not in career/."""
    try:
        rel = path.relative_to(PROJECT_ROOT)
    except ValueError:
        try:
            rel = path.relative_to(Path.cwd())
        except ValueError:
            return None, None
    parts = rel.parts
    if not parts or parts[0] != 'career':
        return None, None
    if len(parts) < 2:
        return None, None
    return parts[1], rel


def id_exists(id_val: str, subdir: str) -> bool:
    """Check if a YAML file with the given ID stem exists in the given career subdir."""
    candidate = CAREER_DIR / subdir / f"{id_val}.yaml"
    return candidate.exists()


def collect_all_embedded_fact_ids() -> set:
    """Collect all fact IDs embedded in career/experiences/X-*.yaml files (v2 structure)."""
    ids = set()
    experiences_dir = CAREER_DIR / 'experiences'
    if not experiences_dir.exists():
        return ids
    for exp_path in experiences_dir.glob('X-*.yaml'):
        try:
            with open(exp_path, encoding='utf-8') as f:
                data = yaml.safe_load(f)
            if data and isinstance(data.get('facts'), list):
                for fact in data['facts']:
                    if isinstance(fact, dict) and fact.get('id'):
                        ids.add(fact['id'])
        except Exception:
            pass
    return ids


def check_refs(data: dict, subdir: str, path: Path) -> list:
    errors = []

    if subdir == 'facts':
        role_ref = data.get('role_ref')
        if role_ref and not id_exists(role_ref, 'experiences'):
            errors.append(f"role_ref {role_ref} not found in career/experiences/")
        for ev_id in (data.get('evidence') or []):
            if not id_exists(ev_id, 'evidence'):
                errors.append(f"evidence ref {ev_id} not found in career/evidence/")

    elif subdir == 'evidence':
        for fact_id in (data.get('backs_facts') or []):
            if not id_exists(fact_id, 'facts'):
                embedded_ids = collect_all_embedded_fact_ids()
                if fact_id not in embedded_ids:
                    errors.append(
                        f"backs_facts ref {fact_id} not found in career/facts/ "
                        f"or embedded in any career/experiences/X-*.yaml"
                    )

    elif subdir in ('experiences', 'projects'):
        for fact_id in (data.get('fact_refs') or []):
            if not id_exists(fact_id, 'facts'):
                errors.append(f"fact_refs ref {fact_id} not found in career/facts/")

        embedded_facts = data.get('facts') or []
        seen_ids = set()
        for i, fact in enumerate(embedded_facts):
            if not isinstance(fact, dict):
                errors.append(f"facts[{i}] is not a mapping")
                continue
            fact_id = fact.get('id', '')
            if not fact_id.startswith('F-'):
                errors.append(f"facts[{i}].id '{fact_id}' does not start with 'F-'")
            if fact_id in seen_ids:
                errors.append(f"facts[{i}].id '{fact_id}' is duplicated within this file")
            seen_ids.add(fact_id)
            for ev_id in (fact.get('evidence') or []):
                if not id_exists(ev_id, 'evidence'):
                    errors.append(
                        f"facts[{i}] ({fact_id}): evidence ref {ev_id} not found in career/evidence/"
                    )

    elif subdir == 'applications':
        fname = path.name
        if fname == 'claim-ledger.yaml':
            jd_ref = data.get('jd_ref')
            if jd_ref and not id_exists(jd_ref, 'jd-analysis'):
                errors.append(f"jd_ref {jd_ref} not found in career/jd-analysis/")
            embedded_ids = collect_all_embedded_fact_ids()
            for bullet in (data.get('bullets') or []):
                for fact_id in (bullet.get('backed_by') or []):
                    if not id_exists(fact_id, 'facts') and fact_id not in embedded_ids:
                        errors.append(
                            f"bullet {bullet.get('bullet_id','?')}: backed_by {fact_id} "
                            f"not found in career/facts/ or embedded in any X-*.yaml"
                        )
        elif fname == 'application.yaml':
            jd_ref = data.get('jd_ref')
            if jd_ref and not id_exists(jd_ref, 'jd-analysis'):
                errors.append(f"jd_ref {jd_ref} not found in career/jd-analysis/")

    return errors


def check_em_dashes_inline(text: str, mode: str, path: Path) -> tuple:
    """Returns (violations: list[str], blocked: bool)."""
    if mode == 'skip':
        return [], False
    violations = []
    blocked = False
    for lineno, line in enumerate(text.splitlines(), 1):
        for char, name in EM_DASH_CHARS.items():
            if char in line:
                if mode == 'strict':
                    violations.append(
                        f"[CAREEROPS LINT EM-DASH BLOCKED] {path}:{lineno}: found {name}"
                    )
                    blocked = True
                else:
                    violations.append(
                        f"[CAREEROPS LINT EM-DASH WARN] {path}:{lineno}: found {name} (not blocked)"
                    )
    return violations, blocked


def lint_file(path: Path, jsonschema_mod) -> bool:
    """Lint a single file. Returns True if any blocking error found."""
    subdir, rel = get_career_subdir(path)
    if subdir is None:
        return False

    if not path.exists() or path.is_dir():
        return False

    if path.suffix.lower() != '.yaml':
        return False

    blocked = False

    # Load YAML
    try:
        raw_text = path.read_text(encoding='utf-8', errors='replace')
        data = yaml.safe_load(raw_text)
    except yaml.YAMLError as e:
        print(f"[CAREEROPS LINT SCHEMA ERROR] {path}: YAML parse error: {e}")
        return True

    if data is None:
        return False

    # Determine schema
    schema_file = None
    if subdir in SCHEMA_MAP:
        schema_file = SCHEMA_MAP[subdir]
    elif subdir == 'applications':
        schema_file = APPLICATION_SCHEMA_MAP.get(path.name)

    # Schema validation
    if schema_file and jsonschema_mod:
        schema = load_schema(schema_file)
        if schema:
            try:
                validator_cls = jsonschema_mod.Draft202012Validator
                validator = validator_cls(schema)
                errors_list = list(validator.iter_errors(data))
                for err in errors_list:
                    field = '.'.join(str(p) for p in err.absolute_path) or '(root)'
                    print(f"[CAREEROPS LINT SCHEMA ERROR] {path}: {field}: {err.message}")
                    blocked = True
            except Exception as e:
                print(f"[CAREEROPS LINT WARNING] Schema validation failed for {path}: {e}")

    # Referential integrity
    ref_errors = check_refs(data, subdir, path)
    for err in ref_errors:
        print(f"[CAREEROPS LINT REF ERROR] {path}: {err}")
        blocked = True

    # Em-dash check
    mode = EM_DASH_MODE.get(subdir, 'skip')
    em_violations, em_blocked = check_em_dashes_inline(raw_text, mode, path)
    for msg in em_violations:
        print(msg)
    if em_blocked:
        blocked = True

    if not blocked and not em_violations:
        print(f"[CAREEROPS LINT OK] {path}")

    return blocked


def main():
    env_paths = os.environ.get('CLAUDE_FILE_PATHS', '')
    raw_paths = env_paths.split() if env_paths else sys.argv[1:]

    if not raw_paths:
        sys.exit(0)

    jsonschema_mod = try_import_jsonschema()
    any_blocked = False

    for raw in raw_paths:
        path = Path(raw).resolve()
        if lint_file(path, jsonschema_mod):
            any_blocked = True

    sys.exit(1 if any_blocked else 0)


if __name__ == '__main__':
    main()
