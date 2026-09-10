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
    "proton_relay_al16_vs_undoped_20260817/pcet_CoO_fragment_Nm1"
)
CASES = {
    "al16_image_00": {
        "task": 0,
        "source": "al16_image_00",
        "dest": "al16_image_00_cleanup",
        "project": "relay_pcet_al16_00_Nm1",
        "retry_project": "relay_pcet_al16_00_Nm1_cleanup",
        "job_name": "RelayAl00Nm1Cleanup",
    },
    "al16_image_06": {
        "task": 2,
        "source": "al16_image_06",
        "dest": "al16_image_06_cleanup",
        "project": "relay_pcet_al16_06_Nm1",
        "retry_project": "relay_pcet_al16_06_Nm1_cleanup",
        "job_name": "RelayAl06Nm1Cleanup",
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
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--case", choices=CASES, required=True)
    args = parser.parse_args()
    cfg = CASES[args.case]

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
        if cfg["job_name"] in queue:
            raise RuntimeError("cleanup recovery already active")
        source = posixpath.join(BASE, cfg["source"])
        dest = posixpath.join(BASE, cfg["dest"])
        output = read_text(sftp, posixpath.join(source, "scan.out"))
        required = (
            "CDFT SCF loop converged",
            "PROGRAM ENDED AT",
            "ABORT in dbcsr_lib.F:322",
        )
        if not all(marker in output for marker in required):
            raise RuntimeError("source is not a converged-then-cleanup-aborted scan")
        if "SCF run NOT converged" in output or "CDFT SCF loop FAILED" in output:
            raise RuntimeError("source has a physical convergence failure")
        target = last_number(output, "Target value of constraint")
        current = last_number(output, "Current value of constraint")
        strength = last_number(output, "Strength of constraint")
        if abs(current - target) > 1.5e-4:
            raise RuntimeError(f"constraint outside tolerance: {target} vs {current}")
        wfn = posixpath.join(source, f"{cfg['project']}-RESTART.wfn")
        if sftp.stat(posixpath.join(ssh_ncw.REMOTE_ROOT, wfn)).st_size < 40_000_000:
            raise RuntimeError("restart WFN is too small")

        mkdir(sftp, dest)
        try:
            if sftp.stat(posixpath.join(ssh_ncw.REMOTE_ROOT, dest, "cleanup.out")).st_size:
                raise RuntimeError("cleanup destination already has output")
        except FileNotFoundError:
            pass
        value = read_text(sftp, posixpath.join(source, "scan.inp"))
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
            r"(?im)^\s*STRENGTH\s+[-+0-9.Ee]+",
            f"        STRENGTH {strength:.12f}",
            value,
            count=1,
        )
        write_text(sftp, posixpath.join(dest, "cleanup.inp"), value)
        run(client, f"cp {wfn} {posixpath.join(dest, 'converged-RESTART.wfn')}")
        slurm = f"""#!/bin/bash
#SBATCH -J {cfg['job_name']}
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
mpirun -np 40 cp2k.popt cleanup.inp 1>cleanup.out 2>cleanup.err
"""
        write_text(sftp, posixpath.join(dest, "submit.slurm"), slurm)
        submit = run(client, f"cd {dest} && sbatch submit.slurm")
        match = re.search(r"Submitted batch job (\d+)", submit)
        if not match:
            raise RuntimeError(f"cannot parse sbatch output: {submit}")
        job_id = match.group(1)

        manifest = read_text(sftp, posixpath.join(BASE, "scan_manifest.tsv"))
        lines = manifest.splitlines()
        fields = lines[cfg["task"] + 1].split("\t")
        if fields[7] != "prepared":
            raise RuntimeError(f"unexpected manifest state: {fields[7]}")
        fields[7] = (
            f"rejected_111141_{cfg['task']}_cleanup_abort_physical_converged_"
            f"recovery_{job_id}_pending"
        )
        lines[cfg["task"] + 1] = "\t".join(fields)
        write_text(sftp, posixpath.join(BASE, "scan_manifest.tsv"), "\n".join(lines) + "\n")
        scheduler = read_text(sftp, posixpath.join(BASE, "scheduler_manifest.tsv"))
        scheduler += (
            f"2026-08-18\tcleanup_abort\t111141_{cfg['task']}\trejected_scheduler\t"
            f"physical_CDFT_converged;target{target:.6f};final{current:.6f};"
            f"strength{strength:.12f};DBCSR_cleanup_abort\n"
            f"2026-08-18\tcleanup_recovery_submission\t{job_id}\tpending\t"
            f"{args.case};fixed_strength{strength:.12f};latest_WFN;n40;no_duplicate\n"
        )
        write_text(sftp, posixpath.join(BASE, "scheduler_manifest.tsv"), scheduler)
        print(job_id)
    finally:
        client.close()


if __name__ == "__main__":
    main()
