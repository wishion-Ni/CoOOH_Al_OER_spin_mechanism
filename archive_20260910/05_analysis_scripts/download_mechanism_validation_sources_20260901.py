from __future__ import annotations

import importlib.util
import posixpath
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SSH_SCRIPT = ROOT / ".codex/skills/ftfan-ncw-ssh/scripts/ssh_ncw.py"
LOCAL = ROOT / "artifacts/mechanism_validation_sources_20260901"

AL_BASE = (
    "sfs/CoOH/cp2k/Al16/oer/spin_config_scan_site03_5OH_current_20260714/"
    "cdft_charge_spin_20260812"
)
UNDOPED_BASE = (
    "sfs/CoOH/cp2k/thermo_vib_5OH_U100_current_20260704/"
    "cdft_charge_spin_undoped_20260816"
)

CASES = {
    "cp2k_undoped_OH": (UNDOPED_BASE, "undoped_valid_co32_OH"),
    "cp2k_undoped_O": (UNDOPED_BASE, "undoped_valid_co32_O"),
    "cp2k_Al16_OH": (AL_BASE, "al16_valid_co48_OH"),
    "cp2k_Al16_O": (AL_BASE, "al16_valid_co48_O"),
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
            for label, (base, case) in CASES.items():
                for name in ("baseline.inp", "baseline.out"):
                    remote_rel = posixpath.join(base, case, name)
                    remote = posixpath.join(ssh.REMOTE_ROOT, remote_rel)
                    local = LOCAL / f"{label}_{name}"
                    sftp.stat(remote)
                    sftp.get(remote, str(local))
                    print(local)
    finally:
        client.close()


if __name__ == "__main__":
    main()
