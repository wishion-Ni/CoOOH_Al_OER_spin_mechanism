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
    "sfs/CoOH/cp2k/Al16/oer/spin_config_scan_site03_5OH_current_20260714/"
    "cdft_charge_spin_20260812/cdft_OH_OOH_Co48_charge_scan"
)
SOURCE = posixpath.join(BASE, "OOH_charge_Nm1")
DEST = posixpath.join(BASE, "OOH_charge_Nm1_recovery")
SCHED = (
    "sfs/CoOH/cp2k/Al16/oer/spin_config_scan_site03_5OH_current_20260714/"
    "cdft_charge_spin_20260812/scheduler_manifest.tsv"
)
MANIFEST = posixpath.join(BASE, "scan_manifest.tsv")


def read_text(sftp, rel: str) -> str:
    with sftp.open(posixpath.join(ssh_ncw.REMOTE_ROOT, rel), "r") as handle:
        return handle.read().decode(errors="replace")


def write_text(sftp, rel: str, value: str) -> None:
    with sftp.open(posixpath.join(ssh_ncw.REMOTE_ROOT, rel), "w") as handle:
        handle.write(value)


def mkdir(sftp, rel: str) -> None:
    try:
        sftp.stat(posixpath.join(ssh_ncw.REMOTE_ROOT, rel))
    except FileNotFoundError:
        sftp.mkdir(posixpath.join(ssh_ncw.REMOTE_ROOT, rel))


def run(client, command: str) -> str:
    _, stdout, stderr = client.exec_command(f"cd {ssh_ncw.REMOTE_ROOT} && {command}")
    code = stdout.channel.recv_exit_status()
    out = stdout.read().decode()
    err = stderr.read().decode()
    if code:
        raise RuntimeError(err or out)
    return out


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
        queue = run(client, "squeue -u ftfan -h -o '%i %j %T'")
        if "Co48_OOH_Nm1_retry" in queue:
            raise RuntimeError("OOH N-1 recovery is already active")
        source_out = read_text(sftp, posixpath.join(SOURCE, "scan.out"))
        required = (
            "CDFT SCF loop converged in   8 iterations",
            "Current value of constraint :                            17.379009336637",
            "PROGRAM ENDED AT",
            "ABORT in dbcsr_lib.F:322",
        )
        if not all(marker in source_out for marker in required):
            raise RuntimeError("source does not match documented converged-then-aborted state")

        mkdir(sftp, DEST)
        retry_out = posixpath.join(DEST, "retry.out")
        try:
            if sftp.stat(posixpath.join(ssh_ncw.REMOTE_ROOT, retry_out)).st_size:
                raise RuntimeError("refusing to overwrite existing recovery output")
        except FileNotFoundError:
            pass
        value = read_text(sftp, posixpath.join(SOURCE, "scan.inp"))
        value = re.sub(
            r"(?im)^\s*PROJECT_NAME\s+\S+",
            "  PROJECT_NAME cdft_Co48_OOH_charge_Nm1_retry",
            value,
            count=1,
        )
        value = re.sub(
            r"(?im)^\s*WFN_RESTART_FILE_NAME\s+\S+",
            "    WFN_RESTART_FILE_NAME converged-RESTART.wfn",
            value,
            count=1,
        )
        value = re.sub(
            r"(?im)^\s*STRENGTH\s+[-+0-9.E]+",
            "        STRENGTH 0.376072022592",
            value,
            count=1,
        )
        write_text(sftp, posixpath.join(DEST, "retry.inp"), value)
        run(
            client,
            f"cp {posixpath.join(SOURCE, 'cdft_Co48_OOH_charge_Nm1-RESTART.wfn')} "
            f"{posixpath.join(DEST, 'converged-RESTART.wfn')}",
        )

        slurm = """#!/bin/bash
#SBATCH -J Co48_OOH_Nm1_retry
#SBATCH --nodes=1
#SBATCH --ntasks=28
#SBATCH --partition=n28
#SBATCH --time=24:00:00
#SBATCH --output=%J.stdout
#SBATCH --error=%J.stderr

set -eo pipefail
export LD_LIBRARY_PATH=/apps/soft/gmp620/lib:${LD_LIBRARY_PATH:-}
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
mpirun -np 28 cp2k.popt retry.inp 1>retry.out 2>retry.err
"""
        write_text(sftp, posixpath.join(DEST, "submit.slurm"), slurm)
        submit = run(client, f"cd {DEST} && sbatch submit.slurm")
        match = re.search(r"Submitted batch job (\d+)", submit)
        if not match:
            raise RuntimeError(submit)
        job_id = match.group(1)

        manifest = read_text(sftp, MANIFEST)
        old = "2\tOOH_charge_Nm1\tCHARGE\t17.379000\t48\tprepared"
        new = f"2\tOOH_charge_Nm1\tCHARGE\t17.379000\t48\trejected_111071_2_recovery_{job_id}_pending"
        if old in manifest:
            manifest = manifest.replace(old, new)
        elif new not in manifest:
            raise RuntimeError("unexpected OOH N-1 manifest row")
        write_text(sftp, MANIFEST, manifest)

        sched = read_text(sftp, SCHED)
        rows = (
            "2026-08-15\tscan_failure\t111071_2\trejected_scheduler\t"
            "OOH_Co48_charge_Nm1_converged_but_DBCSR_abort_exit15;recovery_required",
            f"2026-08-15\trecovery_submission\t{job_id}\tpending\t"
            "OOH_Co48_charge_Nm1_from_converged_WFN;no_duplicate_active_state",
        )
        for row in rows:
            if row not in sched:
                sched += ("" if sched.endswith("\n") else "\n") + row + "\n"
        write_text(sftp, SCHED, sched)
        print(job_id)
    finally:
        client.close()


if __name__ == "__main__":
    main()
