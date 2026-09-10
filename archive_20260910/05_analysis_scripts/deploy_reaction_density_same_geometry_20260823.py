from __future__ import annotations

import hashlib
import shutil
import subprocess
from pathlib import Path


ROOT = Path.cwd().resolve()
PROJECT = Path(
    "sfs/CoOH/cp2k/Al16/oer/"
    "spin_config_scan_site03_5OH_current_20260714/"
    "vasp_jacs6c06054_reconstructed_exact_Al16_3x2_20260809"
)
ES_ROOT = PROJECT / "electronic_structure_al_contribution_20260818"
FORMAL_ROOT = ES_ROOT / "cohp_oh_o_corrected_20260820"
WORK_ROOT = ES_ROOT / "reaction_density_oh_to_o_same_geometry_20260823"
CASES = ("undoped_control", "Al16_adjacent")


def safe(path: Path) -> Path:
    resolved = (ROOT / path).resolve() if not path.is_absolute() else path.resolve()
    resolved.relative_to(ROOT)
    return resolved


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def require_valid_vasp(folder: Path) -> None:
    outcar = folder / "OUTCAR"
    if not outcar.is_file():
        raise RuntimeError(f"Missing OUTCAR: {outcar}")
    text = outcar.read_text(errors="replace")
    if "aborting loop because EDIFF is reached" not in text:
        raise RuntimeError(f"EDIFF not reached: {folder}")
    if "General timing and accounting informations" not in text:
        raise RuntimeError(f"No normal VASP termination: {folder}")
    for filename in ("INCAR", "KPOINTS", "POTCAR", "POSCAR", "CHGCAR"):
        path = folder / filename
        if not path.is_file() or path.stat().st_size == 0:
            raise RuntimeError(f"Missing input/restart file: {path}")


def remove_active_h(source: Path, target: Path) -> None:
    lines = source.read_text().splitlines()
    elements = lines[5].split()
    counts = [int(value) for value in lines[6].split()]
    if "H" not in elements:
        raise RuntimeError(f"No H species in {source}")
    if counts[elements.index("H")] != 144:
        raise RuntimeError(f"Expected 144 H atoms in {source}, found {counts}")
    cursor = 7
    selective = lines[cursor].strip().lower().startswith("s")
    if selective:
        cursor += 1
    coordinate_mode = lines[cursor]
    cursor += 1
    natoms = sum(counts)
    coordinates = lines[cursor : cursor + natoms]
    if len(coordinates) != natoms:
        raise RuntimeError(f"Incomplete POSCAR coordinates: {source}")

    first_h = sum(counts[: elements.index("H")])
    removed_zero_based = first_h + counts[elements.index("H")] - 1
    if removed_zero_based != 203:
        raise RuntimeError(f"Expected active H at one-based index 204, got {removed_zero_based + 1}")
    removed = coordinates.pop(removed_zero_based)
    counts[elements.index("H")] -= 1

    output = [
        "reaction density *O at frozen *OH geometry; removed H204",
        *lines[1:6],
        "  " + "  ".join(str(value) for value in counts),
    ]
    if selective:
        output.append(lines[7])
    output.append(coordinate_mode)
    output.extend(coordinates)
    target.write_text("\n".join(output) + "\n")
    (target.parent / "removed_H204.tsv").write_text(
        "one_based_index\tcoordinate_line\n204\t" + removed.strip() + "\n"
    )


def patch_incar(source: Path, target: Path, case: str) -> None:
    replacements = {
        "SYSTEM": f"SYSTEM = reaction density {case} *O@OHgeom",
        "ISTART": "ISTART = 0",
        "ICHARG": "ICHARG = 1",
        "NSW": "NSW = 0",
        "IBRION": "IBRION = -1",
        "LCHARG": "LCHARG = .TRUE.",
        "LWAVE": "LWAVE = .FALSE.",
        "LAECHG": "LAECHG = .FALSE.",
        "ISYM": "ISYM = -1",
        "LREAL": "LREAL = .FALSE.",
        "NBANDS": "NBANDS = 1120",
    }
    seen: set[str] = set()
    output = []
    for line in source.read_text().splitlines():
        stripped = line.strip()
        key = stripped.split("=", 1)[0].strip().upper() if "=" in stripped else ""
        if key in replacements:
            if key not in seen:
                output.append(replacements[key])
                seen.add(key)
        else:
            output.append(line)
    for key, line in replacements.items():
        if key not in seen:
            output.append(line)
    target.write_text("\n".join(output) + "\n")


def copy_reflink(source: Path, target: Path) -> None:
    if target.is_file() and target.stat().st_size == source.stat().st_size:
        return
    subprocess.run(["cp", "--reflink=auto", str(source), str(target)], check=True)


def prepare_case(case: str) -> Path:
    oh = safe(FORMAL_ROOT / case / "OH")
    o = safe(FORMAL_ROOT / case / "O")
    require_valid_vasp(oh)
    require_valid_vasp(o)
    destination = safe(WORK_ROOT / case / "O_at_OHgeom")
    destination.mkdir(parents=True, exist_ok=True)

    remove_active_h(oh / "POSCAR", destination / "POSCAR")
    patch_incar(o / "INCAR", destination / "INCAR", case)
    for filename in ("KPOINTS", "POTCAR"):
        shutil.copy2(o / filename, destination / filename)
    copy_reflink(o / "CHGCAR", destination / "CHGCAR")

    poscar_lines = (destination / "POSCAR").read_text().splitlines()
    expected = [60, 143, 144] if case == "undoped_control" else [50, 10, 143, 144]
    actual = [int(value) for value in poscar_lines[6].split()]
    if actual != expected or sum(actual) != 347:
        raise RuntimeError(f"Bad deprotonated composition for {case}: {actual}")
    if sha256(destination / "POSCAR") == sha256(oh / "POSCAR"):
        raise RuntimeError(f"POSCAR was not changed for {case}")

    manifest = destination / "input_manifest.tsv"
    manifest.write_text(
        "key\tvalue\n"
        f"case\t{case}\n"
        "removed_atom\tH204\n"
        f"source_OH_POSCAR_sha256\t{sha256(oh / 'POSCAR')}\n"
        f"generated_POSCAR_sha256\t{sha256(destination / 'POSCAR')}\n"
        f"source_O_CHGCAR_size\t{(o / 'CHGCAR').stat().st_size}\n"
        f"local_CHGCAR_size\t{(destination / 'CHGCAR').stat().st_size}\n"
        "nodes_per_task\t1\nntasks_per_task\t40\npartition\tn40\n"
    )
    return destination


def completed(folder: Path) -> bool:
    outcar = folder / "OUTCAR"
    if not outcar.is_file():
        return False
    text = outcar.read_text(errors="replace")
    return (
        "aborting loop because EDIFF is reached" in text
        and "General timing and accounting informations" in text
        and (folder / "CHGCAR").stat().st_size > 1_000_000
    )


def active_submission() -> str | None:
    record = WORK_ROOT / "submission.tsv"
    if not record.is_file():
        return None
    fields = record.read_text().strip().split("\t")
    if not fields or not fields[0].isdigit():
        return None
    job_id = fields[0]
    result = subprocess.run(
        ["squeue", "-h", "-j", job_id, "-o", "%A"],
        check=False,
        capture_output=True,
        text=True,
    )
    return job_id if result.stdout.strip() else None


def write_slurm() -> Path:
    script = WORK_ROOT / "run_reaction_density_O_at_OHgeom.slurm"
    project_rel = ES_ROOT.as_posix()
    content = f"""#!/bin/bash
#SBATCH --job-name=Rho_OatOH
#SBATCH --nodes=1
#SBATCH --ntasks=40
#SBATCH --partition=n40
#SBATCH --array=0-1%2
#SBATCH --output=reaction_density_%A_%a.stdout
#SBATCH --error=reaction_density_%A_%a.stderr

set -eo pipefail
cases=(undoped_control Al16_adjacent)
case_name=${{cases[$SLURM_ARRAY_TASK_ID]}}
work={project_rel}/reaction_density_oh_to_o_same_geometry_20260823/$case_name/O_at_OHgeom
test -d "$work"
test -s "$work/POSCAR"
test -s "$work/INCAR"
test -s "$work/KPOINTS"
test -s "$work/POTCAR"
test -s "$work/CHGCAR"

if test -s "$work/OUTCAR" && grep -q 'aborting loop because EDIFF is reached' "$work/OUTCAR" && grep -q 'General timing and accounting informations' "$work/OUTCAR"; then
    echo "Already valid: $work"
    exit 0
fi

cd "$work"
VASP_HOME=/apps/vasp/6.3.0_vtst_optcell_vaspsol/O3
if test -f "$HOME/intel/oneapi/setvars.sh"; then
    source "$HOME/intel/oneapi/setvars.sh" --force
fi
export LD_LIBRARY_PATH="$HOME/intel/oneapi/mkl/latest/lib/intel64:$HOME/intel/oneapi/compiler/latest/linux/compiler/lib/intel64_lin:${{LD_LIBRARY_PATH:-}}"
ulimit -s unlimited
"$HOME/intel/oneapi/mpi/2021.11/bin/mpirun" -n "$SLURM_NTASKS" "$VASP_HOME/vasp_std" > vasp.out 2>&1
"""
    script.write_text(content)
    return script


def main() -> None:
    safe(ES_ROOT)
    WORK_ROOT.mkdir(parents=True, exist_ok=True)
    active = active_submission()
    if active:
        print(f"Existing active array job: {active}")
        return

    destinations = [prepare_case(case) for case in CASES]
    pending = [folder for folder in destinations if not completed(folder)]
    if not pending:
        print("Both reaction-density calculations are already valid")
        return

    script = write_slurm()
    result = subprocess.run(["sbatch", str(script)], check=True, capture_output=True, text=True)
    print(result.stdout.strip())
    job_id = result.stdout.strip().split()[-1]
    (WORK_ROOT / "submission.tsv").write_text(
        f"{job_id}\tarray=0-1%2\tnodes_per_task=1\tntasks_per_task=40\tpartition=n40\n"
    )
    print(f"Prepared: {', '.join(str(folder) for folder in destinations)}")


if __name__ == "__main__":
    main()
