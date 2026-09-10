from __future__ import annotations

import importlib.util
import argparse
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

CASES = {
    "al16": {
        "input": (
            "sfs/CoOH/cp2k/Al16/oer/spin_config_scan_site03_5OH_current_20260714/"
            "cdft_charge_spin_20260812/al16_valid_co48_OH/baseline.inp"
        ),
        "active_co": 48,
        "active_h": 221,
        "active_o": 222,
    },
    "undoped": {
        "input": (
            "sfs/CoOH/cp2k/thermo_vib_5OH_U100_current_20260704/"
            "cdft_charge_spin_undoped_20260816/undoped_valid_co32_OH/baseline.inp"
        ),
        "active_co": 32,
        "active_h": 211,
        "active_o": 212,
    },
}


def pbc_delta(a: float, b: float, length: float) -> float:
    delta = a - b
    return delta - round(delta / length) * length


def distance(a: tuple[float, float, float], b: tuple[float, float, float], cell):
    return math.sqrt(sum(pbc_delta(x, y, length) ** 2 for x, y, length in zip(a, b, cell)))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", choices=CASES, default="al16")
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
        with sftp.open(posixpath.join(ssh_ncw.REMOTE_ROOT, cfg["input"]), "r") as handle:
            text = handle.read().decode(errors="replace")
    finally:
        client.close()

    lengths = []
    for axis in "ABC":
        match = re.search(rf"(?m)^\s*{axis}\s+([-+0-9.Ee]+)\s+([-+0-9.Ee]+)\s+([-+0-9.Ee]+)", text)
        assert match
        vector = tuple(float(match.group(i)) for i in range(1, 4))
        lengths.append(math.sqrt(sum(value * value for value in vector)))
    cell = tuple(lengths)

    block = re.search(r"(?ms)^\s*&COORD\s*$\n(.*?)^\s*&END COORD\s*$", text)
    assert block
    atoms = []
    for line in block.group(1).splitlines():
        fields = line.split()
        if len(fields) >= 4 and fields[0] in {"Co", "Al", "O", "H"}:
            atoms.append((fields[0], tuple(float(value) for value in fields[1:4])))

    active_co = cfg["active_co"]
    active_h = cfg["active_h"]
    active_o = cfg["active_o"]
    co_xyz = atoms[active_co - 1][1]
    h_xyz = atoms[active_h - 1][1]
    o_xyz = atoms[active_o - 1][1]
    print(f"cell={cell}; atoms={len(atoms)}")
    print(f"active Co{active_co}-O{active_o}={distance(co_xyz, o_xyz, cell):.6f}")
    print(f"active O{active_o}-H{active_h}={distance(o_xyz, h_xyz, cell):.6f}")

    al_indices = [i for i, atom in enumerate(atoms, start=1) if atom[0] == "Al"]
    metal_indices = [
        i for i, atom in enumerate(atoms, start=1) if atom[0] in {"Co", "Al"}
    ]
    print("nearest Al to active Co/O:")
    if al_indices:
        for index in sorted(al_indices, key=lambda i: distance(atoms[i - 1][1], co_xyz, cell)):
            xyz = atoms[index - 1][1]
            print(
                f"Al{index}: Co-Al={distance(co_xyz, xyz, cell):.6f}; "
                f"Oact-Al={distance(o_xyz, xyz, cell):.6f}"
            )
    else:
        print("none")

    oxygen_indices = [i for i, atom in enumerate(atoms, start=1) if atom[0] == "O"]
    hydrogen_indices = [i for i, atom in enumerate(atoms, start=1) if atom[0] == "H"]
    oh_pairs = []
    for oi in oxygen_indices:
        nearest_h = min(
            hydrogen_indices,
            key=lambda hi: distance(atoms[oi - 1][1], atoms[hi - 1][1], cell),
        )
        oh = distance(atoms[oi - 1][1], atoms[nearest_h - 1][1], cell)
        if oh < 1.25:
            oh_pairs.append((oi, nearest_h, oh))

    print("OH groups nearest active O and nearest Al:")
    ranked = []
    for oi, hi, oh in oh_pairs:
        if oi == active_o:
            continue
        ocoord = atoms[oi - 1][1]
        hcoord = atoms[hi - 1][1]
        if al_indices:
            nearest_al = min(al_indices, key=lambda ai: distance(atoms[ai - 1][1], ocoord, cell))
            al_o = distance(atoms[nearest_al - 1][1], ocoord, cell)
        else:
            nearest_al = 0
            al_o = float("nan")
        nearest_metal = min(
            metal_indices, key=lambda mi: distance(atoms[mi - 1][1], ocoord, cell)
        )
        metal_o = distance(atoms[nearest_metal - 1][1], ocoord, cell)
        metal_symbol = atoms[nearest_metal - 1][0]
        oact_o = distance(o_xyz, ocoord, cell)
        hact_o = distance(h_xyz, ocoord, cell)
        ranked.append(
            (
                oact_o,
                oi,
                hi,
                oh,
                nearest_al,
                al_o,
                hact_o,
                metal_symbol,
                nearest_metal,
                metal_o,
            )
        )
    for values in sorted(ranked)[:12]:
        (
            oact_o,
            oi,
            hi,
            oh,
            nearest_al,
            al_o,
            hact_o,
            metal_symbol,
            nearest_metal,
            metal_o,
        ) = values
        print(
            f"O{oi}-H{hi}: OH={oh:.6f}; nearest Al{nearest_al}-O={al_o:.6f}; "
            f"nearest {metal_symbol}{nearest_metal}-O={metal_o:.6f}; "
            f"Oact-O={oact_o:.6f}; Hact-O={hact_o:.6f}"
        )


if __name__ == "__main__":
    main()
