from __future__ import annotations

import importlib.util
import posixpath
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / ".codex/skills/ftfan-ncw-ssh/scripts/ssh_ncw.py"
REMOTE_TOOLS = (
    "sfs/CoOH/cp2k/Al16/oer/spin_config_scan_site03_5OH_current_20260714/"
    "vasp_jacs6c06054_reconstructed_exact_Al16_3x2_20260809/"
    "electronic_structure_al_contribution_20260818/tools"
)
FILES = (
    "deploy_lobster_preconverged_20260819.py",
    "refresh_lobster_pairs_20260819.py",
    "diagnose_lobster_pairs_20260819.py",
    "mark_lobster_site_mapping_rejection_20260819.py",
)


def main() -> None:
    spec = importlib.util.spec_from_file_location("ssh_ncw", HELPER)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load SSH helper")
    ssh_ncw = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ssh_ncw)
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
        for name in FILES:
            local = ROOT / "artifacts" / name
            if not local.is_file():
                raise RuntimeError(f"missing local script: {local}")
            remote = posixpath.join(ssh_ncw.REMOTE_ROOT, REMOTE_TOOLS, name)
            sftp.put(str(local), remote)
    finally:
        client.close()

    script_name = sys.argv[1] if len(sys.argv) > 1 else "refresh_lobster_pairs_20260819.py"
    if script_name not in FILES:
        raise RuntimeError(f"unsupported remote script: {script_name}")
    remote_script = posixpath.join(REMOTE_TOOLS, script_name)
    subprocess.run(
        [sys.executable, str(HELPER), "--", f"python {remote_script}"],
        cwd=ROOT,
        check=True,
    )


if __name__ == "__main__":
    main()
