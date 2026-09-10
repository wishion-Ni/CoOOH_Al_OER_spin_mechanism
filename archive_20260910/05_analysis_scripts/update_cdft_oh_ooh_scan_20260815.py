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
MANIFEST = posixpath.join(BASE, "cdft_OH_OOH_Co48_charge_scan/scan_manifest.tsv")
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
        manifest = read_text(sftp, MANIFEST)
        old = "0\tOH_charge_Nm1\tCHARGE\t17.458000\t48\tprepared"
        new = "0\tOH_charge_Nm1\tCHARGE\t17.458000\t48\tvalid_111071_0_dE4.889379eV_spin3.857"
        if old in manifest:
            manifest = manifest.replace(old, new)
        elif new not in manifest:
            raise RuntimeError("unexpected OH N-1 manifest row")
        old = "1\tOH_charge_Np1\tCHARGE\t19.458000\t48\tprepared"
        new = "1\tOH_charge_Np1\tCHARGE\t19.458000\t48\tvalid_111071_1_dE4.454942eV_spin2.665"
        if old in manifest:
            manifest = manifest.replace(old, new)
        elif new not in manifest:
            raise RuntimeError("unexpected OH N+1 manifest row")
        old = "3\tOOH_charge_Np1\tCHARGE\t19.379000\t48\trejected_111077_cleanup_recovery2_111078_pending"
        new = "3\tOOH_charge_Np1\tCHARGE\t19.379000\t48\tvalid_111078_dE4.165019eV_spin2.476"
        if old in manifest:
            manifest = manifest.replace(old, new)
        elif new not in manifest:
            raise RuntimeError("unexpected OOH N+1 recovery2 manifest row")
        write_text(sftp, MANIFEST, manifest)

        sched = read_text(sftp, SCHED)
        row = (
            "2026-08-15\tscan_completion\t111071_0\tvalid\t"
            "OH_Co48_charge_Nm1_target17.458000;final17.457912;"
            "spin3.857;dE_vs_N0=4.889379eV"
        )
        if row not in sched:
            sched += ("" if sched.endswith("\n") else "\n") + row + "\n"
        row = (
            "2026-08-15\tscan_completion\t111071_1\tvalid\t"
            "OH_Co48_charge_Np1_target19.458000;final19.458056;"
            "spin2.665;dE_vs_N0=4.454942eV"
        )
        if row not in sched:
            sched += ("" if sched.endswith("\n") else "\n") + row + "\n"
        row = (
            "2026-08-15\trecovery_completion\t111078\tvalid\t"
            "OOH_Co48_charge_Np1_target19.379000;final19.379033;"
            "spin2.476;dE_vs_N0=4.165019eV;single_iteration_clean_termination"
        )
        if row not in sched:
            sched += ("" if sched.endswith("\n") else "\n") + row + "\n"
        write_text(sftp, SCHED, sched)
        print("updated")
    finally:
        client.close()


if __name__ == "__main__":
    main()
