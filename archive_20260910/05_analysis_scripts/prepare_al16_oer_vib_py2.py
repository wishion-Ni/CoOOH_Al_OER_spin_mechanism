from __future__ import print_function

import os
import shutil


BASE = os.path.join('sfs', 'CoOH', 'cp2k', 'Al16')
OER = os.path.join(BASE, 'oer')
VIB = os.path.join(BASE, 'vib_corrections')
BASE_ATOMS = 210


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


def write(path, text):
    d = os.path.dirname(path)
    if d and not os.path.isdir(d):
        os.makedirs(d)
    with open(path, 'w') as fh:
        fh.write(text)


def read(path):
    return open(path).read()


def ads_atoms(intermediate, natoms):
    natoms = int(natoms)
    if intermediate == 'O':
        return [BASE_ATOMS + 1]
    if intermediate == 'OH':
        return [BASE_ATOMS + 1, BASE_ATOMS + 2]
    if intermediate == 'OOH':
        return [BASE_ATOMS + 1, BASE_ATOMS + 2, BASE_ATOMS + 3]
    raise ValueError(intermediate)


def strip_motion_and_ext(inp):
    lines = inp.splitlines()
    out = []
    skip = 0
    for line in lines:
        upper = line.strip().upper()
        if upper == '&MOTION' or upper == '&EXT_RESTART':
            skip = 1
            continue
        if skip:
            if upper == '&END MOTION' or upper == '&END EXT_RESTART':
                skip = 0
            continue
        out.append(line)
    return '\n'.join(out) + '\n'


def set_global(inp, old_project, new_project):
    inp = inp.replace('PROJECT %s' % old_project, 'PROJECT %s' % new_project)
    inp = inp.replace('RUN_TYPE GEO_OPT', 'RUN_TYPE VIBRATIONAL_ANALYSIS')
    return inp


def tighten_scf(inp):
    inp = inp.replace('EPS_SCF 1.0E-6', 'EPS_SCF 1.0E-7')
    inp = inp.replace('EPS_SCF 1.0E-06', 'EPS_SCF 1.0E-7')
    return inp


def add_wfn_restart(inp, wfn_name):
    lines = inp.splitlines()
    out = []
    in_dft = False
    inserted = False
    for line in lines:
        upper = line.strip().upper()
        if upper == '&DFT':
            in_dft = True
        if in_dft and upper == '&END DFT' and not inserted:
            out.append('    WFN_RESTART_FILE_NAME %s' % wfn_name)
            inserted = True
        out.append(line)
        if upper == '&END DFT':
            in_dft = False
    return '\n'.join(out) + '\n'


def render_vib(inp, atoms):
    lines = []
    lines.append(inp.rstrip())
    lines.append('')
    lines.append('&VIBRATIONAL_ANALYSIS')
    lines.append('  DX 0.01')
    lines.append('  FULLY_PERIODIC T')
    lines.append('  TC_TEMPERATURE 298.15')
    lines.append('  &MODE_SELECTIVE')
    lines.append('    ATOMS %s' % ' '.join(str(x) for x in atoms))
    lines.append('    RANGE 0.0 4000.0')
    lines.append('    LOWEST_FREQUENCY -100.0')
    lines.append('  &END MODE_SELECTIVE')
    lines.append('&END VIBRATIONAL_ANALYSIS')
    lines.append('')
    return '\n'.join(lines)


def render_cp2k(job_name):
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
""" % job_name


def manifest_existing(path):
    old = {}
    if not os.path.exists(path):
        return old
    _, rows = read_tsv(path)
    for row in rows:
        old[row.get('relative_directory', '')] = row.get('status', '')
    return old


def main():
    if not os.path.isdir(VIB):
        os.makedirs(VIB)
    _, rows = read_tsv(os.path.join(OER, 'submission_manifest.tsv'))
    existing = manifest_existing(os.path.join(VIB, 'vib_manifest.tsv'))
    manifest = ['site\tintermediate\tsource_project\tvib_project\tadsorbate_atoms\trelative_directory\tstatus']
    prepared = 0
    for row in rows:
        if not row['status'].startswith('completed_'):
            continue
        site = row['site']
        inter = row['intermediate']
        src_project = row['project']
        src_rel = row['relative_directory']
        atoms = ads_atoms(inter, row['atoms'])
        vib_project = 'Al16_vib_' + src_project.replace('Al16_', '')
        rel = os.path.join('tasks', site, inter)
        status = existing.get(rel, 'candidate_not_submitted')

        src_dir = os.path.join(OER, src_rel)
        dst_dir = os.path.join(VIB, rel)
        if not os.path.isdir(dst_dir):
            os.makedirs(dst_dir)

        wfn_src = os.path.join(src_dir, src_project + '-RESTART.wfn')
        if os.path.exists(wfn_src):
            wfn_dst = os.path.join(dst_dir, vib_project + '-RESTART.wfn')
            if not os.path.exists(wfn_dst):
                shutil.copy2(wfn_src, wfn_dst)

        inp = read(os.path.join(src_dir, src_project + '.inp'))
        inp = strip_motion_and_ext(inp)
        inp = set_global(inp, src_project, vib_project)
        inp = tighten_scf(inp)
        inp = add_wfn_restart(inp, vib_project + '-RESTART.wfn')
        inp = render_vib(inp, atoms)
        write(os.path.join(dst_dir, vib_project + '.inp'), inp)
        write(os.path.join(dst_dir, 'cp2k'), render_cp2k(vib_project))
        os.chmod(os.path.join(dst_dir, 'cp2k'), 0o755)
        write(os.path.join(dst_dir, 'source.txt'),
              'source_rel\t%s\nsource_project\t%s\nadsorbate_atoms\t%s\n' %
              (src_rel, src_project, ' '.join(str(x) for x in atoms)))
        manifest.append('\t'.join([site, inter, src_project, vib_project,
                                   ' '.join(str(x) for x in atoms), rel, status]))
        prepared += 1

    write(os.path.join(VIB, 'vib_manifest.tsv'), '\n'.join(manifest) + '\n')
    write(os.path.join(VIB, 'submit_vib_next_batch.sh'), """#!/bin/bash
set -e
cap="${1:-1}"
submitted=0
while IFS=$'\\t' read -r site intermediate source_project vib_project atoms rel status; do
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
  awk -F'\\t' -v OFS='\\t' -v r="$rel" -v jid="$jobid" 'NR==1 {print; next} $6==r && $7=="candidate_not_submitted" {$7="submitted_"jid} {print}' vib_manifest.tsv > "$tmp"
  mv "$tmp" vib_manifest.tsv
  submitted=$((submitted+1))
done < vib_manifest.tsv
echo "Submitted $submitted; active cap $cap."
""")
    os.chmod(os.path.join(VIB, 'submit_vib_next_batch.sh'), 0o755)
    if not os.path.exists(os.path.join(VIB, 'submitted_vib_jobs.tsv')):
        write(os.path.join(VIB, 'submitted_vib_jobs.tsv'),
              'time\tjobid\tsite\tintermediate\tvib_project\tstatus\n')
    print('prepared_vib_tasks', prepared)
    print('vib_dir', VIB)


if __name__ == '__main__':
    main()
