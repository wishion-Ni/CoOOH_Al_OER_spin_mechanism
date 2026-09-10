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

VASP_ROOT = (
    "sfs/CoOH/cp2k/Al16/oer/spin_config_scan_site03_5OH_current_20260714/"
    "vasp_jacs6c06054_reconstructed_exact_Al16_3x2_20260809"
)
ANALYSIS = posixpath.join(VASP_ROOT, "electronic_structure_al_contribution_20260818")
TOOLS = posixpath.join(ANALYSIS, "tools")
MANIFEST = posixpath.join(ANALYSIS, "analysis_manifest.tsv")
SCHEDULER = posixpath.join(ANALYSIS, "scheduler_manifest.tsv")
AL_CASE = posixpath.join(ANALYSIS, "fixed_geometry_bader_pdos/Al16_adjacent/bare")
CONTROL_CASE = posixpath.join(ANALYSIS, "fixed_geometry_bader_pdos/undoped_control/bare")
RESULT = posixpath.join(ANALYSIS, "bare_pdos_active_co_pair.tsv")

PARSER = r'''#!/usr/bin/env python
from __future__ import print_function
import sys


def trapz(x, y):
    return sum(0.5 * (y[i] + y[i - 1]) * (x[i] - x[i - 1]) for i in range(1, len(x)))


def center(energy, dos, lower, upper):
    selected = [(e, value) for e, value in zip(energy, dos) if lower <= e <= upper]
    if len(selected) < 2:
        raise RuntimeError("insufficient DOS points in requested window")
    x = [item[0] for item in selected]
    y = [item[1] for item in selected]
    weight = trapz(x, y)
    if weight <= 1.0e-12:
        raise RuntimeError("zero projected-DOS weight")
    return trapz(x, [e * value for e, value in selected]) / weight, weight


def parse(path, target):
    handle = open(path, "r")
    first = handle.readline().split()
    if not first:
        raise RuntimeError("empty DOSCAR")
    natoms = int(first[0])
    for _ in range(4):
        handle.readline()
    total_header = handle.readline().split()
    nedos = int(total_header[2])
    efermi = float(total_header[3])
    for _ in range(nedos):
        handle.readline()
    energy = []
    d_dos = []
    for atom in range(1, natoms + 1):
        atom_header = handle.readline()
        if not atom_header:
            raise RuntimeError("DOSCAR ended before atom block")
        for _ in range(nedos):
            fields = handle.readline().split()
            if atom == target:
                if len(fields) != 19:
                    raise RuntimeError("expected spin-polarized LORBIT=11 DOSCAR with 19 columns, got %d" % len(fields))
                energy.append(float(fields[0]) - efermi)
                d_dos.append(sum(float(value) for value in fields[9:19]))
    handle.close()
    occupied_center, occupied_weight = center(energy, d_dos, -8.0, 0.0)
    full_center, full_weight = center(energy, d_dos, -8.0, 5.0)
    near_center, near_weight = center(energy, d_dos, -2.0, 2.0)
    return natoms, efermi, occupied_center, occupied_weight, full_center, full_weight, near_center, near_weight


def main():
    if len(sys.argv) != 6:
        raise SystemExit("usage: parser.py al_DOSCAR al_index control_DOSCAR control_index output")
    cases = (
        ("Al16", sys.argv[1], int(sys.argv[2])),
        ("control", sys.argv[3], int(sys.argv[4])),
    )
    out = open(sys.argv[5], "w")
    out.write("model\tvasp_index\tnatoms\tefermi_eV\td_center_occ_m8_0_eV\td_weight_occ\td_center_m8_p5_eV\td_weight_m8_p5\td_center_m2_p2_eV\td_weight_m2_p2\n")
    for label, path, index in cases:
        values = parse(path, index)
        out.write("%s\t%d\t%d\t%.8f\t%.8f\t%.8f\t%.8f\t%.8f\t%.8f\t%.8f\n" % ((label, index) + values))
    out.close()


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
        queue = run(client, "squeue -u ftfan -h -o '%i|%j|%T'")
        if "PDOSBarePair" in queue:
            raise RuntimeError("bare PDOS pair analysis is already active")
        if "bare_pdos_active_co_pair.tsv" in sftp.listdir(remote(ANALYSIS)):
            raise RuntimeError("bare PDOS pair result already exists")
        for case in (AL_CASE, CONTROL_CASE):
            if sftp.stat(remote(posixpath.join(case, "DOSCAR"))).st_size < 100_000_000:
                raise RuntimeError(f"invalid DOSCAR: {case}")
        write_text(sftp, posixpath.join(TOOLS, "extract_bare_pdos_pair.py"), PARSER)
        slurm = f"""#!/bin/bash
#SBATCH --job-name=PDOSBarePair
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --partition=n28
#SBATCH --time=01:00:00
#SBATCH --output=pdos_bare_%J.stdout
#SBATCH --error=pdos_bare_%J.stderr

set -eo pipefail
cd {remote(ANALYSIS)}
python {remote(posixpath.join(TOOLS, 'extract_bare_pdos_pair.py'))} \
  {remote(posixpath.join(AL_CASE, 'DOSCAR'))} 16 \
  {remote(posixpath.join(CONTROL_CASE, 'DOSCAR'))} 21 \
  {remote(RESULT)}
test -s {remote(RESULT)}
"""
        write_text(sftp, posixpath.join(ANALYSIS, "pdos_bare_pair.slurm"), slurm)
        submitted = run(client, f"cd {ANALYSIS} && sbatch pdos_bare_pair.slurm")
        match = re.search(r"Submitted batch job (\d+)", submitted)
        if not match:
            raise RuntimeError(f"cannot parse submission: {submitted}")
        job_id = match.group(1)

        lines = read_text(sftp, MANIFEST).splitlines()
        for row_index in (1, 2):
            fields = lines[row_index].split("\t")
            if "bader_" not in fields[7] or "_valid_" not in fields[7] or "_pdos_" in fields[7]:
                raise RuntimeError(f"unexpected manifest status for task{row_index - 1}: {fields[7]}")
            fields[7] += f"_pdos_{job_id}_pending"
            lines[row_index] = "\t".join(fields)
        write_text(sftp, MANIFEST, "\n".join(lines) + "\n")

        scheduler = read_text(sftp, SCHEDULER)
        scheduler += (
            f"2026-08-19\tfixed_geometry_bare_pdos_pair_submission\t{job_id}\tn28\t1\t1\t"
            "Al16_active_Co16;control_active_Co21;occupied_and_full_d_centers;no_duplicate\n"
        )
        write_text(sftp, SCHEDULER, scheduler)
        print(job_id)
    finally:
        client.close()


if __name__ == "__main__":
    main()
