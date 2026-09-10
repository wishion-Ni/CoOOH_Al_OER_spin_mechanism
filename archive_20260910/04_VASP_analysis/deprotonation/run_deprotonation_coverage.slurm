#!/bin/bash
#SBATCH --job-name=S13_dep_cov
#SBATCH --nodes=1
#SBATCH --ntasks=40
#SBATCH --partition=n40
#SBATCH --array=0-9%5
#SBATCH --output=deprotonation_%A_%a.stdout
#SBATCH --error=deprotonation_%A_%a.stderr

set -eo pipefail
ROOT_DIR=${SLURM_SUBMIT_DIR:?SLURM_SUBMIT_DIR is not set}
line=$(awk -F '	' -v task="$SLURM_ARRAY_TASK_ID" 'NR>1 && $1==task {print; exit}' "$ROOT_DIR/coverage_manifest.tsv")
test -n "$line"
relative_dir=$(printf '%s
' "$line" | awk -F '	' '{print $4}')
WORK_DIR="$ROOT_DIR/$relative_dir"
test -s "$WORK_DIR/POSCAR"
test -s "$WORK_DIR/INCAR"
test -s "$WORK_DIR/KPOINTS"
test -s "$WORK_DIR/POTCAR"

if [ -s "$WORK_DIR/OUTCAR" ] &&    grep -q "reached required accuracy - stopping structural energy minimisation" "$WORK_DIR/OUTCAR" &&    grep -q "General timing and accounting informations" "$WORK_DIR/OUTCAR"; then
  echo "Already valid: $WORK_DIR"
  exit 0
fi

printf '%s	%s	%s
' "$SLURM_ARRAY_JOB_ID" "$SLURM_ARRAY_TASK_ID" "$(date -Is)" > "$WORK_DIR/submission.tsv"
cd "$WORK_DIR"
VASP_HOME=/apps/vasp/6.3.0_vtst_optcell_vaspsol/O3
if [ -f "$HOME/intel/oneapi/setvars.sh" ]; then
  source "$HOME/intel/oneapi/setvars.sh" --force
fi
export LD_LIBRARY_PATH="$HOME/intel/oneapi/mkl/latest/lib/intel64:$HOME/intel/oneapi/compiler/latest/linux/compiler/lib/intel64_lin:${LD_LIBRARY_PATH:-}"
ulimit -s unlimited
"$HOME/intel/oneapi/mpi/2021.11/bin/mpirun" -n "$SLURM_NTASKS" "$VASP_HOME/vasp_std" > vasp.out 2>&1
