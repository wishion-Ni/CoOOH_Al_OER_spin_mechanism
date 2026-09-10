from __future__ import annotations

import importlib.util
from pathlib import Path, PurePosixPath


ROOT = PurePosixPath("/home/ftfan/ncw")
REMOTE_BASE = PurePosixPath(
    "/home/ftfan/ncw/sfs/CoOH/cp2k/Al16/oer/"
    "spin_config_scan_site03_5OH_current_20260714/"
    "vasp_jacs6c06054_reconstructed_exact_Al16_3x2_20260809/"
    "electronic_structure_al_contribution_20260818/"
    "cohp_bader_formal_oh_o_20260822"
)
CASES = {
    "undoped_OH": REMOTE_BASE / "undoped_control/OH",
    "undoped_O": REMOTE_BASE / "undoped_control/O_bader",
    "Al16_OH": REMOTE_BASE / "Al16_adjacent/OH_bader",
    "Al16_O": REMOTE_BASE / "Al16_adjacent/O_bader",
}


def load_runner():
    script = (
        Path(__file__).resolve().parents[1]
        / ".codex/skills/ftfan-ncw-ssh/scripts/ssh_ncw.py"
    )
    spec = importlib.util.spec_from_file_location("ftfan_ncw_ssh", script)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load SSH runner: {script}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    runner = load_runner()
    paramiko = runner.ensure_paramiko()
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        hostname=runner.HOST,
        port=runner.PORT,
        username=runner.USER,
        password=runner.load_password(),
        timeout=15,
        banner_timeout=15,
        auth_timeout=60,
        look_for_keys=False,
        allow_agent=False,
    )
    target = Path(__file__).resolve().parent / "bader_structure_inputs_20260823"
    target.mkdir(exist_ok=True)
    try:
        sftp = client.open_sftp()
        for name, remote_dir in CASES.items():
            if ROOT not in remote_dir.parents:
                raise RuntimeError(f"Remote path escapes allowed root: {remote_dir}")
            case_dir = target / name
            case_dir.mkdir(exist_ok=True)
            for filename in ("POSCAR", "ACF.dat"):
                remote = str(remote_dir / filename)
                local = case_dir / filename
                sftp.get(remote, str(local))
                print(f"{name}: {filename} -> {local} ({local.stat().st_size} bytes)")
    finally:
        client.close()


if __name__ == "__main__":
    main()
