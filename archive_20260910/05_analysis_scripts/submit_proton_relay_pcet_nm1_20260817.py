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
    "proton_relay_al16_vs_undoped_20260817"
)
DEST = posixpath.join(BASE, "pcet_CoO_fragment_Nm1")
CASES = {
    "al16": {
        "images": (0, 4, 6),
        "atoms": (48, 222),
        "template": (
            "sfs/CoOH/cp2k/Al16/oer/spin_config_scan_site03_5OH_current_20260714/"
            "cdft_charge_spin_20260812/cdft_Co48_adsorbate_fragment_charge_scan/"
            "OH_frag_Nm1/scan.inp"
        ),
    },
    "undoped": {
        "images": (0, 4, 6),
        "atoms": (32, 212),
        "template": (
            "sfs/CoOH/cp2k/thermo_vib_5OH_U100_current_20260704/"
            "cdft_charge_spin_undoped_20260816/matched_cdft_scans/"
            "OH_frag_Nm1_recovery/retry.inp"
        ),
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


def coord_block(text: str) -> str:
    match = re.search(r"(?ms)^\s*&COORD\s*$.*?^\s*&END COORD\s*$", text)
    if not match:
        raise RuntimeError("missing COORD block")
    return match.group(0)


def final_hirshfeld_population(text: str, atom_index: int) -> float:
    start = text.rfind("Hirshfeld Charges")
    if start < 0:
        raise RuntimeError("missing Hirshfeld table")
    table = text[start:]
    match = re.search(
        rf"(?m)^\s*{atom_index}\s+\S+\s+\d+\s+[-+0-9.]+\s+"
        r"([-+0-9.]+)\s+([-+0-9.]+)\s+[-+0-9.]+\s+[-+0-9.]+\s*$",
        table,
    )
    if not match:
        raise RuntimeError(f"missing Hirshfeld atom {atom_index}")
    return float(match.group(1)) + float(match.group(2))


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
        if "RelayPCETNm1" in queue:
            raise RuntimeError("relay PCET N-1 array is already active")
        try:
            sftp.stat(posixpath.join(ssh_ncw.REMOTE_ROOT, DEST))
            raise RuntimeError(f"destination already exists: {DEST}")
        except FileNotFoundError:
            pass
        mkdir(sftp, DEST)

        task_dirs = []
        rows = [
            "task\tcase\timage\tconstraint\ttarget\tatoms\tunconstrained_energy_Ha\tstatus"
        ]
        task_id = 0
        for case, cfg in CASES.items():
            template = read_text(sftp, cfg["template"])
            for image in cfg["images"]:
                image_dir = posixpath.join(BASE, case, f"image_{image:02d}")
                scan_input = read_text(sftp, posixpath.join(image_dir, "scan.inp"))
                scan_output = read_text(sftp, posixpath.join(image_dir, "scan.out"))
                if "PROGRAM ENDED AT" not in scan_output:
                    raise RuntimeError(f"unconstrained {case} image {image} is not valid")
                populations = [
                    final_hirshfeld_population(scan_output, atom) for atom in cfg["atoms"]
                ]
                target = round(sum(populations) - 1.0, 3)
                energies = re.findall(
                    r"ENERGY\| Total FORCE_EVAL \( QS \) energy \[a\.u\.\]:\s*"
                    r"([-+0-9.Ee]+)",
                    scan_output,
                )
                if not energies:
                    raise RuntimeError("missing unconstrained energy")
                unconstrained_energy = float(energies[-1])

                value = re.sub(
                    r"(?ms)^\s*&COORD\s*$.*?^\s*&END COORD\s*$",
                    coord_block(scan_input),
                    template,
                    count=1,
                )
                project = f"relay_pcet_{case}_{image:02d}_Nm1"
                value = re.sub(
                    r"(?im)^\s*PROJECT_NAME\s+\S+",
                    f"  PROJECT_NAME {project}",
                    value,
                    count=1,
                )
                value = re.sub(
                    r"(?im)^\s*WFN_RESTART_FILE_NAME\s+\S+",
                    "    WFN_RESTART_FILE_NAME seed-RESTART.wfn",
                    value,
                    count=1,
                )
                value = re.sub(
                    r"(?im)^\s*STRENGTH\s+[-+0-9.Ee]+",
                    "        STRENGTH 0.0",
                    value,
                    count=1,
                )
                value = re.sub(
                    r"(?im)^\s*TARGET\s+[-+0-9.Ee]+",
                    f"        TARGET {target:.3f}",
                    value,
                    count=1,
                )
                value = re.sub(
                    r"(?im)^\s*ATOMS\s+.*$",
                    "          ATOMS " + " ".join(str(atom) for atom in cfg["atoms"]),
                    value,
                    count=1,
                )
                value = re.sub(
                    r"(?im)^\s*COEFF\s+.*$",
                    "          COEFF " + " ".join("1.0" for _ in cfg["atoms"]),
                    value,
                    count=1,
                )
                value = re.sub(
                    r"(?im)^\s*EPS_SCF\s+1\.0E-7\s*$",
                    "       EPS_SCF 1.0E-6",
                    value,
                    count=1,
                )

                destination = posixpath.join(DEST, f"{case}_image_{image:02d}")
                mkdir(sftp, destination)
                write_text(sftp, posixpath.join(destination, "scan.inp"), value)
                source_wfn = posixpath.join(
                    image_dir, f"relay_{case}_{image:02d}-RESTART.wfn"
                )
                size = sftp.stat(posixpath.join(ssh_ncw.REMOTE_ROOT, source_wfn)).st_size
                if size < 40_000_000:
                    raise RuntimeError(f"restart WFN is too small: {source_wfn}")
                run(client, f"cp {source_wfn} {posixpath.join(destination, 'seed-RESTART.wfn')}")
                task_dirs.append(f"{case}_image_{image:02d}")
                rows.append(
                    f"{task_id}\t{case}\t{image}\tCoO_fragment_Nm1\t{target:.3f}\t"
                    f"{','.join(str(atom) for atom in cfg['atoms'])}\t"
                    f"{unconstrained_energy:.12f}\tprepared"
                )
                task_id += 1

        write_text(sftp, posixpath.join(DEST, "scan_manifest.tsv"), "\n".join(rows) + "\n")
        slurm = f"""#!/bin/bash
#SBATCH -J RelayPCETNm1
#SBATCH --nodes=1
#SBATCH --ntasks=40
#SBATCH --partition=n40
#SBATCH --array=0-{len(task_dirs) - 1}%2
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

TASK_DIRS=({' '.join(task_dirs)})
TASK_DIR=${{TASK_DIRS[$SLURM_ARRAY_TASK_ID]}}
cd "$SLURM_SUBMIT_DIR/$TASK_DIR"
mpirun -np 40 cp2k.popt scan.inp 1>scan.out 2>scan.err
"""
        write_text(sftp, posixpath.join(DEST, "submit.slurm"), slurm)
        submit = run(client, f"cd {DEST} && sbatch submit.slurm")
        match = re.search(r"Submitted batch job (\d+)", submit)
        if not match:
            raise RuntimeError(f"cannot parse sbatch output: {submit}")
        job_id = match.group(1)
        scheduler = (
            "date\tevent\tjob\tstate\tdetails\n"
            f"2026-08-17\tCoO_fragment_Nm1_submission\t{job_id}\tpending_or_running\t"
            "Al16_and_undoped_images0_4_6;targets_derived_from_each_unconstrained_"
            "Hirshfeld_population_minus1;fixed_geometry;n40_40ranks;concurrency2;"
            "validated_CDFT_syntax;no_duplicates\n"
        )
        write_text(sftp, posixpath.join(DEST, "scheduler_manifest.tsv"), scheduler)
        print(job_id)
        print("\n".join(rows))
    finally:
        client.close()


if __name__ == "__main__":
    main()
