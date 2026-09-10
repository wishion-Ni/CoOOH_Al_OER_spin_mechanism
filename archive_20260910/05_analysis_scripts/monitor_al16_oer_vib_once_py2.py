from __future__ import print_function

import os
import subprocess


BASE = os.path.join('sfs', 'CoOH', 'cp2k', 'Al16')
OER = os.path.join(BASE, 'oer')
VIB = os.path.join(BASE, 'vib_corrections')
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


def collect_text(path):
    text = ''
    if not os.path.isdir(path):
        return text
    for name in os.listdir(path):
        if name.endswith(('.out', '.err', '.stdout', '.stderr')):
            text += '\n' + read_text(os.path.join(path, name))
    return text


def classify_geo(path):
    text = collect_text(path)
    if 'ABORT' in text or 'SCF run NOT converged' in text:
        return 'failed'
    if 'GEOMETRY OPTIMIZATION COMPLETED' in text and 'PROGRAM ENDED' in text:
        return 'completed'
    if 'MAXIMUM NUMBER OF OPTIMIZATION STEPS REACHED' in text and 'PROGRAM ENDED' in text:
        return 'not_converged'
    if 'PROGRAM ENDED' in text:
        return 'not_converged'
    return 'running_or_unknown'


def classify_vib(path):
    text = collect_text(path)
    if ('ABORT' in text or 'SCF run NOT converged' in text or
            'BAD TERMINATION' in text or 'Killed (signal 9)' in text):
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
        if (name.startswith('Al16_s') or name.startswith('Al16_vib') or
                name.startswith('Al16_spin') or name.startswith('CoOH001333_geo')):
            jobs.append(parts)
    return jobs


def main():
    events = []

    oer_path = os.path.join(OER, 'submission_manifest.tsv')
    header, rows = read_tsv(oer_path)
    changed = False
    for row in rows:
        status = row.get('status', '')
        if not status.startswith('submitted_'):
            continue
        jobid = status.split('_', 1)[1]
        task_dir = os.path.join(OER, row['relative_directory'])
        state = classify_geo(task_dir)
        if state == 'completed':
            row['status'] = 'completed_' + jobid
            changed = True
            events.append('OER completed %s %s job %s' % (row['site'], row['intermediate'], jobid))
        elif state == 'failed':
            row['status'] = 'failed_' + jobid
            changed = True
            events.append('OER failed %s %s job %s' % (row['site'], row['intermediate'], jobid))
        elif state == 'not_converged':
            row['status'] = 'not_converged_' + jobid
            changed = True
            events.append('OER not_converged %s %s job %s' % (row['site'], row['intermediate'], jobid))
    if changed:
        write_tsv(oer_path, header, rows)

    vib_path = os.path.join(VIB, 'vib_manifest.tsv')
    vib_candidates = 0
    if os.path.exists(vib_path):
        vheader, vrows = read_tsv(vib_path)
        vchanged = False
        for row in vrows:
            status = row.get('status', '')
            if status == 'candidate_not_submitted':
                vib_candidates += 1
            if not status.startswith('submitted_'):
                continue
            jobid = status.split('_', 1)[1]
            task_dir = os.path.join(VIB, row['relative_directory'])
            state = classify_vib(task_dir)
            if state == 'completed':
                row['status'] = 'completed_' + jobid
                vchanged = True
                events.append('vib completed %s %s job %s' % (row['site'], row['intermediate'], jobid))
            elif state == 'failed':
                row['status'] = 'failed_' + jobid
                vchanged = True
                events.append('vib failed %s %s job %s' % (row['site'], row['intermediate'], jobid))
        if vchanged:
            write_tsv(vib_path, vheader, vrows)
            # Re-count after update.
            vib_candidates = sum(1 for r in vrows if r.get('status') == 'candidate_not_submitted')

    undoped_state = 'missing'
    if os.path.isdir(UNDOPED_GEO):
        undoped_state = classify_geo(UNDOPED_GEO)
        if undoped_state in ('completed', 'failed', 'not_converged'):
            events.append('undoped_geoopt_' + undoped_state + ' job 109336')

    jobs = active_jobs()
    print('ACTIVE_TOTAL\t%d' % len(jobs))
    for j in jobs:
        print('JOB\t%s\t%s\t%s\t%s\t%s' % (j[0], j[1], j[2], j[3], j[5] if len(j) > 5 else ''))
    print('UNDOPED_STATE\t%s' % undoped_state)
    print('VIB_CANDIDATES\t%d' % vib_candidates)
    slots = max(0, 5 - len(jobs))
    print('SUGGEST_VIB_SLOTS\t%d' % min(slots, vib_candidates))
    for e in events:
        print('EVENT\t' + e)


if __name__ == '__main__':
    main()
