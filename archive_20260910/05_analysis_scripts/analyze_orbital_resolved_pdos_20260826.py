from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parent
INPUT = ROOT / "pdos_oh_o_inputs_20260824"
OUTPUT_TSV = ROOT / "orbital_resolved_pdos_oh_to_o_20260826.tsv"
OUTPUT_PNG = ROOT / "orbital_resolved_pdos_oh_to_o_20260826.png"


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

D_ORBITALS = {
    "dxy": (8, 9),
    "dyz": (10, 11),
    "dz2": (12, 13),
    "dxz": (14, 15),
    "dx2-y2": (16, 17),
}
P_ORBITALS = {
    "py": (2, 3),
    "pz": (4, 5),
    "px": (6, 7),
}


def read_doscar(path: Path):
    with path.open("r", encoding="ascii") as handle:
        natoms = int(handle.readline().split()[0])
        for _ in range(4):
            handle.readline()
        header = handle.readline().split()
        nedos = int(header[2])
        efermi = float(header[3])
        for _ in range(nedos):
            handle.readline()
        projected = np.empty((natoms, nedos, 18), dtype=float)
        energy = None
        for atom in range(natoms):
            handle.readline()
            block = np.array([[float(value) for value in handle.readline().split()] for _ in range(nedos)])
            if block.shape[1] != 19:
                raise ValueError(f"Expected spin LORBIT=11 DOS in {path}, got {block.shape}")
            if energy is None:
                energy = block[:, 0] - efermi
            projected[atom] = block[:, 1:]
    return energy, projected


def integrate(energy, dos, lower=-8.0, upper=0.0):
    mask = (energy >= lower) & (energy <= upper)
    weight = np.trapezoid(dos[mask], energy[mask])
    center = np.trapezoid(energy[mask] * dos[mask], energy[mask]) / weight
    return float(weight), float(center)


def load_case(case: Case):
    energy, projected = read_doscar(INPUT / case.key / "DOSCAR")
    result = {}
    for atom_kind, atom_index, orbitals in (
        ("Co", case.active_co, D_ORBITALS),
        ("Oads", case.active_o, P_ORBITALS),
    ):
        atom = projected[atom_index - 1]
        for orbital, columns in orbitals.items():
            for spin, column in zip(("up", "down"), columns):
                weight, center = integrate(energy, atom[:, column])
                result[(atom_kind, orbital, spin)] = (weight, center)
    return result


def main():
    loaded = {case.key: load_case(case) for case in CASES}
    rows = []
    for material, oh_key, o_key in (
        ("Undoped", "undoped_OH", "undoped_O"),
        ("Al16", "Al16_OH", "Al16_O"),
    ):
        for key in loaded[oh_key]:
            atom_kind, orbital, spin = key
            oh_weight, oh_center = loaded[oh_key][key]
            o_weight, o_center = loaded[o_key][key]
            rows.append(
                (material, atom_kind, orbital, spin, oh_weight, o_weight, o_weight - oh_weight,
                 oh_center, o_center, o_center - oh_center)
            )

    with OUTPUT_TSV.open("w", encoding="ascii", newline="\n") as handle:
        handle.write(
            "material\tatom\torbital\tspin\tOH_occupied_weight\tO_occupied_weight\t"
            "delta_occupied_weight\tOH_center_eV\tO_center_eV\tdelta_center_eV\n"
        )
        for row in rows:
            handle.write("\t".join(row[:4]) + "\t" + "\t".join(f"{value:.8f}" for value in row[4:]) + "\n")

    fig, axes = plt.subplots(2, 2, figsize=(10.0, 6.7), dpi=180, constrained_layout=True)
    colors = {"up": "#B8322A", "down": "#2878A6"}
    panels = (
        ("Undoped", "Co", list(D_ORBITALS), "(a) Undoped: active Co 3d"),
        ("Al16", "Co", list(D_ORBITALS), "(b) Al16: active Co 3d"),
        ("Undoped", "Oads", list(P_ORBITALS), r"(c) Undoped: O$_{ads}$ 2p"),
        ("Al16", "Oads", list(P_ORBITALS), r"(d) Al16: O$_{ads}$ 2p"),
    )
    width = 0.36
    for ax, (material, atom_kind, orbitals, title) in zip(axes.ravel(), panels):
        x = np.arange(len(orbitals))
        for offset, spin in ((-width / 2, "up"), (width / 2, "down")):
            values = [
                next(row[6] for row in rows if row[0] == material and row[1] == atom_kind
                     and row[2] == orbital and row[3] == spin)
                for orbital in orbitals
            ]
            ax.bar(x + offset, values, width=width, color=colors[spin], label=f"spin-{spin}")
        ax.axhline(0, color="#222222", lw=0.8)
        ax.set_xticks(x, orbitals)
        ax.set_ylabel(r"$\Delta$ occupied PDOS weight")
        ax.set_title(title, loc="left", fontsize=10)
        ax.spines[["top", "right"]].set_visible(False)
        ax.tick_params(axis="x", labelrotation=18)
    axes[0, 0].legend(frameon=False, ncol=2, fontsize=8)
    fig.suptitle(r"Orbital-resolved occupied-state response: $*O-*OH$ ($-8$ to $0$ eV)", fontsize=11.5)
    fig.savefig(OUTPUT_PNG, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(OUTPUT_TSV)
    print(OUTPUT_PNG)
    for row in rows:
        if row[0] == "Al16":
            print(row[0], row[1], row[2], row[3], f"delta_weight={row[6]:+.6f}",
                  f"delta_center={row[9]:+.6f} eV")


if __name__ == "__main__":
    main()
