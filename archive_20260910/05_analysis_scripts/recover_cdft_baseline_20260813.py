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
        if re.search(r"\bCoOH_cdft_base\b", queue):
            raise RuntimeError("A cDFT baseline array is already active")

        rel = posixpath.join(BASE, "submit_baseline.slurm")
        script = read_text(sftp, rel)
        script = script.replace("set -euo pipefail", "set -eo pipefail", 1)
        runtime = """export LD_LIBRARY_PATH=/apps/soft/gmp620/lib:${LD_LIBRARY_PATH:-}
export LD_LIBRARY_PATH=/apps/soft/mpfr410/lib:$LD_LIBRARY_PATH
export LD_LIBRARY_PATH=/apps/soft/mpc120/lib:$LD_LIBRARY_PATH
export LD_LIBRARY_PATH=/apps/soft/gcc840/lib64:$LD_LIBRARY_PATH
export PATH=/apps/soft/gcc840/bin:$PATH
"""
        marker = "source /apps/soft/cp2k-2024.1/tools/toolchain/install/setup\n"
        if "/apps/soft/gcc840/lib64" not in script:
            script = script.replace(marker, runtime + marker, 1)
        if "set -u\nexport PATH" not in script:
            script = script.replace(marker, marker + "set -u\n", 1)
        write_text(sftp, rel, script)

        manifest_rel = posixpath.join(BASE, "scheduler_manifest.tsv")
        try:
            manifest = read_text(sftp, manifest_rel)
        except FileNotFoundError:
            manifest = "date\tevent\tjob_id\tstatus\tnotes\n"
        failed = (
            "2026-08-13\tfailure\t111003_0-2\trejected_launch\t"
            "CP2K_setup_read_unbound_CP_DFLAGS_before_executable;no_CP2K_run;outputs_preserved\n"
        )
        if "111003_0-2" not in manifest:
            manifest += failed
        if "111046_0-2" not in manifest:
            manifest += (
                "2026-08-13\tfailure\t111046_0-2\trejected_launch\t"
                "cp2k_popt_missing_libgfortran_so_5;no_CP2K_run;outputs_preserved\n"
            )

        submit = run(client, f"cd {BASE} && sbatch submit_baseline.slurm")
        match = re.search(r"Submitted batch job (\d+)", submit)
        if not match:
            raise RuntimeError(submit)
        job = match.group(1)
        manifest += (
            f"2026-08-13\trecovery_submission\t{job}_0-2\tpending\t"
            "moved_set_u_after_CP2K_setup;fixed_geometry_population_baselines;no_duplicates\n"
        )
        write_text(sftp, manifest_rel, manifest)
        print(job)
    finally:
        client.close()


if __name__ == "__main__":
    main()
