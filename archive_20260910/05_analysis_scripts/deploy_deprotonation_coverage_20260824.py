from __future__ import annotations

import importlib.util
import posixpath
import shlex
from pathlib import Path, PurePosixPath


LOCAL_ROOT = Path(__file__).resolve().parent
INPUT_ROOT = LOCAL_ROOT / "pdos_oh_o_inputs_20260824"
STAGING = LOCAL_ROOT / "deprotonation_coverage_inputs_20260824"
REMOTE_ROOT = PurePosixPath("/home/ftfan/ncw")
REMOTE_PROJECT = PurePosixPath(
    "/home/ftfan/ncw/sfs/CoOH/cp2k/Al16/oer/"
    "spin_config_scan_site03_5OH_current_20260714/"
    "vasp_jacs6c06054_reconstructed_exact_Al16_3x2_20260809/"
    "electronic_structure_al_contribution_20260818"
)
REMOTE_OUTPUT = REMOTE_PROJECT / "deprotonation_potential_s13_coverage_20260824"
REMOTE_FORMAL = REMOTE_PROJECT / "cohp_oh_o_corrected_20260820"

# Snake path through the six symmetry-related terminal OH groups. The first
# entry is the already validated active-site deprotonation in the O formal.
DEPROTONATION_H_INDICES = (204, 202, 199, 200, 203, 201)
BRANCHES = {
    "undoped_control": "undoped_OH",
    "Al16_adjacent": "Al16_OH",
}


def load_runner():
    script = (
        Path(__file__).resolve().parents[1]
        / ".codex/skills/ftfan-ncw-ssh/scripts/ssh_ncw.py"
    )
    spec = importlib.util.spec_from_file_location("ftfan_ncw_ssh", script)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load SSH runner: {script}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_poscar(path: Path):
    lines = path.read_text(encoding="ascii").splitlines()
    scale = lines[1]
    lattice = lines[2:5]
    species = lines[5].split()
    counts = [int(value) for value in lines[6].split()]
    cursor = 7
    selective = False
    if lines[cursor].lower().startswith("s"):
        selective = True
        cursor += 1
    mode = lines[cursor]
    cursor += 1
    atoms = []
    for symbol, count in zip(species, counts):
        for _ in range(count):
            atoms.append((symbol, lines[cursor]))
            cursor += 1
    return scale, lattice, species, selective, mode, atoms


def write_poscar(source: Path, target: Path, title: str, removed_global_indices: set[int]) -> list[tuple[str, str]]:
    scale, lattice, species, selective, mode, atoms = read_poscar(source)
    kept = [atom for index, atom in enumerate(atoms, 1) if index not in removed_global_indices]
    counts = [sum(symbol == wanted for symbol, _ in kept) for wanted in species]
    lines = [title, scale, *lattice, "  " + "  ".join(species),
             "  " + "  ".join(str(value) for value in counts)]
    if selective:
        lines.append("Selective dynamics")
    lines.append(mode)
    for symbol in species:
        lines.extend(coords for atom_symbol, coords in kept if atom_symbol == symbol)
    target.write_bytes(("\n".join(lines) + "\n").encode("ascii"))
    return kept


def write_incar(target: Path, title: str, atoms: list[tuple[str, str]]) -> None:
    symbols = [symbol for symbol, _ in atoms]
    unique = []
    for symbol in symbols:
        if symbol not in unique:
            unique.append(symbol)
    magmom = ["3.0" if symbol == "Co" else "0.0" for symbol in symbols]
    ldau_l = ["2" if symbol == "Co" else "-1" for symbol in unique]
    ldau_u = ["4.5" if symbol == "Co" else "0" for symbol in unique]
    text = f"""SYSTEM = {title}
ISTART = 0
ICHARG = 2
ISPIN = 2
MAGMOM = {' '.join(magmom)}
LDAU = .TRUE.
LDAUTYPE = 2
LDAUL = {' '.join(ldau_l)}
LDAUU = {' '.join(ldau_u)}
LDAUJ = {' '.join('0' for _ in unique)}
LMAXMIX = 4
GGA = PE
IVDW = 11
ENCUT = 520
PREC = Accurate
EDIFF = 1E-6
NELM = 300
NELMIN = 8
ALGO = Normal
ISMEAR = 1
SIGMA = 0.20
IBRION = 2
NSW = 360
ISIF = 2
EDIFFG = -0.02
LREAL = .FALSE.
ADDGRID = .TRUE.
LASPH = .TRUE.
LWAVE = .TRUE.
LCHARG = .TRUE.
ISYM = 0
NCORE = 4
"""
    target.write_bytes(text.encode("ascii"))


def prepare_local() -> list[tuple[int, str, int, Path]]:
    STAGING.mkdir(exist_ok=True)
    jobs = []
    task = 0
    for branch, local_case in BRANCHES.items():
        source = INPUT_ROOT / local_case / "POSCAR"
        for n_deprotonated in range(2, 7):
            relative = Path(branch) / f"Ocount_{n_deprotonated:02d}_of_06"
            case_dir = STAGING / relative
            case_dir.mkdir(parents=True, exist_ok=True)
            removed = set(DEPROTONATION_H_INDICES[:n_deprotonated])
            title = f"S13-style {branch} terminal OH deprotonation {n_deprotonated}/6"
            atoms = write_poscar(source, case_dir / "POSCAR", title, removed)
            write_incar(case_dir / "INCAR", title, atoms)
            jobs.append((task, branch, n_deprotonated, relative))
            task += 1
    manifest = STAGING / "coverage_manifest.tsv"
    with manifest.open("w", encoding="ascii", newline="\n") as handle:
        handle.write("task\tbranch\tn_deprotonated\trelative_dir\tremoved_H_indices\n")
        for task, branch, n_deprotonated, relative in jobs:
            removed = ",".join(str(value) for value in DEPROTONATION_H_INDICES[:n_deprotonated])
            handle.write(f"{task}\t{branch}\t{n_deprotonated}\t{relative.as_posix()}\t{removed}\n")
    slurm = STAGING / "run_deprotonation_coverage.slurm"
    slurm.write_bytes("""#!/bin/bash
#SBATCH --job-name=S13_dep_cov
#SBATCH --nodes=1
#SBATCH --ntasks=40
#SBATCH --partition=n40
#SBATCH --array=0-9%5
#SBATCH --output=deprotonation_%A_%a.stdout
#SBATCH --error=deprotonation_%A_%a.stderr

set -eo pipefail
ROOT_DIR=${SLURM_SUBMIT_DIR:?SLURM_SUBMIT_DIR is not set}
line=$(awk -F '\t' -v task="$SLURM_ARRAY_TASK_ID" 'NR>1 && $1==task {print; exit}' "$ROOT_DIR/coverage_manifest.tsv")
test -n "$line"
relative_dir=$(printf '%s\n' "$line" | awk -F '\t' '{print $4}')
WORK_DIR="$ROOT_DIR/$relative_dir"
test -s "$WORK_DIR/POSCAR"
test -s "$WORK_DIR/INCAR"
test -s "$WORK_DIR/KPOINTS"
test -s "$WORK_DIR/POTCAR"

if [ -s "$WORK_DIR/OUTCAR" ] && \
   grep -q "reached required accuracy - stopping structural energy minimisation" "$WORK_DIR/OUTCAR" && \
   grep -q "General timing and accounting informations" "$WORK_DIR/OUTCAR"; then
  echo "Already valid: $WORK_DIR"
  exit 0
fi

printf '%s\t%s\t%s\n' "$SLURM_ARRAY_JOB_ID" "$SLURM_ARRAY_TASK_ID" "$(date -Is)" > "$WORK_DIR/submission.tsv"
cd "$WORK_DIR"
VASP_HOME=/apps/vasp/6.3.0_vtst_optcell_vaspsol/O3
if [ -f "$HOME/intel/oneapi/setvars.sh" ]; then
  source "$HOME/intel/oneapi/setvars.sh" --force
fi
export LD_LIBRARY_PATH="$HOME/intel/oneapi/mkl/latest/lib/intel64:$HOME/intel/oneapi/compiler/latest/linux/compiler/lib/intel64_lin:${LD_LIBRARY_PATH:-}"
ulimit -s unlimited
"$HOME/intel/oneapi/mpi/2021.11/bin/mpirun" -n "$SLURM_NTASKS" "$VASP_HOME/vasp_std" > vasp.out 2>&1
""".encode("ascii"))
    return jobs


def mkdir_sftp(sftp, path: PurePosixPath) -> None:
    parts = path.parts
    current = PurePosixPath(parts[0])
    for part in parts[1:]:
        current /= part
        try:
            sftp.stat(str(current))
        except OSError:
            sftp.mkdir(str(current))


def ensure_inside_root(path: PurePosixPath) -> None:
    if path != REMOTE_ROOT and REMOTE_ROOT not in path.parents:
        raise RuntimeError(f"Remote path escapes allowed root: {path}")


def run_remote(client, command: str) -> str:
    stdin, stdout, stderr = client.exec_command(command)
    out = stdout.read().decode(errors="replace")
    err = stderr.read().decode(errors="replace")
    code = stdout.channel.recv_exit_status()
    if code:
        raise RuntimeError(f"Remote command failed ({code}): {command}\n{out}\n{err}")
    return out.strip()


def main() -> None:
    jobs = prepare_local()
    runner = load_runner()
    paramiko = runner.ensure_paramiko()
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        hostname=runner.HOST,
        port=runner.PORT,
        username=runner.USER,
        password=runner.load_password(),
        timeout=15,
        banner_timeout=15,
        auth_timeout=60,
        look_for_keys=False,
        allow_agent=False,
    )
    try:
        sftp = client.open_sftp()
        ensure_inside_root(REMOTE_OUTPUT)
        mkdir_sftp(sftp, REMOTE_OUTPUT)
        for filename in ("coverage_manifest.tsv", "run_deprotonation_coverage.slurm"):
            sftp.put(str(STAGING / filename), str(REMOTE_OUTPUT / filename))
        for _, branch, _, relative in jobs:
            remote_dir = REMOTE_OUTPUT / PurePosixPath(relative.as_posix())
            ensure_inside_root(remote_dir)
            mkdir_sftp(sftp, remote_dir)
            local_dir = STAGING / relative
            for filename in ("POSCAR", "INCAR"):
                sftp.put(str(local_dir / filename), str(remote_dir / filename))
            source_dir = REMOTE_FORMAL / branch / "OH"
            for filename in ("KPOINTS", "POTCAR"):
                link = remote_dir / filename
                target = source_dir / filename
                ensure_inside_root(target)
                try:
                    sftp.lstat(str(link))
                except OSError:
                    sftp.symlink(str(target), str(link))

        active = run_remote(
            client,
            "squeue -h -u ftfan -o '%A %j' | awk '$2==\"S13_dep_cov\" {print $1}' | sort -u",
        )
        if active:
            print(f"Existing active array: {active}")
            return
        submit_dir = shlex.quote(str(REMOTE_OUTPUT))
        output = run_remote(client, f"cd {submit_dir} && sbatch run_deprotonation_coverage.slurm")
        print(output)
    finally:
        client.close()


if __name__ == "__main__":
    main()
