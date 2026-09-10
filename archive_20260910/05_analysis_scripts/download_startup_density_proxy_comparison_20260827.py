from __future__ import annotations

import importlib.util
import posixpath
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SSH_SCRIPT = ROOT / ".codex/skills/ftfan-ncw-ssh/scripts/ssh_ncw.py"
LOCAL = ROOT / "artifacts/startup_density_proxy_comparison_20260827"
REMOTE_BASE = (
    "sfs/CoOH/cp2k/Al16/oer/spin_config_scan_site03_5OH_current_20260714/"
    "vasp_jacs6c06054_reconstructed_exact_Al16_3x2_20260809/"
    "electronic_structure_al_contribution_20260818"
)
REMOTE_REACTION = posixpath.join(REMOTE_BASE, "reaction_density_oh_to_o_same_geometry_20260823")
REMOTE_PROXY = posixpath.join(REMOTE_REACTION, "startup_density_proxy_comparison_20260827")
REMOTE_FORMAL = posixpath.join(REMOTE_BASE, "cohp_oh_o_corrected_20260820")


def load_ssh_module():
    spec = importlib.util.spec_from_file_location("ssh_ncw", SSH_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load SSH helper")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def connect(ssh, paramiko):
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
    transport = client.get_transport()
    if transport is not None:
        transport.set_keepalive(15)
    return client


def download_resumable(ssh, paramiko, remote: str, local: Path) -> None:
    for attempt in range(1, 11):
        client = connect(ssh, paramiko)
        try:
            with client.open_sftp() as sftp:
                remote_size = sftp.stat(remote).st_size
                local_size = local.stat().st_size if local.exists() else 0
                if local_size > remote_size:
                    local.unlink()
                    local_size = 0
                if local_size == remote_size:
                    print(f"complete {local}")
                    return
                with sftp.file(remote, "rb") as source, local.open("ab") as target:
                    source.seek(local_size)
                    while local_size < remote_size:
                        block = source.read(min(1024 * 1024, remote_size - local_size))
                        if not block:
                            raise IOError("remote file ended early")
                        target.write(block)
                        local_size += len(block)
                if local_size != remote_size:
                    raise IOError(f"size mismatch {local_size} != {remote_size}")
                print(f"downloaded {local}")
                return
        except Exception as exc:
            if attempt == 10:
                raise
            print(f"retry {attempt} {local.name}: {exc}")
            time.sleep(3)
        finally:
            client.close()


def main() -> None:
    LOCAL.mkdir(parents=True, exist_ok=True)
    files: dict[str, Path] = {}
    for case in ("undoped_control", "Al16_adjacent"):
        for field in ("charge", "spin"):
            stem = f"{case}_startup_O_minus_OH_{field}_ds2"
            files[posixpath.join(REMOTE_PROXY, stem + ".raw")] = LOCAL / (stem + ".raw")
            files[posixpath.join(REMOTE_PROXY, stem + ".stats")] = LOCAL / (stem + ".stats")
        files[posixpath.join(REMOTE_REACTION, case, "O_at_OHgeom/POSCAR")] = LOCAL / f"{case}_O_at_OHgeom_POSCAR"
        files[posixpath.join(REMOTE_FORMAL, case, "OH/POSCAR")] = LOCAL / f"{case}_OH_formal_POSCAR"

    ssh = load_ssh_module()
    paramiko = ssh.ensure_paramiko()
    for relative, local in files.items():
        remote = posixpath.join(ssh.REMOTE_ROOT, relative)
        download_resumable(ssh, paramiko, remote, local)


if __name__ == "__main__":
    main()
