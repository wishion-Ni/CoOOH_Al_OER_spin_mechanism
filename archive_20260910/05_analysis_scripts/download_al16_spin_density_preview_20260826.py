from __future__ import annotations

import importlib.util
import posixpath
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SSH_SCRIPT = ROOT / ".codex/skills/ftfan-ncw-ssh/scripts/ssh_ncw.py"
REMOTE = (
    "sfs/CoOH/cp2k/Al16/oer/spin_config_scan_site03_5OH_current_20260714/"
    "vasp_jacs6c06054_reconstructed_exact_Al16_3x2_20260809/"
    "electronic_structure_al_contribution_20260818/"
    "reaction_density_oh_to_o_same_geometry_20260823/Al16_spin_preview"
)
FILES = {
    "Al16_O_minus_OH_spin_ds2.raw": ROOT / "artifacts/Al16_O_minus_OH_spin_ds2.raw",
    "Al16_O_minus_OH_spin_ds2.stats": ROOT / "artifacts/Al16_O_minus_OH_spin_ds2.stats",
}


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
        with client.open_sftp() as sftp:
            for name, local in FILES.items():
                remote = posixpath.join(ssh.REMOTE_ROOT, REMOTE, name)
                sftp.stat(remote)
                sftp.get(remote, str(local))
                print(local)
    finally:
        client.close()


if __name__ == "__main__":
    main()
