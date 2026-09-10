from __future__ import annotations

import argparse
import importlib.util
import posixpath
import re
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
MANIFEST = posixpath.join(SCAN, "scan_manifest.tsv")
SCHEDULER = posixpath.join(BASE, "scheduler_manifest.tsv")
HARTREE_TO_EV = 27.211386245988
CASES = {
    "O_Co_Mm2": {
        "task": "6",
        "case_dir": "O_Co_Mm2_recovery",
        "output": "recovery.out",
        "baseline": posixpath.join(BASE, "undoped_valid_co32_O", "baseline.out"),
        "source_job": "111162",
        "old_status": "rejected_111098_6_TIMEOUT_recovery_111162_n40_pending",
    },
    "O_Co_Mp2": {
        "task": "7",
        "case_dir": "O_Co_Mp2_recovery",
        "output": "recovery.out",
        "baseline": posixpath.join(BASE, "undoped_valid_co32_O", "baseline.out"),
        "source_job": "111160",
        "old_status": "rejected_111154_0_CDFT_nonconverged_recovery_111160_pending",
    },
    "O_frag_Np1": {
        "task": "9",
        "case_dir": "O_frag_Np1",
        "output": "scan.out",
        "baseline": posixpath.join(BASE, "undoped_valid_co32_O", "baseline.out"),
        "source_job": "111154_1",
        "old_status": "prepared",
    },
    "OOH_Co_Nm1": {
        "task": "10",
        "case_dir": "OOH_Co_Nm1",
        "output": "scan.out",
        "baseline": posixpath.join(BASE, "undoped_valid_co32_OOH", "baseline.out"),
        "source_job": "111154_2",
        "old_status": "prepared",
    },
    "OOH_Co_Np1": {
        "task": "11",
        "case_dir": "OOH_Co_Np1",
        "output": "scan.out",
        "baseline": posixpath.join(BASE, "undoped_valid_co32_OOH", "baseline.out"),
        "source_job": "111154_3",
        "old_status": "prepared",
    },
    "OOH_frag_Np1": {
        "task": "13",
        "case_dir": "OOH_frag_Np1",
        "output": "scan.out",
        "baseline": posixpath.join(BASE, "undoped_valid_co32_OOH", "baseline.out"),
        "source_job": "111154_4",
        "old_status": "prepared",
    },
    "OH_Co_Np1": {
        "task": "1",
        "case_dir": "OH_Co_Np1_recovery2",
        "output": "cleanup.out",
        "baseline": posixpath.join(BASE, "undoped_valid_co32_OH", "baseline.out"),
        "source_job": "111151",
        "old_status": (
            "rejected_111098_1_inner_scf_then_111102_cleanup_recovery_111114_"
            "pending_canceled_pending_redistributed_111151_n40_pending"
        ),
    },
    "OH_frag_Nm1": {
        "task": "2",
        "case_dir": "OH_frag_Nm1_recovery3",
        "output": "cleanup.out",
        "baseline": posixpath.join(BASE, "undoped_valid_co32_OH", "baseline.out"),
        "source_job": "111158",
        "old_status": (
            "rejected_111098_2_then_111117_0_then_111152_cleanup_recovery_"
            "111158_pending"
        ),
    },
    "O_Co_Nm1": {
        "task": "4",
        "case_dir": "O_Co_Nm1_recovery",
        "output": "cleanup.out",
        "baseline": posixpath.join(BASE, "undoped_valid_co32_O", "baseline.out"),
        "source_job": "111153",
        "old_status": (
            "rejected_111098_4_cleanup_recovery_111115_pending_canceled_pending_"
            "redistributed_111153_n40_pending"
        ),
    },
    "O_frag_Nm1": {
        "task": "8",
        "case_dir": "O_frag_Nm1",
        "output": "scan.out",
        "baseline": posixpath.join(BASE, "undoped_valid_co32_O", "baseline.out"),
        "source_job": "111117_1",
        "old_status": "redistributed_111098_8_cancelled_to_111117_1_pending",
    },
    "OOH_frag_Nm1": {
        "task": "12",
        "case_dir": "OOH_frag_Nm1",
        "output": "scan.out",
        "baseline": posixpath.join(BASE, "undoped_valid_co32_OOH", "baseline.out"),
        "source_job": "111117_2",
        "old_status": "redistributed_111098_12_cancelled_to_111117_2_pending",
    },
}


def read_text(sftp, rel: str) -> str:
    with sftp.open(posixpath.join(ssh_ncw.REMOTE_ROOT, rel), "r") as handle:
        return handle.read().decode(errors="replace")


def write_text(sftp, rel: str, value: str) -> None:
    with sftp.open(posixpath.join(ssh_ncw.REMOTE_ROOT, rel), "w") as handle:
        handle.write(value)


def last_number(text: str, label: str) -> float:
    values = re.findall(rf"{re.escape(label)}\s*:\s*([-+0-9.Ee]+)", text)
    if not values:
        raise RuntimeError(f"missing {label}")
    return float(values[-1])


def last_energy(text: str) -> float:
    values = re.findall(
        r"ENERGY\| Total FORCE_EVAL \( QS \) energy \[a\.u\.\]:\s*([-+0-9.Ee]+)",
        text,
    )
    if not values:
        raise RuntimeError("missing final FORCE_EVAL energy")
    return float(values[-1])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", choices=CASES, required=True)
    args = parser.parse_args()
    cfg = CASES[args.case]

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
        output = read_text(
            sftp, posixpath.join(SCAN, cfg["case_dir"], cfg["output"])
        )
        required = ("CDFT SCF loop converged", "PROGRAM ENDED AT")
        if not all(marker in output for marker in required):
            raise RuntimeError("scan did not terminate with converged cDFT")
        forbidden = (
            "ABORT in",
            "SCF run NOT converged",
            "CDFT SCF loop FAILED",
            "Cholesky decompose failed",
        )
        if any(marker in output for marker in forbidden):
            raise RuntimeError("scan contains a fatal or convergence signature")

        target = last_number(output, "Target value of constraint")
        current = last_number(output, "Current value of constraint")
        strength = last_number(output, "Strength of constraint")
        if abs(current - target) > 1.5e-4:
            raise RuntimeError(
                f"constraint outside tolerance: target={target}, current={current}"
            )

        baseline = read_text(sftp, cfg["baseline"])
        delta_ev = (last_energy(output) - last_energy(baseline)) * HARTREE_TO_EV
        co_spins = re.findall(
            r"^\s*32\s+Co\s+T\s+17\.000\s+[-+0-9.]+\s+[-+0-9.]+\s+"
            r"[-+0-9.]+\s+([-+0-9.]+)\s*$",
            output,
            flags=re.MULTILINE,
        )
        group_spins = re.findall(
            r"Total Charge and Spin Moment:\s+[-+0-9.]+\s+([-+0-9.]+)", output
        )
        if not co_spins or not group_spins:
            raise RuntimeError("missing final constrained Co/group spin")
        co_spin = float(co_spins[-1])
        group_spin = float(group_spins[-1])

        manifest = read_text(sftp, MANIFEST)
        lines = manifest.splitlines()
        found = False
        for index, line in enumerate(lines):
            fields = line.split("\t")
            if len(fields) >= 7 and fields[0] == cfg["task"]:
                if fields[1] != args.case or fields[6] != cfg["old_status"]:
                    raise RuntimeError(f"unexpected manifest row: {line}")
                fields[6] = (
                    f"valid_{cfg['source_job']}_dE{delta_ev:.6f}eV_"
                    f"CoSpin{co_spin:.3f}_GroupSpin{group_spin:.3f}"
                )
                lines[index] = "\t".join(fields)
                found = True
                break
        if not found:
            raise RuntimeError(f"missing manifest task {cfg['task']}")
        write_text(sftp, MANIFEST, "\n".join(lines) + "\n")

        scheduler = read_text(sftp, SCHEDULER)
        row = (
            f"2026-08-18\tmatched_scan_valid_completion\t{cfg['source_job']}\t"
            f"completed\t{args.case};target{target:.6f};final{current:.6f};"
            f"strength{strength:.12f};dE{delta_ev:.6f}eV;"
            f"CoSpin{co_spin:.3f};GroupSpin{group_spin:.3f};clean_PROGRAM_ENDED"
        )
        if row not in scheduler:
            scheduler += ("" if scheduler.endswith("\n") else "\n") + row + "\n"
        write_text(sftp, SCHEDULER, scheduler)
        print(
            f"{args.case}|target={target:.6f}|current={current:.6f}|"
            f"dE={delta_ev:.6f}|CoSpin={co_spin:.3f}|GroupSpin={group_spin:.3f}"
        )
    finally:
        client.close()


if __name__ == "__main__":
    main()
