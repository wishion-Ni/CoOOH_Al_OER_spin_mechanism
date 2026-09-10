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
    "cdft_charge_spin_20260812"
)
SOURCE = posixpath.join(BASE, "al16_valid_co48_O")
DEST = posixpath.join(BASE, "cdft_pilot_O_Co48_N0")
TARGET = 18.470


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
        try:
            sftp.stat(posixpath.join(ssh_ncw.REMOTE_ROOT, DEST))
        except FileNotFoundError:
            sftp.mkdir(posixpath.join(ssh_ncw.REMOTE_ROOT, DEST))

        queue = run(client, "squeue -u ftfan -h -o '%i %j %T'")
        if "Co48_cdft_N0" in queue:
            raise RuntimeError("pilot is already active")

        text = read_text(sftp, posixpath.join(SOURCE, "baseline.inp"))
        text = re.sub(r"(?im)^\s*PROJECT_NAME\s+\S+", "  PROJECT_NAME cdft_O_Co48_N0", text, count=1)
        text = re.sub(r"(?im)^\s*WFN_RESTART_FILE_NAME\s+\S+", "    WFN_RESTART_FILE_NAME baseline-RESTART.wfn", text, count=1)
        cdft = f"""      &CDFT
        TYPE_OF_CONSTRAINT HIRSHFELD
        ATOMIC_CHARGES TRUE
        STRENGTH 0.0
        TARGET {TARGET:.6f}
        &ATOM_GROUP
          ATOMS 48
          COEFF 1.0
          CONSTRAINT_TYPE CHARGE
        &END ATOM_GROUP
        &OUTER_SCF ON
          TYPE CDFT_CONSTRAINT
          EXTRAPOLATION_ORDER 2
          MAX_SCF 20
          EPS_SCF 1.0E-4
          OPTIMIZER NEWTON_LS
          STEP_SIZE -2.0
          &CDFT_OPT ON
            MAX_LS 5
            CONTINUE_LS
            FACTOR_LS 0.5
            JACOBIAN_STEP 1.0E-2
            JACOBIAN_FREQ 1 1
            JACOBIAN_TYPE FD1
            JACOBIAN_RESTART FALSE
          &END CDFT_OPT
        &END OUTER_SCF
        &HIRSHFELD_CONSTRAINT
          SHAPE_FUNCTION GAUSSIAN
          GAUSSIAN_SHAPE COVALENT
        &END HIRSHFELD_CONSTRAINT
      &END CDFT
"""
        text = re.sub(r"(?im)^(\s*&END\s+QS\b)", cdft + r"\1", text, count=1)
        write_text(sftp, posixpath.join(DEST, "pilot.inp"), text)
        run(client, f"cp {posixpath.join(SOURCE, 'cdf_base_al16_valid_co48_O-RESTART.wfn')} {posixpath.join(DEST, 'baseline-RESTART.wfn')}")

        slurm = """#!/bin/bash
#SBATCH -J Co48_cdft_N0
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
mpirun -np 28 cp2k.popt pilot.inp 1>pilot.out 2>pilot.err
"""
        write_text(sftp, posixpath.join(DEST, "submit.slurm"), slurm)
        submit = run(client, f"cd {DEST} && sbatch submit.slurm")
        job = re.search(r"Submitted batch job (\d+)", submit)
        if not job:
            raise RuntimeError(submit)
        print(job.group(1))
    finally:
        client.close()


if __name__ == "__main__":
    main()
