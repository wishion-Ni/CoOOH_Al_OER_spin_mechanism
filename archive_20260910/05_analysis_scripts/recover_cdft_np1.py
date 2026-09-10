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
    "cdft_charge_spin_20260812/cdft_O_Co48_scan"
)
SOURCE = posixpath.join(BASE, "charge_Np1")
DEST = posixpath.join(BASE, "charge_Np1_recovery")


def read_text(sftp, rel: str) -> str:
    with sftp.open(posixpath.join(ssh_ncw.REMOTE_ROOT, rel), "r") as handle:
        return handle.read().decode(errors="replace")


def write_text(sftp, rel: str, text: str) -> None:
    with sftp.open(posixpath.join(ssh_ncw.REMOTE_ROOT, rel), "w") as handle:
        handle.write(text)


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
    client.connect(hostname=ssh_ncw.HOST, port=ssh_ncw.PORT, username=ssh_ncw.USER,
                   password=ssh_ncw.load_password(), look_for_keys=False, allow_agent=False)
    try:
        sftp = client.open_sftp()
        queue = run(client, "squeue -u ftfan -h -o '%i %j %T'")
        if "Co48_Np1_retry" in queue:
            raise RuntimeError("N+1 recovery is already active")
        try:
            sftp.stat(posixpath.join(ssh_ncw.REMOTE_ROOT, DEST))
        except FileNotFoundError:
            sftp.mkdir(posixpath.join(ssh_ncw.REMOTE_ROOT, DEST))

        out = read_text(sftp, posixpath.join(SOURCE, "scan.out"))
        required = (
            "CDFT SCF loop converged in   9 iterations",
            "Current value of constraint :                            19.470064697420",
            "PROGRAM ENDED AT",
        )
        if not all(marker in out for marker in required):
            raise RuntimeError("source did not reach the documented converged N+1 state")

        text = read_text(sftp, posixpath.join(SOURCE, "scan.inp"))
        text = re.sub(r"(?im)^\s*PROJECT_NAME\s+\S+", "  PROJECT_NAME cdft_O_Co48_charge_Np1_retry", text, count=1)
        text = re.sub(
            r"(?im)^\s*WFN_RESTART_FILE_NAME\s+\S+",
            "    WFN_RESTART_FILE_NAME converged-RESTART.wfn",
            text,
            count=1,
        )
        text = re.sub(r"(?im)^\s*STRENGTH\s+[-+0-9.E]+", "        STRENGTH -0.321901237345", text, count=1)
        write_text(sftp, posixpath.join(DEST, "retry.inp"), text)
        run(
            client,
            f"cp {posixpath.join(SOURCE, 'cdft_O_Co48_charge_Np1-RESTART.wfn')} "
            f"{posixpath.join(DEST, 'converged-RESTART.wfn')}",
        )

        slurm = """#!/bin/bash
#SBATCH -J Co48_Np1_retry
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
        print(match.group(1))
    finally:
        client.close()


if __name__ == "__main__":
    main()
