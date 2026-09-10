from __future__ import annotations

import importlib.util
import posixpath
import re
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / ".codex/skills/ftfan-ncw-ssh/scripts/ssh_ncw.py"
spec = importlib.util.spec_from_file_location("ssh_ncw", HELPER)
ssh_ncw = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(ssh_ncw)

BASE = (
    "sfs/CoOH/cp2k/thermo_vib_5OH_U100_current_20260704/"
    "cdft_charge_spin_undoped_20260816/matched_cdft_scans"
)
ARRAY_TASKS = [
    (7, "O_Co_Mp2"),
    (9, "O_frag_Np1"),
    (10, "OOH_Co_Nm1"),
    (11, "OOH_Co_Np1"),
    (13, "OOH_frag_Np1"),
]
CLEANUPS = [
    (1, "111114", "OH_Co_Np1_recovery2", "UndopOHCoNp1n40"),
    (2, "111121", "OH_frag_Nm1_recovery2", "UndopOHFragNm1n40"),
    (4, "111115", "O_Co_Nm1_recovery", "UndopOCoNm1n40"),
]


def read_text(sftp, rel: str) -> str:
    with sftp.open(posixpath.join(ssh_ncw.REMOTE_ROOT, rel), "r") as handle:
        return handle.read().decode(errors="replace")


def write_text(sftp, rel: str, value: str) -> None:
    with sftp.open(posixpath.join(ssh_ncw.REMOTE_ROOT, rel), "w") as handle:
        handle.write(value)


def run(client, command: str, allow_empty: bool = False) -> str:
    _, stdout, stderr = client.exec_command(f"cd {ssh_ncw.REMOTE_ROOT} && {command}")
    code = stdout.channel.recv_exit_status()
    output = stdout.read().decode()
    error = stderr.read().decode()
    if code and not allow_empty:
        raise RuntimeError(error or output)
    return output


def pending_state(client, job: str) -> str:
    return run(client, f"squeue -h -j {job} -o '%T|%R'").strip()


def parse_submit(output: str) -> str:
    match = re.search(r"Submitted batch job (\d+)", output)
    if not match:
        raise RuntimeError(f"cannot parse sbatch output: {output}")
    return match.group(1)


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
        if "UndopRemainn40" in queue or any(item[3] in queue for item in CLEANUPS):
            raise RuntimeError("n40 redistribution jobs already active")

        old_jobs = [f"111098_{task}" for task, _ in ARRAY_TASKS]
        old_jobs.extend(item[1] for item in CLEANUPS)
        for job in old_jobs:
            state = pending_state(client, job)
            if not state.startswith("PENDING|"):
                raise RuntimeError(f"job {job} is not safely pending: {state}")

        for _, case in ARRAY_TASKS:
            try:
                output_size = sftp.stat(
                    posixpath.join(ssh_ncw.REMOTE_ROOT, BASE, case, "scan.out")
                ).st_size
            except FileNotFoundError:
                output_size = 0
            if output_size:
                raise RuntimeError(f"pending case {case} already has scan output")

        for _, _, directory, _ in CLEANUPS:
            try:
                output_size = sftp.stat(
                    posixpath.join(ssh_ncw.REMOTE_ROOT, BASE, directory, "cleanup.out")
                ).st_size
            except FileNotFoundError:
                output_size = 0
            if output_size:
                raise RuntimeError(f"pending cleanup {directory} already has output")

        run(client, "scancel " + " ".join(old_jobs))
        for _ in range(20):
            remaining = [job for job in old_jobs if pending_state(client, job)]
            if not remaining:
                break
            time.sleep(0.5)
        else:
            raise RuntimeError(f"canceled jobs still visible: {remaining}")

        cleanup_jobs = {}
        for task, old_job, directory, job_name in CLEANUPS:
            source = read_text(sftp, posixpath.join(BASE, directory, "submit.slurm"))
            value = re.sub(r"(?m)^#SBATCH -J .+$", f"#SBATCH -J {job_name}", source)
            value = re.sub(r"(?m)^#SBATCH --ntasks=28$", "#SBATCH --ntasks=40", value)
            value = re.sub(r"(?m)^#SBATCH --partition=n28$", "#SBATCH --partition=n40", value)
            value = re.sub(r"(?m)^mpirun -np 28 ", "mpirun -np 40 ", value)
            if value == source:
                raise RuntimeError(f"failed to convert cleanup script for {directory}")
            write_text(sftp, posixpath.join(BASE, directory, "submit_n40.slurm"), value)
            submitted = run(client, f"cd {posixpath.join(BASE, directory)} && sbatch submit_n40.slurm")
            cleanup_jobs[task] = parse_submit(submitted)

        cases = " ".join(case for _, case in ARRAY_TASKS)
        array_script = f"""#!/bin/bash
#SBATCH -J UndopRemainn40
#SBATCH --nodes=1
#SBATCH --ntasks=40
#SBATCH --partition=n40
#SBATCH --array=0-4%3
#SBATCH --time=24:00:00
#SBATCH --output=slurm-%A_%a.out
#SBATCH --error=slurm-%A_%a.err

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
CASES=({cases})
CASE=${{CASES[$SLURM_ARRAY_TASK_ID]}}
cd "$SLURM_SUBMIT_DIR/$CASE"
mpirun -np 40 cp2k.popt scan.inp 1>scan.out 2>scan.err
"""
        write_text(sftp, posixpath.join(BASE, "submit_remaining_n40.slurm"), array_script)
        array_submit = run(client, f"cd {BASE} && sbatch submit_remaining_n40.slurm")
        array_job = parse_submit(array_submit)

        manifest = read_text(sftp, posixpath.join(BASE, "scan_manifest.tsv"))
        lines = manifest.splitlines()
        expected_status = {
            1: "rejected_111098_1_inner_scf_then_111102_cleanup_recovery_111114_pending",
            2: "rejected_111098_2_inner_scf_then_111117_0_cleanup_recovery_111121_pending",
            4: "rejected_111098_4_cleanup_recovery_111115_pending",
        }
        for task, new_job in cleanup_jobs.items():
            fields = lines[task + 1].split("\t")
            if fields[6] != expected_status[task]:
                raise RuntimeError(f"unexpected cleanup manifest status task{task}: {fields[6]}")
            fields[6] = (
                f"{expected_status[task]}_canceled_pending_"
                f"redistributed_{new_job}_n40_pending"
            )
            lines[task + 1] = "\t".join(fields)
        write_text(sftp, posixpath.join(BASE, "scan_manifest.tsv"), "\n".join(lines) + "\n")

        scheduler_path = posixpath.join(BASE, "scheduler_manifest.tsv")
        scheduler = read_text(sftp, scheduler_path)
        scheduler += (
            "2026-08-18\tresource_redistribution\t111098_7,9-11,13\t"
            f"canceled_pending_to_{array_job}_0-4\tn28_to_n40;concurrency3;no_duplicate\n"
        )
        for task, old_job, directory, _ in CLEANUPS:
            scheduler += (
                f"2026-08-18\tresource_redistribution\t{old_job}\t"
                f"canceled_pending_to_{cleanup_jobs[task]}\t{directory};n28_to_n40;no_duplicate\n"
            )
        write_text(sftp, scheduler_path, scheduler)
        print(
            f"array={array_job};"
            + ";".join(f"task{task}_cleanup={job}" for task, job in cleanup_jobs.items())
        )
    finally:
        client.close()


if __name__ == "__main__":
    main()
