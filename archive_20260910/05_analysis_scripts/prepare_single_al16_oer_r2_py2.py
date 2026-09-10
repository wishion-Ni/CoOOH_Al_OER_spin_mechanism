from __future__ import print_function

import os
import shutil


BASE = os.path.join('sfs', 'CoOH', 'cp2k', 'Al16', 'oer')

TASK = {
    'site': 'site02_surface_Al47',
    'intermediate': 'OH',
    'old_rel': os.path.join('restarts', 'site02_surface_Al47', '01_OH_r1'),
    'old_project': 'Al16_s2surfaceAl47_OH_r1',
    'new_rel': os.path.join('restarts', 'site02_surface_Al47', '01_OH_r2'),
    'new_project': 'Al16_s2surfaceAl47_OH_r2',
    'atoms': '212',
}


def read(path):
    return open(path).read()


def write(path, text):
    d = os.path.dirname(path)
    if d and not os.path.isdir(d):
        os.makedirs(d)
    with open(path, 'w') as fh:
        fh.write(text)


def patch_input(inp, old, new):
    inp = inp.replace('PROJECT %s' % old, 'PROJECT %s' % new)
    inp = inp.replace(old + '-RESTART.wfn', new + '-RESTART.wfn')
    inp = inp.replace(old + '-1.restart', new + '-1.restart')
    inp = inp.replace('MAX_ITER 500', 'MAX_ITER 1000')
    return inp


def patch_cp2k(cp2k_text, job_name):
    out = []
    for line in cp2k_text.splitlines():
        if line.startswith('#SBATCH -J '):
            out.append('#SBATCH -J %s' % job_name)
        else:
            out.append(line)
    return '\n'.join(out) + '\n'


def update_manifest(task):
    path = os.path.join(BASE, 'submission_manifest.tsv')
    lines = [line.rstrip('\n') for line in open(path)]
    for line in lines[1:]:
        parts = line.split('\t')
        if len(parts) >= 6 and parts[2] == task['new_rel']:
            return
    lines.append('\t'.join([
        task['site'], task['intermediate'], task['new_rel'], task['new_project'],
        task['atoms'], 'restart_prepared'
    ]))
    write(path, '\n'.join(lines) + '\n')


def main():
    t = TASK
    old_dir = os.path.join(BASE, t['old_rel'])
    new_dir = os.path.join(BASE, t['new_rel'])
    if not os.path.isdir(new_dir):
        os.makedirs(new_dir)

    for suffix in ['-1.restart', '-RESTART.wfn', '-BFGS.Hessian']:
        src = os.path.join(old_dir, t['old_project'] + suffix)
        dst = os.path.join(new_dir, t['new_project'] + suffix)
        if os.path.exists(src) and not os.path.exists(dst):
            shutil.copy2(src, dst)

    inp = patch_input(read(os.path.join(old_dir, t['old_project'] + '.inp')),
                      t['old_project'], t['new_project'])
    write(os.path.join(new_dir, t['new_project'] + '.inp'), inp)
    cp2k = patch_cp2k(read(os.path.join(old_dir, 'cp2k')), t['new_project'])
    write(os.path.join(new_dir, 'cp2k'), cp2k)
    os.chmod(os.path.join(new_dir, 'cp2k'), 0o755)
    write(os.path.join(new_dir, 'restart_from.txt'),
          'from\t%s\nold_project\t%s\nnew_project\t%s\nreason\tr1_used MAX_ITER 500 with restart step 500\n' %
          (t['old_rel'], t['old_project'], t['new_project']))
    update_manifest(t)
    print('prepared', t['new_rel'], t['new_project'])


if __name__ == '__main__':
    main()
