#!/usr/bin/env python3
"""
CareerOps em-dash scanner.
Invoked by Claude Code PostToolUse hook on Write|Edit tool calls.
Exit 1 (blocking) for strict-mode violations; exit 0 for warn/skip.
"""

import os
import sys
import re
from pathlib import Path
sys.path.insert(0, os.path.dirname(__file__))
from _paths import data_root

EM_DASH_CHARS = {
    '—': 'U+2014 EM DASH',
    '―': 'U+2015 HORIZONTAL BAR',
    '⸺': 'U+2E3A TWO-EM DASH',
    '⸻': 'U+2E3B THREE-EM DASH',
}

def get_mode(path: Path) -> str:
    """Return 'strict', 'warn', or 'skip' for a given path."""
    try:
        rel = path.relative_to(data_root())
        parts = rel.parts
    except ValueError:
        # Try relative from cwd
        try:
            rel = path.relative_to(Path.cwd())
            parts = rel.parts
        except ValueError:
            return 'skip'

    if not parts:
        return 'skip'

    if parts[0] != 'career':
        return 'skip'

    if len(parts) < 2:
        return 'skip'

    subdir = parts[1]

    if subdir == 'applications':
        return 'strict'
    if subdir in ('jd-analysis',):
        return 'skip'
    if subdir in ('facts', 'projects', 'experiences', 'skills', 'education', 'contact', 'config'):
        return 'warn'

    return 'skip'


def scan_text(text: str, path: Path, mode: str) -> list:
    """Return list of violation messages (empty = clean)."""
    violations = []
    lines = text.splitlines()
    for lineno, line in enumerate(lines, 1):
        for char, name in EM_DASH_CHARS.items():
            if char in line:
                violations.append(f"{path}:{lineno}: found {name}")
    return violations


def scan_pdf(path: Path, mode: str) -> list:
    """Extract text from PDF and scan. Returns violations or empty list."""
    try:
        from pypdf import PdfReader
    except ImportError:
        print(f"[CAREEROPS WARNING] pypdf not installed; PDF em-dash check skipped for {path}")
        return []

    try:
        reader = PdfReader(str(path))
        full_text = '\n'.join(
            page.extract_text() or '' for page in reader.pages
        )
        return scan_text(full_text, path, mode)
    except Exception as e:
        print(f"[CAREEROPS WARNING] Could not read PDF {path}: {e}")
        return []


def scan_file(path: Path, mode: str) -> list:
    """Scan a single file. Returns violation messages."""
    if not path.exists() or path.is_dir():
        return []

    suffix = path.suffix.lower()

    if suffix == '.pdf':
        return scan_pdf(path, mode)

    try:
        text = path.read_text(encoding='utf-8', errors='replace')
        return scan_text(text, path, mode)
    except Exception as e:
        print(f"[CAREEROPS WARNING] Could not read {path}: {e}")
        return []


def main():
    # Collect paths from env var or CLI args
    env_paths = os.environ.get('CLAUDE_FILE_PATHS', '')
    if env_paths:
        raw_paths = env_paths.split()
    else:
        raw_paths = sys.argv[1:]

    if not raw_paths:
        sys.exit(0)

    blocked = False

    for raw in raw_paths:
        path = Path(raw).resolve()
        mode = get_mode(path)

        if mode == 'skip':
            continue

        violations = scan_file(path, mode)

        for msg in violations:
            if mode == 'strict':
                print(f"[CAREEROPS EM-DASH BLOCKED] {msg}")
                blocked = True
            else:
                print(f"[CAREEROPS EM-DASH WARN] {msg} (not blocked)")

    sys.exit(1 if blocked else 0)


if __name__ == '__main__':
    main()
