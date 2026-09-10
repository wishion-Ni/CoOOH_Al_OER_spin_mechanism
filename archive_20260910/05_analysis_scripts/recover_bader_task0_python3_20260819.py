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
        state = run(client, "sacct -j 111188 -n -P -o State,Elapsed,ExitCode").splitlines()[0]
        if not state.startswith("FAILED|00:00:00|1:0"):
            raise RuntimeError(f"unexpected source state: {state}")
        error = read_text(sftp, posixpath.join(CASE, "111188.stderr"))
        if "SyntaxError: invalid syntax" not in error or "sum_chgcar.py" not in error:
            raise RuntimeError("source failure is not the diagnosed Python 2 syntax error")
        queue = run(client, "squeue -u ftfan -h -o '%i|%j|%T'")
        if "Bader0AlCtrR" in queue:
            raise RuntimeError("recovery is already active")

        slurm = f"""#!/bin/bash
#SBATCH --job-name=Bader0AlCtrR
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --partition=n28
#SBATCH --time=06:00:00
#SBATCH --output=%J.stdout
#SBATCH --error=%J.stderr

set -eo pipefail
cd {remote(CASE)}
python3 {remote(posixpath.join(TOOLS, 'sum_chgcar.py'))} AECCAR0 AECCAR2 CHGCAR_sum
{remote(posixpath.join(TOOLS, 'bader-bin', 'bader'))} CHGCAR -ref CHGCAR_sum > bader.out
test -s ACF.dat
"""
        write_text(sftp, posixpath.join(CASE, "bader_recovery.slurm"), slurm)
        submitted = run(client, f"cd {CASE} && sbatch bader_recovery.slurm")
        match = re.search(r"Submitted batch job (\d+)", submitted)
        if not match:
            raise RuntimeError(f"cannot parse submission: {submitted}")
        job_id = match.group(1)

        lines = read_text(sftp, MANIFEST).splitlines()
        fields = lines[1].split("\t")
        expected = "valid_vasp_111172_0_bader_111188_pending"
        if fields[7] != expected:
            raise RuntimeError(f"unexpected task0 status: {fields[7]}")
        fields[7] = f"valid_vasp_111172_0_bader_111188_python2_failed_recovery_{job_id}_pending"
        lines[1] = "\t".join(fields)
        write_text(sftp, MANIFEST, "\n".join(lines) + "\n")

        scheduler = read_text(sftp, SCHEDULER)
        scheduler += (
            "2026-08-19\tfixed_geometry_bader_failure\t111188\tn28\t1\t1\t"
            "task0;zero_second;login_default_python2_fstring_SyntaxError;no_scientific_output\n"
            f"2026-08-19\tfixed_geometry_bader_recovery_submission\t{job_id}\tn28\t1\t1\t"
            "task0;python3;same_valid_densities;no_duplicate\n"
        )
        write_text(sftp, SCHEDULER, scheduler)
        print(job_id)
    finally:
        client.close()


if __name__ == "__main__":
    main()
