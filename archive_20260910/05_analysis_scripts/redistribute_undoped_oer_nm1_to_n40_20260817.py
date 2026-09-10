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
MANIFEST = posixpath.join(SCAN, "scan_manifest.tsv")
SCHEDULER = posixpath.join(BASE, "scheduler_manifest.tsv")
CASES = (
    ("OH_frag_Nm1_recovery", "retry.inp", "retry.out", "retry.err"),
    ("O_frag_Nm1", "scan.inp", "scan.out", "scan.err"),
    ("OOH_frag_Nm1", "scan.inp", "scan.out", "scan.err"),
)


def read_text(sftp, rel: str) -> str:
    with sftp.open(posixpath.join(ssh_ncw.REMOTE_ROOT, rel), "r") as handle:
        return handle.read().decode(errors="replace")


def write_text(sftp, rel: str, value: str) -> None:
    with sftp.open(posixpath.join(ssh_ncw.REMOTE_ROOT, rel), "w") as handle:
        handle.write(value)


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
        queue = run(client, "squeue -u ftfan -h -o '%i|%j|%T|%P'")
        if "Undop_OER_Nm1_n40" in queue:
            raise RuntimeError("the n40 OER N-1 array is already active")
        if "111103|Undop_OH_frag_Nm1_retry|PENDING|n28" not in queue:
            raise RuntimeError("OH fragment N-1 recovery is not pending on n28")
        if "111098_[7-13%1]|Undop_cdft_scan|PENDING|n28" not in queue:
            raise RuntimeError("the source array tasks are not pending as expected")

        for case, input_name, output_name, _ in CASES:
            case_dir = posixpath.join(SCAN, case)
            input_text = read_text(sftp, posixpath.join(case_dir, input_name))
            if not re.search(r"(?im)^\s*EPS_SCF\s+1\.0E-6\s*$", input_text):
                raise RuntimeError(f"{case} is not aligned to inner EPS_SCF 1E-6")
            try:
                output_size = sftp.stat(
                    posixpath.join(ssh_ncw.REMOTE_ROOT, case_dir, output_name)
                ).st_size
            except FileNotFoundError:
                output_size = 0
            if output_size:
                raise RuntimeError(f"refusing to duplicate started case {case}")

        slurm = """#!/bin/bash
#SBATCH -J Undop_OER_Nm1_n40
#SBATCH --nodes=1
#SBATCH --ntasks=40
#SBATCH --partition=n40
#SBATCH --array=0-2%1
#SBATCH --time=24:00:00
#SBATCH --output=slurm-%A_%a.out
#SBATCH --error=slurm-%A_%a.err

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

CASES=(OH_frag_Nm1_recovery O_frag_Nm1 OOH_frag_Nm1)
INPUTS=(retry.inp scan.inp scan.inp)
OUTPUTS=(retry.out scan.out scan.out)
ERRORS=(retry.err scan.err scan.err)
CASE=${CASES[$SLURM_ARRAY_TASK_ID]}
cd "$SLURM_SUBMIT_DIR/$CASE"
mpirun -np 40 cp2k.popt "${INPUTS[$SLURM_ARRAY_TASK_ID]}" \
  1>"${OUTPUTS[$SLURM_ARRAY_TASK_ID]}" \
  2>"${ERRORS[$SLURM_ARRAY_TASK_ID]}"
"""
        write_text(sftp, posixpath.join(SCAN, "submit_oer_nm1_n40.slurm"), slurm)

        # All three source tasks are pending and have no output. Cancel only these
        # user-owned tasks, then submit the unique replacement array immediately.
        run(client, "scancel 111103 111098_8 111098_12")
        submit = run(client, f"cd {SCAN} && sbatch submit_oer_nm1_n40.slurm")
        match = re.search(r"Submitted batch job (\d+)", submit)
        if not match:
            raise RuntimeError(f"cannot parse sbatch output: {submit}")
        job_id = match.group(1)

        manifest = read_text(sftp, MANIFEST)
        replacements = {
            "rejected_111098_2_inner_scf_recovery_111103_pending": (
                f"rejected_111098_2_inner_scf_recovery_111103_cancelled_for_"
                f"n40_{job_id}_0_pending"
            ),
            "8\tO_frag_Nm1\tundoped_valid_co32_O\tCHARGE\t23.251000\t32,211\tprepared": (
                "8\tO_frag_Nm1\tundoped_valid_co32_O\tCHARGE\t23.251000\t32,211\t"
                f"redistributed_111098_8_cancelled_to_{job_id}_1_pending"
            ),
            "12\tOOH_frag_Nm1\tundoped_valid_co32_OOH\tCHARGE\t29.944000\t"
            "32,211,212,213\tprepared": (
                "12\tOOH_frag_Nm1\tundoped_valid_co32_OOH\tCHARGE\t29.944000\t"
                f"32,211,212,213\tredistributed_111098_12_cancelled_to_{job_id}_2_pending"
            ),
        }
        for old, new in replacements.items():
            if old not in manifest:
                raise RuntimeError(f"unexpected manifest state: {old}")
            manifest = manifest.replace(old, new, 1)
        write_text(sftp, MANIFEST, manifest)

        scheduler = read_text(sftp, SCHEDULER)
        scheduler += (
            f"2026-08-17\tresource_redistribution\t111103,111098_8,111098_12_to_"
            f"{job_id}_0-2\tpending\tOER_priority_fragment_Nm1;pending_n28_tasks_"
            "cancelled_before_start;unique_n40_40rank_array_concurrency1;"
            "OH_O_OOH;inputs_and_constraints_unchanged;no_duplicates\n"
        )
        write_text(sftp, SCHEDULER, scheduler)
        print(job_id)
    finally:
        client.close()


if __name__ == "__main__":
    main()
