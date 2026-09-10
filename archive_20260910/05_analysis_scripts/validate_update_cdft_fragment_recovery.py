from __future__ import annotations

import argparse
import importlib.util
import posixpath
import re
from pathlib import Path


HARTREE_TO_EV = 27.211386245988
ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / ".codex/skills/ftfan-ncw-ssh/scripts/ssh_ncw.py"
spec = importlib.util.spec_from_file_location("ssh_ncw", HELPER)
ssh_ncw = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(ssh_ncw)

ROOT_REL = (
    "sfs/CoOH/cp2k/Al16/oer/spin_config_scan_site03_5OH_current_20260714/"
    "cdft_charge_spin_20260812"
)
BASE = posixpath.join(ROOT_REL, "cdft_Co48_adsorbate_fragment_charge_scan")
MANIFEST = posixpath.join(BASE, "scan_manifest.tsv")
SCHED = posixpath.join(ROOT_REL, "scheduler_manifest.tsv")


def read_text(sftp, rel: str) -> str:
    with sftp.open(posixpath.join(ssh_ncw.REMOTE_ROOT, rel), "r") as handle:
        return handle.read().decode(errors="replace")


def write_text(sftp, rel: str, value: str) -> None:
    with sftp.open(posixpath.join(ssh_ncw.REMOTE_ROOT, rel), "w") as handle:
        handle.write(value)


def run(client, command: str) -> str:
    _, stdout, stderr = client.exec_command(f"cd {ssh_ncw.REMOTE_ROOT} && {command}")
    code = stdout.channel.recv_exit_status()
    out = stdout.read().decode()
    err = stderr.read().decode()
    if code:
        raise RuntimeError(err or out)
    return out


def last_number(text: str, label: str) -> float:
    values = re.findall(rf"{re.escape(label)}\s*:\s*([-+0-9.Ee]+)", text)
    if not values:
        raise RuntimeError(f"missing {label}")
    return float(values[-1])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", required=True)
    parser.add_argument("--job", required=True)
    args = parser.parse_args()
    if not re.fullmatch(r"(?:OH|O|OOH)_frag_N[mp]1", args.case):
        raise RuntimeError(f"unsupported case: {args.case}")
    state = args.case.split("_", 1)[0]
    baseline_name = {
        "OH": "al16_valid_co48_OH",
        "O": "al16_valid_co48_O",
        "OOH": "al16_valid_co48_OOH",
    }[state]

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
        accounting = run(
            client,
            f"sacct -j {args.job} --format=JobIDRaw,State,ExitCode -n -P",
        )
        if f"{args.job}|COMPLETED|0:0" not in accounting:
            raise RuntimeError(f"job is not a clean Slurm completion: {accounting}")
        output = read_text(sftp, posixpath.join(BASE, f"{args.case}_recovery/retry.out"))
        if "PROGRAM ENDED AT" not in output or "CDFT SCF loop converged" not in output:
            raise RuntimeError("recovery did not converge normally")
        if "ABORT" in output or "SCF run NOT converged" in output or "CDFT SCF loop FAILED" in output:
            raise RuntimeError("recovery contains a fatal or unconverged signature")
        target = last_number(output, "Target value of constraint")
        current = last_number(output, "Current value of constraint")
        energy = last_number(output, "Total energy")
        baseline = read_text(sftp, posixpath.join(ROOT_REL, baseline_name, "baseline.out"))
        baseline_energy = last_number(baseline, "Total energy")
        delta_ev = (energy - baseline_energy) * HARTREE_TO_EV

        final_section = output.rsplit("CDFT atomic charges", 1)[-1]
        co_match = re.search(r"(?m)^\s*48\s+Co\s+.*?\s([-+0-9.]+)\s*$", final_section)
        total_match = re.search(
            r"Total Charge and Spin Moment:\s+[-+0-9.]+\s+([-+0-9.]+)",
            final_section,
        )
        if not co_match or not total_match:
            raise RuntimeError("could not extract final fragment spin populations")
        co_spin = float(co_match.group(1))
        fragment_spin = float(total_match.group(1))

        manifest = read_text(sftp, MANIFEST)
        lines = manifest.splitlines()
        found = False
        for index, line in enumerate(lines):
            fields = line.split("\t")
            if len(fields) >= 6 and fields[1] == args.case:
                if f"recovery_{args.job}_pending" not in fields[5]:
                    raise RuntimeError(f"unexpected manifest status: {fields[5]}")
                fields[5] = (
                    f"valid_{args.job}_dE{delta_ev:.6f}eV_"
                    f"CoSpin{co_spin:.3f}_FragSpin{fragment_spin:.3f}"
                )
                lines[index] = "\t".join(fields)
                found = True
                break
        if not found:
            raise RuntimeError("case missing from manifest")
        write_text(sftp, MANIFEST, "\n".join(lines) + "\n")

        sched = read_text(sftp, SCHED)
        row = (
            f"2026-08-16\tfragment_recovery_completion\t{args.job}\tvalid\t"
            f"{args.case}_target{target:.6f};final{current:.6f};"
            f"CoSpin{co_spin:.3f};FragSpin{fragment_spin:.3f};dE_vs_N0={delta_ev:.6f}eV"
        )
        if row not in sched:
            sched += ("" if sched.endswith("\n") else "\n") + row + "\n"
            write_text(sftp, SCHED, sched)
        print(
            f"{args.case}\t{target:.6f}\t{current:.6f}\t"
            f"{delta_ev:.6f}\t{co_spin:.3f}\t{fragment_spin:.3f}"
        )
    finally:
        client.close()


if __name__ == "__main__":
    main()
