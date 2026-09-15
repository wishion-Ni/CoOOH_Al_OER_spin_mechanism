#!/usr/bin/env python3
"""
Publication figure data audit helper.

Purpose:
- inspect whether manuscript-ready theory figure components have the required
  data tables, structures, scripts and metadata;
- generate a checklist for Codex/analysts before figure rendering.

This script does not modify calculation results.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGETS = {
    "V01_COHP": ROOT / "04_VASP_analysis",
    "V02_diff_density": ROOT / "04_VASP_analysis" / "diff_density_publication_data",
    "V03_spin_density": ROOT / "04_VASP_analysis",
    "V04_PDOS": ROOT / "04_VASP_analysis",
}

REQUIRED_PATTERNS = {
    "V01_COHP": ["cohp", "icohp"],
    "V02_diff_density": ["csv", "tsv", "svg", "pdf"],
    "V03_spin_density": ["spin"],
    "V04_PDOS": ["pdos"],
}


def scan():
    print("Publication figure data audit")
    print("=" * 50)
    for name, path in TARGETS.items():
        print(f"\n[{name}] {path}")
        if not path.exists():
            print("MISSING")
            continue
        files = [p.name.lower() for p in path.rglob('*') if p.is_file()]
        for key in REQUIRED_PATTERNS[name]:
            found = any(key in f for f in files)
            print(f"  {key}: {'PASS' if found else 'CHECK'}")


if __name__ == '__main__':
    scan()
