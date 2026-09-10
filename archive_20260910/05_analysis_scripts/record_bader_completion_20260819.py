from __future__ import annotations

import argparse
import importlib.util
import math
import posixpath
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / ".codex/skills/ftfan-ncw-ssh/scripts/ssh_ncw.py"
spec = importlib.util.spec_from_file_location("ssh_ncw", HELPER)
ssh_ncw = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(ssh_ncw)

VASP_ROOT = (
    "sfs/CoOH/cp2k/Al16/oer/spin_config_scan_site03_5OH_current_20260714/"
    "vasp_jacs6c06054_reconstructed_exact_Al16_3x2_20260809"
)
ANALYSIS = posixpath.join(VASP_ROOT, "electronic_structure_al_contribution_20260818")
FIXED = posixpath.join(ANALYSIS, "fixed_geometry_bader_pdos")
MANIFEST = posixpath.join(ANALYSIS, "analysis_manifest.tsv")
SCHEDULER = posixpath.join(ANALYSIS, "scheduler_manifest.tsv")
SUMMARY = posixpath.join(ANALYSIS, "bader_case_summary.tsv")
CASES = (
    ("Al16_adjacent", "bare"),
    ("undoped_control", "bare"),
    ("Al16_adjacent", "OH"),
    ("undoped_control", "OH"),
    ("Al16_adjacent", "O"),
    ("undoped_control", "O"),
    ("Al16_adjacent", "OOH_o03"),
    ("undoped_control", "OOH_o03"),
)


def remote(rel: str) -> str:
    return posixpath.join(ssh_ncw.REMOTE_ROOT, rel)


def run(client, command: str) -> str:
    _, stdout, stderr = client.exec_command(f"cd {ssh_ncw.REMOTE_ROOT} && {command}")
    code = stdout.channel.recv_exit_status()
    output = stdout.read().decode(errors="replace")
    error = stderr.read().decode(errors="replace")
    if code:
        raise RuntimeError(error or output)
    return output


def read_text(sftp, rel: str) -> str:
    with sftp.open(remote(rel), "r") as handle:
        return handle.read().decode(errors="replace")


def write_text(sftp, rel: str, value: str) -> None:
    with sftp.open(remote(rel), "w") as handle:
        handle.write(value)


def atom_count(poscar: str) -> int:
    lines = poscar.splitlines()
    fields = lines[5].split()
    count_line = fields if all(value.lstrip("+-").isdigit() for value in fields) else lines[6].split()
    return sum(int(value) for value in count_line)


def parse_acf(text: str) -> tuple[list[float], float, float]:
    charges = []
    vacuum = None
    electrons = None
    for line in text.splitlines():
        fields = line.split()
        if len(fields) == 7 and fields[0].isdigit():
            if int(fields[0]) != len(charges) + 1:
                raise RuntimeError("nonconsecutive ACF atom indices")
            charges.append(float(fields[4]))
        elif "VACUUM CHARGE:" in line:
            vacuum = float(fields[-1])
        elif "NUMBER OF ELECTRONS:" in line:
            electrons = float(fields[-1])
    if not charges or vacuum is None or electrons is None:
        raise RuntimeError("incomplete ACF.dat")
    return charges, vacuum, electrons


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", type=int, choices=range(8), required=True)
    parser.add_argument("--job", required=True)
    args = parser.parse_args()
    branch, state = CASES[args.task]
    case = posixpath.join(FIXED, branch, state)

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
        state_line = run(client, f"sacct -j {args.job} -n -P -o State,ExitCode").splitlines()[0]
        if state_line != "COMPLETED|0:0":
            raise RuntimeError(f"Bader job is not cleanly complete: {state_line}")
        bader_out = read_text(sftp, posixpath.join(case, "bader.out"))
        if "GRID BASED BADER ANALYSIS  (Version 1.05" not in bader_out:
            raise RuntimeError("wrong or missing Bader version")
        if "WRITING BADER ATOMIC CHARGES TO ACF.dat" not in bader_out:
            raise RuntimeError("Bader did not write atomic charges")
        if any(marker in bader_out.upper() for marker in ("ERROR", "ABORT", "FAILED")):
            raise RuntimeError("Bader output contains a fatal marker")
        charges, vacuum, electrons = parse_acf(read_text(sftp, posixpath.join(case, "ACF.dat")))
        expected_atoms = atom_count(read_text(sftp, posixpath.join(case, "POSCAR")))
        if len(charges) != expected_atoms:
            raise RuntimeError(f"ACF atom count mismatch: {len(charges)} vs {expected_atoms}")
        outcar = read_text(sftp, posixpath.join(case, "OUTCAR"))
        nelect_matches = re.findall(r"NELECT\s*=\s*([-+0-9.Ee]+)", outcar)
        if not nelect_matches:
            raise RuntimeError("OUTCAR NELECT is missing")
        nelect = float(nelect_matches[-1])
        if not math.isclose(electrons + vacuum, nelect, rel_tol=0.0, abs_tol=1e-4):
            raise RuntimeError(f"Bader charge is not conserved: {electrons}+{vacuum} vs {nelect}")

        lines = read_text(sftp, MANIFEST).splitlines()
        fields = lines[args.task + 1].split("\t")
        if f"recovery_{args.job}_pending" not in fields[7] and f"bader_{args.job}_pending" not in fields[7]:
            raise RuntimeError(f"unexpected manifest status: {fields[7]}")
        fields[7] = (
            f"valid_vasp_111172_{args.task}_bader_{args.job}_valid_"
            f"atoms{expected_atoms}_electrons{electrons:.5f}_vacuum{vacuum:.4f}"
        )
        lines[args.task + 1] = "\t".join(fields)
        write_text(sftp, MANIFEST, "\n".join(lines) + "\n")

        try:
            summary = read_text(sftp, SUMMARY)
        except FileNotFoundError:
            summary = "task\tbranch\tstate\tbader_job\tatoms\telectrons\tvacuum_charge\tmin_atomic_charge\tmax_atomic_charge\n"
        if any(line.startswith(f"{args.task}\t") for line in summary.splitlines()[1:]):
            raise RuntimeError("Bader summary already contains this task")
        summary += (
            f"{args.task}\t{branch}\t{state}\t{args.job}\t{expected_atoms}\t{electrons:.6f}\t"
            f"{vacuum:.6f}\t{min(charges):.6f}\t{max(charges):.6f}\n"
        )
        write_text(sftp, SUMMARY, summary)

        scheduler = read_text(sftp, SCHEDULER)
        scheduler += (
            f"2026-08-19\tfixed_geometry_bader_valid_completion\t{args.job}\tn28\t1\t1\t"
            f"task{args.task};{branch};{state};atoms{expected_atoms};electrons{electrons:.5f};"
            f"vacuum{vacuum:.4f};Bader1.05\n"
        )
        write_text(sftp, SCHEDULER, scheduler)
        print(f"task={args.task} atoms={expected_atoms} electrons={electrons:.5f} vacuum={vacuum:.4f}")
    finally:
        client.close()


if __name__ == "__main__":
    main()
