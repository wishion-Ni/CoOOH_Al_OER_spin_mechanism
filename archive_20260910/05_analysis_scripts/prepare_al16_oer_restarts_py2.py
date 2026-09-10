from __future__ import print_function

import os
import shutil


BASE = os.path.join('sfs', 'CoOH', 'cp2k', 'Al16', 'oer')

TASKS = [
    {
        'site': 'site02_surface_Al47',
        'intermediate': 'OH',
        'old_rel': os.path.join('sites', 'site02_surface_Al47', '01_OH'),
        'old_project': 'Al16_s2surfaceAl47_OH',
        'new_rel': os.path.join('restarts', 'site02_surface_Al47', '01_OH_r1'),
        'new_project': 'Al16_s2surfaceAl47_OH_r1',
        'atoms': '212',
    },
    {
        'site': 'site03_bulk_Co7_adjAl',
        'intermediate': 'O',
        'old_rel': os.path.join('sites', 'site03_bulk_Co7_adjAl', '02_O'),
        'old_project': 'Al16_s3bulkCo7adjAl_O',
        'new_rel': os.path.join('restarts', 'site03_bulk_Co7_adjAl', '02_O_r1'),
        'new_project': 'Al16_s3bulkCo7adjAl_O_r1',
        'atoms': '211',
    },
]


def read(path):
    return open(path).read()


def write(path, text):
    with open(path, 'w') as fh:
        fh.write(text)


def replace_project(inp, old, new):
    inp = inp.replace('PROJECT %s' % old, 'PROJECT %s' % new)
    return inp


def add_ext_restart(inp, restart_name, wfn_name):
    inp = inp.replace('MAX_ITER 500', 'MAX_ITER 1000')
    lines = inp.splitlines()
    out = []
    inserted_global = False
    inserted_dft = False
    in_global = False
    in_dft = False
    for line in lines:
        stripped = line.strip().upper()
        if stripped == '&GLOBAL':
            in_global = True
        elif stripped == '&DFT':
            in_dft = True
        if in_global and stripped == '&END GLOBAL' and not inserted_global:
            out.append('  EXTENDED_FFT_LENGTHS T')
            inserted_global = True
        if in_dft and stripped == '&END DFT' and not inserted_dft:
            out.append('    WFN_RESTART_FILE_NAME %s' % wfn_name)
            inserted_dft = True
        out.append(line)
        if stripped == '&END GLOBAL':
            in_global = False
        elif stripped == '&END DFT':
            in_dft = False
    out.append('')
    out.append('&EXT_RESTART')
    out.append('  RESTART_FILE_NAME %s' % restart_name)
    out.append('  RESTART_DEFAULT T')
    out.append('&END EXT_RESTART')
    out.append('')
    return '\n'.join(out)


def set_job_name(cp2k_text, job_name):
    lines = []
    for line in cp2k_text.splitlines():
        if line.startswith('#SBATCH -J '):
            lines.append('#SBATCH -J %s' % job_name)
        else:
            lines.append(line)
    return '\n'.join(lines) + '\n'


def update_manifest(path, task):
    lines = [line.rstrip('\n') for line in open(path)]
    header = lines[0]
    rows = lines[1:]
    marker = 'restart_prepared'
    for row in rows:
        parts = row.split('\t')
        if len(parts) >= 5 and parts[2] == task['new_rel'] and parts[3] == task['new_project']:
            return
    rows.append('\t'.join([
        task['site'],
        task['intermediate'],
        task['new_rel'],
        task['new_project'],
        task['atoms'],
        marker,
    ]))
    write(path, header + '\n' + '\n'.join(rows) + '\n')


def main():
    for task in TASKS:
        old_dir = os.path.join(BASE, task['old_rel'])
        new_dir = os.path.join(BASE, task['new_rel'])
        if not os.path.isdir(new_dir):
            os.makedirs(new_dir)

        restart = task['old_project'] + '-1.restart'
        wfn = task['old_project'] + '-RESTART.wfn'
        for name in [restart, wfn, task['old_project'] + '-BFGS.Hessian']:
            src = os.path.join(old_dir, name)
            if os.path.exists(src):
                dst_name = name.replace(task['old_project'], task['new_project'])
                dst = os.path.join(new_dir, dst_name)
                if not os.path.exists(dst):
                    shutil.copy2(src, dst)

        old_inp = read(os.path.join(old_dir, task['old_project'] + '.inp'))
        new_inp = replace_project(old_inp, task['old_project'], task['new_project'])
        new_inp = add_ext_restart(
            new_inp,
            task['new_project'] + '-1.restart',
            task['new_project'] + '-RESTART.wfn',
        )
        write(os.path.join(new_dir, task['new_project'] + '.inp'), new_inp)

        cp2k = read(os.path.join(old_dir, 'cp2k'))
        write(os.path.join(new_dir, 'cp2k'), set_job_name(cp2k, task['new_project']))
        os.chmod(os.path.join(new_dir, 'cp2k'), 0o755)

        write(os.path.join(new_dir, 'restart_from.txt'),
              'from\t%s\nold_project\t%s\nnew_project\t%s\n' %
              (task['old_rel'], task['old_project'], task['new_project']))
        update_manifest(os.path.join(BASE, 'submission_manifest.tsv'), task)
        print('prepared', task['new_rel'], task['new_project'])


if __name__ == '__main__':
    main()
