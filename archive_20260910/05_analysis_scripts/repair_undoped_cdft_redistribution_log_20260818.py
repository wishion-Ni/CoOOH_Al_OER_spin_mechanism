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

BASE = (
    "sfs/CoOH/cp2k/thermo_vib_5OH_U100_current_20260704/"
    "cdft_charge_spin_undoped_20260816"
)
SCAN = posixpath.join(BASE, "matched_cdft_scans")
SCHEDULER = posixpath.join(BASE, "scheduler_manifest.tsv")


def read_text(sftp, rel: str) -> str:
    with sftp.open(posixpath.join(ssh_ncw.REMOTE_ROOT, rel), "r") as handle:
        return handle.read().decode(errors="replace")


def write_text(sftp, rel: str, value: str) -> None:
    with sftp.open(posixpath.join(ssh_ncw.REMOTE_ROOT, rel), "w") as handle:
        handle.write(value)


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
        manifest = read_text(sftp, posixpath.join(SCAN, "scan_manifest.tsv"))
        required = (
            "valid_111151_dE4.397178eV_CoSpin2.532_GroupSpin2.532",
            "redistributed_111152_n40_pending",
            "valid_111153_dE5.255931eV_CoSpin2.972_GroupSpin2.972",
        )
        if not all(marker in manifest for marker in required):
            raise RuntimeError("scan manifest does not match the verified redistribution state")

        scheduler = read_text(sftp, SCHEDULER)
        rows = [
            "2026-08-18\tresource_redistribution\t111098_7,9-11,13\t"
            "canceled_pending_to_111154_0-4\tn28_to_n40;concurrency3;no_duplicate",
            "2026-08-18\tresource_redistribution\t111114\t"
            "canceled_pending_to_111151\tOH_Co_Np1_recovery2;n28_to_n40;no_duplicate",
            "2026-08-18\tresource_redistribution\t111121\t"
            "canceled_pending_to_111152\tOH_frag_Nm1_recovery2;n28_to_n40;no_duplicate",
            "2026-08-18\tresource_redistribution\t111115\t"
            "canceled_pending_to_111153\tO_Co_Nm1_recovery;n28_to_n40;no_duplicate",
        ]
        for row in rows:
            if row not in scheduler:
                scheduler += ("" if scheduler.endswith("\n") else "\n") + row + "\n"
        write_text(sftp, SCHEDULER, scheduler)
        print("redistribution_log_repaired")
    finally:
        client.close()


if __name__ == "__main__":
    main()
