#!/bin/bash
#SBATCH --job-name=AlOH_preSCF_R1
#SBATCH --nodes=1
#SBATCH --ntasks=40
#SBATCH --partition=n40
#SBATCH --output=aloh_recovery_%j.stdout
#SBATCH --error=aloh_recovery_%j.stderr

set -eo pipefail

ROOT_DIR=${SLURM_SUBMIT_DIR:?SLURM_SUBMIT_DIR is not set}
SOURCE_DIR="$ROOT_DIR/electronic_preconverge/Al16_adjacent/OH"
WORK_DIR="$ROOT_DIR/electronic_preconverge_recovery/Al16_adjacent/OH"

if grep -q "aborting loop because EDIFF is reached" "$SOURCE_DIR/OUTCAR" && \
   grep -q "General timing and accounting informations" "$SOURCE_DIR/OUTCAR"; then
  echo "Original Al16/OH preconvergence is valid; recovery is not needed."
  exit 0
fi

grep -q "General timing and accounting informations" "$SOURCE_DIR/OUTCAR"
if grep -Eqi "VERY BAD NEWS|ZBRENT|BRMIX: very serious problems|segmentation fault|FORTRAN STOP|MPI_ABORT" "$SOURCE_DIR/OUTCAR" "$SOURCE_DIR/vasp.out"; then
  echo "Fatal signature found; refusing automatic recovery." >&2
  exit 3
fi

if [ -f "$WORK_DIR/OUTCAR" ] && grep -q "General timing and accounting informations" "$WORK_DIR/OUTCAR"; then
  echo "Recovery already complete: $WORK_DIR"
  exit 0
fi

mkdir -p "$WORK_DIR"
for file in KPOINTS POTCAR CHGCAR WAVECAR; do
  test -s "$SOURCE_DIR/$file"
  cp --reflink=auto "$SOURCE_DIR/$file" "$WORK_DIR/$file"
done
test -s "$SOURCE_DIR/CONTCAR"
cp "$SOURCE_DIR/CONTCAR" "$WORK_DIR/POSCAR"

awk '
BEGIN {
  replacement["SYSTEM"] = "SYSTEM = corrected preconverge Al16_adjacent/OH recovery 1"
  replacement["ISTART"] = "ISTART = 1"
  replacement["ICHARG"] = "ICHARG = 1"
  replacement["ALGO"] = "ALGO = Normal"
  replacement["NELM"] = "NELM = 160"
  replacement["NELMIN"] = "NELMIN = 8"
  replacement["NELMDL"] = "NELMDL = -8"
  replacement["AMIX"] = "AMIX = 0.10"
  replacement["BMIX"] = "BMIX = 0.0001"
  replacement["AMIX_MAG"] = "AMIX_MAG = 0.40"
  replacement["BMIX_MAG"] = "BMIX_MAG = 0.0001"
}
{
  key = $1
  if (key in replacement) {
    if (!seen[key]) print replacement[key]
    seen[key] = 1
  } else {
    print
  }
}
' "$SOURCE_DIR/INCAR" > "$WORK_DIR/INCAR"

printf '%s\t%s\t%s\n' "$SLURM_JOB_ID" "Al16_adjacent/OH recovery 1" "$(date -Is)" > "$WORK_DIR/submission.tsv"

cd "$WORK_DIR"
VASP_HOME=/apps/vasp/6.3.0_vtst_optcell_vaspsol/O3
if [ -f "$HOME/intel/oneapi/setvars.sh" ]; then
  source "$HOME/intel/oneapi/setvars.sh" --force
fi
export LD_LIBRARY_PATH="$HOME/intel/oneapi/mkl/latest/lib/intel64:$HOME/intel/oneapi/compiler/latest/linux/compiler/lib/intel64_lin:${LD_LIBRARY_PATH:-}"
ulimit -s unlimited
"$HOME/intel/oneapi/mpi/2021.11/bin/mpirun" -n "$SLURM_NTASKS" "$VASP_HOME/vasp_std" > vasp.out 2>&1
