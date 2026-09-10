#!/bin/bash
#SBATCH --job-name=OH_O_COHPC
#SBATCH --nodes=1
#SBATCH --ntasks=40
#SBATCH --partition=n40
#SBATCH --output=cohp_static_%j.stdout
#SBATCH --error=cohp_static_%j.stderr

set -eo pipefail

: "${CASE:?CASE must be Al16_adjacent/OH, Al16_adjacent/O, undoped_control/OH, or undoped_control/O}"
: "${NBANDS:?NBANDS must be provided}"
SOURCE_SUBROOT=${SOURCE_SUBROOT:-electronic_preconverge}

case "$CASE" in
  Al16_adjacent/OH|Al16_adjacent/O|undoped_control/OH|undoped_control/O) ;;
  *) echo "Rejected CASE: $CASE" >&2; exit 2 ;;
esac

ROOT_DIR=${SLURM_SUBMIT_DIR:?SLURM_SUBMIT_DIR is not set}
RECON_ROOT=$(dirname "$ROOT_DIR")
SOURCE_DIR="$RECON_ROOT/corrected_adsorbates_20260819/$SOURCE_SUBROOT/$CASE"
WORK_DIR="$ROOT_DIR/cohp_oh_o_corrected_20260820/$CASE"

grep -q "aborting loop because EDIFF is reached" "$SOURCE_DIR/OUTCAR"
grep -q "General timing and accounting informations" "$SOURCE_DIR/OUTCAR"

if [ -f "$WORK_DIR/OUTCAR" ] && grep -q "General timing and accounting informations" "$WORK_DIR/OUTCAR"; then
  echo "Already complete: $WORK_DIR"
  exit 0
fi

mkdir -p "$WORK_DIR"
copy_if_needed() {
  local source_file=$1
  local target_file=$2
  test -s "$source_file"
  if [ -s "$target_file" ] && [ "$(stat -c %s "$source_file")" = "$(stat -c %s "$target_file")" ]; then
    echo "Reusing complete copy: $target_file"
  else
    cp --reflink=auto "$source_file" "$target_file"
  fi
}
for file in KPOINTS POTCAR CHGCAR; do
  copy_if_needed "$SOURCE_DIR/$file" "$WORK_DIR/$file"
done
test -s "$SOURCE_DIR/CONTCAR"
cp "$SOURCE_DIR/CONTCAR" "$WORK_DIR/POSCAR"

awk -v syslabel="corrected COHP/Bader $CASE" -v nbands="$NBANDS" '
BEGIN {
  replacement["SYSTEM"] = "SYSTEM = " syslabel
  replacement["ISTART"] = "ISTART = 0"
  replacement["ICHARG"] = "ICHARG = 1"
  replacement["NBANDS"] = "NBANDS = " nbands
  replacement["ISYM"] = "ISYM = -1"
  replacement["LREAL"] = "LREAL = .FALSE."
  replacement["LWAVE"] = "LWAVE = .TRUE."
  replacement["LCHARG"] = "LCHARG = .TRUE."
  replacement["LAECHG"] = "LAECHG = .TRUE."
  replacement["LORBIT"] = "LORBIT = 11"
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
END {
  order[1]="NBANDS"; order[2]="LAECHG"; order[3]="LORBIT"
  for (i=1; i<=3; i++) if (!seen[order[i]]) print replacement[order[i]]
}
' "$SOURCE_DIR/INCAR" > "$WORK_DIR/INCAR"

printf '%s\t%s\t%s\t%s\n' "$SLURM_JOB_ID" "$CASE" "$NBANDS" "$(date -Is)" > "$WORK_DIR/submission.tsv"

cd "$WORK_DIR"
VASP_HOME=/apps/vasp/6.3.0_vtst_optcell_vaspsol/O3
if [ -f "$HOME/intel/oneapi/setvars.sh" ]; then
  source "$HOME/intel/oneapi/setvars.sh" --force
fi
export LD_LIBRARY_PATH="$HOME/intel/oneapi/mkl/latest/lib/intel64:$HOME/intel/oneapi/compiler/latest/linux/compiler/lib/intel64_lin:${LD_LIBRARY_PATH:-}"
ulimit -s unlimited
"$HOME/intel/oneapi/mpi/2021.11/bin/mpirun" -n "$SLURM_NTASKS" "$VASP_HOME/vasp_std" > vasp.out 2>&1
