from __future__ import print_function

import os
import subprocess


BASE = os.path.join('sfs', 'CoOH', 'cp2k', 'Al16')
VA = os.path.join(BASE, 'valence_analysis')
MANIFEST = os.path.join(VA, 'spin_scan_manifest.tsv')


def read_tsv(path):
    if not os.path.exists(path):
        return [], []
    lines = [line.rstrip('\n') for line in open(path) if line.strip()]
    if not lines:
        return [], []
    header = lines[0].split('\t')
    rows = []
    for line in lines[1:]:
        vals = line.split('\t')
        row = {}
        for i, key in enumerate(header):
            row[key] = vals[i] if i < len(vals) else ''
        rows.append(row)
    return header, rows


def write_tsv(path, header, rows):
    tmp = path + '.tmp'
    with open(tmp, 'w') as fh:
        fh.write('\t'.join(header) + '\n')
        for row in rows:
            fh.write('\t'.join(row.get(key, '') for key in header) + '\n')
    os.rename(tmp, path)


def key(row):
    return (row.get('spin_project', ''), row.get('relative_directory', ''))


def main():
    old_header, old_rows = read_tsv(MANIFEST)
    preserved = {}
    for row in old_rows:
        status = row.get('status', '')
        if status != 'candidate_not_submitted':
            preserved[key(row)] = status

    subprocess.check_call('cd sfs/CoOH/cp2k/Al16 && python prepare_valence_analysis_py2.py', shell=True)

    header, rows = read_tsv(MANIFEST)
    restored = 0
    for row in rows:
        k = key(row)
        if k in preserved and row.get('status') != preserved[k]:
            row['status'] = preserved[k]
            restored += 1
    write_tsv(MANIFEST, header, rows)

    candidates = sum(1 for row in rows if row.get('status') == 'candidate_not_submitted')
    submitted = sum(1 for row in rows if row.get('status', '').startswith('submitted_'))
    completed = sum(1 for row in rows if row.get('status', '').startswith('completed_'))
    failed = sum(1 for row in rows if row.get('status', '').startswith('failed_'))
    print('restored_statuses', restored)
    print('candidate_not_submitted', candidates)
    print('submitted', submitted)
    print('completed', completed)
    print('failed', failed)


if __name__ == '__main__':
    main()
