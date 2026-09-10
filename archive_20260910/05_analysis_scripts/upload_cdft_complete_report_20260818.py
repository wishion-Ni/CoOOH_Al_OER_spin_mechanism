from __future__ import annotations

import importlib.util
import posixpath
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / ".codex/skills/ftfan-ncw-ssh/scripts/ssh_ncw.py"
spec = importlib.util.spec_from_file_location("ssh_ncw", HELPER)
ssh_ncw = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(ssh_ncw)

REMOTE = (
    "sfs/CoOH/cp2k/thermo_vib_5OH_U100_current_20260704/"
    "cdft_charge_spin_undoped_20260816/final_undoped_vs_al16_comparison_20260818"
)
STEM = "cdft_undoped_vs_al16_complete_20260818"
SUFFIXES = (".png", ".svg", ".pdf", ".tsv", ".md")


def main() -> None:
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
        absolute = posixpath.join(ssh_ncw.REMOTE_ROOT, REMOTE)
        try:
            sftp.stat(absolute)
        except FileNotFoundError:
            sftp.mkdir(absolute)
        for suffix in SUFFIXES:
            source = ROOT / "artifacts" / f"{STEM}{suffix}"
            if not source.exists() or source.stat().st_size == 0:
                raise RuntimeError(f"missing local artifact: {source}")
            sftp.put(str(source), posixpath.join(absolute, source.name))
        with sftp.open(posixpath.join(absolute, "completion_status.txt"), "w") as handle:
            handle.write(
                "undoped_matched_cdft=14/14_clean_valid\n"
                "al16_charge_scans=complete_valid\n"
                "al16_O_Co_Mm2=rejected_spin_branch_discontinuity\n"
                "comparison_scope=fixed_geometry_mechanistic_trend\n"
            )
        print(REMOTE)
    finally:
        client.close()


if __name__ == "__main__":
    main()
