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
    "cdft_charge_spin_undoped_20260816"
)


def read_text(sftp, rel: str) -> str:
    with sftp.open(posixpath.join(ssh_ncw.REMOTE_ROOT, rel), "r") as handle:
        return handle.read().decode(errors="replace")


def write_text(sftp, rel: str, content: str) -> None:
    with sftp.open(posixpath.join(ssh_ncw.REMOTE_ROOT, rel), "w") as handle:
        handle.write(content)


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
        accounting = run(
            client,
            "sacct -j 111089 --format=JobIDRaw,State,ExitCode -n -P",
        )
        failed = sum("|FAILED|1:0" in line for line in accounting.splitlines())
        if failed < 3:
            raise RuntimeError(f"unexpected 111089 accounting: {accounting}")
        queue = run(client, "squeue -u ftfan -h -o '%j'")
        if "Undop_cdft_base" in queue:
            raise RuntimeError("an undoped baseline array is already active")

        slurm_rel = posixpath.join(BASE, "submit_baseline.slurm")
        slurm = read_text(sftp, slurm_rel)
        if "set -euo pipefail" not in slurm:
            raise RuntimeError("unexpected baseline Slurm script")
        slurm = slurm.replace("set -euo pipefail", "set -eo pipefail", 1)
        write_text(sftp, slurm_rel, slurm)

        manifest_rel = posixpath.join(BASE, "scheduler_manifest.tsv")
        manifest = read_text(sftp, manifest_rel)
        manifest += (
            "2026-08-16\tbaseline_failure\t111089_0-2\trejected_scheduler\t"
            "zero_second_exit1;CP_DFLAGS_unbound_during_toolchain_setup;"
            "CP2K_not_started;no_scientific_output\n"
        )
        submit = run(client, f"cd {BASE} && sbatch submit_baseline.slurm")
        match = re.search(r"Submitted batch job (\d+)", submit)
        if not match:
            raise RuntimeError(f"cannot parse sbatch output: {submit}")
        job_id = match.group(1)
        manifest += (
            f"2026-08-16\tbaseline_recovery_submission\t{job_id}_0-2\tpending\t"
            "toolchain_setup_with_nounset_disabled;n28_concurrency1;"
            "same_inputs_and_WFN;no_duplicates\n"
        )
        write_text(sftp, manifest_rel, manifest)
        print(job_id)
    finally:
        client.close()


if __name__ == "__main__":
    main()
