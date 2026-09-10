from __future__ import annotations

import argparse
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

ROOT_REL = (
    "sfs/CoOH/cp2k/Al16/oer/spin_config_scan_site03_5OH_current_20260714/"
    "cdft_charge_spin_20260812"
)
BASE = posixpath.join(ROOT_REL, "cdft_Co48_adsorbate_fragment_charge_scan")
MANIFEST = posixpath.join(BASE, "scan_manifest.tsv")
SCHED = posixpath.join(ROOT_REL, "scheduler_manifest.tsv")


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


def last_number(text: str, label: str) -> float:
    matches = re.findall(rf"{re.escape(label)}\s*:\s*([-+0-9.Ee]+)", text)
    if not matches:
        raise RuntimeError(f"missing {label}")
    return float(matches[-1])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", required=True)
    parser.add_argument("--array-task", required=True)
    args = parser.parse_args()
    if not re.fullmatch(r"(?:OH|O|OOH)_frag_N[mp]1", args.case):
        raise RuntimeError(f"unsupported case: {args.case}")

    source = posixpath.join(BASE, args.case)
    dest = posixpath.join(BASE, f"{args.case}_recovery")
    project = f"cdft_{args.case}"
    retry_project = f"{project}_retry"

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
        job_name = f"Frag_{args.case}_retry"
        queue = run(client, "squeue -u ftfan -h -o '%i %j %T'")
        if job_name in queue:
            raise RuntimeError(f"recovery already active: {job_name}")
        output = read_text(sftp, posixpath.join(source, "scan.out"))
        required = ("CDFT SCF loop converged", "PROGRAM ENDED AT", "ABORT in dbcsr_lib.F:322")
        if not all(marker in output for marker in required):
            raise RuntimeError("source is not a converged-then-aborted fragment scan")
        target = last_number(output, "Target value of constraint")
        current = last_number(output, "Current value of constraint")
        strength = last_number(output, "Strength of constraint")

        mkdir(sftp, dest)
        try:
            if sftp.stat(posixpath.join(ssh_ncw.REMOTE_ROOT, dest, "retry.out")).st_size:
                raise RuntimeError("refusing to overwrite recovery output")
        except FileNotFoundError:
            pass
        value = read_text(sftp, posixpath.join(source, "scan.inp"))
        value = re.sub(
            r"(?im)^\s*PROJECT_NAME\s+\S+",
            f"  PROJECT_NAME {retry_project}",
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
            f"        STRENGTH {strength:.12f}",
            value,
            count=1,
        )
        write_text(sftp, posixpath.join(dest, "retry.inp"), value)
        run(
            client,
            f"cp {posixpath.join(source, project + '-RESTART.wfn')} "
            f"{posixpath.join(dest, 'converged-RESTART.wfn')}",
        )

        slurm = f"""#!/bin/bash
#SBATCH -J {job_name}
#SBATCH --nodes=1
#SBATCH --ntasks=28
#SBATCH --partition=n28
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
mpirun -np 28 cp2k.popt retry.inp 1>retry.out 2>retry.err
"""
        write_text(sftp, posixpath.join(dest, "submit.slurm"), slurm)
        submit = run(client, f"cd {dest} && sbatch submit.slurm")
        match = re.search(r"Submitted batch job (\d+)", submit)
        if not match:
            raise RuntimeError(submit)
        job_id = match.group(1)

        manifest = read_text(sftp, MANIFEST)
        lines = manifest.splitlines()
        found = False
        for index, line in enumerate(lines):
            fields = line.split("\t")
            if len(fields) >= 6 and fields[1] == args.case:
                if fields[5] != "prepared":
                    raise RuntimeError(f"unexpected manifest status: {fields[5]}")
                fields[5] = f"rejected_{args.array_task}_cleanup_recovery_{job_id}_pending"
                lines[index] = "\t".join(fields)
                found = True
                break
        if not found:
            raise RuntimeError("case missing from manifest")
        write_text(sftp, MANIFEST, "\n".join(lines) + "\n")

        sched = read_text(sftp, SCHED)
        rows = (
            f"2026-08-16\tfragment_scan_failure\t{args.array_task}\trejected_scheduler\t"
            f"{args.case}_converged_current{current:.6f}_target{target:.6f}_but_DBCSR_abort",
            f"2026-08-16\tfragment_recovery_submission\t{job_id}\tpending\t"
            f"{args.case}_latest_WFN_fixed_strength{strength:.12f};no_duplicate",
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
