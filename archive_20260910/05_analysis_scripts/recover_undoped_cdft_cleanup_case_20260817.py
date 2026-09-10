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

BASE = (
    "sfs/CoOH/cp2k/thermo_vib_5OH_U100_current_20260704/"
    "cdft_charge_spin_undoped_20260816"
)
SCAN = posixpath.join(BASE, "matched_cdft_scans")
MANIFEST = posixpath.join(SCAN, "scan_manifest.tsv")
SCHEDULER = posixpath.join(BASE, "scheduler_manifest.tsv")
CASES = {
    "OH_frag_Nm1_cleanup2": {
        "source": "OH_frag_Nm1_recovery2",
        "dest": "OH_frag_Nm1_recovery3",
        "input": "cleanup.inp",
        "output": "cleanup.out",
        "project": "undop_cdft_OH_frag_Nm1_cleanup",
        "retry_project": "undop_cdft_OH_frag_Nm1_cleanup2",
        "job_name": "UndopOHFragNm1Clean2",
        "manifest_case": "OH_frag_Nm1",
        "manifest_old": (
            "rejected_111098_2_inner_scf_then_111117_0_cleanup_recovery_111121_"
            "pending_canceled_pending_redistributed_111152_n40_pending"
        ),
        "manifest_prefix": (
            "rejected_111098_2_then_111117_0_then_111152_cleanup_recovery"
        ),
        "source_job": "111152",
        "ranks": 40,
        "partition": "n40",
    },
    "OH_frag_Nm1": {
        "source": "OH_frag_Nm1_recovery",
        "dest": "OH_frag_Nm1_recovery2",
        "input": "retry.inp",
        "output": "retry.out",
        "project": "undop_cdft_OH_frag_Nm1_retry",
        "retry_project": "undop_cdft_OH_frag_Nm1_cleanup",
        "job_name": "Undop_OH_frag_Nm1_cleanup",
        "manifest_old": (
            "rejected_111098_2_inner_scf_recovery_111103_cancelled_for_"
            "n40_111117_0_pending"
        ),
        "manifest_prefix": (
            "rejected_111098_2_inner_scf_then_111117_0_cleanup_recovery"
        ),
        "source_job": "111117_0",
    },
    "OH_Co_Np1": {
        "source": "OH_Co_Np1_recovery",
        "dest": "OH_Co_Np1_recovery2",
        "input": "retry.inp",
        "output": "retry.out",
        "project": "undop_cdft_OH_Co_Np1_retry",
        "retry_project": "undop_cdft_OH_Co_Np1_cleanup",
        "job_name": "Undop_OH_Co_Np1_cleanup",
        "manifest_old": (
            "rejected_111098_1_inner_scf_recovery_111102_pending"
        ),
        "manifest_prefix": (
            "rejected_111098_1_inner_scf_then_111102_cleanup_recovery"
        ),
        "source_job": "111102",
    },
    "O_Co_Nm1": {
        "source": "O_Co_Nm1",
        "dest": "O_Co_Nm1_recovery",
        "input": "scan.inp",
        "output": "scan.out",
        "project": "undop_cdft_O_Co_Nm1",
        "retry_project": "undop_cdft_O_Co_Nm1_cleanup",
        "job_name": "Undop_O_Co_Nm1_cleanup",
        "manifest_old": "prepared",
        "manifest_prefix": "rejected_111098_4_cleanup_recovery",
        "source_job": "111098_4",
    },
}


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


def last_number(text: str, label: str) -> float:
    values = re.findall(rf"{re.escape(label)}\s*:\s*([-+0-9.Ee]+)", text)
    if not values:
        raise RuntimeError(f"missing {label}")
    return float(values[-1])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", choices=CASES, required=True)
    args = parser.parse_args()
    cfg = CASES[args.case]
    manifest_case = cfg.get("manifest_case", args.case)
    ranks = cfg.get("ranks", 28)
    partition = cfg.get("partition", "n28")
    source = posixpath.join(SCAN, cfg["source"])
    dest = posixpath.join(SCAN, cfg["dest"])

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
        if cfg["job_name"] in queue:
            raise RuntimeError(f"cleanup recovery already active: {args.case}")

        output = read_text(sftp, posixpath.join(source, cfg["output"]))
        required = (
            "CDFT SCF loop converged",
            "PROGRAM ENDED AT",
            "ABORT in dbcsr_lib.F:322",
        )
        if not all(marker in output for marker in required):
            raise RuntimeError("source is not a converged-then-cleanup-aborted scan")
        if "SCF run NOT converged" in output or "CDFT SCF loop FAILED" in output:
            raise RuntimeError("source contains a physical convergence failure")
        target = last_number(output, "Target value of constraint")
        current = last_number(output, "Current value of constraint")
        strength = last_number(output, "Strength of constraint")
        if abs(current - target) > 1.0e-4:
            raise RuntimeError(
                f"constraint is outside tolerance: target={target}, current={current}"
            )

        wfn_rel = posixpath.join(source, f"{cfg['project']}-RESTART.wfn")
        wfn_size = sftp.stat(posixpath.join(ssh_ncw.REMOTE_ROOT, wfn_rel)).st_size
        if wfn_size < 40_000_000:
            raise RuntimeError(f"restart WFN is too small: {wfn_size}")

        mkdir(sftp, dest)
        try:
            if sftp.stat(posixpath.join(ssh_ncw.REMOTE_ROOT, dest, "cleanup.out")).st_size:
                raise RuntimeError("refusing to overwrite cleanup recovery output")
        except FileNotFoundError:
            pass

        value = read_text(sftp, posixpath.join(source, cfg["input"]))
        value = re.sub(
            r"(?im)^\s*PROJECT_NAME\s+\S+",
            f"  PROJECT_NAME {cfg['retry_project']}",
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
        write_text(sftp, posixpath.join(dest, "cleanup.inp"), value)
        run(
            client,
            f"cp {wfn_rel} {posixpath.join(dest, 'converged-RESTART.wfn')}",
        )

        slurm = f"""#!/bin/bash
#SBATCH -J {cfg['job_name']}
#SBATCH --nodes=1
#SBATCH --ntasks={ranks}
#SBATCH --partition={partition}
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
mpirun -np {ranks} cp2k.popt cleanup.inp 1>cleanup.out 2>cleanup.err
"""
        write_text(sftp, posixpath.join(dest, "submit.slurm"), slurm)
        submit = run(client, f"cd {dest} && sbatch submit.slurm")
        match = re.search(r"Submitted batch job (\d+)", submit)
        if not match:
            raise RuntimeError(f"cannot parse sbatch output: {submit}")
        job_id = match.group(1)

        manifest = read_text(sftp, MANIFEST)
        lines = manifest.splitlines()
        found = False
        for index, line in enumerate(lines):
            fields = line.split("\t")
            if len(fields) >= 7 and fields[1] == manifest_case:
                if fields[6] != cfg["manifest_old"]:
                    raise RuntimeError(f"unexpected manifest status: {fields[6]}")
                fields[6] = f"{cfg['manifest_prefix']}_{job_id}_pending"
                lines[index] = "\t".join(fields)
                found = True
                break
        if not found:
            raise RuntimeError(f"case missing from manifest: {args.case}")
        write_text(sftp, MANIFEST, "\n".join(lines) + "\n")

        scheduler = read_text(sftp, SCHEDULER)
        rows = (
            f"2026-08-18\tmatched_scan_cleanup_failure\t{cfg['source_job']}\t"
            f"rejected_scheduler\t{manifest_case};physical_CDFT_converged;target"
            f"{target:.6f};final{current:.6f};strength{strength:.12f};DBCSR_cleanup_abort",
            f"2026-08-18\tmatched_scan_cleanup_recovery_submission\t{job_id}\tpending\t"
            f"{manifest_case};latest_complete_WFN;fixed_strength{strength:.12f};"
            f"fixed_geometry;{partition};no_duplicate_active_state",
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
