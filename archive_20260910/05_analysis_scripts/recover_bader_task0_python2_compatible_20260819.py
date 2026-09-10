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
CASE = posixpath.join(ANALYSIS, "fixed_geometry_bader_pdos/Al16_adjacent/bare")
TOOLS = posixpath.join(ANALYSIS, "tools")
MANIFEST = posixpath.join(ANALYSIS, "analysis_manifest.tsv")
SCHEDULER = posixpath.join(ANALYSIS, "scheduler_manifest.tsv")

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
        state = run(client, "sacct -j 111189 -n -P -o State,Elapsed,ExitCode").splitlines()[0]
        if not state.startswith("FAILED|00:00:00|127:0"):
            raise RuntimeError(f"unexpected source state: {state}")
        error = read_text(sftp, posixpath.join(CASE, "111189.stderr"))
        if "python3: command not found" not in error:
            raise RuntimeError("source failure is not the diagnosed missing-python3 error")
        queue = run(client, "squeue -u ftfan -h -o '%i|%j|%T'")
        if "Bader0AlCtr" in queue:
            raise RuntimeError("task0 Bader analysis is already active")
        if any(name in sftp.listdir(remote(CASE)) for name in ("ACF.dat", "CHGCAR_sum", "bader.out")):
            raise RuntimeError("unexpected Bader output already exists")

        write_text(sftp, posixpath.join(TOOLS, "sum_chgcar.py"), SUM_SCRIPT)
        slurm = f"""#!/bin/bash
#SBATCH --job-name=Bader0AlCtrP2
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --partition=n28
#SBATCH --time=06:00:00
#SBATCH --output=%J.stdout
#SBATCH --error=%J.stderr

set -eo pipefail
cd {remote(CASE)}
python {remote(posixpath.join(TOOLS, 'sum_chgcar.py'))} AECCAR0 AECCAR2 CHGCAR_sum
{remote(posixpath.join(TOOLS, 'bader-bin', 'bader'))} CHGCAR -ref CHGCAR_sum > bader.out
test -s ACF.dat
"""
        write_text(sftp, posixpath.join(CASE, "bader_python2_compatible_recovery.slurm"), slurm)
        submitted = run(client, f"cd {CASE} && sbatch bader_python2_compatible_recovery.slurm")
        match = re.search(r"Submitted batch job (\d+)", submitted)
        if not match:
            raise RuntimeError(f"cannot parse submission: {submitted}")
        job_id = match.group(1)

        lines = read_text(sftp, MANIFEST).splitlines()
        fields = lines[1].split("\t")
        expected = "valid_vasp_111172_0_bader_111188_python2_failed_recovery_111189_pending"
        if fields[7] != expected:
            raise RuntimeError(f"unexpected task0 status: {fields[7]}")
        fields[7] = (
            "valid_vasp_111172_0_bader_111188_python2_syntax_failed_"
            f"111189_python3_missing_recovery_{job_id}_pending"
        )
        lines[1] = "\t".join(fields)
        write_text(sftp, MANIFEST, "\n".join(lines) + "\n")

        scheduler = read_text(sftp, SCHEDULER)
        scheduler += (
            "2026-08-19\tfixed_geometry_bader_recovery_failure\t111189\tn28\t1\t1\t"
            "task0;zero_second;python3_command_not_found;no_scientific_output\n"
            f"2026-08-19\tfixed_geometry_bader_python2_compatible_recovery\t{job_id}\tn28\t1\t1\t"
            "task0;python2_compatible_sum_script;same_valid_densities;no_duplicate\n"
        )
        write_text(sftp, SCHEDULER, scheduler)
        print(job_id)
    finally:
        client.close()


if __name__ == "__main__":
    main()
