from __future__ import print_function

import os
import shutil


ROOT = "sfs/CoOH/cp2k/Al16/oer/spin_config_scan_site03_5OH_current_20260714/vasp_jacs6c06054_reconstructed_exact_Al16_3x2_20260809"
OUTPUT = os.path.join(ROOT, "electronic_preconverge_20260810")
JOBS = (
    "Al16_adjacent/bare",
    "undoped_control/bare",
    "Al16_adjacent/OH",
    "undoped_control/OH",
    "Al16_adjacent/O",
    "undoped_control/O",
    "Al16_adjacent/OOH_o03",
    "undoped_control/OOH_o03",
)


def update_incar(source, target, label):
    replacements = {
        "SYSTEM": "SYSTEM = preconverge " + label,
        "ISTART": "ISTART = 0",
        "ICHARG": "ICHARG = 2",
        "EDIFF": "EDIFF = 1E-4",
        "NELM": "NELM = 160",
        "ALGO": "ALGO = Fast",
        "IBRION": "IBRION = -1",
        "NSW": "NSW = 0",
        "LREAL": "LREAL = Auto",
        "LWAVE": "LWAVE = .TRUE.",
        "LCHARG": "LCHARG = .TRUE.",
    }
    output = []
    seen = set()
    for line in open(source):
        stripped = line.strip()
        key = stripped.split("=", 1)[0].strip() if "=" in stripped else ""
        if key in replacements:
            output.append(replacements[key] + "\n")
            seen.add(key)
        else:
            output.append(line)
    for key in replacements:
        if key not in seen:
            output.append(replacements[key] + "\n")
    output.extend((
        "KPAR = 2\n",
        "NELMDL = -12\n",
        "AMIX = 0.20\n",
        "BMIX = 0.0001\n",
        "AMIX_MAG = 0.80\n",
        "BMIX_MAG = 0.0001\n",
    ))
    open(target, "w").writelines(output)


if not os.path.isdir(OUTPUT):
    os.makedirs(OUTPUT)

for job in JOBS:
    source = os.path.join(ROOT, job)
    target = os.path.join(OUTPUT, job)
    if not os.path.isdir(target):
        os.makedirs(target)
    for name in ("POSCAR", "POTCAR", "KPOINTS"):
        shutil.copyfile(os.path.join(source, name), os.path.join(target, name))
    update_incar(os.path.join(source, "INCAR"), os.path.join(target, "INCAR"), job)

open(os.path.join(OUTPUT, "jobs.list"), "w").write("\n".join(JOBS) + "\n")
open(os.path.join(OUTPUT, "METHOD.txt"), "w").write(
    "Electronic preconvergence after array 110958 failed to complete its first SCF in 22 hours.\n"
    "Geometry and 2x2x1 k mesh are unchanged. This stage uses ALGO=Fast, LREAL=Auto, EDIFF=1e-4, KPAR=2, delayed mixing, and magnetic DFT+U mixing.\n"
    "It is not used for final energies or forces. Converged WAVECAR/CHGCAR seed the original strict ALGO=Normal, LREAL=FALSE, EDIFF=1e-6 relaxation.\n"
)

slurm = """#!/bin/bash
#SBATCH --job-name=Al16_preSCF
#SBATCH --nodes=1
#SBATCH --ntasks=40
#SBATCH --partition=n40
#SBATCH --array=0-7%2
#SBATCH --output=array_%A_%a.stdout
#SBATCH --error=array_%A_%a.stderr

set -eo pipefail
WORKDIR="$(sed -n "$((SLURM_ARRAY_TASK_ID + 1))p" jobs.list)"
cd "$WORKDIR"
if [ -f OUTCAR ] && grep -q "General timing and accounting informations" OUTCAR; then
  echo "Already complete: $WORKDIR"
  exit 0
fi
VASP_HOME=/apps/vasp/6.3.0_vtst_optcell_vaspsol/O3
if [ -f "$HOME/intel/oneapi/setvars.sh" ]; then
  source "$HOME/intel/oneapi/setvars.sh" --force
fi
export LD_LIBRARY_PATH="$HOME/intel/oneapi/mkl/latest/lib/intel64:$HOME/intel/oneapi/compiler/latest/linux/compiler/lib/intel64_lin:${LD_LIBRARY_PATH:-}"
ulimit -s unlimited
"$HOME/intel/oneapi/mpi/2021.11/bin/mpirun" -n "$SLURM_NTASKS" "$VASP_HOME/vasp_std" > vasp.out 2>&1
"""
open(os.path.join(OUTPUT, "vasp_array.slurm"), "w").write(slurm)

open(os.path.join(OUTPUT, "submission_manifest.tsv"), "w").write(
    "task\tbranch\tstate\tpurpose\n" +
    "\n".join("%d\t%s\t%s\telectronic_preconvergence_only" % (
        index, job.split("/")[0], job.split("/")[1]) for index, job in enumerate(JOBS)) + "\n"
)

print("OUTPUT", OUTPUT)
print("JOBS", len(JOBS))
