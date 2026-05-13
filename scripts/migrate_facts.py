#!/usr/bin/env python3
"""
CareerOps v2 migration utility.

Moves standalone F-*.yaml fact files from career/facts/ into their parent
X-*.yaml experience files under the facts[] array.

Usage:
  python scripts/migrate_facts.py              # dry run (no writes)
  python scripts/migrate_facts.py --apply      # execute migration
  python scripts/migrate_facts.py --apply --verbose  # show each fact moved

This script is NOT run automatically. Run it once after upgrading to v2.
It is idempotent: re-running after a partial migration skips already-moved facts.

After a successful --apply run, career/facts/ will be empty and removed.
Evidence files (E-*.yaml) are NOT modified -- they reference fact IDs by string,
which are unchanged.
"""

import argparse
import os
import sys
import yaml
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from _paths import career_dir


def load_yaml(path: Path):
    with open(path, encoding='utf-8') as f:
        return yaml.safe_load(f)


def dump_yaml(data: dict, path: Path):
    with open(path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)


def strip_inherited_fields(fact: dict) -> dict:
    stripped = dict(fact)
    for field in ('role_ref', 'employer', 'role_title'):
        stripped.pop(field, None)
    return stripped


def find_experience_for_fact(fact: dict, experiences_dir: Path) -> tuple:
    role_ref = fact.get('role_ref')
    if not role_ref:
        return None, None
    exp_path = experiences_dir / f'{role_ref}.yaml'
    if not exp_path.exists():
        return None, None
    try:
        exp_data = load_yaml(exp_path)
    except Exception as e:
        print(f'  [ERROR] Could not load {exp_path}: {e}')
        return None, None
    return exp_path, exp_data


def fact_already_embedded(fact_id: str, exp_data: dict) -> bool:
    existing_facts = exp_data.get('facts') or []
    return any(
        isinstance(f, dict) and f.get('id') == fact_id
        for f in existing_facts
    )


def migrate(career: Path, apply: bool, verbose: bool) -> int:
    facts_dir = career / 'facts'
    experiences_dir = career / 'experiences'

    if not facts_dir.exists():
        print('[migrate_facts] career/facts/ does not exist -- nothing to migrate.')
        return 0

    if not experiences_dir.exists():
        print('[migrate_facts] career/experiences/ does not exist -- cannot migrate.')
        return 0

    fact_files = sorted(facts_dir.glob('F-*.yaml'))
    if not fact_files:
        print('[migrate_facts] career/facts/ is empty -- nothing to migrate.')
        return 0

    print(f'[migrate_facts] Found {len(fact_files)} fact file(s) in career/facts/')
    if not apply:
        print('[migrate_facts] DRY RUN -- pass --apply to execute changes.')
    print()

    migrated = 0
    skipped_already_present = 0
    skipped_no_role_ref = 0
    skipped_no_experience = 0
    errors = 0

    pending_writes: dict = {}

    for fact_path in fact_files:
        try:
            fact = load_yaml(fact_path)
        except Exception as e:
            print(f'  [ERROR] Could not load {fact_path.name}: {e}')
            errors += 1
            continue

        if not fact or not isinstance(fact, dict):
            print(f'  [SKIP] {fact_path.name}: empty or not a mapping')
            skipped_no_role_ref += 1
            continue

        fact_id = fact.get('id', fact_path.stem)
        role_ref = fact.get('role_ref')

        if not role_ref:
            print(f'  [SKIP] {fact_id}: no role_ref -- cannot determine parent experience')
            skipped_no_role_ref += 1
            continue

        exp_path, exp_data = find_experience_for_fact(fact, experiences_dir)

        if exp_path is None:
            print(f'  [SKIP] {fact_id}: role_ref {role_ref} not found in experiences/')
            skipped_no_experience += 1
            continue

        working_data = pending_writes.get(exp_path, exp_data)

        if fact_already_embedded(fact_id, working_data):
            if verbose:
                print(f'  [SKIP] {fact_id}: already embedded in {exp_path.name}')
            skipped_already_present += 1
            continue

        if 'facts' not in working_data or working_data['facts'] is None:
            working_data['facts'] = []

        stripped = strip_inherited_fields(fact)
        working_data['facts'].append(stripped)
        pending_writes[exp_path] = working_data

        action = 'MIGRATE' if apply else 'WOULD MIGRATE'
        print(f'  [{action}] {fact_id} -> {exp_path.name}')
        if verbose:
            print(f'           title: {fact.get("title", "?")}')
        migrated += 1

    print()

    if apply and pending_writes:
        for exp_path, updated_data in pending_writes.items():
            try:
                dump_yaml(updated_data, exp_path)
                print(f'  [WRITTEN] {exp_path.name}')
            except Exception as e:
                print(f'  [ERROR] Could not write {exp_path.name}: {e}')
                errors += 1

        for fact_path in fact_files:
            try:
                fact = load_yaml(fact_path)
                if not fact:
                    continue
                fact_id = fact.get('id', fact_path.stem)
                role_ref = fact.get('role_ref')
                if not role_ref:
                    continue
                exp_path = experiences_dir / f'{role_ref}.yaml'
                if not exp_path.exists():
                    continue
                written_data = load_yaml(exp_path)
                if fact_already_embedded(fact_id, written_data or {}):
                    fact_path.unlink()
                    if verbose:
                        print(f'  [DELETED] {fact_path.name}')
            except Exception as e:
                print(f'  [ERROR] Could not delete {fact_path.name}: {e}')
                errors += 1

        remaining = list(facts_dir.glob('F-*.yaml'))
        if not remaining:
            try:
                for leftover in facts_dir.iterdir():
                    leftover.unlink()
                facts_dir.rmdir()
                print('\n  [DONE] career/facts/ directory removed (all facts migrated).')
            except Exception as e:
                print(f'\n  [WARN] Could not remove career/facts/ directory: {e}')
        else:
            print(
                f'\n  [WARN] {len(remaining)} fact file(s) remain in career/facts/ '
                f'(could not be migrated). Review manually.'
            )

    print()
    print('[migrate_facts] Summary:')
    print(f'  Migrated              : {migrated}')
    print(f'  Already embedded      : {skipped_already_present}')
    print(f'  No role_ref (skipped) : {skipped_no_role_ref}')
    print(f'  No experience found   : {skipped_no_experience}')
    print(f'  Errors                : {errors}')

    if not apply and migrated > 0:
        print()
        print(f'[migrate_facts] Re-run with --apply to execute {migrated} migration(s).')

    return migrated


def main():
    parser = argparse.ArgumentParser(
        description='CareerOps v2 migration: move F-*.yaml facts into parent X-*.yaml experience files.'
    )
    parser.add_argument('--apply', action='store_true', help='Execute the migration (default is dry run)')
    parser.add_argument('--verbose', action='store_true', help='Print additional detail for each fact')
    args = parser.parse_args()

    career = career_dir()
    migrate(career, apply=args.apply, verbose=args.verbose)


if __name__ == '__main__':
    main()
