from __future__ import annotations

import importlib.util
import math
import posixpath
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / ".codex/skills/ftfan-ncw-ssh/scripts/ssh_ncw.py"
spec = importlib.util.spec_from_file_location("ssh_ncw", HELPER)
ssh_ncw = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(ssh_ncw)

DEST = (
    "sfs/CoOH/cp2k/thermo_vib_5OH_U100_current_20260704/"
    "proton_relay_al16_vs_undoped_20260817"
)
CASES = {
    "al16": {
        "input": (
            "sfs/CoOH/cp2k/Al16/oer/spin_config_scan_site03_5OH_current_20260714/"
            "cdft_charge_spin_20260812/al16_valid_co48_OH/baseline.inp"
        ),
        "wfn": (
            "sfs/CoOH/cp2k/Al16/oer/spin_config_scan_site03_5OH_current_20260714/"
            "cdft_charge_spin_20260812/al16_valid_co48_OH/seed-RESTART.wfn"
        ),
        "active_co": 48,
        "donor_h": 221,
        "donor_o": 222,
        "acceptor_metal": 32,
        "acceptor_h": 102,
        "acceptor_o": 210,
        "acceptor_label": "Al32-O210H102",
    },
    "undoped": {
        "input": (
            "sfs/CoOH/cp2k/thermo_vib_5OH_U100_current_20260704/"
            "cdft_charge_spin_undoped_20260816/undoped_valid_co32_OH/baseline.inp"
        ),
        "wfn": (
            "sfs/CoOH/cp2k/thermo_vib_5OH_U100_current_20260704/"
            "cdft_charge_spin_undoped_20260816/undoped_valid_co32_OH/"
            "seed-RESTART.wfn"
        ),
        "active_co": 32,
        "donor_h": 211,
        "donor_o": 212,
        "acceptor_metal": 16,
        "acceptor_h": 216,
        "acceptor_o": 215,
        "acceptor_label": "Co16-O215H216",
    },
}
TRANSFER_FRACTIONS = (0.20, 0.40, 0.60, 0.80, 1.00)


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


def parse_input(text: str):
    lengths = []
    for axis in "ABC":
        match = re.search(
            rf"(?m)^\s*{axis}\s+([-+0-9.Ee]+)\s+([-+0-9.Ee]+)\s+([-+0-9.Ee]+)",
            text,
        )
        if not match:
            raise RuntimeError(f"missing cell vector {axis}")
        vector = tuple(float(match.group(i)) for i in range(1, 4))
        if sum(abs(vector[i]) for i in range(3) if i != len(lengths)) > 1e-8:
            raise RuntimeError("pilot expects an orthorhombic cell")
        lengths.append(math.sqrt(sum(value * value for value in vector)))

    block = re.search(r"(?ms)^(\s*&COORD\s*$\n)(.*?)(^\s*&END COORD\s*$)", text)
    if not block:
        raise RuntimeError("missing COORD block")
    coord_lines = block.group(2).splitlines()
    atoms = []
    line_indices = []
    for line_index, line in enumerate(coord_lines):
        fields = line.split()
        if len(fields) >= 4 and fields[0] in {"Co", "Al", "O", "H"}:
            atoms.append((fields[0], tuple(float(value) for value in fields[1:4])))
            line_indices.append(line_index)
    return tuple(lengths), atoms, coord_lines, line_indices, block


def unwrap_near(point, reference, cell):
    values = []
    for value, center, length in zip(point, reference, cell):
        delta = value - center
        values.append(center + delta - round(delta / length) * length)
    return tuple(values)


def vector(a, b):
    return tuple(y - x for x, y in zip(a, b))


def add(a, b):
    return tuple(x + y for x, y in zip(a, b))


def scale(a, factor):
    return tuple(value * factor for value in a)


def norm(a):
    return math.sqrt(sum(value * value for value in a))


def interpolate(a, b, fraction):
    return tuple(x + fraction * (y - x) for x, y in zip(a, b))


def replace_h_coordinate(text, parsed, atom_index: int, coordinate) -> str:
    _, atoms, coord_lines, line_indices, block = parsed
    symbol = atoms[atom_index - 1][0]
    if symbol != "H":
        raise RuntimeError(f"atom {atom_index} is {symbol}, expected H")
    coord_lines = list(coord_lines)
    coord_lines[line_indices[atom_index - 1]] = (
        f"       H {coordinate[0]:18.10f} {coordinate[1]:18.10f} "
        f"{coordinate[2]:18.10f}"
    )
    new_block = block.group(1) + "\n".join(coord_lines) + "\n" + block.group(3)
    return text[: block.start()] + new_block + text[block.end() :]


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
        if "ProtonRelayPilot" in queue:
            raise RuntimeError("proton relay pilot is already active")
        try:
            sftp.stat(posixpath.join(ssh_ncw.REMOTE_ROOT, DEST))
            raise RuntimeError(f"destination already exists: {DEST}")
        except FileNotFoundError:
            pass

        mkdir(sftp, DEST)
        manifest_rows = [
            "task\tcase\timage\tsegment\tactive_co\tdonor_OH\tacceptor_site\t"
            "Odonor_Oacceptor_A\tdonorH_acceptorO_A\tstatus"
        ]
        task_dirs = []
        task_id = 0
        for case_name, cfg in CASES.items():
            source = read_text(sftp, cfg["input"])
            parsed = parse_input(source)
            cell, atoms, _, _, _ = parsed
            donor_o = atoms[cfg["donor_o"] - 1][1]
            donor_h = unwrap_near(atoms[cfg["donor_h"] - 1][1], donor_o, cell)
            acceptor_o = unwrap_near(
                atoms[cfg["acceptor_o"] - 1][1], donor_o, cell
            )
            oo_vector = vector(donor_o, acceptor_o)
            oo_distance = norm(oo_vector)
            unit = scale(oo_vector, 1.0 / oo_distance)
            donor_h_length = norm(vector(donor_o, donor_h))
            rotated = add(donor_o, scale(unit, donor_h_length))
            product = add(acceptor_o, scale(unit, -donor_h_length))
            points = [("initial", donor_h), ("rotated", rotated)]
            points.extend(
                (f"transfer_{fraction:.2f}", interpolate(rotated, product, fraction))
                for fraction in TRANSFER_FRACTIONS
            )

            case_dir = posixpath.join(DEST, case_name)
            mkdir(sftp, case_dir)
            for image_index, (segment, coordinate) in enumerate(points):
                image_dir = posixpath.join(case_dir, f"image_{image_index:02d}")
                mkdir(sftp, image_dir)
                project = f"relay_{case_name}_{image_index:02d}"
                value = replace_h_coordinate(
                    source, parsed, cfg["donor_h"], coordinate
                )
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
                    r"(?im)^\s*EPS_SCF\s+1\.0E-7\s*$",
                    "       EPS_SCF 1.0E-6",
                    value,
                    count=1,
                )
                write_text(sftp, posixpath.join(image_dir, "scan.inp"), value)
                run(
                    client,
                    f"cp {cfg['wfn']} {posixpath.join(image_dir, 'seed-RESTART.wfn')}",
                )
                h_to_acceptor = norm(vector(coordinate, acceptor_o))
                manifest_rows.append(
                    f"{task_id}\t{case_name}\t{image_index}\t{segment}\t"
                    f"{cfg['active_co']}\tO{cfg['donor_o']}-H{cfg['donor_h']}\t"
                    f"{cfg['acceptor_label']}\t{oo_distance:.6f}\t"
                    f"{h_to_acceptor:.6f}\tprepared"
                )
                task_dirs.append(posixpath.join(case_name, f"image_{image_index:02d}"))
                task_id += 1

        write_text(sftp, posixpath.join(DEST, "scan_manifest.tsv"), "\n".join(manifest_rows) + "\n")
        task_dir_text = " ".join(task_dirs)
        slurm = f"""#!/bin/bash
#SBATCH -J ProtonRelayPilot
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

TASK_DIRS=({task_dir_text})
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
            f"2026-08-17\tfixed_path_submission\t{job_id}\tpending_or_running\t"
            "neutral_fixed_heavy_atom_proton_relay_pilot;Al16_CoOH_to_AlOH_vs_"
            "undoped_CoOH_to_CoOH;7_images_each;n40_40ranks;concurrency2;"
            "same_baseline_WFN_and_DFTplusU;not_final_NEB_or_CHE\n"
        )
        write_text(sftp, posixpath.join(DEST, "scheduler_manifest.tsv"), scheduler)
        print(job_id)
        print("\n".join(manifest_rows[:3] + manifest_rows[7:10]))
    finally:
        client.close()


if __name__ == "__main__":
    main()
