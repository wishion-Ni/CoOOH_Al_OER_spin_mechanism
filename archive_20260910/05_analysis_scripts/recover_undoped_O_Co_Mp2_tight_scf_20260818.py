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
SOURCE = posixpath.join(SCAN, "O_Co_Mp2")
DEST = posixpath.join(SCAN, "O_Co_Mp2_recovery")
MANIFEST = posixpath.join(SCAN, "scan_manifest.tsv")
SCHEDULER = posixpath.join(BASE, "scheduler_manifest.tsv")
SOURCE_PROJECT = "undop_cdft_O_Co_Mp2"
RECOVERY_PROJECT = "undop_cdft_O_Co_Mp2_recovery"
JOB_NAME = "UndopOCoMp2Recover"
TASK = 7


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


def tighten_input(value: str, strength: float) -> str:
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
    cdft = re.search(r"(?im)^\s*&CDFT\b", value)
    if not cdft:
        raise RuntimeError("missing CDFT block")
    prefix = value[: cdft.start()]
    suffix = value[cdft.start() :]
    prefix, eps_count = re.subn(
        r"(?im)^(\s*EPS_SCF\s+)[-+0-9.Ee]+\s*$",
        r"\g<1>1.0E-7",
        prefix,
    )
    if eps_count != 2:
        raise RuntimeError(f"expected two electronic EPS_SCF entries, found {eps_count}")
    value = prefix + suffix
    value, max_count = re.subn(
        r"(?im)^(\s*MAX_SCF\s+)30\s*$",
        r"\g<1>80",
        value,
    )
    if max_count != 2:
        raise RuntimeError(f"expected two MAX_SCF30 entries, found {max_count}")
    return value


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
            raise RuntimeError("M+2 recovery already active")

        output = read_text(sftp, posixpath.join(SOURCE, "scan.out"))
        required = (
            "CDFT SCF loop FAILED to converge after   31 iterations",
            "PROGRAM ENDED AT",
            "ABORT in dbcsr_lib.F:322",
        )
        if not all(marker in output for marker in required):
            raise RuntimeError("source is not the diagnosed M+2 convergence failure")
        if "CDFT SCF loop converged" in output:
            raise RuntimeError("source unexpectedly contains cDFT convergence")
        target = last_number(output, "Target value of constraint")
        current = last_number(output, "Current value of constraint")
        strength = last_number(output, "Strength of constraint")
        if abs(current - target) <= 1.5e-4:
            raise RuntimeError("failed source is already within accepted tolerance")

        wfn = posixpath.join(SOURCE, f"{SOURCE_PROJECT}-RESTART.wfn")
        if sftp.stat(posixpath.join(ssh_ncw.REMOTE_ROOT, wfn)).st_size < 40_000_000:
            raise RuntimeError("restart WFN is too small")
        mkdir(sftp, DEST)
        try:
            if sftp.stat(posixpath.join(ssh_ncw.REMOTE_ROOT, DEST, "recovery.out")).st_size:
                raise RuntimeError("recovery destination already has output")
        except FileNotFoundError:
            pass

        value = read_text(sftp, posixpath.join(SOURCE, "scan.inp"))
        value = tighten_input(value, strength)
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
        fields[6] = f"rejected_111154_0_CDFT_nonconverged_recovery_{job_id}_pending"
        lines[TASK + 1] = "\t".join(fields)
        write_text(sftp, MANIFEST, "\n".join(lines) + "\n")

        scheduler = read_text(sftp, SCHEDULER)
        scheduler += (
            "2026-08-18\tmatched_scan_CDFT_failure\t111154_0\trejected_scientific\t"
            f"O_Co_Mp2;target{target:.6f};final{current:.6f};strength{strength:.12f};"
            "CDFT_MAX_SCF30_exhausted;DBCSR_cleanup_abort\n"
            f"2026-08-18\tmatched_scan_convergence_recovery_submission\t{job_id}\tpending\t"
            f"O_Co_Mp2;latest_WFN;initial_strength{strength:.12f};electronic_EPS_SCF1E-7;"
            "SCF_and_CDFT_MAX_SCF80;n40;no_duplicate\n"
        )
        write_text(sftp, SCHEDULER, scheduler)
        print(job_id)
    finally:
        client.close()


if __name__ == "__main__":
    main()
