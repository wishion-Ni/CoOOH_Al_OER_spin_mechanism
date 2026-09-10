from __future__ import print_function

import json
import math
import os


BASE = os.path.join('sfs', 'CoOH', 'cp2k', 'undoped_001333')
GEO = os.path.join(BASE, 'geo_opt')
OER = os.path.join(BASE, 'oer')
BASE_PROJECT = 'CoOH_001333_geoopt'
SITE = {
    'site': 'site01_surface_Co32',
    'atom_index': 32,
    'label': 'Co32',
}
DIR = (0.0, 1.0 / math.sqrt(2.0), 1.0 / math.sqrt(2.0))
TASKS = [
    ('OH', '01_OH', 'Undoped_s1surfaceCo32_OH', 2),
    ('O', '02_O', 'Undoped_s1surfaceCo32_O', 1),
    ('OOH', '03_OOH', 'Undoped_s1surfaceCo32_OOH', 2),
]


def read(path):
    return open(path).read()


def write(path, text):
    d = os.path.dirname(path)
    if d and not os.path.isdir(d):
        os.makedirs(d)
    with open(path, 'w') as fh:
        fh.write(text)


def read_last_xyz(path):
    lines = [line.rstrip('\n') for line in open(path)]
    natoms = int(lines[0].strip())
    stride = natoms + 2
    start = len(lines) - stride
    atoms = []
    for line in lines[start + 2:start + 2 + natoms]:
        p = line.split()
        atoms.append((p[0], float(p[1]), float(p[2]), float(p[3])))
    return atoms


def add_vec(a, scale):
    return (a[0] + DIR[0] * scale, a[1] + DIR[1] * scale, a[2] + DIR[2] * scale)


def adsorbates(intermediate, site_xyz):
    if intermediate == 'O':
        return [('O',) + add_vec(site_xyz, 1.72)]
    if intermediate == 'OH':
        o = add_vec(site_xyz, 1.90)
        h = add_vec(o, 0.98)
        return [('H',) + h, ('O',) + o]
    if intermediate == 'OOH':
        o_site = add_vec(site_xyz, 1.90)
        o_h = add_vec(o_site, 1.45)
        h = add_vec(o_h, 0.98)
        return [('H',) + h, ('O',) + o_site, ('O',) + o_h]
    raise ValueError(intermediate)


def nearest_checks(base_atoms, ads):
    checks = []
    for i, atom in enumerate(ads):
        species, x, y, z = atom
        best = None
        for j, batom in enumerate(base_atoms):
            _, bx, by, bz = batom
            d = math.sqrt((x - bx) ** 2 + (y - by) ** 2 + (z - bz) ** 2)
            if best is None or d < best[0]:
                best = (d, j + 1, batom[0])
        checks.append({
            'ads': 'ads_%s_%d' % (species, i + 1),
            'nearest_index': best[1],
            'nearest_species': best[2],
            'distance_A': round(best[0], 4),
        })
    return checks


def coords_block(atoms):
    out = []
    for sp, x, y, z in atoms:
        out.append('      %-2s %18.10f  %18.10f  %18.10f' % (sp, x, y, z))
    return '\n'.join(out)


def make_input(base_inp, project, multiplicity, atoms):
    lines = base_inp.splitlines()
    out = []
    in_coord = False
    inserted_coord = False
    for line in lines:
        if line.strip() == 'PROJECT %s' % BASE_PROJECT:
            line = '  PROJECT %s' % project
        if line.strip() == 'MULTIPLICITY 1':
            line = '    MULTIPLICITY %d' % multiplicity
        if line.strip() == '&COORD':
            in_coord = True
            out.append(line)
            out.append(coords_block(atoms))
            inserted_coord = True
            continue
        if in_coord:
            if line.strip() == '&END COORD':
                in_coord = False
                out.append(line)
            continue
        out.append(line)
    if not inserted_coord:
        raise SystemExit('failed to replace coord block')
    return '\n'.join(out) + '\n'


def render_xyz(atoms, title):
    out = [str(len(atoms)), title]
    for sp, x, y, z in atoms:
        out.append('%-2s %16.10f %16.10f %16.10f' % (sp, x, y, z))
    return '\n'.join(out) + '\n'


def render_cp2k(project):
    return """#!/bin/bash
#SBATCH -J %s
#SBATCH --nodes=1
#SBATCH --ntasks=40
#SBATCH --partition=n40
#SBATCH --error=%%J.stderr
#SBATCH --output=%%J.stdout

export LD_LIBRARY_PATH=/apps/soft/gmp620/lib:$LD_LIBRARY_PATH
export LD_LIBRARY_PATH=/apps/soft/mpfr410/lib:$LD_LIBRARY_PATH
export LD_LIBRARY_PATH=/apps/soft/mpc120/lib:$LD_LIBRARY_PATH
export LD_LIBRARY_PATH=/apps/soft/gcc840/lib64:$LD_LIBRARY_PATH
export PATH=/apps/soft/gcc840/bin:$PATH

CP2K_ROOT=/apps/soft/cp2k-2024.1
source ${CP2K_ROOT}/tools/toolchain/install/setup
export PATH=$PATH:${CP2K_ROOT}/exe/local
export CP2K_DATA_DIR=${CP2K_ROOT}/data

NPROCS=$SLURM_NTASKS
ulimit -s unlimited
INPUT=$1
OUTPUT=`echo ${INPUT} | awk -F'.' '{print $1".out"}'`
ERR=`echo ${INPUT} | awk -F'.' '{print $1".err"}'`
mpirun -np ${NPROCS} cp2k.popt ${INPUT} 1>${OUTPUT} 2>${ERR}
""" % project


def write_submitter():
    write(os.path.join(OER, 'submit_next_batch.sh'), """#!/bin/bash
set -e
cap="${1:-1}"
submitted=0
while IFS=$'\\t' read -r site intermediate rel project atoms status; do
  [ "$site" = "site" ] && continue
  [ "$status" = "not_submitted" ] || continue
  [ "$submitted" -lt "$cap" ] || break
  cd "$rel"
  echo "Submit: $rel/${project}.inp"
  out=$(sbatch cp2k "${project}.inp")
  echo "$out"
  jobid=$(echo "$out" | awk '{print $4}')
  cd - >/dev/null
  printf '%s\\t%s\\t%s\\t%s\\t%s\\t%s\\n' "$(date '+%F %T')" "$jobid" "$site" "$intermediate" "$project" "submitted" >> submitted_jobs.tsv
  tmp=$(mktemp)
  awk -F'\\t' -v OFS='\\t' -v r="$rel" -v jid="$jobid" 'NR==1 {print; next} $3==r && $6=="not_submitted" {$6="submitted_"jid} {print}' submission_manifest.tsv > "$tmp"
  mv "$tmp" submission_manifest.tsv
  submitted=$((submitted+1))
done < submission_manifest.tsv
echo "Submitted $submitted; active cap $cap."
""")
    os.chmod(os.path.join(OER, 'submit_next_batch.sh'), 0o755)
    if not os.path.exists(os.path.join(OER, 'submitted_jobs.tsv')):
        write(os.path.join(OER, 'submitted_jobs.tsv'),
              'time\tjobid\tsite\tintermediate\tproject\tstatus\n')


def main():
    base_atoms = read_last_xyz(os.path.join(GEO, BASE_PROJECT + '-pos-1.xyz'))
    if len(base_atoms) != 210:
        raise SystemExit('expected 210 base atoms, got %d' % len(base_atoms))
    site_atom = base_atoms[SITE['atom_index'] - 1]
    site_xyz = site_atom[1:4]
    base_inp = read(os.path.join(GEO, BASE_PROJECT + '.inp'))
    rows = ['site\tintermediate\trelative_directory\tproject\tatoms\tstatus']
    for inter, subdir, project, mult in TASKS:
        rel = os.path.join('sites', SITE['site'], subdir)
        task_dir = os.path.join(OER, rel)
        ads = adsorbates(inter, site_xyz)
        atoms = base_atoms + ads
        write(os.path.join(task_dir, project + '.inp'),
              make_input(base_inp, project, mult, atoms))
        write(os.path.join(task_dir, project + '.xyz'),
              render_xyz(atoms, project))
        write(os.path.join(task_dir, 'cp2k'), render_cp2k(project))
        os.chmod(os.path.join(task_dir, 'cp2k'), 0o755)
        check = {
            'site': SITE['site'],
            'intermediate': inter,
            'direction': [round(x, 8) for x in DIR],
            'site_atom_index': SITE['atom_index'],
            'site_xyz_A': [round(x, 8) for x in site_xyz],
            'checks': nearest_checks(base_atoms, ads),
        }
        write(os.path.join(task_dir, 'placement_check.json'),
              json.dumps(check, indent=2, sort_keys=True) + '\n')
        rows.append('\t'.join([SITE['site'], inter, rel, project, str(len(atoms)), 'not_submitted']))
    write(os.path.join(OER, 'submission_manifest.tsv'), '\n'.join(rows) + '\n')
    write_submitter()
    print('site_xyz %.8f %.8f %.8f' % site_xyz)
    print('prepared_oer_tasks', len(TASKS))


if __name__ == '__main__':
    main()
