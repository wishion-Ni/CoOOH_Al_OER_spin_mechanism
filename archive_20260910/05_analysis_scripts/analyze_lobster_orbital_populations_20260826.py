from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parent
INPUT = ROOT / "lobster_grosspop_oh_o_20260826"
OUTPUT_TSV = ROOT / "lobster_orbital_population_oh_to_o_20260826.tsv"
OUTPUT_PNG = ROOT / "lobster_orbital_population_oh_to_o_20260826.png"


@dataclass(frozen=True)
class Case:
    key: str
    material: str
    state: str
    active_co: int
    active_o: int


CASES = (
    Case("undoped_OH", "Undoped", "OH", 21, 348),
    Case("undoped_O", "Undoped", "O", 21, 347),
    Case("Al16_OH", "Al16", "OH", 16, 348),
    Case("Al16_O", "Al16", "O", 16, 347),
)

D_ORDER = ("3d_xy", "3d_yz", "3d_z^2", "3d_xz", "3d_x^2-y^2")
P_ORDER = ("2p_y", "2p_z", "2p_x")
DISPLAY = {
    "3d_xy": "dxy",
    "3d_yz": "dyz",
    "3d_z^2": "dz2",
    "3d_xz": "dxz",
    "3d_x^2-y^2": "dx2-y2",
    "2p_y": "py",
    "2p_z": "pz",
    "2p_x": "px",
}


def parse_atom(path: Path, atom_index: int):
    lines = path.read_text(encoding="ascii").splitlines()
    start = None
    first_fields = None
    for index, line in enumerate(lines):
        fields = line.split()
        if len(fields) >= 7 and fields[0].isdigit() and int(fields[0]) == atom_index:
            start = index
            first_fields = fields
            break
    if start is None or first_fields is None:
        raise ValueError(f"atom {atom_index} not found in {path}")

    result = {
        first_fields[2]: tuple(float(value) for value in first_fields[3:7]),
    }
    for line in lines[start + 1:]:
        fields = line.split()
        if not fields:
            continue
        if fields[0] == "total":
            result["total"] = tuple(float(value) for value in fields[1:5])
            break
        if len(fields) >= 5:
            result[fields[0]] = tuple(float(value) for value in fields[1:5])
    if "total" not in result:
        raise ValueError(f"atom block {atom_index} incomplete in {path}")
    return result


def main():
    loaded = {}
    for case in CASES:
        path = INPUT / f"{case.key}_GROSSPOP.lobster"
        loaded[case.key] = {
            "Co": parse_atom(path, case.active_co),
            "Oads": parse_atom(path, case.active_o),
        }

    rows = []
    for material, oh_key, o_key in (
        ("Undoped", "undoped_OH", "undoped_O"),
        ("Al16", "Al16_OH", "Al16_O"),
    ):
        for atom_kind, orbitals in (("Co", D_ORDER), ("Oads", P_ORDER)):
            for orbital in orbitals:
                for population, offset in (("Mulliken", 0), ("Loewdin", 2)):
                    for spin, spin_offset in (("up", 0), ("down", 1)):
                        column = offset + spin_offset
                        oh_value = loaded[oh_key][atom_kind][orbital][column]
                        o_value = loaded[o_key][atom_kind][orbital][column]
                        rows.append(
                            (material, atom_kind, orbital, population, spin, oh_value, o_value, o_value - oh_value)
                        )

    with OUTPUT_TSV.open("w", encoding="ascii", newline="\n") as handle:
        handle.write("material\tatom\torbital\tpopulation\tspin\tOH_e\tO_e\tdelta_e\n")
        for row in rows:
            handle.write("\t".join(row[:5]) + "\t" + "\t".join(f"{value:.4f}" for value in row[5:]) + "\n")

    fig, axes = plt.subplots(2, 2, figsize=(10.0, 6.8), dpi=180, constrained_layout=True)
    colors = {"up": "#B8322A", "down": "#2878A6"}
    panels = (
        ("Undoped", "Co", D_ORDER, "(a) Undoped: active Co 3d"),
        ("Al16", "Co", D_ORDER, "(b) Al16: active Co 3d"),
        ("Undoped", "Oads", P_ORDER, r"(c) Undoped: O$_{ads}$ 2p"),
        ("Al16", "Oads", P_ORDER, r"(d) Al16: O$_{ads}$ 2p"),
    )
    width = 0.36
    for ax, (material, atom_kind, orbitals, title) in zip(axes.ravel(), panels):
        x = np.arange(len(orbitals))
        for offset, spin in ((-width / 2, "up"), (width / 2, "down")):
            values = [
                next(
                    row[7] for row in rows
                    if row[0] == material and row[1] == atom_kind and row[2] == orbital
                    and row[3] == "Loewdin" and row[4] == spin
                )
                for orbital in orbitals
            ]
            ax.bar(x + offset, values, width=width, color=colors[spin], label=f"spin-{spin}")
        ax.axhline(0, color="#222222", lw=0.8)
        ax.set_xticks(x, [DISPLAY[orbital] for orbital in orbitals])
        ax.set_ylabel(r"$\Delta$ Löwdin orbital population (e)")
        ax.set_title(title, loc="left", fontsize=10)
        ax.spines[["top", "right"]].set_visible(False)
        ax.tick_params(axis="x", labelrotation=18)
    axes[0, 0].legend(frameon=False, ncol=2, fontsize=8)
    fig.suptitle(r"LOBSTER orbital populations: $*O-*OH$", fontsize=11.5)
    fig.savefig(OUTPUT_PNG, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(OUTPUT_TSV)
    print(OUTPUT_PNG)

    for material in ("Undoped", "Al16"):
        for atom_kind in ("Co", "Oads"):
            up = sum(row[7] for row in rows if row[0] == material and row[1] == atom_kind
                     and row[3] == "Loewdin" and row[4] == "up")
            down = sum(row[7] for row in rows if row[0] == material and row[1] == atom_kind
                       and row[3] == "Loewdin" and row[4] == "down")
            print(material, atom_kind, f"orbital_sum_delta_charge={up + down:+.4f}",
                  f"orbital_sum_delta_m={up - down:+.4f}")


if __name__ == "__main__":
    main()
