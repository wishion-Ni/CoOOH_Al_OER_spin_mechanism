from __future__ import annotations

import importlib.util
import posixpath
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / ".codex/skills/ftfan-ncw-ssh/scripts/ssh_ncw.py"
LOCAL_SCRIPT = ROOT / "artifacts/deploy_lobster_preconverged_20260819.py"
REMOTE_ANALYSIS = (
    "sfs/CoOH/cp2k/Al16/oer/spin_config_scan_site03_5OH_current_20260714/"
    "vasp_jacs6c06054_reconstructed_exact_Al16_3x2_20260809/"
    "electronic_structure_al_contribution_20260818"
)
REMOTE_TOOLS = posixpath.join(REMOTE_ANALYSIS, "tools")
REMOTE_SCRIPT = posixpath.join(REMOTE_TOOLS, LOCAL_SCRIPT.name)


def load_helper():
    spec = importlib.util.spec_from_file_location("ssh_ncw", HELPER)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load SSH helper")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    if not LOCAL_SCRIPT.is_file():
        raise RuntimeError(f"missing deployment script: {LOCAL_SCRIPT}")
    ssh_ncw = load_helper()
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
        remote_tools = posixpath.join(ssh_ncw.REMOTE_ROOT, REMOTE_TOOLS)
        try:
            sftp.stat(remote_tools)
        except FileNotFoundError:
            sftp.mkdir(remote_tools)
        sftp.put(str(LOCAL_SCRIPT), posixpath.join(ssh_ncw.REMOTE_ROOT, REMOTE_SCRIPT))
    finally:
        client.close()

    command = [sys.executable, str(HELPER), "--", f"python {REMOTE_SCRIPT}"]
    subprocess.run(command, cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
