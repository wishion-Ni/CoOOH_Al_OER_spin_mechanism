#!/bin/bash
#SBATCH --job-name=cohp_bare_dry
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --partition=n28
#SBATCH --time=12:00:00
#SBATCH --array=0-1%1
#SBATCH --output=array_%A_%a.stdout
#SBATCH --error=array_%A_%a.stderr

set -eu

ROOT_DIR=${SLURM_SUBMIT_DIR:?SLURM_SUBMIT_DIR is not set}
CASE=$(sed -n "$((SLURM_ARRAY_TASK_ID + 1))p" "$ROOT_DIR/jobs.list")
LOBSTER_BIN="$ROOT_DIR/../tools/lobster-5.1.1/lobster-5.1.1"
export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-8}

cd "$ROOT_DIR/$CASE"

if [ -f BLOCKED_REASON.txt ]; then
  cat BLOCKED_REASON.txt >&2
  exit 2
fi

if [ ! -x "$LOBSTER_BIN" ]; then
  echo "BLOCKED: LOBSTER binary is missing or not executable: $LOBSTER_BIN" >&2
  exit 3
fi

for file in INCAR KPOINTS POSCAR CONTCAR POTCAR OUTCAR WAVECAR vasprun.xml lobsterin; do
  if [ ! -s "$file" ]; then
    echo "BLOCKED: missing $file in $CASE" >&2
    exit 4
  fi
done

"$LOBSTER_BIN"
grep -qi "finished" lobsterout
