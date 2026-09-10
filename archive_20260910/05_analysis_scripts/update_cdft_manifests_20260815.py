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
    "sfs/CoOH/cp2k/Al16/oer/spin_config_scan_site03_5OH_current_20260714/"
    "cdft_charge_spin_20260812"
)
SCAN = posixpath.join(BASE, "cdft_O_Co48_scan/scan_manifest.tsv")
SCHED = posixpath.join(BASE, "scheduler_manifest.tsv")


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
        scan = read_text(sftp, SCAN)
        replacements = {
            "0\tcharge_Nm1\tCHARGE\t17.470000\t48\tprepared":
                "0\tcharge_Nm1\tCHARGE\t17.470000\t48\tvalid_111055_dE5.146837eV",
            "1\tcharge_Np1\tCHARGE\t19.470000\t48\tprepared":
                "1\tcharge_Np1\tCHARGE\t19.470000\t48\tvalid_111058_recovery_dE4.141331eV",
            "2\tmag_Mm2\tMAGNETIZATION\t0.776000\t48\tprepared":
                "2\tmag_Mm2\tMAGNETIZATION\t0.776000\t48\trejected_111057_timeout_spin_branch_discontinuity",
            "3\tmag_Mp2\tMAGNETIZATION\t4.776000\t48\tprepared":
                "3\tmag_Mp2\tMAGNETIZATION\t4.776000\t48\trunning_111054_3",
            "3\tmag_Mp2\tMAGNETIZATION\t4.776000\t48\trunning_111054_3":
                "3\tmag_Mp2\tMAGNETIZATION\t4.776000\t48\tvalid_111054_3_dE4.036604eV",
        }
        for old, new in replacements.items():
            if old in scan:
                scan = scan.replace(old, new)
            elif new not in scan:
                raise RuntimeError(f"unexpected scan manifest row: {old}")
        write_text(sftp, SCAN, scan)

        sched = read_text(sftp, SCHED)
        rows = [
            "2026-08-13\tpilot_completion\t111053\tvalid\tO_Co48_charge_N0_target18.470000;normal_CP2K_termination",
            "2026-08-14\tscan_completion\t111055\tvalid\tO_Co48_charge_Nm1_target17.470000;dE_vs_N0=5.146837eV",
            "2026-08-14\tscan_failure\t111056\trejected_scheduler\tO_Co48_charge_Np1_converged_but_slurm_FAILED_exit15;recovery_required",
            "2026-08-15\trecovery_completion\t111058\tvalid\tO_Co48_charge_Np1_target19.470000;final19.470007;dE_vs_N0=4.141331eV",
            "2026-08-15\tscan_failure\t111057\trejected_timeout\tO_Co48_mag_Mm2_target0.776000;24h_timeout;positive_negative_spin_branch_discontinuity",
            "2026-08-15\tscan_start\t111054_3\trunning\tO_Co48_mag_Mp2_target4.776000;nonduplicate_array_continuation",
            "2026-08-15\tscan_completion\t111054_3\tvalid\tO_Co48_mag_Mp2_target4.776000;final4.776074;dE_vs_N0=4.036604eV",
        ]
        for row in rows:
            if row not in sched:
                sched += ("" if sched.endswith("\n") else "\n") + row + "\n"
        write_text(sftp, SCHED, sched)
        print("updated")
    finally:
        client.close()


if __name__ == "__main__":
    main()
