from __future__ import annotations

import importlib.util
import posixpath
from pathlib import Path


WORKSPACE = Path(__file__).resolve().parents[1]
SSH_HELPER = WORKSPACE / ".codex" / "skills" / "ftfan-ncw-ssh" / "scripts" / "ssh_ncw.py"
LOCAL_DIR = WORKSPACE / "artifacts" / "frontier_level_postprocess_20260903"
LOCAL_ZIP = WORKSPACE / "artifacts" / "frontier_level_postprocess_20260903.zip"
REMOTE_ROOT = "/home/ftfan/ncw"
REMOTE_DIR = (
    REMOTE_ROOT
    + "/sfs/CoOH/cp2k/Al16/oer/spin_config_scan_site03_5OH_current_20260714/"
    "vasp_jacs6c06054_reconstructed_exact_Al16_3x2_20260809/"
    "electronic_structure_al_contribution_20260818/frontier_level_postprocess_20260903"
)


def load_helper():
    spec = importlib.util.spec_from_file_location("ftfan_ncw_ssh", SSH_HELPER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {SSH_HELPER}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def ensure_remote_dir(sftp, path: str) -> None:
    current = REMOTE_ROOT
    relative = posixpath.relpath(path, REMOTE_ROOT)
    if relative.startswith(".."):
        raise ValueError(f"Remote path escapes allowed root: {path}")
    for part in relative.split("/"):
        current = posixpath.join(current, part)
        try:
            sftp.stat(current)
        except OSError:
            sftp.mkdir(current)


def main() -> None:
    helper = load_helper()
    paramiko = helper.ensure_paramiko()
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        helper.HOST,
        port=helper.PORT,
        username=helper.USER,
        password=helper.load_password(),
        timeout=20,
        banner_timeout=20,
        auth_timeout=20,
    )
    try:
        sftp = client.open_sftp()
        try:
            ensure_remote_dir(sftp, REMOTE_DIR)
            files = sorted(LOCAL_DIR.iterdir()) + [LOCAL_ZIP]
            for local in files:
                remote = posixpath.join(REMOTE_DIR, local.name)
                if not remote.startswith(REMOTE_ROOT + "/"):
                    raise ValueError(f"Refusing unsafe remote path: {remote}")
                sftp.put(str(local), remote)
                stat = sftp.stat(remote)
                if stat.st_size != local.stat().st_size:
                    raise IOError(f"Size mismatch after upload: {local} -> {remote}")
                print(f"UPLOADED={remote}|{stat.st_size}")
        finally:
            sftp.close()
    finally:
        client.close()
    print(f"REMOTE_DIR={REMOTE_DIR}")
    print(f"REMOTE_ZIP={posixpath.join(REMOTE_DIR, LOCAL_ZIP.name)}")


if __name__ == "__main__":
    main()
