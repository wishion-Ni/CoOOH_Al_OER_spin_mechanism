from __future__ import print_function

import os
import shutil


BASE = os.path.join('sfs', 'CoOH', 'cp2k', 'Al16', 'oer')
OLD_REL = os.path.join('restarts', 'site03_bulk_Co7_adjAl', '02_O_r1')
NEW_REL = os.path.join('restarts', 'site03_bulk_Co7_adjAl', '02_O_r2')
OLD_PROJECT = 'Al16_s3bulkCo7adjAl_O_r1'
NEW_PROJECT = 'Al16_s3bulkCo7adjAl_O_r2'


def read(path):
    return open(path).read()


def write(path, text):
    d = os.path.dirname(path)
    if d and not os.path.isdir(d):
        os.makedirs(d)
    with open(path, 'w') as fh:
        fh.write(text)


def main():
    old_dir = os.path.join(BASE, OLD_REL)
    new_dir = os.path.join(BASE, NEW_REL)
    if not os.path.isdir(new_dir):
        os.makedirs(new_dir)
    for suffix in ['-1.restart', '-RESTART.wfn', '-BFGS.Hessian']:
        src = os.path.join(old_dir, OLD_PROJECT + suffix)
        dst = os.path.join(new_dir, NEW_PROJECT + suffix)
        if os.path.exists(src) and not os.path.exists(dst):
            shutil.copy2(src, dst)
    inp = read(os.path.join(old_dir, OLD_PROJECT + '.inp'))
    inp = inp.replace('PROJECT %s' % OLD_PROJECT, 'PROJECT %s' % NEW_PROJECT)
    inp = inp.replace(OLD_PROJECT + '-RESTART.wfn', NEW_PROJECT + '-RESTART.wfn')
    inp = inp.replace(OLD_PROJECT + '-1.restart', NEW_PROJECT + '-1.restart')
    inp = inp.replace('MAX_ITER 500', 'MAX_ITER 1000')
    write(os.path.join(new_dir, NEW_PROJECT + '.inp'), inp)
    cp2k = read(os.path.join(old_dir, 'cp2k')).replace('#SBATCH -J %s' % OLD_PROJECT,
                                                     '#SBATCH -J %s' % NEW_PROJECT)
    write(os.path.join(new_dir, 'cp2k'), cp2k)
    os.chmod(os.path.join(new_dir, 'cp2k'), 0o755)
    write(os.path.join(new_dir, 'restart_from.txt'),
          'from\t%s\nold_project\t%s\nnew_project\t%s\nreason\tr1 used MAX_ITER 500 with restart step 500\n' %
          (OLD_REL, OLD_PROJECT, NEW_PROJECT))
    manifest = os.path.join(BASE, 'submission_manifest.tsv')
    lines = [line.rstrip('\n') for line in open(manifest)]
    for line in lines[1:]:
        parts = line.split('\t')
        if len(parts) >= 6 and parts[2] == NEW_REL:
            print('already_prepared', NEW_REL)
            return
    lines.append('\t'.join([
        'site03_bulk_Co7_adjAl', 'O', NEW_REL, NEW_PROJECT, '211', 'restart_prepared'
    ]))
    write(manifest, '\n'.join(lines) + '\n')
    print('prepared', NEW_REL, NEW_PROJECT)


if __name__ == '__main__':
    main()
