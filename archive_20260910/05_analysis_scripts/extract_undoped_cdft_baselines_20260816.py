from __future__ import annotations

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
CASES = {
    "undoped_valid_co32_OH": (32, 211, 212),
    "undoped_valid_co32_O": (32, 211),
    "undoped_valid_co32_OOH": (32, 211, 212, 213),
}


def read_text(sftp, rel: str) -> str:
    with sftp.open(posixpath.join(ssh_ncw.REMOTE_ROOT, rel), "r") as handle:
        return handle.read().decode(errors="replace")


def write_text(sftp, rel: str, content: str) -> None:
    with sftp.open(posixpath.join(ssh_ncw.REMOTE_ROOT, rel), "w") as handle:
        handle.write(content)


def table(text: str, title: str) -> dict[int, list[str]]:
    start = text.rfind(title)
    if start < 0:
        raise RuntimeError(f"missing {title}")
    rows: dict[int, list[str]] = {}
    for line in text[start:].splitlines():
        match = re.match(r"\s*(\d+)\s+([A-Za-z]+)\s+(\d+)\s+(.+)$", line)
        if match:
            rows[int(match.group(1))] = [
                match.group(2),
                match.group(3),
                *match.group(4).split(),
            ]
        elif rows and ("Total" in line or "!----" in line):
            break
    return rows


def elements(text: str) -> list[str]:
    match = re.search(r"(?is)&COORD\b(.*?)&END\s+COORD", text)
    if not match:
        raise RuntimeError("missing COORD")
    return [
        line.split()[0]
        for line in match.group(1).splitlines()
        if len(line.split()) >= 4
    ]


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
        accounting = run(
            client,
            "sacct -j 111095 --format=JobIDRaw,State,ExitCode -n -P",
        )
        if sum("|COMPLETED|0:0" in line for line in accounting.splitlines()) < 3:
            raise RuntimeError(f"baseline array incomplete: {accounting}")

        output_lines = [
            "case\tatom\telement\tmull_population\tmull_charge\tmull_spin\t"
            "hirsh_population\thirsh_charge\thirsh_spin"
        ]
        for case, atom_ids in CASES.items():
            output = read_text(sftp, posixpath.join(BASE, case, "baseline.out"))
            if "PROGRAM ENDED AT" not in output:
                raise RuntimeError(f"{case} lacks normal termination")
            if "ABORT" in output or "SCF run NOT converged" in output:
                raise RuntimeError(f"{case} has fatal or unconverged output")
            inp = read_text(sftp, posixpath.join(BASE, case, "baseline.inp"))
            atom_elements = elements(inp)
            mulliken = table(output, "Mulliken Population Analysis")
            hirshfeld = table(output, "Hirshfeld Charges")
            for atom in atom_ids:
                mull = mulliken[atom]
                hirsh = hirshfeld[atom]
                mull_pop = float(mull[2]) + float(mull[3])
                hirsh_pop = float(hirsh[3]) + float(hirsh[4])
                output_lines.append(
                    f"{case}\t{atom}\t{atom_elements[atom - 1]}\t"
                    f"{mull_pop:.6f}\t{float(mull[4]):.6f}\t{float(mull[5]):.6f}\t"
                    f"{hirsh_pop:.6f}\t{float(hirsh[6]):.6f}\t{float(hirsh[5]):.6f}"
                )

        summary = "\n".join(output_lines) + "\n"
        write_text(sftp, posixpath.join(BASE, "baseline_population_summary.tsv"), summary)
        local = ROOT / "artifacts/undoped_cdft_baseline_population_summary.tsv"
        local.write_text(summary, encoding="ascii", newline="\n")

        manifest_rel = posixpath.join(BASE, "baseline_manifest.tsv")
        manifest = read_text(sftp, manifest_rel).replace("\tprepared\n", "\tvalid\n")
        write_text(sftp, manifest_rel, manifest)
        scheduler_rel = posixpath.join(BASE, "scheduler_manifest.tsv")
        scheduler = read_text(sftp, scheduler_rel)
        scheduler += (
            "2026-08-16\tbaseline_completion\t111095_0-2\tvalid\t"
            "normal_CP2K;Gaussian_Hirshfeld;Mulliken;DFT+U_occupations;"
            "fixed_geometry\n"
        )
        write_text(sftp, scheduler_rel, scheduler)
        print(summary, end="")
    finally:
        client.close()


if __name__ == "__main__":
    main()
