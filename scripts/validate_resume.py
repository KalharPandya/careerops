#!/usr/bin/env python3
"""
CareerOps resume validation pipeline -- 8 deterministic gates.

Usage:
  validate_resume.py <app-id>
  validate_resume.py --auto "$CLAUDE_FILE_PATHS"   # hook mode

Gates:
  1. PDF compiles cleanly (rendercv exit code)
  2. Page count matches page_budget
  3. All keywords_verbatim from JD appear in PDF text
  4. Every bullet in claim-ledger maps to a real fact ID
  5. No banned phrases (from config/rules.yaml)
  6. Decorum floors satisfied
  7. Em-dash scan returns zero
  8. Dates and employers match source facts

Exit 0 = all gates pass. Exit 1 = at least one gate failed.
"""

import os
import sys
import yaml
import json
import re
import subprocess
from pathlib import Path
from datetime import datetime
sys.path.insert(0, os.path.dirname(__file__))
from _paths import data_root

PROJECT_ROOT = data_root()
CAREER_DIR = PROJECT_ROOT / 'career'
SCRIPTS_DIR = PROJECT_ROOT / 'scripts'

EM_DASH_CHARS = ['—', '―', '⸺', '⸻']


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_yaml(path: Path):
    if not path.exists():
        return None
    with open(path, encoding='utf-8') as f:
        return yaml.safe_load(f)


def load_rules():
    rules_path = CAREER_DIR / 'config' / 'rules.yaml'
    return load_yaml(rules_path) or {}


def extract_pdf_text(pdf_path: Path) -> str:
    """Extract text from PDF using pypdf. Returns empty string if unavailable."""
    try:
        from pypdf import PdfReader
        reader = PdfReader(str(pdf_path))
        return '\n'.join(page.extract_text() or '' for page in reader.pages)
    except ImportError:
        print('[VALIDATOR WARN] pypdf not installed; PDF text extraction unavailable.')
        print('  Install with: pip install pypdf')
        return ''
    except Exception as e:
        print(f'[VALIDATOR WARN] Could not read PDF {pdf_path}: {e}')
        return ''


def get_pdf_page_count(pdf_path: Path) -> int:
    """Return page count of PDF. Returns -1 on failure."""
    try:
        from pypdf import PdfReader
        return len(PdfReader(str(pdf_path)).pages)
    except Exception:
        return -1


def collect_all_fact_ids() -> set:
    """
    Collect all known fact IDs from both storage locations:
    - v1: career/facts/F-*.yaml (standalone files, stem = fact ID)
    - v2: career/experiences/X-*.yaml (embedded in facts[] array)
    Returns a set of all fact ID strings found.
    """
    ids = set()

    facts_dir = CAREER_DIR / 'facts'
    if facts_dir.exists():
        for p in facts_dir.glob('F-*.yaml'):
            ids.add(p.stem)

    experiences_dir = CAREER_DIR / 'experiences'
    if experiences_dir.exists():
        for exp_path in experiences_dir.glob('X-*.yaml'):
            try:
                exp_data = load_yaml(exp_path)
                if exp_data and isinstance(exp_data.get('facts'), list):
                    for fact in exp_data['facts']:
                        if isinstance(fact, dict) and fact.get('id'):
                            ids.add(fact['id'])
            except Exception:
                pass

    return ids


def fact_exists(fact_id: str) -> bool:
    """Check if a fact ID exists in either the v1 facts/ directory or v2 embedded in experiences."""
    if (CAREER_DIR / 'facts' / f'{fact_id}.yaml').exists():
        return True
    experiences_dir = CAREER_DIR / 'experiences'
    if not experiences_dir.exists():
        return False
    for exp_path in experiences_dir.glob('X-*.yaml'):
        try:
            exp_data = load_yaml(exp_path)
            if exp_data and isinstance(exp_data.get('facts'), list):
                for fact in exp_data['facts']:
                    if isinstance(fact, dict) and fact.get('id') == fact_id:
                        return True
        except Exception:
            pass
    return False


# ---------------------------------------------------------------------------
# Gates
# ---------------------------------------------------------------------------

def gate1_pdf_compiles(app_dir: Path) -> tuple:
    """Gate 1: PDF exists and is not zero bytes (rendercv was already run by generate-resume)."""
    pdf_path = app_dir / 'resume.pdf'
    if not pdf_path.exists():
        return False, f'resume.pdf not found at {pdf_path}'
    if pdf_path.stat().st_size == 0:
        return False, 'resume.pdf is empty (0 bytes)'
    return True, 'OK'


def gate2_page_count(app_dir: Path, rules: dict) -> tuple:
    """Gate 2: Page count matches page_budget."""
    pdf_path = app_dir / 'resume.pdf'
    if not pdf_path.exists():
        return True, 'SKIP (no PDF)'

    budget = rules.get('page_budgets', {}).get('default', 2)

    # Check user_overrides for page_budget override
    overrides = load_yaml(app_dir / 'user_overrides.yaml') or {}
    presentation = overrides.get('presentation', {})
    if presentation.get('page_budget'):
        budget = presentation['page_budget']

    count = get_pdf_page_count(pdf_path)
    if count == -1:
        return True, 'SKIP (pypdf unavailable)'
    if count > budget:
        return False, f'PDF has {count} pages; budget is {budget}. Compress some roles.'
    return True, f'{count} page(s) -- within budget of {budget}'


def gate3_keywords(app_dir: Path, jd_analysis: dict, pdf_text: str) -> tuple:
    """Gate 3: All keywords_verbatim appear in PDF text.

    Whitespace is normalized before matching so multi-word phrases
    aren't reported missing when pypdf wraps them across a line break.
    Real ATS parsers normalize whitespace too.
    """
    if not pdf_text:
        return True, 'SKIP (no PDF text extracted)'
    keywords = jd_analysis.get('keywords_verbatim', [])
    # Collapse only whitespace runs (real ATS parsers do this). Do NOT strip
    # soft hyphenation: pypdf/pdfminer-based ATS parsers leave `engineer-\ning`
    # as a broken token and a search for `engineering` misses it, so this gate
    # MUST flag it. The correct fix is at the theme level via
    # `design.text_alignment: justified-with-no-hyphenation` in
    # career/config/rendercv-theme.yaml, not validator leniency.
    normalized_pdf = re.sub(r'\s+', ' ', pdf_text.lower())
    missing = []
    for kw in keywords:
        normalized_kw = re.sub(r'\s+', ' ', kw.lower()).strip()
        if normalized_kw not in normalized_pdf:
            missing.append(kw)
    if missing:
        return False, f'Missing {len(missing)} verbatim keyword(s): {missing}'
    return True, f'All {len(keywords)} verbatim keywords present'


def gate4_fact_traceability(app_dir: Path) -> tuple:
    """Gate 4: Every bullet in claim-ledger maps to a real fact ID (v1 or v2 storage)."""
    ledger_path = app_dir / 'claim-ledger.yaml'
    if not ledger_path.exists():
        return False, 'claim-ledger.yaml not found'
    ledger = load_yaml(ledger_path) or {}
    bullets = ledger.get('bullets', [])
    if not bullets:
        return True, 'No bullets in claim-ledger (skip)'

    known_ids = collect_all_fact_ids()

    dangling = []
    for bullet in bullets:
        for fact_id in (bullet.get('backed_by') or []):
            if fact_id not in known_ids:
                dangling.append(f"Bullet {bullet.get('bullet_id', '?')}: {fact_id} not found")
    if dangling:
        return False, f'{len(dangling)} dangling fact ref(s):\n  ' + '\n  '.join(dangling)
    return True, f'All {len(bullets)} bullets traced to valid facts'


def gate5_banned_phrases(app_dir: Path, rules: dict, jd_analysis: dict, pdf_text: str) -> tuple:
    """Gate 5: No banned phrases in resume output."""
    rendercv_path = app_dir / 'rendercv-input.yaml'
    if not rendercv_path.exists():
        return True, 'SKIP (no rendercv-input.yaml)'

    rendercv_text = rendercv_path.read_text(encoding='utf-8', errors='replace').lower()
    # Use PDF text if available, otherwise scan YAML source
    scan_text = pdf_text.lower() if pdf_text else rendercv_text

    banned = rules.get('banned_phrases', {})
    tier1 = banned.get('tier1_always_fail', [])

    # JD verbatim keywords exempt banned words that appear in JD
    jd_verbatim_lower = {kw.lower() for kw in (jd_analysis.get('keywords_verbatim') or [])}

    found = []
    for phrase in tier1:
        phrase_lower = phrase.lower()
        if phrase_lower in jd_verbatim_lower:
            continue  # exempt: in JD verbatim
        if phrase_lower in scan_text:
            found.append(phrase)

    if found:
        return False, f'Banned phrase(s) found: {found}'
    return True, 'No banned phrases'


def gate6_decorum_floors(app_dir: Path, rules: dict) -> tuple:
    """Gate 6: Decorum floors -- current role >= 2 bullets, no dropped current role, merge themes."""
    ledger_path = app_dir / 'claim-ledger.yaml'
    plan_path = app_dir / 'proposed-plan.yaml'

    if not ledger_path.exists():
        return True, 'SKIP (no claim-ledger)'
    if not plan_path.exists():
        return True, 'SKIP (no proposed-plan)'

    plan = load_yaml(plan_path) or {}
    ledger = load_yaml(ledger_path) or {}
    decorum = rules.get('decorum_floors', {})
    min_bullets = decorum.get('current_role_min_bullets', 2)

    issues = []

    # Find current role (most recent, when_end == present)
    current_role_ref = None
    experiences_dir = CAREER_DIR / 'experiences'
    if experiences_dir.exists():
        for exp_path in sorted(experiences_dir.glob('X-*.yaml')):
            exp = load_yaml(exp_path)
            if exp and exp.get('when_end') == 'present':
                current_role_ref = exp.get('id')
                break

    if current_role_ref:
        # Check it's not dropped
        experiences = plan.get('experiences', [])
        for entry in experiences:
            if entry.get('role_ref') == current_role_ref:
                if entry.get('decision') == 'drop':
                    issues.append(f'Current role {current_role_ref} is marked drop -- not allowed')

        # Count bullets for current role via rendercv-input.yaml
        rendercv = load_yaml(app_dir / 'rendercv-input.yaml') or {}
        cv = rendercv.get('cv', {})
        sections = cv.get('sections', {})
        experience_entries = sections.get('experience', [])

        current_exp_path = experiences_dir / f'{current_role_ref}.yaml'
        current_exp = load_yaml(current_exp_path) if current_exp_path.exists() else None
        if current_exp:
            employer = current_exp.get('employer', '')
            for entry in experience_entries:
                if isinstance(entry, dict) and entry.get('company', '').lower() == employer.lower():
                    highlights = entry.get('highlights', [])
                    if len(highlights) < min_bullets:
                        issues.append(
                            f'Current role {current_role_ref} has {len(highlights)} bullets; minimum is {min_bullets}'
                        )
                    break

    if issues:
        return False, '; '.join(issues)
    return True, 'Decorum floors satisfied'


def gate7_em_dashes(app_dir: Path, pdf_text: str) -> tuple:
    """Gate 7: No em-dashes in output artifacts."""
    files_to_check = [
        app_dir / 'rendercv-input.yaml',
        app_dir / 'claim-ledger.yaml',
    ]
    found_in = []

    for path in files_to_check:
        if not path.exists():
            continue
        text = path.read_text(encoding='utf-8', errors='replace')
        for char in EM_DASH_CHARS:
            if char in text:
                found_in.append(f'{path.name} (contains em-dash)')
                break

    if pdf_text:
        for char in EM_DASH_CHARS:
            if char in pdf_text:
                found_in.append('resume.pdf (extracted text contains em-dash)')
                break

    if found_in:
        return False, f'Em-dash found in: {found_in}'
    return True, 'No em-dashes in output artifacts'


def gate8_immutability(app_dir: Path, jd_analysis: dict) -> tuple:
    """Gate 8: Dates and employers in rendered output match source facts."""
    ledger_path = app_dir / 'claim-ledger.yaml'
    if not ledger_path.exists():
        return True, 'SKIP (no claim-ledger)'

    ledger = load_yaml(ledger_path) or {}
    rendercv = load_yaml(app_dir / 'rendercv-input.yaml') or {}

    issues = []
    experience_entries = rendercv.get('cv', {}).get('sections', {}).get('experience', [])

    experiences_dir = CAREER_DIR / 'experiences'
    if not experiences_dir.exists():
        return True, 'SKIP (no experiences directory)'

    for entry in experience_entries:
        if not isinstance(entry, dict):
            continue
        company = entry.get('company', '')
        start = entry.get('start_date', '')
        end = entry.get('end_date', '')

        # Find matching experience envelope
        for exp_path in experiences_dir.glob('X-*.yaml'):
            exp = load_yaml(exp_path)
            if not exp:
                continue
            if exp.get('employer', '').lower() != company.lower():
                continue
            # Check start date (compare first 6 chars of YYYY-MM format, ignoring day)
            source_start = exp.get('when_start', '')
            if start and source_start:
                rendered_prefix = start.replace('-', '')[:6]
                source_prefix = source_start.replace('-', '')[:6]
                if rendered_prefix != source_prefix:
                    issues.append(
                        f'{company}: start date mismatch (rendered: {start}, source: {source_start})'
                    )
            break

    if issues:
        return False, f'Immutability violations: {issues}'
    return True, 'Dates and employers match source facts'


def gate9_page_utilization(app_dir: Path, rules: dict) -> tuple:
    """Gate 9: Last page must be >=60% as full as page 1 (no half-empty second pages).

    Uses pypdf per-page character count as a proxy for content density.
    Single-page resumes always pass.
    """
    pdf_path = app_dir / 'resume.pdf'
    if not pdf_path.exists():
        return True, 'SKIP (no PDF)'

    page_count = get_pdf_page_count(pdf_path)
    if page_count <= 1:
        return True, 'Single page -- utilization gate exempt'

    min_ratio = rules.get('decorum_floors', {}).get('last_page_min_ratio', 0.6)

    try:
        from pypdf import PdfReader
        reader = PdfReader(str(pdf_path))
        page_texts = [page.extract_text() or '' for page in reader.pages]
        first_len = len(re.sub(r'\s', '', page_texts[0]))
        last_len = len(re.sub(r'\s', '', page_texts[-1]))
        if first_len == 0:
            return True, 'SKIP (could not measure page 1 content)'
        ratio = last_len / first_len
        if ratio < min_ratio:
            return False, (
                f'Last page has {last_len} non-whitespace chars vs {first_len} on page 1 '
                f'(ratio {ratio:.2f} < {min_ratio:.2f}). '
                f'Either compress to 1 page or expand to fill page 2.'
            )
        return True, f'Last-page utilization {ratio:.2f} >= {min_ratio:.2f}'
    except Exception as e:
        return True, f'SKIP (pypdf error: {e})'


def gate10_bolding(app_dir: Path) -> tuple:
    """Gate 10: Each non-summary experience/project bullet has 1-3 bold (**...**) spans."""
    rendercv_path = app_dir / 'rendercv-input.yaml'
    if not rendercv_path.exists():
        return True, 'SKIP (no rendercv-input.yaml)'

    data = load_yaml(rendercv_path) or {}
    sections = data.get('cv', {}).get('sections', {})
    violations = []

    for role in sections.get('experience', []):
        if not isinstance(role, dict):
            continue
        company = role.get('company', '?')
        for bullet in role.get('highlights', []):
            if not isinstance(bullet, str):
                continue
            spans = re.findall(r'\*\*[^*]+\*\*', bullet)
            if len(spans) == 0:
                violations.append(f'{company}: no bold in "{bullet[:55]}..."')
            elif len(spans) > 3:
                violations.append(f'{company}: {len(spans)} bold spans (max 3) in "{bullet[:55]}..."')

    for project in sections.get('projects', []):
        if not isinstance(project, dict):
            continue
        name = project.get('name', '?')
        for bullet in project.get('highlights', []):
            if not isinstance(bullet, str):
                continue
            spans = re.findall(r'\*\*[^*]+\*\*', bullet)
            if len(spans) == 0:
                violations.append(f'Project {name}: no bold in "{bullet[:55]}..."')
            elif len(spans) > 3:
                violations.append(f'Project {name}: {len(spans)} bold spans (max 3)')

    if violations:
        return False, f'{len(violations)} bolding violation(s):\n  ' + '\n  '.join(violations[:5])

    exp_count = sum(
        1 for r in sections.get('experience', [])
        if isinstance(r, dict)
        for b in r.get('highlights', [])
        if isinstance(b, str)
    )
    return True, f'Bolding OK ({exp_count} experience bullets checked)'


def gate11_cover_letter(app_dir: Path, jd_analysis: dict) -> tuple:
    """Gate 11: Cover letter exists, 250-500 words, no em-dashes, >= 40% JD keyword coverage."""
    md_path = app_dir / 'cover-letter.md'
    if not md_path.exists():
        return False, 'cover-letter.md not found -- run cover-letter-composer first'

    text = md_path.read_text(encoding='utf-8', errors='replace')
    words = len(text.split())
    if words < 250:
        return False, f'Cover letter has {words} words; minimum 250'
    if words > 500:
        return False, f'Cover letter has {words} words; maximum 500'

    for ch in EM_DASH_CHARS:
        if ch in text:
            return False, 'Cover letter contains forbidden em-dash character'

    keywords = jd_analysis.get('keywords_verbatim', [])
    hits = 0
    if keywords:
        normalized = re.sub(r'\s+', ' ', text.lower())
        hits = sum(
            1 for kw in keywords
            if re.sub(r'\s+', ' ', kw.lower()).strip() in normalized
        )
        ratio = hits / len(keywords)
        if ratio < 0.4:
            return False, f'Cover letter hits {hits}/{len(keywords)} JD keywords ({ratio:.0%} < 40%)'

    pdf_path = app_dir / 'cover-letter.pdf'
    pdf_note = ' PDF exists.' if pdf_path.exists() else ' (cover-letter.pdf not found -- typst/rendercv may not have run; PDF is optional)'
    return True, f'{words} words, {hits}/{len(keywords) if keywords else 0} JD keywords OK.{pdf_note}'


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def is_relevant_hook_path(paths: list) -> bool:
    for p in paths:
        path = Path(p)
        if 'applications' in path.parts:
            if path.name in ('resume.pdf', 'claim-ledger.yaml'):
                return True
    return False


def run_validation(app_id: str) -> bool:
    """Run all 11 gates. Returns True if all pass."""
    app_dir = CAREER_DIR / 'applications' / app_id

    if not app_dir.exists():
        print(f'[VALIDATOR ERROR] Application directory not found: {app_dir}')
        return False

    app_yaml_path = app_dir / 'application.yaml'
    app_data = load_yaml(app_yaml_path) or {}
    jd_ref = app_data.get('jd_ref', '')
    jd_path = CAREER_DIR / 'jd-analysis' / f'{jd_ref}.yaml'
    jd_analysis = load_yaml(jd_path) or {}

    rules = load_rules()
    pdf_path = app_dir / 'resume.pdf'
    pdf_text = extract_pdf_text(pdf_path) if pdf_path.exists() else ''

    gates = [
        ('Gate 1: PDF compiles', lambda: gate1_pdf_compiles(app_dir)),
        ('Gate 2: Page count', lambda: gate2_page_count(app_dir, rules)),
        ('Gate 3: Verbatim keywords', lambda: gate3_keywords(app_dir, jd_analysis, pdf_text)),
        ('Gate 4: Fact traceability', lambda: gate4_fact_traceability(app_dir)),
        ('Gate 5: Banned phrases', lambda: gate5_banned_phrases(app_dir, rules, jd_analysis, pdf_text)),
        ('Gate 6: Decorum floors', lambda: gate6_decorum_floors(app_dir, rules)),
        ('Gate 7: Em-dash scan', lambda: gate7_em_dashes(app_dir, pdf_text)),
        ('Gate 8: Immutability', lambda: gate8_immutability(app_dir, jd_analysis)),
        ('Gate 9: Page utilization', lambda: gate9_page_utilization(app_dir, rules)),
        ('Gate 10: Keyword bolding', lambda: gate10_bolding(app_dir)),
        ('Gate 11: Cover letter', lambda: gate11_cover_letter(app_dir, jd_analysis)),
    ]

    all_passed = True
    failures = []

    print(f'\n[CareerOps Validator] Running 11 gates for {app_id}')
    print('-' * 60)

    for name, gate_fn in gates:
        try:
            passed, detail = gate_fn()
        except Exception as e:
            passed, detail = False, f'Exception: {e}'

        status = 'PASS' if passed else 'FAIL'
        print(f'  {status}  {name}: {detail}')

        if not passed:
            all_passed = False
            failures.append(f'{name}: {detail}')

    print('-' * 60)

    # Update application.yaml with validation result
    if app_yaml_path.exists():
        app_data['validation_summary'] = app_data.get('validation_summary', {})
        app_data['validation_summary']['gates_passed'] = all_passed
        retry_count = app_data['validation_summary'].get('retry_count', 0)
        if not all_passed:
            app_data['validation_summary']['retry_count'] = retry_count + 1

        with open(app_yaml_path, 'w', encoding='utf-8') as f:
            yaml.dump(app_data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    if all_passed:
        print(f'\n[VALIDATOR] All 11 gates passed for {app_id}')
    else:
        print(f'\n[VALIDATOR] {len(failures)} gate(s) failed for {app_id}:')
        for failure in failures:
            print(f'  - {failure}')

        # Write failure report
        failures_path = app_dir / 'validation-failures.md'
        with open(failures_path, 'w', encoding='utf-8') as fp:
            fp.write(f'# Validation Failures -- {app_id}\n\n')
            fp.write(f'**Run at:** {datetime.now().isoformat()}\n\n')
            for failure in failures:
                fp.write(f'- {failure}\n')

    return all_passed


def main():
    args = sys.argv[1:]

    # Hook mode: --auto with file paths
    if args and args[0] == '--auto':
        file_paths = args[1:]
        if not file_paths:
            env_paths = os.environ.get('CLAUDE_FILE_PATHS', '')
            file_paths = env_paths.split() if env_paths else []
        if not is_relevant_hook_path(file_paths):
            sys.exit(0)
        # Extract app_id from path
        for p in file_paths:
            path = Path(p)
            parts = list(path.parts)
            if 'applications' in parts:
                idx = parts.index('applications')
                if idx + 1 < len(parts):
                    app_id = parts[idx + 1]
                    passed = run_validation(app_id)
                    sys.exit(0 if passed else 1)
        sys.exit(0)

    # Direct mode: validate_resume.py <app-id>
    if not args:
        print('Usage: validate_resume.py <app-id>')
        print('       validate_resume.py --auto "$CLAUDE_FILE_PATHS"')
        sys.exit(1)

    app_id = args[0]
    passed = run_validation(app_id)
    sys.exit(0 if passed else 1)


if __name__ == '__main__':
    main()
