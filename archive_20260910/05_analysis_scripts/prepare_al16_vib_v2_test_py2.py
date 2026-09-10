from __future__ import print_function

import os
import shutil


BASE = os.path.join('sfs', 'CoOH', 'cp2k', 'Al16')
OLD = os.path.join(BASE, 'vib_corrections', 'tasks', 'site01_surface_Co13_adjAl', 'O')
NEW = os.path.join(BASE, 'vib_corrections_v2', 'tasks', 'site01_surface_Co13_adjAl', 'O')
OLD_PROJECT = 'Al16_vib_s1surfaceCo13adjAl_O'
NEW_PROJECT = 'Al16_vib2_s1surfaceCo13adjAl_O'


def read(path):
    return open(path).read()


def write(path, text):
    d = os.path.dirname(path)
    if d and not os.path.isdir(d):
        os.makedirs(d)
    with open(path, 'w') as fh:
        fh.write(text)


def main():
    if not os.path.isdir(NEW):
        os.makedirs(NEW)
    src_wfn = os.path.join(OLD, OLD_PROJECT + '-RESTART.wfn')
    dst_wfn = os.path.join(NEW, NEW_PROJECT + '-RESTART.wfn')
    if os.path.exists(src_wfn) and not os.path.exists(dst_wfn):
        shutil.copy2(src_wfn, dst_wfn)

    inp = read(os.path.join(OLD, OLD_PROJECT + '.inp'))
    inp = inp.replace('PROJECT %s' % OLD_PROJECT, 'PROJECT %s' % NEW_PROJECT)
    inp = inp.replace(OLD_PROJECT + '-RESTART.wfn', NEW_PROJECT + '-RESTART.wfn')
    inp = inp.replace('EPS_SCF 1.0E-7', 'EPS_SCF 1.0E-8')
    inp = inp.replace('&VIBRATIONAL_ANALYSIS\n', '&VIBRATIONAL_ANALYSIS\n  NPROC_REP 4\n')
    write(os.path.join(NEW, NEW_PROJECT + '.inp'), inp)

    cp2k = read(os.path.join(OLD, 'cp2k'))
    cp2k = cp2k.replace('#SBATCH -J %s' % OLD_PROJECT, '#SBATCH -J %s' % NEW_PROJECT)
    write(os.path.join(NEW, 'cp2k'), cp2k)
    os.chmod(os.path.join(NEW, 'cp2k'), 0o755)
    write(os.path.join(NEW, 'source.txt'),
          'source\t%s\nold_project\t%s\nnew_project\t%s\nchanges\tNPROC_REP 4; EPS_SCF 1E-8\n' %
          (OLD, OLD_PROJECT, NEW_PROJECT))

    manifest = os.path.join(BASE, 'vib_corrections_v2', 'vib_manifest.tsv')
    if not os.path.exists(manifest):
        write(manifest, 'site\tintermediate\tvib_project\trelative_directory\tstatus\n')
    lines = [line.rstrip('\n') for line in open(manifest) if line.strip()]
    rel = os.path.join('tasks', 'site01_surface_Co13_adjAl', 'O')
    if not any(line.split('\t')[3] == rel for line in lines[1:]):
        lines.append('\t'.join([
            'site01_surface_Co13_adjAl', 'O', NEW_PROJECT, rel, 'candidate_not_submitted'
        ]))
        write(manifest, '\n'.join(lines) + '\n')
    print('prepared', NEW_PROJECT, rel)


if __name__ == '__main__':
    main()
