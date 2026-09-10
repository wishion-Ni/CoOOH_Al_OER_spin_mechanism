from __future__ import annotations

import importlib.util
import posixpath
from pathlib import Path


WORKSPACE = Path(__file__).resolve().parents[1]
LOCAL_ROOT = WORKSPACE / "artifacts" / "orbital_assignment_audit_20260903"
SSH_HELPER = WORKSPACE / ".codex" / "skills" / "ftfan-ncw-ssh" / "scripts" / "ssh_ncw.py"
REMOTE_HOME = "/home/ftfan/ncw"
REMOTE_ROOT = (
    "/home/ftfan/ncw/sfs/CoOH/cp2k/Al16/oer/"
    "spin_config_scan_site03_5OH_current_20260714/"
    "vasp_jacs6c06054_reconstructed_exact_Al16_3x2_20260809/"
    "electronic_structure_al_contribution_20260818/"
    "orbital_assignment_audit_20260903"
)


def load_helper():
    spec = importlib.util.spec_from_file_location("ssh_ncw", SSH_HELPER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {SSH_HELPER}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    helper = load_helper()
    paramiko = helper.ensure_paramiko()
    password = helper.load_password()
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        hostname=helper.HOST,
        port=helper.PORT,
        username=helper.USER,
        password=password,
        timeout=15,
        banner_timeout=15,
        auth_timeout=60,
        look_for_keys=False,
        allow_agent=False,
    )
    try:
        sftp = client.open_sftp()
        try:
            uploaded = []
            for source in sorted(LOCAL_ROOT.iterdir()):
                if not source.is_file():
                    continue
                target = posixpath.join(REMOTE_ROOT, source.name)
                if not target.startswith(REMOTE_HOME + "/"):
                    raise RuntimeError(f"Target outside allowed root: {target}")
                sftp.put(str(source), target)
                if sftp.stat(target).st_size != source.stat().st_size:
                    raise RuntimeError(f"Upload size mismatch: {source.name}")
                uploaded.append(source.name)
        finally:
            sftp.close()
        print(f"REMOTE_ROOT={REMOTE_ROOT}")
        print("UPLOADED=" + ",".join(uploaded))
        return 0
    finally:
        client.close()


if __name__ == "__main__":
    raise SystemExit(main())
