from __future__ import annotations

import importlib.util
import posixpath
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SSH_SCRIPT = ROOT / ".codex/skills/ftfan-ncw-ssh/scripts/ssh_ncw.py"
CPP = ROOT / "artifacts/chgcar_difference_downsample.cpp"
REMOTE_BASE = (
    "sfs/CoOH/cp2k/Al16/oer/spin_config_scan_site03_5OH_current_20260714/"
    "vasp_jacs6c06054_reconstructed_exact_Al16_3x2_20260809/"
    "electronic_structure_al_contribution_20260818"
)
REMOTE_WORK = posixpath.join(REMOTE_BASE, "reaction_density_oh_to_o_same_geometry_20260823/Al16_preview")


def load_ssh_module():
    spec = importlib.util.spec_from_file_location("ssh_ncw", SSH_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load SSH helper")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    ssh = load_ssh_module()
    paramiko = ssh.ensure_paramiko()
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        hostname=ssh.HOST,
        port=ssh.PORT,
        username=ssh.USER,
        password=ssh.load_password(),
        timeout=15,
        banner_timeout=15,
        auth_timeout=60,
        look_for_keys=False,
        allow_agent=False,
    )
    try:
        command = f"cd {ssh.REMOTE_ROOT} && mkdir -p {REMOTE_WORK}"
        _, stdout, stderr = client.exec_command(command)
        code = stdout.channel.recv_exit_status()
        if code:
            raise RuntimeError(stderr.read().decode(errors="replace"))
        with client.open_sftp() as sftp:
            sftp.put(str(CPP), posixpath.join(ssh.REMOTE_ROOT, REMOTE_WORK, CPP.name))

            slurm = f"""#!/bin/bash
#SBATCH --job-name=Al16_rho_preview
#SBATCH --partition=n28
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --time=02:00:00
#SBATCH --output=preview_%j.stdout
#SBATCH --error=preview_%j.stderr
set -euo pipefail
cd {ssh.REMOTE_ROOT}/{REMOTE_WORK}
g++ -O3 -std=c++11 {CPP.name} -o chgcar_difference_downsample
O=../Al16_adjacent/O_at_OHgeom/CHGCAR
OH=../../cohp_oh_o_corrected_20260820/Al16_adjacent/OH/CHGCAR
test -s "$O"
test -s "$OH"
./chgcar_difference_downsample "$O" "$OH" Al16_O_minus_OH_ds2.raw 2 | tee Al16_O_minus_OH_ds2.stats
"""
            with sftp.file(posixpath.join(ssh.REMOTE_ROOT, REMOTE_WORK, "run_preview.slurm"), "w") as handle:
                handle.write(slurm)

        command = f"cd {ssh.REMOTE_ROOT}/{REMOTE_WORK} && sbatch --parsable run_preview.slurm"
        _, stdout, stderr = client.exec_command(command)
        job_id = stdout.read().decode().strip()
        error = stderr.read().decode().strip()
        code = stdout.channel.recv_exit_status()
        if code:
            raise RuntimeError(error or "sbatch failed")
        print(job_id)
    finally:
        client.close()


if __name__ == "__main__":
    sys.exit(main())
