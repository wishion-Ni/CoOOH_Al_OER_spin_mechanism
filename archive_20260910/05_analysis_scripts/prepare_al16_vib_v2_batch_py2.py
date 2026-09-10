from __future__ import print_function

import os
import shutil


BASE = os.path.join('sfs', 'CoOH', 'cp2k', 'Al16')
OLD_BASE = os.path.join(BASE, 'vib_corrections')
NEW_BASE = os.path.join(BASE, 'vib_corrections_v2')


def read_tsv(path):
    lines = [line.rstrip('\n') for line in open(path) if line.strip()]
    header = lines[0].split('\t')
    rows = []
    for line in lines[1:]:
        vals = line.split('\t')
        row = {}
        for i, key in enumerate(header):
            row[key] = vals[i] if i < len(vals) else ''
        rows.append(row)
    return header, rows


def read(path):
    return open(path).read()


def write(path, text):
    d = os.path.dirname(path)
    if d and not os.path.isdir(d):
        os.makedirs(d)
    with open(path, 'w') as fh:
        fh.write(text)


def project_v2(old_project):
    return old_project.replace('Al16_vib_', 'Al16_vib2_')


def main():
    old_header, old_rows = read_tsv(os.path.join(OLD_BASE, 'vib_manifest.tsv'))
    v2_manifest = os.path.join(NEW_BASE, 'vib_manifest.tsv')
    existing = {}
    if os.path.exists(v2_manifest):
        _, rows = read_tsv(v2_manifest)
        for row in rows:
            existing[row['relative_directory']] = row['status']
    out = ['site\tintermediate\tvib_project\trelative_directory\tstatus']
    prepared = 0
    for row in old_rows:
        if row['status'].startswith('failed_'):
            # Recreate failed v1 jobs as v2 candidates too.
            pass
        old_rel = row['relative_directory']
        old_dir = os.path.join(OLD_BASE, old_rel)
        old_project = row['vib_project']
        new_project = project_v2(old_project)
        new_rel = old_rel
        new_dir = os.path.join(NEW_BASE, new_rel)
        if not os.path.isdir(new_dir):
            os.makedirs(new_dir)

        old_wfn = os.path.join(old_dir, old_project + '-RESTART.wfn')
        new_wfn = os.path.join(new_dir, new_project + '-RESTART.wfn')
        if os.path.exists(old_wfn) and not os.path.exists(new_wfn):
            shutil.copy2(old_wfn, new_wfn)

        inp = read(os.path.join(old_dir, old_project + '.inp'))
        inp = inp.replace('PROJECT %s' % old_project, 'PROJECT %s' % new_project)
        inp = inp.replace(old_project + '-RESTART.wfn', new_project + '-RESTART.wfn')
        inp = inp.replace('EPS_SCF 1.0E-7', 'EPS_SCF 1.0E-8')
        if 'NPROC_REP ' not in inp:
            inp = inp.replace('&VIBRATIONAL_ANALYSIS\n', '&VIBRATIONAL_ANALYSIS\n  NPROC_REP 4\n')
        write(os.path.join(new_dir, new_project + '.inp'), inp)

        cp2k = read(os.path.join(old_dir, 'cp2k'))
        cp2k = cp2k.replace('#SBATCH -J %s' % old_project, '#SBATCH -J %s' % new_project)
        write(os.path.join(new_dir, 'cp2k'), cp2k)
        os.chmod(os.path.join(new_dir, 'cp2k'), 0o755)
        write(os.path.join(new_dir, 'source.txt'),
              'source\t%s\nold_project\t%s\nnew_project\t%s\nchanges\tNPROC_REP 4; EPS_SCF 1E-8\n' %
              (old_dir, old_project, new_project))

        status = existing.get(new_rel, 'candidate_not_submitted')
        out.append('\t'.join([row['site'], row['intermediate'], new_project, new_rel, status]))
        prepared += 1

    write(v2_manifest, '\n'.join(out) + '\n')
    write(os.path.join(NEW_BASE, 'submit_vib_v2_next_batch.sh'), """#!/bin/bash
set -e
cap="${1:-1}"
submitted=0
while IFS=$'\\t' read -r site intermediate vib_project rel status; do
  [ "$site" = "site" ] && continue
  [ "$status" = "candidate_not_submitted" ] || continue
  [ "$submitted" -lt "$cap" ] || break
  cd "$rel"
  echo "Submit: $rel/${vib_project}.inp"
  out=$(sbatch cp2k "${vib_project}.inp")
  echo "$out"
  jobid=$(echo "$out" | awk '{print $4}')
  cd - >/dev/null
  printf '%s\\t%s\\t%s\\t%s\\t%s\\t%s\\n' "$(date '+%F %T')" "$jobid" "$site" "$intermediate" "$vib_project" "submitted" >> submitted_vib_jobs.tsv
  tmp=$(mktemp)
  awk -F'\\t' -v OFS='\\t' -v r="$rel" -v jid="$jobid" 'NR==1 {print; next} $4==r && $5=="candidate_not_submitted" {$5="submitted_"jid} {print}' vib_manifest.tsv > "$tmp"
  mv "$tmp" vib_manifest.tsv
  submitted=$((submitted+1))
done < vib_manifest.tsv
echo "Submitted $submitted; active cap $cap."
""")
    os.chmod(os.path.join(NEW_BASE, 'submit_vib_v2_next_batch.sh'), 0o755)
    if not os.path.exists(os.path.join(NEW_BASE, 'submitted_vib_jobs.tsv')):
        write(os.path.join(NEW_BASE, 'submitted_vib_jobs.tsv'),
              'time\tjobid\tsite\tintermediate\tvib_project\tstatus\n')
    print('prepared_v2_tasks', prepared)


if __name__ == '__main__':
    main()
