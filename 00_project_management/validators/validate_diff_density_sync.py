#!/usr/bin/env python3
"""Validate difference density publication data package."""
from pathlib import Path
import sys
import csv

BASE = Path('04_VASP_analysis/diff_density_publication_data')
errors = []

required = [
    BASE/'README.md',
    BASE/'PROVENANCE.md',
    BASE/'source_manifest.tsv',
    BASE/'mapping/state_mapping.tsv',
    BASE/'mapping/slice_definition.tsv'
]

for f in required:
    if not f.exists():
        errors.append(f'Missing {f}')

maps = {
    'charge_density': 'charge_diff',
    'magnetization': 'magnetization_diff',
    'spin_up': 'spin_up_diff',
    'spin_down': 'spin_down_diff'
}

for folder, key in maps.items():
    d = BASE/folder/'source_data'
    if not d.exists():
        errors.append(f'Missing folder {d}')
        continue
    files = list(d.glob('*.tsv'))
    if len(files) == 0:
        errors.append(f'No TSV data in {d}')

if errors:
    print('FAIL: difference-density validation failed')
    for e in errors:
        print(e)
    sys.exit(1)

print('PASS: difference-density synchronization validated; 0 hard errors')
