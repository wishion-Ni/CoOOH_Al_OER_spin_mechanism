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
SCAN = posixpath.join(BASE, "cdft_OH_OOH_Co48_charge_scan")
CASES = (
    ("OH_charge_Nm1", "al16_valid_co48_OH", 17.458),
    ("OH_charge_Np1", "al16_valid_co48_OH", 19.458),
    ("OOH_charge_Nm1", "al16_valid_co48_OOH", 17.379),
    ("OOH_charge_Np1", "al16_valid_co48_OOH", 19.379),
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
    _, stdout, stderr = client.exec_command(f"cd {ssh_ncw.REMOTE_ROOT} && {command}")
    code = stdout.channel.recv_exit_status()
    out = stdout.read().decode()
    err = stderr.read().decode()
    if code:
        raise RuntimeError(err or out)
    return out


def make_input(baseline: str, name: str, target: float) -> str:
    value = re.sub(
        r"(?im)^\s*PROJECT_NAME\s+\S+",
        f"  PROJECT_NAME cdft_Co48_{name}",
        baseline,
        count=1,
    )
    value = re.sub(
        r"(?im)^\s*WFN_RESTART_FILE_NAME\s+\S+",
        "    WFN_RESTART_FILE_NAME baseline-RESTART.wfn",
        value,
        count=1,
    )
    cdft = f"""      &CDFT
        TYPE_OF_CONSTRAINT HIRSHFELD
        ATOMIC_CHARGES TRUE
        STRENGTH 0.0
        TARGET {target:.6f}
        &ATOM_GROUP
          ATOMS 48
          COEFF 1.0
          CONSTRAINT_TYPE CHARGE
        &END ATOM_GROUP
        &OUTER_SCF ON
          TYPE CDFT_CONSTRAINT
          EXTRAPOLATION_ORDER 2
          MAX_SCF 30
          EPS_SCF 1.0E-4
          OPTIMIZER NEWTON_LS
          STEP_SIZE -2.0
          &CDFT_OPT ON
            MAX_LS 8
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
    return re.sub(r"(?im)^(\s*&END\s+QS\b)", cdft + r"\1", value, count=1)


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
        if "Co48_cdft_OH_OOH_q" in queue:
            raise RuntimeError("OH/OOH charge scan is already active")
        mkdir(sftp, SCAN)
        manifest = ["task\tcase\tconstraint\ttarget\tactive_atom\tstatus"]
        for task, (name, source_name, target) in enumerate(CASES):
            dest = posixpath.join(SCAN, name)
            mkdir(sftp, dest)
            output = posixpath.join(dest, "scan.out")
            try:
                if sftp.stat(posixpath.join(ssh_ncw.REMOTE_ROOT, output)).st_size:
                    raise RuntimeError(f"refusing to overwrite existing output: {output}")
            except FileNotFoundError:
                pass
            source = posixpath.join(BASE, source_name)
            baseline = read_text(sftp, posixpath.join(source, "baseline.inp"))
            write_text(sftp, posixpath.join(dest, "scan.inp"), make_input(baseline, name, target))
            wfn = f"cdf_base_{source_name}-RESTART.wfn"
            run(client, f"cp {posixpath.join(source, wfn)} {posixpath.join(dest, 'baseline-RESTART.wfn')}")
            manifest.append(f"{task}\t{name}\tCHARGE\t{target:.6f}\t48\tprepared")
        write_text(sftp, posixpath.join(SCAN, "scan_manifest.tsv"), "\n".join(manifest) + "\n")

        slurm = """#!/bin/bash
#SBATCH -J Co48_cdft_OH_OOH_q
#SBATCH --nodes=1
#SBATCH --ntasks=28
#SBATCH --partition=n28
#SBATCH --array=0-3%1
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
CASES=(OH_charge_Nm1 OH_charge_Np1 OOH_charge_Nm1 OOH_charge_Np1)
CASE=${CASES[$SLURM_ARRAY_TASK_ID]}
cd "$SLURM_SUBMIT_DIR/$CASE"
mpirun -np 28 cp2k.popt scan.inp 1>scan.out 2>scan.err
"""
        write_text(sftp, posixpath.join(SCAN, "submit.slurm"), slurm)
        submit = run(client, f"cd {SCAN} && sbatch submit.slurm")
        match = re.search(r"Submitted batch job (\d+)", submit)
        if not match:
            raise RuntimeError(submit)
        job_id = match.group(1)

        sched_rel = posixpath.join(BASE, "scheduler_manifest.tsv")
        sched = read_text(sftp, sched_rel)
        row = (
            f"2026-08-15\tscan_submission\t{job_id}_0-3\tpending\t"
            "OH_OOH_Co48_charge_N0pm1;fixed_geometry;array_concurrency1;no_duplicates"
        )
        if row not in sched:
            sched += ("" if sched.endswith("\n") else "\n") + row + "\n"
            write_text(sftp, sched_rel, sched)
        print(job_id)
    finally:
        client.close()


if __name__ == "__main__":
    main()
