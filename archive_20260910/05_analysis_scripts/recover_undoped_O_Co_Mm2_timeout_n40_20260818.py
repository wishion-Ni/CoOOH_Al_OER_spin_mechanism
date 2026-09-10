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

BASE = (
    "sfs/CoOH/cp2k/thermo_vib_5OH_U100_current_20260704/"
    "cdft_charge_spin_undoped_20260816"
)
SCAN = posixpath.join(BASE, "matched_cdft_scans")
SOURCE = posixpath.join(SCAN, "O_Co_Mm2")
DEST = posixpath.join(SCAN, "O_Co_Mm2_recovery")
MANIFEST = posixpath.join(SCAN, "scan_manifest.tsv")
SCHEDULER = posixpath.join(BASE, "scheduler_manifest.tsv")
RECOVERY_PROJECT = "undop_cdft_O_Co_Mm2_recovery"
JOB_NAME = "UndopOCoMm2Recover"
TASK = 6


def read_text(sftp, rel: str) -> str:
    with sftp.open(posixpath.join(ssh_ncw.REMOTE_ROOT, rel), "r") as handle:
        return handle.read().decode(errors="replace")


def write_text(sftp, rel: str, value: str) -> None:
    with sftp.open(posixpath.join(ssh_ncw.REMOTE_ROOT, rel), "w") as handle:
        handle.write(value)


def run(client, command: str) -> str:
    _, stdout, stderr = client.exec_command(f"cd {ssh_ncw.REMOTE_ROOT} && {command}")
    code = stdout.channel.recv_exit_status()
    output = stdout.read().decode()
    error = stderr.read().decode()
    if code:
        raise RuntimeError(error or output)
    return output


def mkdir(sftp, rel: str) -> None:
    try:
        sftp.stat(posixpath.join(ssh_ncw.REMOTE_ROOT, rel))
    except FileNotFoundError:
        sftp.mkdir(posixpath.join(ssh_ncw.REMOTE_ROOT, rel))


def last_number(text: str, label: str) -> float:
    values = re.findall(rf"{re.escape(label)}\s*:\s*([-+0-9.Ee]+)", text)
    if not values:
        raise RuntimeError(f"missing {label}")
    return float(values[-1])


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
        queue = run(client, "squeue -u ftfan -h -o '%i|%j|%T|%P'")
        if JOB_NAME in queue:
            raise RuntimeError("M-2 timeout recovery already active")
        state = run(client, "sacct -j 111098_6 -n -P -o State").strip().splitlines()[0]
        if state != "TIMEOUT":
            raise RuntimeError(f"source task is not a timeout: {state}")

        output = read_text(sftp, posixpath.join(SOURCE, "scan.out"))
        if "CDFT SCF loop converged" in output or "PROGRAM ENDED AT" in output:
            raise RuntimeError("timed-out source unexpectedly completed")
        forbidden = ("SCF run NOT converged", "CDFT SCF loop FAILED", "ABORT in dbcsr")
        if any(marker in output for marker in forbidden):
            raise RuntimeError("source contains a physical failure beyond timeout")
        target = last_number(output, "Target value of constraint")
        current = last_number(output, "Current value of constraint")
        strength = last_number(output, "Strength of constraint")
        if abs(current - target) <= 1.5e-4:
            raise RuntimeError("timed-out source is already within target tolerance")

        wfn = posixpath.join(SOURCE, "-RESTART.wfn")
        if sftp.stat(posixpath.join(ssh_ncw.REMOTE_ROOT, wfn)).st_size < 40_000_000:
            raise RuntimeError("latest timeout WFN is too small")
        mkdir(sftp, DEST)
        try:
            if sftp.stat(posixpath.join(ssh_ncw.REMOTE_ROOT, DEST, "recovery.out")).st_size:
                raise RuntimeError("recovery destination already has output")
        except FileNotFoundError:
            pass

        value = read_text(sftp, posixpath.join(SOURCE, "scan.inp"))
        value = re.sub(
            r"(?im)^\s*PROJECT_NAME\s+\S+",
            f"  PROJECT_NAME {RECOVERY_PROJECT}",
            value,
            count=1,
        )
        value = re.sub(
            r"(?im)^\s*WFN_RESTART_FILE_NAME\s+\S+",
            "    WFN_RESTART_FILE_NAME latest-RESTART.wfn",
            value,
            count=1,
        )
        value = re.sub(
            r"(?im)^\s*STRENGTH\s+[-+0-9.Ee]+",
            f"        STRENGTH {strength:.12f}",
            value,
            count=1,
        )
        write_text(sftp, posixpath.join(DEST, "recovery.inp"), value)
        run(client, f"cp {wfn} {posixpath.join(DEST, 'latest-RESTART.wfn')}")

        slurm = f"""#!/bin/bash
#SBATCH -J {JOB_NAME}
#SBATCH --nodes=1
#SBATCH --ntasks=40
#SBATCH --partition=n40
#SBATCH --time=24:00:00
#SBATCH --output=%J.stdout
#SBATCH --error=%J.stderr

set -eo pipefail
export LD_LIBRARY_PATH=/apps/soft/gmp620/lib:${{LD_LIBRARY_PATH:-}}
export LD_LIBRARY_PATH=/apps/soft/mpfr410/lib:$LD_LIBRARY_PATH
export LD_LIBRARY_PATH=/apps/soft/mpc120/lib:$LD_LIBRARY_PATH
export LD_LIBRARY_PATH=/apps/soft/gcc840/lib64:$LD_LIBRARY_PATH
export PATH=/apps/soft/gcc840/bin:$PATH
source /apps/soft/cp2k-2024.1/tools/toolchain/install/setup
set -u
export PATH=$PATH:/apps/soft/cp2k-2024.1/exe/local
export CP2K_DATA_DIR=/apps/soft/cp2k-2024.1/data
export OMP_NUM_THREADS=1
export OMPI_MCA_btl=self,vader,tcp
export OMPI_MCA_pml=ob1
ulimit -s unlimited
mpirun -np 40 cp2k.popt recovery.inp 1>recovery.out 2>recovery.err
"""
        write_text(sftp, posixpath.join(DEST, "submit.slurm"), slurm)
        submitted = run(client, f"cd {DEST} && sbatch submit.slurm")
        match = re.search(r"Submitted batch job (\d+)", submitted)
        if not match:
            raise RuntimeError(f"cannot parse sbatch output: {submitted}")
        job_id = match.group(1)

        manifest = read_text(sftp, MANIFEST)
        lines = manifest.splitlines()
        fields = lines[TASK + 1].split("\t")
        if fields[6] != "prepared":
            raise RuntimeError(f"unexpected manifest status: {fields[6]}")
        fields[6] = f"rejected_111098_6_TIMEOUT_recovery_{job_id}_n40_pending"
        lines[TASK + 1] = "\t".join(fields)
        write_text(sftp, MANIFEST, "\n".join(lines) + "\n")

        scheduler = read_text(sftp, SCHEDULER)
        scheduler += (
            "2026-08-18\tmatched_scan_timeout\t111098_6\trejected_incomplete\t"
            f"O_Co_Mm2;target{target:.6f};last{current:.6f};strength{strength:.12f};"
            "24h_walltime;no_CDFT_convergence\n"
            f"2026-08-18\tmatched_scan_timeout_recovery_submission\t{job_id}\tpending\t"
            f"O_Co_Mm2;latest_WFN;initial_strength{strength:.12f};fixed_geometry;"
            "n40_40ranks;no_duplicate\n"
        )
        write_text(sftp, SCHEDULER, scheduler)
        print(job_id)
    finally:
        client.close()


if __name__ == "__main__":
    main()
