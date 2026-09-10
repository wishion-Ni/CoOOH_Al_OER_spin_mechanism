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
    "proton_relay_al16_vs_undoped_20260817/pcet_CoO_fragment_Nm1"
)
HARTREE_TO_EV = 27.211386245988


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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", type=int, required=True)
    args = parser.parse_args()
    if args.task not in range(6):
        raise RuntimeError("task must be 0..5")

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
        manifest = read_text(sftp, posixpath.join(BASE, "scan_manifest.tsv"))
        lines = manifest.splitlines()
        fields = lines[args.task + 1].split("\t")
        if int(fields[0]) != args.task:
            raise RuntimeError(f"unexpected manifest row: {lines[args.task + 1]}")
        case, image = fields[1], int(fields[2])
        atom_indices = [int(value) for value in fields[5].split(",")]
        recovery_outputs = {
            0: (
                "rejected_111141_0_cleanup_abort_physical_converged_recovery_111146_pending",
                "al16_image_00_cleanup",
                "cleanup.out",
                "111146",
            ),
            2: (
                "rejected_111141_2_cleanup_abort_physical_converged_recovery_111148_pending",
                "al16_image_06_cleanup",
                "cleanup.out",
                "111148",
            ),
            3: (
                "rejected_111141_3_and_111149_CDFT_nonconverged_"
                "tight_SCF_recovery_111150_pending",
                "undoped_image_00_tight_scf_recovery",
                "recovery.out",
                "111150",
            ),
        }
        if args.task in recovery_outputs:
            expected_status, output_dir, output_name, valid_job = recovery_outputs[args.task]
            if fields[7] != expected_status:
                raise RuntimeError(f"unexpected recovery status: {fields[7]}")
        else:
            if fields[7] != "prepared":
                raise RuntimeError(f"unexpected manifest status: {fields[7]}")
            output_dir = f"{case}_image_{image:02d}"
            output_name = "scan.out"
            valid_job = f"111141_{args.task}"
        output_rel = posixpath.join(BASE, output_dir, output_name)
        output = read_text(sftp, output_rel)
        if "PROGRAM ENDED AT" not in output or "CDFT SCF loop converged" not in output:
            raise RuntimeError("cDFT did not complete cleanly")
        forbidden = ("ABORT in", "SCF run NOT converged", "CDFT SCF loop FAILED")
        if any(marker in output for marker in forbidden):
            raise RuntimeError("cDFT output contains a fatal signature")
        target = last_number(output, "Target value of constraint")
        current = last_number(output, "Current value of constraint")
        if abs(current - target) > 1.5e-4:
            raise RuntimeError(f"constraint outside tolerance: {target} vs {current}")
        energies = re.findall(
            r"ENERGY\| Total FORCE_EVAL \( QS \) energy \[a\.u\.\]:\s*"
            r"([-+0-9.Ee]+)",
            output,
        )
        if not energies:
            raise RuntimeError("missing final constrained energy")
        constrained = float(energies[-1])
        unconstrained = float(fields[6])
        delta_ev = (constrained - unconstrained) * HARTREE_TO_EV

        spins = []
        for atom in atom_indices:
            matches = re.findall(
                rf"(?m)^\s*{atom}\s+\S+\s+T\s+[-+0-9.]+\s+"
                r"[-+0-9.]+\s+[-+0-9.]+\s+[-+0-9.]+\s+([-+0-9.]+)\s*$",
                output,
            )
            if not matches:
                raise RuntimeError(f"missing constrained spin for atom {atom}")
            spins.append(float(matches[-1]))
        fields[7] = (
            f"valid_{valid_job}_dE{delta_ev:.6f}eV_"
            f"CoSpin{spins[0]:.3f}_OSpin{spins[1]:.3f}"
        )
        lines[args.task + 1] = "\t".join(fields)
        write_text(sftp, posixpath.join(BASE, "scan_manifest.tsv"), "\n".join(lines) + "\n")

        scheduler = read_text(sftp, posixpath.join(BASE, "scheduler_manifest.tsv"))
        row = (
            f"2026-08-18\tCoO_fragment_Nm1_valid\t{valid_job}\tcompleted\t"
            f"{case}_image{image};target{target:.6f};final{current:.6f};"
            f"dE{delta_ev:.6f}eV;CoSpin{spins[0]:.3f};OSpin{spins[1]:.3f}\n"
        )
        if row not in scheduler:
            scheduler += ("" if scheduler.endswith("\n") else "\n") + row
        write_text(sftp, posixpath.join(BASE, "scheduler_manifest.tsv"), scheduler)
        print(fields[7])
    finally:
        client.close()


if __name__ == "__main__":
    main()
