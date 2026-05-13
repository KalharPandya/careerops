#!/usr/bin/env python3
"""
CareerOps cover letter renderer.

Reads cover-letter.md from an application folder, fills
career/config/cover-letter-template.typ, compiles to cover-letter.pdf
using the typst Python package.

Usage:
  python scripts/render_cover_letter.py <app-id>
"""

import sys
import os
import re
import tempfile
from pathlib import Path
sys.path.insert(0, os.path.dirname(__file__))
from _paths import data_root

PROJECT_ROOT = data_root()
CAREER_DIR = PROJECT_ROOT / 'career'
TEMPLATE_PATH = CAREER_DIR / 'config' / 'cover-letter-template.typ'


def escape_typst(text: str) -> str:
    """Escape characters that Typst treats as markup."""
    replacements = [
        ('\\', '\\\\'),
        ('#', '\\#'),
        ('$', '\\$'),
        ('@', '\\@'),
        ('*', '\\*'),
        ('_', '\\_'),
        ('`', '\\`'),
        ('<', '\\<'),
        ('>', '\\>'),
        ('~', '\\~'),
        ('^', '\\^'),
    ]
    for old, new in replacements:
        text = text.replace(old, new)
    return text


def load_contact() -> dict:
    """Load candidate contact info from career/contact/contact.yaml."""
    try:
        import yaml
        path = CAREER_DIR / 'contact' / 'contact.yaml'
        data = yaml.safe_load(path.read_text(encoding='utf-8')) or {}
        return data
    except Exception:
        return {}


def build_contact_line(contact: dict) -> str:
    """Build a single-line contact string."""
    parts = []
    if contact.get('email'):
        parts.append(contact['email'])
    if contact.get('website'):
        url = contact['website'].replace('https://', '').replace('http://', '')
        parts.append(url)
    sn = contact.get('social_networks', {})
    if sn.get('linkedin'):
        parts.append(f"linkedin.com/in/{sn['linkedin']}")
    if sn.get('github'):
        parts.append(f"github.com/{sn['github']}")
    return ' | '.join(parts)


def parse_cover_letter(text: str) -> list[str]:
    """Split cover letter text into paragraphs, stripping blank lines."""
    paragraphs = []
    for block in re.split(r'\n{2,}', text.strip()):
        block = block.strip()
        if block:
            paragraphs.append(block)
    return paragraphs


def render(app_id: str) -> bool:
    app_dir = CAREER_DIR / 'applications' / app_id
    md_path = app_dir / 'cover-letter.md'

    if not md_path.exists():
        print(f'[render_cover_letter] cover-letter.md not found in {app_dir}')
        return False

    if not TEMPLATE_PATH.exists():
        print(f'[render_cover_letter] Template not found: {TEMPLATE_PATH}')
        return False

    # Load content
    letter_text = md_path.read_text(encoding='utf-8')
    contact = load_contact()
    name = contact.get('name')
    if not name:
        raise ValueError("contact.yaml missing required 'name' field")
    contact_line = build_contact_line(contact)

    # Parse paragraphs
    paragraphs = parse_cover_letter(letter_text)

    # Build Typst body: each paragraph is escape-processed,
    # paragraphs separated by a blank line (Typst parbreak).
    # Within a paragraph, single newlines become `\` + newline so Typst
    # renders them as explicit line breaks rather than collapsing to spaces.
    body_parts = []
    for para in paragraphs:
        lines = para.split('\n')
        escaped_lines = [escape_typst(l) for l in lines]
        # Join lines within a paragraph with Typst line-break marker
        body_parts.append(' \\\n'.join(escaped_lines))

    body_typst = '\n\n'.join(body_parts)

    # Fill template
    template = TEMPLATE_PATH.read_text(encoding='utf-8')
    filled = (
        template
        .replace('<<NAME>>', escape_typst(name))
        .replace('<<CONTACT>>', escape_typst(contact_line))
        .replace('<<BODY>>', body_typst)
    )

    # Write temp .typ file and compile
    try:
        import typst as typst_pkg
    except ImportError:
        print('[render_cover_letter] typst package not installed. Run: pip install typst')
        return False

    with tempfile.NamedTemporaryFile(
        suffix='.typ', mode='w', encoding='utf-8', delete=False, dir=app_dir
    ) as tmp:
        tmp.write(filled)
        tmp_path = Path(tmp.name)

    try:
        pdf_bytes = typst_pkg.compile(str(tmp_path))
        out_path = app_dir / 'cover-letter.pdf'
        out_path.write_bytes(pdf_bytes)
        print(f'[render_cover_letter] cover-letter.pdf written ({len(pdf_bytes):,} bytes)')
        return True
    except Exception as e:
        print(f'[render_cover_letter] Typst compile error: {e}')
        return False
    finally:
        tmp_path.unlink(missing_ok=True)


def main():
    if len(sys.argv) < 2:
        print('Usage: render_cover_letter.py <app-id>')
        sys.exit(1)
    ok = render(sys.argv[1])
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
