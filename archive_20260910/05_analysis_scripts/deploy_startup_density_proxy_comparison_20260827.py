from __future__ import annotations

import importlib.util
import posixpath
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SSH_SCRIPT = ROOT / ".codex/skills/ftfan-ncw-ssh/scripts/ssh_ncw.py"
CHARGE_CPP = ROOT / "artifacts/chgcar_difference_downsample.cpp"
SPIN_CPP = ROOT / "artifacts/chgcar_magnetization_difference_downsample.cpp"
REMOTE_BASE = (
    "sfs/CoOH/cp2k/Al16/oer/spin_config_scan_site03_5OH_current_20260714/"
    "vasp_jacs6c06054_reconstructed_exact_Al16_3x2_20260809/"
    "electronic_structure_al_contribution_20260818"
)
REMOTE_WORK = posixpath.join(
    REMOTE_BASE,
    "reaction_density_oh_to_o_same_geometry_20260823/startup_density_proxy_comparison_20260827",
)


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
        _stdin, stdout, stderr = client.exec_command(command)
        code = stdout.channel.recv_exit_status()
        if code:
            raise RuntimeError(stderr.read().decode(errors="replace"))

        with client.open_sftp() as sftp:
            for source in (CHARGE_CPP, SPIN_CPP):
                sftp.put(str(source), posixpath.join(ssh.REMOTE_ROOT, REMOTE_WORK, source.name))

            slurm = f"""#!/bin/bash
#SBATCH --job-name=start_rho_proxy
#SBATCH --partition=n28
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --time=00:20:00
#SBATCH --output=proxy_%j.stdout
#SBATCH --error=proxy_%j.stderr
set -euo pipefail
cd {ssh.REMOTE_ROOT}/{REMOTE_WORK}
g++ -O3 -std=c++11 {CHARGE_CPP.name} -o chgcar_difference_downsample
g++ -O3 -std=c++11 {SPIN_CPP.name} -o chgcar_magnetization_difference_downsample

FORMAL=../../cohp_oh_o_corrected_20260820
for case in undoped_control Al16_adjacent; do
    O="$FORMAL/$case/O/CHGCAR"
    OH="$FORMAL/$case/OH/CHGCAR"
    test -s "$O"
    test -s "$OH"
    ./chgcar_difference_downsample "$O" "$OH" "${{case}}_startup_O_minus_OH_charge_ds2.raw" 2 \
        | tee "${{case}}_startup_O_minus_OH_charge_ds2.stats"
    ./chgcar_magnetization_difference_downsample "$O" "$OH" \
        "${{case}}_startup_O_minus_OH_spin_ds2.raw" 2 \
        | tee "${{case}}_startup_O_minus_OH_spin_ds2.stats"
done
"""
            remote_slurm = posixpath.join(ssh.REMOTE_ROOT, REMOTE_WORK, "run_proxy.slurm")
            with sftp.file(remote_slurm, "w") as handle:
                handle.write(slurm)

        command = f"cd {ssh.REMOTE_ROOT}/{REMOTE_WORK} && sbatch --parsable run_proxy.slurm"
        _stdin, stdout, stderr = client.exec_command(command)
        job_id = stdout.read().decode().strip()
        error = stderr.read().decode().strip()
        code = stdout.channel.recv_exit_status()
        if code:
            raise RuntimeError(error or "sbatch failed")
        print(job_id)
    finally:
        client.close()


if __name__ == "__main__":
    main()
