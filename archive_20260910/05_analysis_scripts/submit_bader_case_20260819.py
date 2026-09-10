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

VASP_ROOT = (
    "sfs/CoOH/cp2k/Al16/oer/spin_config_scan_site03_5OH_current_20260714/"
    "vasp_jacs6c06054_reconstructed_exact_Al16_3x2_20260809"
)
ANALYSIS = posixpath.join(VASP_ROOT, "electronic_structure_al_contribution_20260818")
FIXED = posixpath.join(ANALYSIS, "fixed_geometry_bader_pdos")
TOOLS = posixpath.join(ANALYSIS, "tools")
MANIFEST = posixpath.join(ANALYSIS, "analysis_manifest.tsv")
SCHEDULER = posixpath.join(ANALYSIS, "scheduler_manifest.tsv")
CASES = (
    ("Al16_adjacent", "bare"),
    ("undoped_control", "bare"),
    ("Al16_adjacent", "OH"),
    ("undoped_control", "OH"),
    ("Al16_adjacent", "O"),
    ("undoped_control", "O"),
    ("Al16_adjacent", "OOH_o03"),
    ("undoped_control", "OOH_o03"),
)

SUM_SCRIPT = r'''#!/usr/bin/env python
import sys


def header(handle):
    lines = [handle.readline() for _ in range(5)]
    species_or_counts = handle.readline()
    lines.append(species_or_counts)
    fields = species_or_counts.split()
    if fields and all(field.lstrip("+-").isdigit() for field in fields):
        counts = [int(field) for field in fields]
    else:
        count_line = handle.readline()
        lines.append(count_line)
        counts = [int(field) for field in count_line.split()]
    line = handle.readline()
    lines.append(line)
    if line.strip().lower().startswith("s"):
        line = handle.readline()
        lines.append(line)
    for _ in range(sum(counts)):
        lines.append(handle.readline())
    while True:
        line = handle.readline()
        if not line:
            raise RuntimeError("missing density grid")
        lines.append(line)
        fields = line.split()
        if len(fields) == 3 and all(field.lstrip("+-").isdigit() for field in fields):
            dims = [int(field) for field in fields]
            return "".join(lines), dims[0] * dims[1] * dims[2]


def values(handle):
    while True:
        line = handle.readline()
        if not line:
            raise RuntimeError("density ended early")
        fields = line.split()
        if fields:
            return [float(field) for field in fields]


def main():
    if len(sys.argv) != 4:
        raise SystemExit("usage: sum_chgcar.py AECCAR0 AECCAR2 CHGCAR_sum")
    with open(sys.argv[1], "r") as first, open(sys.argv[2], "r") as second, open(sys.argv[3], "w") as out:
        first_header, n_first = header(first)
        _, n_second = header(second)
        if n_first != n_second:
            raise RuntimeError("density grids differ")
        out.write(first_header)
        written = 0
        while written < n_first:
            left = values(first)
            right = values(second)
            if len(left) != len(right) or written + len(left) > n_first:
                raise RuntimeError("density line layout differs")
            out.write("".join(" {0:18.11E}".format(a + b) for a, b in zip(left, right)) + "\n")
            written += len(left)
        if written != n_first:
            raise RuntimeError("incomplete summed density")


if __name__ == "__main__":
    main()
'''


def remote(rel: str) -> str:
    return posixpath.join(ssh_ncw.REMOTE_ROOT, rel)


def run(client, command: str) -> str:
    _, stdout, stderr = client.exec_command(f"cd {ssh_ncw.REMOTE_ROOT} && {command}")
    code = stdout.channel.recv_exit_status()
    output = stdout.read().decode(errors="replace")
    error = stderr.read().decode(errors="replace")
    if code:
        raise RuntimeError(error or output)
    return output


def read_text(sftp, rel: str) -> str:
    with sftp.open(remote(rel), "r") as handle:
        return handle.read().decode(errors="replace")


def write_text(sftp, rel: str, value: str) -> None:
    with sftp.open(remote(rel), "w") as handle:
        handle.write(value)


def geometry(text: str) -> tuple[list[list[float]], list[list[float]]]:
    lines = text.splitlines()
    scale = float(lines[1].split()[0])
    lattice = [[scale * float(value) for value in lines[index].split()[:3]] for index in range(2, 5)]
    cursor = 5
    fields = lines[cursor].split()
    if all(field.lstrip("+-").isdigit() for field in fields):
        counts = [int(field) for field in fields]
    else:
        cursor += 1
        counts = [int(field) for field in lines[cursor].split()]
    cursor += 1
    if lines[cursor].strip().lower().startswith("s"):
        cursor += 1
    direct = lines[cursor].strip().lower().startswith("d")
    cursor += 1
    coordinates = [[float(value) for value in lines[cursor + index].split()[:3]] for index in range(sum(counts))]
    if not direct:
        coordinates = [[value / scale for value in row] for row in coordinates]
    return lattice, coordinates


def unchanged_geometry(poscar: str, contcar: str, tolerance: float = 2e-10) -> bool:
    lattice_a, coords_a = geometry(poscar)
    lattice_b, coords_b = geometry(contcar)
    if len(coords_a) != len(coords_b):
        return False
    values = [abs(a - b) for row_a, row_b in zip(lattice_a, lattice_b) for a, b in zip(row_a, row_b)]
    for row_a, row_b in zip(coords_a, coords_b):
        for a, b in zip(row_a, row_b):
            delta = abs(a - b)
            values.append(min(delta, abs(delta - 1.0)))
    return max(values, default=0.0) <= tolerance


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", type=int, choices=range(8), required=True)
    args = parser.parse_args()
    branch, state = CASES[args.task]
    case = posixpath.join(FIXED, branch, state)
    job_name = f"Bader{args.task}AlCtr"

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
        queue = run(client, "squeue -u ftfan -h -o '%i|%j|%T'")
        if job_name in queue:
            raise RuntimeError(f"Bader task {args.task} is already active")
        outcar = read_text(sftp, posixpath.join(case, "OUTCAR"))
        if "General timing and accounting informations" not in outcar:
            raise RuntimeError("VASP source has not terminated normally")
        if any(marker in outcar for marker in ("VERY BAD NEWS", "internal error", "FATAL")):
            raise RuntimeError("VASP source contains a fatal marker")
        for name, minimum in (
            ("AECCAR0", 500_000_000),
            ("AECCAR2", 500_000_000),
            ("DOSCAR", 100_000_000),
            ("vasprun.xml", 100_000_000),
        ):
            size = sftp.stat(remote(posixpath.join(case, name))).st_size
            if size < minimum:
                raise RuntimeError(f"incomplete {name}: {size}")
        if not unchanged_geometry(
            read_text(sftp, posixpath.join(case, "POSCAR")),
            read_text(sftp, posixpath.join(case, "CONTCAR")),
        ):
            raise RuntimeError("fixed geometry changed")
        if any(name in sftp.listdir(remote(case)) for name in ("ACF.dat", "CHGCAR_sum", "bader.out")):
            raise RuntimeError("Bader outputs already exist")

        write_text(sftp, posixpath.join(TOOLS, "sum_chgcar.py"), SUM_SCRIPT)
        slurm = f"""#!/bin/bash
#SBATCH --job-name={job_name}
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --partition=n28
#SBATCH --time=06:00:00
#SBATCH --output=%J.stdout
#SBATCH --error=%J.stderr

set -eo pipefail
cd {remote(case)}
python {remote(posixpath.join(TOOLS, 'sum_chgcar.py'))} AECCAR0 AECCAR2 CHGCAR_sum
{remote(posixpath.join(TOOLS, 'bader-bin', 'bader'))} CHGCAR -ref CHGCAR_sum > bader.out
test -s ACF.dat
"""
        write_text(sftp, posixpath.join(case, "bader.slurm"), slurm)
        submitted = run(client, f"cd {case} && sbatch bader.slurm")
        match = re.search(r"Submitted batch job (\d+)", submitted)
        if not match:
            raise RuntimeError(f"cannot parse sbatch output: {submitted}")
        job_id = match.group(1)

        manifest = read_text(sftp, MANIFEST)
        lines = manifest.splitlines()
        fields = lines[args.task + 1].split("\t")
        if fields[7] != "prepared":
            raise RuntimeError(f"unexpected analysis status: {fields[7]}")
        fields[7] = f"valid_vasp_111172_{args.task}_bader_{job_id}_pending"
        lines[args.task + 1] = "\t".join(fields)
        write_text(sftp, MANIFEST, "\n".join(lines) + "\n")

        scheduler = read_text(sftp, SCHEDULER)
        scheduler += (
            f"2026-08-19\tfixed_geometry_bader_submission\t{job_id}\tn28\t1\t1\t"
            f"task{args.task};{branch};{state};AECCAR0_plus_AECCAR2_reference;no_duplicate\n"
        )
        write_text(sftp, SCHEDULER, scheduler)
        print(job_id)
    finally:
        client.close()


if __name__ == "__main__":
    main()
