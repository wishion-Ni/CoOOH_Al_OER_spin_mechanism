from __future__ import annotations

import importlib.util
import posixpath
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SSH_SCRIPT = ROOT / ".codex/skills/ftfan-ncw-ssh/scripts/ssh_ncw.py"
REMOTE_BASE = (
    "sfs/CoOH/cp2k/Al16/oer/spin_config_scan_site03_5OH_current_20260714/"
    "vasp_jacs6c06054_reconstructed_exact_Al16_3x2_20260809/"
    "electronic_structure_al_contribution_20260818/"
    "cohp_bader_formal_oh_o_20260822"
)
LOCAL = ROOT / "artifacts/lobster_grosspop_oh_o_20260826"
FILES = {
    "undoped_OH": "undoped_control/OH_pair_corrected_nomadelung/GROSSPOP.lobster",
    "undoped_O": "undoped_control/O_nomadelung/GROSSPOP.lobster",
    "Al16_OH": "Al16_adjacent/OH_nomadelung/GROSSPOP.lobster",
    "Al16_O": "Al16_adjacent/O_nomadelung/GROSSPOP.lobster",
}


def load_ssh_module():
    spec = importlib.util.spec_from_file_location("ssh_ncw", SSH_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load SSH helper")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    LOCAL.mkdir(parents=True, exist_ok=True)
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
            for key, relative in FILES.items():
                remote = posixpath.join(ssh.REMOTE_ROOT, REMOTE_BASE, relative)
                local = LOCAL / f"{key}_GROSSPOP.lobster"
                sftp.stat(remote)
                sftp.get(remote, str(local))
                print(local)
    finally:
        client.close()


if __name__ == "__main__":
    main()
