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
STATE = "OOH_o03"
TASK = 7
SOURCE_JOB = "110991_7"
SOURCE = posixpath.join(PRE, f"{BRANCH}/{STATE}")
DEST = posixpath.join(WORK, f"{BRANCH}/{STATE}")


def read_text(sftp, rel: str) -> str:
    with sftp.open(posixpath.join(ssh_ncw.REMOTE_ROOT, rel), "r") as handle:
        return handle.read().decode(errors="replace")


def write_text(sftp, rel: str, content: str) -> None:
    with sftp.open(posixpath.join(ssh_ncw.REMOTE_ROOT, rel), "w") as handle:
        handle.write(content)


def append_unique(sftp, rel: str, line: str, marker: str) -> None:
    content = read_text(sftp, rel)
    if marker not in content:
        write_text(sftp, rel, content.rstrip("\n") + "\n" + line + "\n")


def run(client, command: str) -> str:
    _, stdout, stderr = client.exec_command(
        f"cd {ssh_ncw.REMOTE_ROOT} && {command}"
    )
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
        fatal = re.search(
            r"VERY BAD NEWS|ZBRENT|BRMIX|internal error|FATAL|"
            r"ERROR FEXCP|ERROR RSPHER|ERROR in subspace rotation",
            outcar,
            re.IGNORECASE,
        )
        if fatal:
            raise RuntimeError(f"{SOURCE_JOB} contains fatal signature: {fatal.group(0)}")

        poscar = read_text(sftp, posixpath.join(SOURCE, "POSCAR")).splitlines()
        if poscar[5].split() != ["Co", "H", "O"] or poscar[6].split() != [
            "60",
            "144",
            "145",
        ]:
            raise RuntimeError("Unexpected control OOH composition")

        queue = run(client, "squeue -u ftfan -h -o '%i %j %T'")
        if re.search(r"\bCtrl_strict_OOH\b", queue):
            raise RuntimeError("A control OOH strict job is already active")

        sizes = {}
        for name in ("WAVECAR", "CHGCAR"):
            source = posixpath.join(SOURCE, name)
            sizes[name] = sftp.stat(
                posixpath.join(ssh_ncw.REMOTE_ROOT, source)
            ).st_size
            if sizes[name] == 0:
                raise RuntimeError(f"Empty {name}")
            run(client, f"cp {source} {posixpath.join(DEST, name)}")

        incar_rel = posixpath.join(DEST, "INCAR")
        incar = read_text(sftp, incar_rel)
        incar = re.sub(r"(?m)^ISTART\s*=.*$", "ISTART = 1", incar)
        incar = re.sub(r"(?m)^ICHARG\s*=.*$", "ICHARG = 1", incar)
        write_text(sftp, incar_rel, incar)

        append_unique(
            sftp,
            posixpath.join(PRE, "validation_status.tsv"),
            f"{SOURCE_JOB}\t{BRANCH}\t{STATE}\tvalid_seed_only\tyes\tnone\t"
            f"{sizes['WAVECAR']}\t{sizes['CHGCAR']}\t"
            "electronic_preconvergence;converged_RMM144;not_scientific_energy",
            f"{SOURCE_JOB}\t{BRANCH}\t{STATE}\t",
        )

        submit = run(
            client,
            f"cd {WORK} && sbatch --job-name=Ctrl_strict_OOH "
            f"--partition=n28 --ntasks=28 --array={TASK}%1 vasp_array.slurm",
        )
        match = re.search(r"Submitted batch job (\d+)", submit)
        if not match:
            raise RuntimeError(f"Cannot parse sbatch output: {submit}")
        job_id = match.group(1)

        append_unique(
            sftp,
            posixpath.join(WORK, "submission_manifest.tsv"),
            f"{job_id}\t{TASK}\t{BRANCH}\t{STATE}\tn28\t28\t"
            f"strict_restart_from_valid_{SOURCE_JOB}_seed",
            f"{job_id}\t{TASK}\t{BRANCH}\t{STATE}\t",
        )
        append_unique(
            sftp,
            posixpath.join(WORK, "scheduler_manifest.tsv"),
            f"2026-08-16\tsubmission\t{job_id}_{TASK}\tn28\t28\t1\t"
            f"strict_control_OOH_restart;seed_from_valid_{SOURCE_JOB};"
            "ALGO_Normal;LREAL_FALSE;EDIFF_1e-6;no_duplicates",
            f"\tsubmission\t{job_id}_{TASK}\t",
        )
        print(job_id)
    finally:
        client.close()


if __name__ == "__main__":
    main()
