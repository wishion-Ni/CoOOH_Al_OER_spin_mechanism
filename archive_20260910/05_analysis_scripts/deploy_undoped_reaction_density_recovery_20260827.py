#!/usr/bin/env python3
"""Deploy the single-node undoped reaction-density convergence recovery."""

from __future__ import annotations

import importlib.util
import re
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SSH_HELPER = ROOT / ".codex" / "skills" / "ftfan-ncw-ssh" / "scripts" / "ssh_ncw.py"
BASE = (
    "sfs/CoOH/cp2k/Al16/oer/spin_config_scan_site03_5OH_current_20260714/"
    "vasp_jacs6c06054_reconstructed_exact_Al16_3x2_20260809/"
    "electronic_structure_al_contribution_20260818"
)
REACTION_ROOT = f"{BASE}/reaction_density_oh_to_o_same_geometry_20260823"
SOURCE = f"{REACTION_ROOT}/undoped_control/O_at_OHgeom"
RECOVERY = f"{REACTION_ROOT}/undoped_control/O_at_OHgeom_recovery_normal_20260827"
OLD_ARRAY_TASK = "111338_0"


def load_ssh_helper():
    spec = importlib.util.spec_from_file_location("ftfan_ncw_ssh", SSH_HELPER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {SSH_HELPER}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ssh_helper = load_ssh_helper()
paramiko = ssh_helper.ensure_paramiko()


def run(client, command: str, check: bool = True) -> tuple[int, str, str]:
    remote = f"cd {ssh_helper.REMOTE_ROOT!r} && {command}"
    _stdin, stdout, stderr = client.exec_command(remote, timeout=None)
    out = stdout.read().decode(errors="replace")
    err = stderr.read().decode(errors="replace")
    code = stdout.channel.recv_exit_status()
    if check and code != 0:
        raise RuntimeError(f"Remote command failed ({code}): {command}\n{out}{err}")
    return code, out, err


def update_incar(text: str) -> str:
    replacements = {
        "SYSTEM": "reaction density undoped_control *O@OHgeom recovery Normal",
        "ALGO": "Normal",
        "NELM": "160",
        "NELMIN": "8",
        "NELMDL": "-8",
        "AMIX": "0.10",
        "BMIX": "0.0001",
        "AMIX_MAG": "0.40",
        "BMIX_MAG": "0.0001",
    }
    found: set[str] = set()
    lines: list[str] = []
    for line in text.splitlines():
        match = re.match(r"^(\s*)([A-Za-z_]+)(\s*=\s*)(.*)$", line)
        if match and match.group(2).upper() in replacements:
            key = match.group(2).upper()
            lines.append(f"{match.group(1)}{match.group(2)}{match.group(3)}{replacements[key]}")
            found.add(key)
        else:
            lines.append(line)
    missing = set(replacements) - found
    if missing:
        raise RuntimeError(f"Missing INCAR keys: {sorted(missing)}")
    return "\n".join(lines) + "\n"


SLURM = f"""#!/bin/bash
#SBATCH --job-name=Rho_u_R1
#SBATCH --nodes=1
#SBATCH --ntasks=40
#SBATCH --partition=n40
#SBATCH --output=slurm-%j.out
#SBATCH --error=slurm-%j.err

set -eo pipefail
cd "$HOME/ncw/{RECOVERY}"

for file in INCAR POSCAR KPOINTS POTCAR CHGCAR; do
    test -s "$file"
done
test "${{SLURM_NNODES}}" -eq 1
test "${{SLURM_NTASKS}}" -eq 40

VASP_HOME=/apps/vasp/6.3.0_vtst_optcell_vaspsol/O3
source "$HOME/intel/oneapi/setvars.sh" --force
export LD_LIBRARY_PATH="$HOME/intel/oneapi/mkl/2024.0/lib:$HOME/intel/oneapi/compiler/2024.0/lib:$HOME/intel/oneapi/mpi/2021.11/lib:${{LD_LIBRARY_PATH:-}}"
ulimit -s unlimited
"$HOME/intel/oneapi/mpi/2021.11/bin/mpirun" -n "$SLURM_NTASKS" "$VASP_HOME/vasp_std" > vasp.out 2>&1
"""


def main() -> None:
    password = ssh_helper.load_password()
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        hostname=ssh_helper.HOST,
        port=ssh_helper.PORT,
        username=ssh_helper.USER,
        password=password,
        timeout=15,
        banner_timeout=15,
        auth_timeout=60,
        look_for_keys=False,
        allow_agent=False,
    )
    try:
        run(
            client,
            f"test -s {SOURCE}/INCAR && test -s {SOURCE}/POSCAR && "
            f"test -s {SOURCE}/KPOINTS && test -s {SOURCE}/POTCAR && "
            f"test -s {SOURCE}/CHGCAR",
        )
        _code, state, _err = run(
            client, f"squeue -j {OLD_ARRAY_TASK} -h -o '%T'", check=False
        )
        old_task_running = state.strip() == "RUNNING"
        if state.strip() not in {"", "RUNNING"}:
            raise RuntimeError(f"Unexpected {OLD_ARRAY_TASK} state: {state.strip()!r}")

        run(client, f"mkdir -p {RECOVERY}")
        run(
            client,
            f"for f in POSCAR KPOINTS POTCAR input_manifest.tsv removed_H204.tsv; do "
            f"if test -e {SOURCE}/$f; then cp -p {SOURCE}/$f {RECOVERY}/$f; fi; done",
        )
        run(client, f"cp --reflink=auto -p {SOURCE}/CHGCAR {RECOVERY}/CHGCAR")

        sftp = client.open_sftp()
        try:
            source_incar_path = f"{ssh_helper.REMOTE_ROOT}/{SOURCE}/INCAR"
            recovery_incar_path = f"{ssh_helper.REMOTE_ROOT}/{RECOVERY}/INCAR"
            with sftp.open(source_incar_path, "r") as handle:
                source_incar = handle.read().decode()
            recovery_incar = update_incar(source_incar)
            with sftp.open(recovery_incar_path, "w") as handle:
                handle.write(recovery_incar)
            with sftp.open(f"{ssh_helper.REMOTE_ROOT}/{RECOVERY}/run_recovery.slurm", "w") as handle:
                handle.write(SLURM)
        finally:
            sftp.close()

        run(
            client,
            f"cmp -s {SOURCE}/POSCAR {RECOVERY}/POSCAR && "
            f"cmp -s {SOURCE}/CHGCAR {RECOVERY}/CHGCAR && "
            f"test -s {RECOVERY}/INCAR && test -s {RECOVERY}/run_recovery.slurm",
        )
        _code, settings, _err = run(
            client,
            f"grep -E '^(ISTART|ICHARG|ALGO|NELM|NELMIN|NELMDL|AMIX|BMIX|AMIX_MAG|BMIX_MAG|NSW|NBANDS|KPAR|NCORE)' {RECOVERY}/INCAR",
        )
        expected = {
            "ISTART = 0",
            "ICHARG = 1",
            "ALGO = Normal",
            "NELM = 160",
            "NELMIN = 8",
            "NELMDL = -8",
            "AMIX = 0.10",
            "BMIX = 0.0001",
            "AMIX_MAG = 0.40",
            "BMIX_MAG = 0.0001",
            "NSW = 0",
            "NBANDS = 1120",
            "KPAR = 2",
            "NCORE = 4",
        }
        actual = {line.strip() for line in settings.splitlines()}
        missing = expected - actual
        if missing:
            raise RuntimeError(f"Recovery INCAR validation failed: {sorted(missing)}")

        if old_task_running:
            run(client, f"scancel {OLD_ARRAY_TASK}")
            for _ in range(30):
                _code, remaining, _err = run(
                    client, f"squeue -j {OLD_ARRAY_TASK} -h -o '%T'", check=False
                )
                if not remaining.strip():
                    break
                time.sleep(2)
            else:
                raise RuntimeError(f"{OLD_ARRAY_TASK} did not leave the queue")

        _code, submit_out, _err = run(
            client, f"cd {RECOVERY} && sbatch --parsable run_recovery.slurm"
        )
        job_id = submit_out.strip().split(";")[0]
        if not job_id.isdigit():
            raise RuntimeError(f"Unexpected sbatch output: {submit_out!r}")

        manifest = (
            "recovery_job_id\t" + job_id + "\n"
            "superseded_array_task\t" + OLD_ARRAY_TASK + "\n"
            "source_directory\t" + SOURCE + "\n"
            "algorithm\tALGO=Normal; NELM=160; NELMDL=-8; AMIX=0.10; AMIX_MAG=0.40\n"
            "geometry_and_density\tPOSCAR and initial CHGCAR byte-identical to source\n"
        )
        sftp = client.open_sftp()
        try:
            with sftp.open(
                f"{ssh_helper.REMOTE_ROOT}/{RECOVERY}/recovery_manifest.tsv", "w"
            ) as handle:
                handle.write(manifest)
        finally:
            sftp.close()

        _code, queue, _err = run(
            client,
            f"squeue -j {job_id} -h -o '%A %T %M %D %C %P %R'",
        )
        print(f"RECOVERY_JOB_ID={job_id}")
        print(settings, end="")
        print(queue, end="")
    finally:
        client.close()


if __name__ == "__main__":
    main()
