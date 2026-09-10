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
SOURCE = posixpath.join(SCAN, "OH_frag_Nm1")
DEST = posixpath.join(SCAN, "OH_frag_Nm1_recovery")
MANIFEST = posixpath.join(SCAN, "scan_manifest.tsv")
SCHEDULER = posixpath.join(BASE, "scheduler_manifest.tsv")
SOURCE_PROJECT = "undop_cdft_OH_frag_Nm1"
RECOVERY_PROJECT = "undop_cdft_OH_frag_Nm1_retry"
INITIAL_STRENGTH = 0.217913960352
PENDING_CASES = (
    "OH_frag_Np1",
    "O_Co_Nm1",
    "O_Co_Np1",
    "O_Co_Mm2",
    "O_Co_Mp2",
    "O_frag_Nm1",
    "O_frag_Np1",
    "OOH_Co_Nm1",
    "OOH_Co_Np1",
    "OOH_frag_Nm1",
    "OOH_frag_Np1",
)


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
    _, stdout, stderr = client.exec_command(
        f"cd {ssh_ncw.REMOTE_ROOT} && {command}"
    )
    code = stdout.channel.recv_exit_status()
    output = stdout.read().decode()
    error = stderr.read().decode()
    if code:
        raise RuntimeError(error or output)
    return output


def align_inner_eps(value: str) -> str:
    value, count = re.subn(
        r"(?im)^(\s*EPS_SCF\s+)1\.0E-7\s*$",
        r"\g<1>1.0E-6",
        value,
        count=1,
    )
    if count != 1:
        raise RuntimeError("failed to match exactly one inner EPS_SCF line")
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
        queue = run(client, "squeue -u ftfan -h -o '%i %j %T'")
        if "Undop_OH_frag_Nm1_retry" in queue:
            raise RuntimeError("OH fragment N-1 recovery is already active")
        if "111098_2" in queue:
            raise RuntimeError("original array task 2 is unexpectedly still active")
        for task in range(3, 14):
            if f"111098_{task} " in queue and "PENDING" not in next(
                line for line in queue.splitlines() if f"111098_{task} " in line
            ):
                raise RuntimeError(f"array task {task} is no longer pending")

        source_output = read_text(sftp, posixpath.join(SOURCE, "scan.out"))
        line_search = read_text(
            sftp, posixpath.join(SOURCE, f"{SOURCE_PROJECT}-LineSearch.out")
        )
        required_output = (
            "Target value of constraint  :                            23.903000000000",
            "SCF run NOT converged",
        )
        required_line = (
            "Strength of constraint      :                             0.217913960352",
            "Current value of constraint :                            24.006027712940",
        )
        if not all(marker in source_output for marker in required_output):
            raise RuntimeError("source output does not match documented SCF failure")
        if not all(marker in line_search for marker in required_line):
            raise RuntimeError("line search does not contain the documented near-target state")
        if "CDFT SCF loop converged" in source_output:
            raise RuntimeError("source unexpectedly contains a converged cDFT state")

        wfn_rel = posixpath.join(SOURCE, f"{SOURCE_PROJECT}-RESTART.wfn")
        wfn_size = sftp.stat(posixpath.join(ssh_ncw.REMOTE_ROOT, wfn_rel)).st_size
        if wfn_size < 40_000_000:
            raise RuntimeError(f"complete restart WFN is too small: {wfn_size}")

        for case in PENDING_CASES:
            case_dir = posixpath.join(SCAN, case)
            try:
                output_size = sftp.stat(
                    posixpath.join(ssh_ncw.REMOTE_ROOT, case_dir, "scan.out")
                ).st_size
            except FileNotFoundError:
                output_size = 0
            if output_size:
                raise RuntimeError(f"refusing to edit started case {case}")
            input_rel = posixpath.join(case_dir, "scan.inp")
            write_text(sftp, input_rel, align_inner_eps(read_text(sftp, input_rel)))

        mkdir(sftp, DEST)
        try:
            if sftp.stat(posixpath.join(ssh_ncw.REMOTE_ROOT, DEST, "retry.out")).st_size:
                raise RuntimeError("refusing to overwrite recovery output")
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
            "    WFN_RESTART_FILE_NAME converged-RESTART.wfn",
            value,
            count=1,
        )
        value = align_inner_eps(value)
        value = re.sub(
            r"(?im)^\s*STRENGTH\s+[-+0-9.E]+",
            f"        STRENGTH {INITIAL_STRENGTH:.12f}",
            value,
            count=1,
        )
        write_text(sftp, posixpath.join(DEST, "retry.inp"), value)
        run(
            client,
            f"cp {wfn_rel} {posixpath.join(DEST, 'converged-RESTART.wfn')}",
        )

        slurm = """#!/bin/bash
#SBATCH -J Undop_OH_frag_Nm1_retry
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
            raise RuntimeError(f"cannot parse sbatch output: {submit}")
        job_id = match.group(1)

        manifest = read_text(sftp, MANIFEST)
        old = (
            "2\tOH_frag_Nm1\tundoped_valid_co32_OH\tCHARGE\t23.903000\t"
            "32,211,212\tprepared"
        )
        new = (
            "2\tOH_frag_Nm1\tundoped_valid_co32_OH\tCHARGE\t23.903000\t"
            "32,211,212\t"
            f"rejected_111098_2_inner_scf_recovery_{job_id}_pending"
        )
        if old not in manifest:
            raise RuntimeError("unexpected OH fragment N-1 manifest row")
        write_text(sftp, MANIFEST, manifest.replace(old, new, 1))

        scheduler = read_text(sftp, SCHEDULER)
        rows = (
            "2026-08-17\tmatched_scan_failure\t111098_2\trejected_convergence\t"
            "physical_job111101;OH_frag_Nm1;inner_OT_SCF_reached_MAX_SCF500_"
            "during_CDFT_line_search;target23.903000;near_target24.006028_at_"
            "strength0.217913960352;no_CDFT_convergence",
            f"2026-08-17\tmatched_scan_recovery_submission\t{job_id}\tpending\t"
            "OH_frag_Nm1;complete_restart_WFN;initial_strength0.217913960352;"
            "inner_EPS_SCF1E-6_matched_to_validated_Al16_CDFT;fixed_geometry;"
            "n28;no_duplicate_active_state",
            "2026-08-17\tmatched_scan_input_alignment\t111098_3-13\tprepared\t"
            "inner_EPS_SCF_changed_1E-7_to_1E-6_before_start;matched_to_validated_"
            "Al16_CDFT;targets_constraints_geometries_and_other_settings_unchanged",
        )
        for row in rows:
            if row not in scheduler:
                scheduler += ("" if scheduler.endswith("\n") else "\n") + row + "\n"
        write_text(sftp, SCHEDULER, scheduler)
        print(job_id)
    finally:
        client.close()


if __name__ == "__main__":
    main()
