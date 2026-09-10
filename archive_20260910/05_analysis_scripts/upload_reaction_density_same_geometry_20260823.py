from __future__ import annotations

import importlib.util
import posixpath
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / ".codex/skills/ftfan-ncw-ssh/scripts/ssh_ncw.py"
LOCAL_SCRIPT = ROOT / "artifacts/deploy_reaction_density_same_geometry_20260823.py"
REMOTE_DIR = (
    "sfs/CoOH/cp2k/Al16/oer/spin_config_scan_site03_5OH_current_20260714/"
    "vasp_jacs6c06054_reconstructed_exact_Al16_3x2_20260809/"
    "electronic_structure_al_contribution_20260818/tools"
)
REMOTE_SCRIPT = posixpath.join(REMOTE_DIR, LOCAL_SCRIPT.name)


def load_helper():
    spec = importlib.util.spec_from_file_location("ssh_ncw", HELPER)
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot load ftfan-ncw-ssh helper")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    helper = load_helper()
    paramiko = helper.ensure_paramiko()
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        hostname=helper.HOST,
        port=helper.PORT,
        username=helper.USER,
        password=helper.load_password(),
        look_for_keys=False,
        allow_agent=False,
    )
    try:
        sftp = client.open_sftp()
        remote_path = posixpath.join(helper.REMOTE_ROOT, REMOTE_SCRIPT)
        sftp.put(str(LOCAL_SCRIPT), remote_path)
    finally:
        client.close()
    subprocess.run(
        [sys.executable, str(HELPER), "--", f"./conda/bin/python3.8 {REMOTE_SCRIPT}"],
        cwd=ROOT,
        check=True,
    )


if __name__ == "__main__":
    main()
