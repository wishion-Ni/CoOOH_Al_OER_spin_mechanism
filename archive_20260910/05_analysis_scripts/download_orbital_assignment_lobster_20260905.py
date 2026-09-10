from __future__ import annotations

import importlib.util
import posixpath
from pathlib import Path


WORKSPACE = Path(__file__).resolve().parents[1]
SSH_HELPER = WORKSPACE / ".codex" / "skills" / "ftfan-ncw-ssh" / "scripts" / "ssh_ncw.py"
LOCAL_ROOT = WORKSPACE / "artifacts" / "orbital_assignment_audit_20260903" / "lobster_sixbond"
REMOTE_HOME = "/home/ftfan/ncw"
REMOTE_ROOT = (
    "/home/ftfan/ncw/sfs/CoOH/cp2k/Al16/oer/"
    "spin_config_scan_site03_5OH_current_20260714/"
    "vasp_jacs6c06054_reconstructed_exact_Al16_3x2_20260809/"
    "electronic_structure_al_contribution_20260818/"
    "orbital_assignment_audit_20260903/lobster_sixbond"
)
CASES = ("pristine_OH", "pristine_O", "Al16_OH", "Al16_O")
FILES = (
    "COHPCAR.lobster",
    "ICOHPLIST.lobster",
    "DOSCAR.lobster",
    "GROSSPOP.lobster",
    "lobsterin",
    "lobsterout",
    "POSCAR",
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
            downloaded = []
            for case in CASES:
                local_dir = LOCAL_ROOT / case
                local_dir.mkdir(parents=True, exist_ok=True)
                for filename in FILES:
                    remote = posixpath.join(REMOTE_ROOT, case, filename)
                    if not remote.startswith(REMOTE_HOME + "/"):
                        raise RuntimeError(f"Remote path outside allowed root: {remote}")
                    size = sftp.stat(remote).st_size
                    if size <= 0:
                        raise RuntimeError(f"Empty remote file: {remote}")
                    local = local_dir / filename
                    sftp.get(remote, str(local))
                    if local.stat().st_size != size:
                        raise RuntimeError(f"Size mismatch: {case}/{filename}")
                    downloaded.append(f"{case}/{filename}:{size}")
        finally:
            sftp.close()
        print("\n".join(downloaded))
        return 0
    finally:
        client.close()


if __name__ == "__main__":
    raise SystemExit(main())
