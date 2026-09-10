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

REMOTE = (
    "sfs/CoOH/cp2k/Al16/oer/spin_config_scan_site03_5OH_current_20260714/"
    "cdft_charge_spin_20260812"
)
CASES = ("al16_valid_co48_OH", "al16_valid_co48_O", "al16_valid_co48_OOH")


def table(text: str, title: str) -> dict[int, list[str]]:
    start = text.rfind(title)
    if start < 0:
        raise ValueError(f"missing {title}")
    rows: dict[int, list[str]] = {}
    for line in text[start:].splitlines():
        match = re.match(r"\s*(\d+)\s+([A-Za-z]+)\s+(\d+)\s+(.+)$", line)
        if match:
            rows[int(match.group(1))] = [match.group(2), match.group(3), *match.group(4).split()]
        elif rows and ("Total" in line or "!----" in line):
            break
    return rows


def coords(text: str) -> list[str]:
    match = re.search(r"&COORD\b(.*?)&END\s+COORD", text, re.I | re.S)
    if not match:
        raise ValueError("missing COORD")
    return [line.split()[0] for line in match.group(1).splitlines() if len(line.split()) >= 4]


def main() -> None:
    paramiko = ssh_ncw.ensure_paramiko()
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=ssh_ncw.HOST, port=ssh_ncw.PORT, username=ssh_ncw.USER,
                   password=ssh_ncw.load_password(), look_for_keys=False, allow_agent=False)
    try:
        sftp = client.open_sftp()
        lines = ["case\tatom\telement\tmull_population\tmull_charge\tmull_spin\thirsh_population\thirsh_charge\thirsh_spin"]
        for case in CASES:
            base = posixpath.join(ssh_ncw.REMOTE_ROOT, REMOTE, case)
            with sftp.open(posixpath.join(base, "baseline.out"), "r") as handle:
                out = handle.read().decode(errors="replace")
            with sftp.open(posixpath.join(base, "baseline.inp"), "r") as handle:
                inp = handle.read().decode(errors="replace")
            mull = table(out, "Mulliken Population Analysis")
            hirsh = table(out, "Hirshfeld Charges")
            elements = coords(inp)
            # Active Co plus appended adsorbate atoms after the 220-atom background.
            atom_ids = [48, *range(221, len(elements) + 1)]
            for atom in atom_ids:
                m = mull[atom]
                h = hirsh[atom]
                m_pop = float(m[2]) + float(m[3])
                h_pop = float(h[3]) + float(h[4])
                lines.append(
                    f"{case}\t{atom}\t{elements[atom-1]}\t{m_pop:.6f}\t{float(m[4]):.6f}\t{float(m[5]):.6f}"
                    f"\t{h_pop:.6f}\t{float(h[6]):.6f}\t{float(h[5]):.6f}"
                )
        text = "\n".join(lines) + "\n"
        with sftp.open(posixpath.join(ssh_ncw.REMOTE_ROOT, REMOTE, "baseline_population_summary.tsv"), "w") as handle:
            handle.write(text)
        local = ROOT / "artifacts/cdft_baseline_population_summary.tsv"
        local.write_text(text, encoding="ascii", newline="\n")
        print(text, end="")
    finally:
        client.close()


if __name__ == "__main__":
    main()
