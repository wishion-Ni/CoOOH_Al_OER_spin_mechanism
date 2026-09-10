from __future__ import print_function

import os
import subprocess


BASE = os.path.join('sfs', 'CoOH', 'cp2k', 'Al16')
OER = os.path.join(BASE, 'oer')
VAL = os.path.join(BASE, 'valence_analysis')
UNDOPED_GEO = os.path.join('sfs', 'CoOH', 'cp2k', 'undoped_001333', 'geo_opt')


def read_text(path):
    try:
        return open(path).read()
    except IOError:
        return ''


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


def write_tsv(path, header, rows):
    tmp = path + '.tmp'
    with open(tmp, 'w') as fh:
        fh.write('\t'.join(header) + '\n')
        for row in rows:
            fh.write('\t'.join(row.get(key, '') for key in header) + '\n')
    os.rename(tmp, path)


def classify_geo(path):
    text = ''
    for name in os.listdir(path):
        if name.endswith(('.out', '.err', '.stdout', '.stderr')):
            text += '\n' + read_text(os.path.join(path, name))
    if 'ABORT' in text or 'SCF run NOT converged' in text:
        return 'failed'
    if 'GEOMETRY OPTIMIZATION COMPLETED' in text and 'PROGRAM ENDED' in text:
        return 'completed'
    if 'MAXIMUM NUMBER OF OPTIMIZATION STEPS' in text or 'MAX_ITER' in text and 'PROGRAM ENDED' in text:
        return 'not_converged'
    return 'running_or_unknown'


def classify_spin(path):
    text = ''
    for name in os.listdir(path):
        if name.endswith(('.out', '.err', '.stdout', '.stderr')):
            text += '\n' + read_text(os.path.join(path, name))
    if 'ABORT' in text or 'SCF run NOT converged' in text:
        return 'failed'
    if 'PROGRAM ENDED' in text:
        return 'completed'
    return 'running_or_unknown'


def active_jobs():
    out = subprocess.check_output("squeue -u ftfan -o '%i\t%j\t%T\t%M\t%D\t%R'", shell=True)
    if not isinstance(out, str):
        out = out.decode('utf-8', 'replace')
    jobs = []
    for line in out.splitlines()[1:]:
        parts = line.split('\t')
        if len(parts) < 3:
            continue
        name = parts[1]
        if name.startswith('Al16_s') or name.startswith('Al16_spin') or name.startswith('CoOH001333_geo'):
            jobs.append(parts)
    return jobs


def main():
    events = []
    jobs = active_jobs()
    active_al16 = [j for j in jobs if j[1].startswith('Al16_s') or j[1].startswith('Al16_spin')]
    active_total = jobs[:]

    oer_path = os.path.join(OER, 'submission_manifest.tsv')
    header, rows = read_tsv(oer_path)
    changed_oer = False
    for row in rows:
        status = row.get('status', '')
        if not status.startswith('submitted_'):
            continue
        jobid = status.split('_', 1)[1]
        task_dir = os.path.join(OER, row['relative_directory'])
        state = classify_geo(task_dir)
        if state == 'completed':
            row['status'] = 'completed_' + jobid
            changed_oer = True
            events.append('OER completed %s %s job %s' % (row['site'], row['intermediate'], jobid))
        elif state == 'failed':
            row['status'] = 'failed_' + jobid
            changed_oer = True
            events.append('OER failed %s %s job %s' % (row['site'], row['intermediate'], jobid))
        elif state == 'not_converged':
            row['status'] = 'not_converged_' + jobid
            changed_oer = True
            events.append('OER not_converged %s %s job %s' % (row['site'], row['intermediate'], jobid))
    if changed_oer:
        write_tsv(oer_path, header, rows)

    spin_path = os.path.join(VAL, 'spin_scan_manifest.tsv')
    if os.path.exists(spin_path):
        sheader, srows = read_tsv(spin_path)
        changed_spin = False
        for row in srows:
            status = row.get('status', '')
            if not status.startswith('submitted_'):
                continue
            jobid = status.split('_', 1)[1]
            task_dir = os.path.join(VAL, row['relative_directory'])
            state = classify_spin(task_dir)
            if state == 'completed':
                row['status'] = 'completed_' + jobid
                changed_spin = True
                events.append('spin completed %s %s M%s job %s' %
                              (row['site'], row['intermediate'], row['multiplicity'], jobid))
            elif state == 'failed':
                row['status'] = 'failed_' + jobid
                changed_spin = True
                events.append('spin failed %s %s M%s job %s' %
                              (row['site'], row['intermediate'], row['multiplicity'], jobid))
        if changed_spin:
            write_tsv(spin_path, sheader, srows)

    undoped_state = 'missing'
    if os.path.isdir(UNDOPED_GEO):
        undoped_state = classify_geo(UNDOPED_GEO)
        if undoped_state in ('completed', 'failed', 'not_converged'):
            events.append('undoped_geoopt_' + undoped_state + ' job 109336')

    # Recompute active after status updates.
    jobs = active_jobs()
    active_al16 = [j for j in jobs if j[1].startswith('Al16_s') or j[1].startswith('Al16_spin')]
    active_total = jobs[:]

    print('ACTIVE_TOTAL\t%d' % len(active_total))
    for j in active_total:
        print('JOB\t%s\t%s\t%s\t%s\t%s' % (j[0], j[1], j[2], j[3], j[5] if len(j) > 5 else ''))
    print('ACTIVE_AL16\t%d' % len(active_al16))
    print('UNDOPED_STATE\t%s' % undoped_state)
    for e in events:
        print('EVENT\t' + e)

    # Keep total workflow at 5 including undoped insertion.
    slots = max(0, 5 - len(active_total))
    candidates = 0
    if os.path.exists(spin_path):
        for row in read_tsv(spin_path)[1]:
            if row.get('status') == 'candidate_not_submitted':
                candidates += 1
    print('SPIN_CANDIDATES\t%d' % candidates)
    print('SUGGEST_SPIN_SLOTS\t%d' % min(slots, candidates))


if __name__ == '__main__':
    main()
