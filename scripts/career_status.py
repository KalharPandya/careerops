#!/usr/bin/env python3
"""
CareerOps session-start career DB health summary.
Stub — full implementation in Session 4.
"""
import sys, os
from pathlib import Path
sys.path.insert(0, os.path.dirname(__file__))
from _paths import career_dir

CAREER_DIR = career_dir()

def main():
    facts_count = len(list((CAREER_DIR / 'facts').glob('F-*.yaml'))) if (CAREER_DIR / 'facts').exists() else 0
    apps_count = len(list((CAREER_DIR / 'applications').glob('A-*'))) if (CAREER_DIR / 'applications').exists() else 0
    jds_count = len(list((CAREER_DIR / 'jd-analysis').glob('JD-*.yaml'))) if (CAREER_DIR / 'jd-analysis').exists() else 0
    print(f"[CareerOps] Facts: {facts_count} | Applications: {apps_count} | JDs ingested: {jds_count}")

if __name__ == '__main__':
    main()
