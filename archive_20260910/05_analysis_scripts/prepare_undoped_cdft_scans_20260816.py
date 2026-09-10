from __future__ import annotations

import csv
import importlib.util
import io
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
SOURCE_CASES = {
    "OH": "undoped_valid_co32_OH",
    "O": "undoped_valid_co32_O",
    "OOH": "undoped_valid_co32_OOH",
}
FRAGMENTS = {
    "OH": (32, 211, 212),
    "O": (32, 211),
    "OOH": (32, 211, 212, 213),
}


def read_text(sftp, rel: str) -> str:
    with sftp.open(posixpath.join(ssh_ncw.REMOTE_ROOT, rel), "r") as handle:
        return handle.read().decode(errors="replace")


def write_text(sftp, rel: str, content: str) -> None:
    with sftp.open(posixpath.join(ssh_ncw.REMOTE_ROOT, rel), "w") as handle:
        handle.write(content)


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


def make_input(
    baseline: str,
    name: str,
    atoms: tuple[int, ...],
    constraint: str,
    target: float,
    outer_max: int,
) -> str:
    value = re.sub(
        r"(?im)^\s*PROJECT_NAME\s+\S+",
        f"  PROJECT_NAME undop_cdft_{name}",
        baseline,
        count=1,
    )
    value = re.sub(
        r"(?im)^\s*WFN_RESTART_FILE_NAME\s+\S+",
        "    WFN_RESTART_FILE_NAME baseline-RESTART.wfn",
        value,
        count=1,
    )
    atom_text = " ".join(str(atom) for atom in atoms)
    coeff_text = " ".join("1.0" for _ in atoms)
    cdft = f"""      &CDFT
        TYPE_OF_CONSTRAINT HIRSHFELD
        ATOMIC_CHARGES TRUE
        STRENGTH 0.0
        TARGET {target:.6f}
        &ATOM_GROUP
          ATOMS {atom_text}
          COEFF {coeff_text}
          CONSTRAINT_TYPE {constraint}
        &END ATOM_GROUP
        &OUTER_SCF ON
          TYPE CDFT_CONSTRAINT
          EXTRAPOLATION_ORDER 2
          MAX_SCF {outer_max}
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
        queue = run(client, "squeue -u ftfan -h -o '%j'")
        if "Undop_cdft_scan" in queue:
            raise RuntimeError("an undoped cDFT scan array is already active")
        try:
            sftp.stat(posixpath.join(ssh_ncw.REMOTE_ROOT, SCAN))
            raise RuntimeError(f"refusing to overwrite {SCAN}")
        except FileNotFoundError:
            pass
        mkdir(sftp, SCAN)

        rows = list(
            csv.DictReader(
                io.StringIO(read_text(sftp, posixpath.join(BASE, "baseline_population_summary.tsv"))),
                delimiter="\t",
            )
        )
        populations = {
            (row["case"], int(row["atom"])): float(row["hirsh_population"])
            for row in rows
        }
        spins = {
            (row["case"], int(row["atom"])): float(row["hirsh_spin"])
            for row in rows
        }

        cases: list[tuple[str, str, tuple[int, ...], str, float, int]] = []
        for state in ("OH", "O", "OOH"):
            source = SOURCE_CASES[state]
            co_pop = populations[(source, 32)]
            cases.extend(
                [
                    (f"{state}_Co_Nm1", source, (32,), "CHARGE", co_pop - 1.0, 30),
                    (f"{state}_Co_Np1", source, (32,), "CHARGE", co_pop + 1.0, 30),
                ]
            )
            if state == "O":
                co_spin = spins[(source, 32)]
                cases.extend(
                    [
                        ("O_Co_Mm2", source, (32,), "MAGNETIZATION", co_spin - 2.0, 30),
                        ("O_Co_Mp2", source, (32,), "MAGNETIZATION", co_spin + 2.0, 30),
                    ]
                )
            atoms = FRAGMENTS[state]
            fragment_pop = sum(populations[(source, atom)] for atom in atoms)
            cases.extend(
                [
                    (f"{state}_frag_Nm1", source, atoms, "CHARGE", fragment_pop - 1.0, 40),
                    (f"{state}_frag_Np1", source, atoms, "CHARGE", fragment_pop + 1.0, 40),
                ]
            )

        manifest = ["task\tcase\tsource\tconstraint\ttarget\tatoms\tstatus"]
        names = []
        for task, (name, source, atoms, constraint, target, outer_max) in enumerate(cases):
            names.append(name)
            dest = posixpath.join(SCAN, name)
            mkdir(sftp, dest)
            baseline = read_text(sftp, posixpath.join(BASE, source, "baseline.inp"))
            write_text(
                sftp,
                posixpath.join(dest, "scan.inp"),
                make_input(baseline, name, atoms, constraint, target, outer_max),
            )
            wfn = f"cdf_base_{source}-RESTART.wfn"
            run(
                client,
                f"cp {posixpath.join(BASE, source, wfn)} "
                f"{posixpath.join(dest, 'baseline-RESTART.wfn')}",
            )
            manifest.append(
                f"{task}\t{name}\t{source}\t{constraint}\t{target:.6f}\t"
                f"{','.join(str(atom) for atom in atoms)}\tprepared"
            )
        write_text(sftp, posixpath.join(SCAN, "scan_manifest.tsv"), "\n".join(manifest) + "\n")

        slurm = f"""#!/bin/bash
#SBATCH -J Undop_cdft_scan
#SBATCH --nodes=1
#SBATCH --ntasks=28
#SBATCH --partition=n28
#SBATCH --array=0-{len(cases) - 1}%1
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
CASES=({' '.join(names)})
CASE=${{CASES[$SLURM_ARRAY_TASK_ID]}}
cd "$SLURM_SUBMIT_DIR/$CASE"
mpirun -np 28 cp2k.popt scan.inp 1>scan.out 2>scan.err
"""
        write_text(sftp, posixpath.join(SCAN, "submit.slurm"), slurm)
        submit = run(client, f"cd {SCAN} && sbatch submit.slurm")
        match = re.search(r"Submitted batch job (\d+)", submit)
        if not match:
            raise RuntimeError(f"cannot parse sbatch output: {submit}")
        job_id = match.group(1)

        scheduler_rel = posixpath.join(BASE, "scheduler_manifest.tsv")
        scheduler = read_text(sftp, scheduler_rel)
        scheduler += (
            f"2026-08-16\tmatched_scan_submission\t{job_id}_0-{len(cases)-1}\t"
            "pending\tundoped_Co32_Co_only_and_Co_adsorbate_N0pm1;"
            "O_M0pm2;targets_from_valid_baselines;fixed_geometry;"
            "n28_concurrency1;no_duplicates\n"
        )
        write_text(sftp, scheduler_rel, scheduler)
        print(job_id)
    finally:
        client.close()


if __name__ == "__main__":
    main()
