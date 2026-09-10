from __future__ import annotations

import importlib.util
import posixpath
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / ".codex/skills/ftfan-ncw-ssh/scripts/ssh_ncw.py"
spec = importlib.util.spec_from_file_location("ssh_ncw", HELPER)
ssh_ncw = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(ssh_ncw)

WORK = (
    "sfs/CoOH/cp2k/Al16/oer/spin_config_scan_site03_5OH_current_20260714/"
    "vasp_jacs6c06054_reconstructed_exact_Al16_3x2_20260809"
)
PRE = posixpath.join(WORK, "electronic_preconverge_20260810")
BRANCH = "undoped_control"
STATE = "O"
TASK = 5
SOURCE_JOB = "110991_5"
SOURCE = posixpath.join(PRE, f"{BRANCH}/{STATE}")
DEST = posixpath.join(WORK, f"{BRANCH}/{STATE}")


def read_text(sftp, rel: str) -> str:
    with sftp.open(posixpath.join(ssh_ncw.REMOTE_ROOT, rel), "r") as handle:
        return handle.read().decode(errors="replace")


def write_text(sftp, rel: str, text: str) -> None:
    with sftp.open(posixpath.join(ssh_ncw.REMOTE_ROOT, rel), "w") as handle:
        handle.write(text)


def append_unique(sftp, rel: str, line: str, marker: str) -> None:
    text = read_text(sftp, rel)
    if marker not in text:
        write_text(sftp, rel, text.rstrip("\n") + "\n" + line + "\n")


def run(client, command: str) -> str:
    _, stdout, stderr = client.exec_command(f"cd {ssh_ncw.REMOTE_ROOT} && {command}")
    code = stdout.channel.recv_exit_status()
    output = stdout.read().decode()
    error = stderr.read().decode()
    if code:
        raise RuntimeError(error or output)
    return output


def main() -> None:
    paramiko = ssh_ncw.ensure_paramiko()
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        hostname=ssh_ncw.HOST,
        port=ssh_ncw.PORT,
        username=ssh_ncw.USER,
        password=ssh_ncw.load_password(),
        look_for_keys=False,
        allow_agent=False,
    )
    try:
        sftp = client.open_sftp()
        outcar = read_text(sftp, posixpath.join(SOURCE, "OUTCAR"))
        if "aborting loop because EDIFF is reached" not in outcar:
            raise RuntimeError(f"{SOURCE_JOB} did not reach EDIFF")
        if "General timing and accounting informations" not in outcar:
            raise RuntimeError(f"{SOURCE_JOB} lacks normal VASP termination")

        queue = run(client, "squeue -u ftfan -h -o '%i %j %T'")
        if re.search(r"\bCtrl_strict_O\b", queue):
            raise RuntimeError("A control O strict job is already active")

        for name in ("WAVECAR", "CHGCAR"):
            source = posixpath.join(SOURCE, name)
            dest = posixpath.join(DEST, name)
            run(client, f"cp {source} {dest}")

        incar_rel = posixpath.join(DEST, "INCAR")
        incar = read_text(sftp, incar_rel)
        incar = re.sub(r"(?m)^ISTART\s*=.*$", "ISTART = 1", incar)
        incar = re.sub(r"(?m)^ICHARG\s*=.*$", "ICHARG = 1", incar)
        write_text(sftp, incar_rel, incar)

        wave_bytes = sftp.stat(posixpath.join(ssh_ncw.REMOTE_ROOT, SOURCE, "WAVECAR")).st_size
        charge_bytes = sftp.stat(posixpath.join(ssh_ncw.REMOTE_ROOT, SOURCE, "CHGCAR")).st_size
        append_unique(
            sftp,
            posixpath.join(PRE, "validation_status.tsv"),
            f"{SOURCE_JOB}\t{BRANCH}\t{STATE}\tvalid_seed_only\tyes\tnone\t{wave_bytes}\t{charge_bytes}\telectronic_preconvergence;converged_RMM139;not_scientific_energy",
            f"{SOURCE_JOB}\t{BRANCH}\t{STATE}\t",
        )

        submit = run(client, f"cd {WORK} && sbatch --job-name=Ctrl_strict_O --array={TASK}%1 vasp_array.slurm")
        match = re.search(r"Submitted batch job (\d+)", submit)
        if not match:
            raise RuntimeError(f"Cannot parse sbatch output: {submit}")
        job_id = match.group(1)

        append_unique(
            sftp,
            posixpath.join(WORK, "submission_manifest.tsv"),
            f"{job_id}\t{TASK}\t{BRANCH}\t{STATE}\tn40\t40\tstrict_restart_from_valid_{SOURCE_JOB}_seed",
            f"{job_id}\t{TASK}\t{BRANCH}\t{STATE}\t",
        )
        append_unique(
            sftp,
            posixpath.join(WORK, "scheduler_manifest.tsv"),
            f"2026-08-13\tsubmission\t{job_id}_{TASK}\tn40\t40\t1\tstrict_control_O_restart;seed_from_valid_{SOURCE_JOB};ALGO_Normal;LREAL_FALSE;EDIFF_1e-6;no_duplicates",
            f"\tsubmission\t{job_id}_{TASK}\t",
        )
        print(job_id)
    finally:
        client.close()


if __name__ == "__main__":
    main()
