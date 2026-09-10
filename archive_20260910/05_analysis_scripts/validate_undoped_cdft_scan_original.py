from __future__ import annotations

import argparse
import csv
import importlib.util
import io
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

BASE = (
    "sfs/CoOH/cp2k/thermo_vib_5OH_U100_current_20260704/"
    "cdft_charge_spin_undoped_20260816"
)
SCAN = posixpath.join(BASE, "matched_cdft_scans")


def read_text(sftp, rel: str) -> str:
    with sftp.open(posixpath.join(ssh_ncw.REMOTE_ROOT, rel), "r") as handle:
        return handle.read().decode(errors="replace")


def write_text(sftp, rel: str, content: str) -> None:
    with sftp.open(posixpath.join(ssh_ncw.REMOTE_ROOT, rel), "w") as handle:
        handle.write(content)


def run(client, command: str) -> str:
    _, stdout, stderr = client.exec_command(
        f"cd {ssh_ncw.REMOTE_ROOT} && {command}"
    )
    code = stdout.channel.recv_exit_status()
    output = stdout.read().decode()
    error = stderr.read().decode()
    if code:
        raise RuntimeError(error or output)
    return output


def last_number(text: str, label: str) -> float:
    values = re.findall(rf"{re.escape(label)}\s*:\s*([-+0-9.Ee]+)", text)
    if not values:
        raise RuntimeError(f"missing {label}")
    return float(values[-1])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", required=True)
    parser.add_argument("--array-task", required=True)
    parser.add_argument("--job", required=True)
    args = parser.parse_args()

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
        manifest_rel = posixpath.join(SCAN, "scan_manifest.tsv")
        manifest_text = read_text(sftp, manifest_rel)
        rows = list(csv.DictReader(io.StringIO(manifest_text), delimiter="\t"))
        row = next((item for item in rows if item["case"] == args.case), None)
        if row is None:
            raise RuntimeError(f"case missing from manifest: {args.case}")
        if row["status"] != "prepared":
            raise RuntimeError(f"unexpected status: {row['status']}")

        accounting = run(
            client,
            f"sacct -j {args.job} --format=JobIDRaw,State,ExitCode -n -P",
        )
        if f"{args.job}|COMPLETED|0:0" not in accounting:
            raise RuntimeError(f"job is not a clean Slurm completion: {accounting}")
        output = read_text(sftp, posixpath.join(SCAN, args.case, "scan.out"))
        if "PROGRAM ENDED AT" not in output or "CDFT SCF loop converged" not in output:
            raise RuntimeError("scan did not converge normally")
        if "ABORT" in output or "SCF run NOT converged" in output or "CDFT SCF loop FAILED" in output:
            raise RuntimeError("scan contains fatal or unconverged signature")

        target = last_number(output, "Target value of constraint")
        current = last_number(output, "Current value of constraint")
        energy = last_number(output, "Total energy")
        baseline = read_text(
            sftp, posixpath.join(BASE, row["source"], "baseline.out")
        )
        baseline_energy = last_number(baseline, "Total energy")
        delta_ev = (energy - baseline_energy) * HARTREE_TO_EV

        final_section = output.rsplit("CDFT atomic charges", 1)[-1]
        co_match = re.search(r"(?m)^\s*32\s+Co\s+.*?\s([-+0-9.]+)\s*$", final_section)
        total_match = re.search(
            r"Total Charge and Spin Moment:\s+[-+0-9.]+\s+([-+0-9.]+)",
            final_section,
        )
        if not co_match or not total_match:
            raise RuntimeError("could not extract final spin populations")
        co_spin = float(co_match.group(1))
        group_spin = float(total_match.group(1))

        lines = manifest_text.splitlines()
        for index, line in enumerate(lines):
            fields = line.split("\t")
            if len(fields) >= 7 and fields[1] == args.case:
                fields[6] = (
                    f"valid_{args.array_task}_dE{delta_ev:.6f}eV_"
                    f"CoSpin{co_spin:.3f}_GroupSpin{group_spin:.3f}"
                )
                lines[index] = "\t".join(fields)
                break
        write_text(sftp, manifest_rel, "\n".join(lines) + "\n")

        scheduler_rel = posixpath.join(BASE, "scheduler_manifest.tsv")
        scheduler = read_text(sftp, scheduler_rel)
        scheduler += (
            f"2026-08-17\tmatched_scan_completion\t{args.array_task}\tvalid\t"
            f"physical_job{args.job};{args.case};target{target:.6f};"
            f"final{current:.6f};CoSpin{co_spin:.3f};GroupSpin{group_spin:.3f};"
            f"dE_vs_N0={delta_ev:.6f}eV\n"
        )
        write_text(sftp, scheduler_rel, scheduler)
        print(
            f"{args.case}\t{target:.6f}\t{current:.6f}\t{delta_ev:.6f}\t"
            f"{co_spin:.3f}\t{group_spin:.3f}"
        )
    finally:
        client.close()


if __name__ == "__main__":
    main()
