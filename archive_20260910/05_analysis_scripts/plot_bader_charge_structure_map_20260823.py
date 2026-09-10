from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import Normalize, TwoSlopeNorm
from matplotlib.lines import Line2D


BASE = Path(__file__).resolve().parent / "bader_structure_inputs_20260823"
OUT = Path(__file__).resolve().parent / "bader_charge_structure_map_20260823.png"

VALENCE = {"Co": 9.0, "Al": 3.0, "H": 1.0, "O": 6.0}
ATOM_SIZE = {"Co": 270, "Al": 270, "O": 150, "H": 65}
EDGE_COLOR = {"Co": "#20242a", "Al": "#f0b44d", "O": "#20242a", "H": "#707780"}


@dataclass
class Case:
    name: str
    species: list[str]
    lattice: np.ndarray
    frac: np.ndarray
    xyz: np.ndarray
    electrons: np.ndarray
    charge: np.ndarray
    active_co: int
    adjacent_metal: int
    ads_o: int


def parse_case(name: str, active_co: int, adjacent_metal: int, ads_o: int) -> Case:
    folder = BASE / name
    lines = (folder / "POSCAR").read_text().splitlines()
    scale = float(lines[1].split()[0])
    lattice = np.array([[float(x) for x in lines[i].split()] for i in range(2, 5)]) * scale
    elements = lines[5].split()
    counts = [int(x) for x in lines[6].split()]
    species = [element for element, count in zip(elements, counts) for _ in range(count)]
    cursor = 7
    if lines[cursor].strip().lower().startswith("s"):
        cursor += 1
    direct = lines[cursor].strip().lower().startswith("d")
    cursor += 1
    coords = np.array([[float(x) for x in lines[cursor + i].split()[:3]] for i in range(sum(counts))])
    if direct:
        frac = coords
        xyz = frac @ lattice
    else:
        xyz = coords * scale
        frac = xyz @ np.linalg.inv(lattice)

    rows = []
    for line in (folder / "ACF.dat").read_text().splitlines():
        fields = line.split()
        if len(fields) >= 7 and fields[0].isdigit():
            rows.append([float(value) for value in fields[1:7]])
    electrons = np.array(rows)[:, 3]
    if len(electrons) != len(species):
        raise ValueError(f"{name}: POSCAR has {len(species)} atoms but ACF has {len(electrons)}")
    charge = np.array([VALENCE[element] for element in species]) - electrons
    return Case(name, species, lattice, frac, xyz, electrons, charge, active_co - 1, adjacent_metal - 1, ads_o - 1)


CASES = {
    "undoped_OH": parse_case("undoped_OH", 21, 23, 348),
    "undoped_O": parse_case("undoped_O", 21, 23, 347),
    "Al16_OH": parse_case("Al16_OH", 16, 51, 348),
    "Al16_O": parse_case("Al16_O", 16, 51, 347),
}


def unwrap(case: Case, center: int) -> np.ndarray:
    delta = case.frac - case.frac[center]
    delta -= np.round(delta)
    return delta @ case.lattice


def projection_basis(case: Case) -> tuple[np.ndarray, np.ndarray]:
    unwrapped = unwrap(case, case.active_co)
    metal_vector = unwrapped[case.adjacent_metal].copy()
    metal_vector[2] = 0.0
    u = metal_vector / np.linalg.norm(metal_vector)
    v = np.array([-u[1], u[0], 0.0])
    return u, v


def project(rel_xyz: np.ndarray, u: np.ndarray, v: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    depth = rel_xyz @ v
    x = rel_xyz @ u + 0.30 * depth
    y = rel_xyz[:, 2] + 0.12 * depth
    return x, y, depth


def local_indices(case: Case, radius: float = 5.2) -> np.ndarray:
    rel = unwrap(case, case.active_co)
    distance = np.linalg.norm(rel, axis=1)
    z = rel[:, 2]
    return np.where((distance <= radius) & (z >= -4.6))[0]


def bond_cutoff(a: str, b: str) -> float | None:
    pair = frozenset((a, b))
    if pair == frozenset(("H", "O")):
        return 1.22
    if pair in (frozenset(("Co", "O")), frozenset(("Al", "O"))):
        return 2.38
    return None


def draw_bonds(ax, case: Case, indices: np.ndarray, x: np.ndarray, y: np.ndarray, rel: np.ndarray) -> None:
    for ii, atom_i in enumerate(indices):
        for jj in range(ii + 1, len(indices)):
            atom_j = indices[jj]
            cutoff = bond_cutoff(case.species[atom_i], case.species[atom_j])
            if cutoff is None:
                continue
            if np.linalg.norm(rel[atom_i] - rel[atom_j]) <= cutoff:
                ax.plot(
                    [x[atom_i], x[atom_j]],
                    [y[atom_i], y[atom_j]],
                    color="#a7adb5",
                    linewidth=1.25,
                    zorder=1,
                )


def match_electron_change(oh: Case, o: Case) -> np.ndarray:
    delta = np.full(len(oh.species), np.nan)
    available: dict[str, set[int]] = {}
    for element in set(o.species):
        available[element] = {i for i, value in enumerate(o.species) if value == element}

    # Greedy nearest matching is exact here because fixed substrate coordinates are unchanged.
    candidates = []
    for i, element in enumerate(oh.species):
        for j in available.get(element, set()):
            df = o.frac[j] - oh.frac[i]
            df -= np.round(df)
            distance = np.linalg.norm(df @ oh.lattice)
            candidates.append((distance, i, j, element))
    candidates.sort()
    used_oh: set[int] = set()
    used_o: set[int] = set()
    for distance, i, j, _ in candidates:
        if i in used_oh or j in used_o:
            continue
        if distance > 0.65:
            continue
        used_oh.add(i)
        used_o.add(j)
        delta[i] = o.electrons[j] - oh.electrons[i]
    return delta


def label_key_atoms(ax, case: Case, x: np.ndarray, y: np.ndarray, values: np.ndarray, delta: bool) -> None:
    keys = [
        (case.active_co, r"Co$_{act}$", (-30, 16)),
        (case.ads_o, r"O$_{ads}$", (-42, 18)),
        (
            case.adjacent_metal,
            (r"Al$_{adj}$" if case.species[case.adjacent_metal] == "Al" else r"Co$_{adj}$"),
            (15, -22),
        ),
    ]
    for atom, label, offset in keys:
        value = values[atom]
        if np.isnan(value):
            continue
        symbol = r"$\Delta N$" if delta else r"$q$"
        ax.annotate(
            f"{label}\n{symbol}={value:+.3f}",
            (x[atom], y[atom]),
            xytext=offset,
            textcoords="offset points",
            fontsize=8.4,
            linespacing=1.05,
            arrowprops=dict(arrowstyle="-", color="#555b63", lw=0.8),
            bbox=dict(boxstyle="round,pad=0.18", fc="white", ec="#c8ccd1", alpha=0.93),
            zorder=10,
        )


def draw_panel(ax, case: Case, values: np.ndarray, norm, cmap, title: str, delta: bool = False) -> None:
    rel = unwrap(case, case.active_co)
    u, v = projection_basis(case)
    x, y, depth = project(rel, u, v)
    indices = local_indices(case)
    draw_bonds(ax, case, indices, x, y, rel)

    order = indices[np.argsort(depth[indices])]
    for atom in order:
        value = values[atom]
        if np.isnan(value):
            face = "#dddddd"
        else:
            face = cmap(norm(value))
        size = ATOM_SIZE[case.species[atom]]
        if atom in (case.active_co, case.adjacent_metal, case.ads_o):
            size *= 1.42
        ax.scatter(
            x[atom],
            y[atom],
            s=size,
            c=[face],
            edgecolors=EDGE_COLOR[case.species[atom]],
            linewidths=1.15,
            zorder=3 + depth[atom] / 20,
        )

    label_key_atoms(ax, case, x, y, values, delta)
    shown_x = x[indices]
    shown_y = y[indices]
    ax.set_xlim(shown_x.min() - 0.8, shown_x.max() + 0.9)
    ax.set_ylim(shown_y.min() - 0.8, shown_y.max() + 0.9)
    ax.set_aspect("equal")
    ax.set_title(title, fontsize=12.5, pad=8)
    ax.set_xlabel("local surface direction (A)", fontsize=9)
    ax.set_ylabel("height (A)", fontsize=9)
    ax.tick_params(labelsize=8, length=3)
    ax.grid(color="#e4e7ea", linewidth=0.6, alpha=0.65)
    ax.set_axisbelow(True)


def main() -> None:
    undoped_delta = match_electron_change(CASES["undoped_OH"], CASES["undoped_O"])
    al16_delta = match_electron_change(CASES["Al16_OH"], CASES["Al16_O"])
    charge_norm = Normalize(vmin=-1.15, vmax=2.15)
    delta_norm = TwoSlopeNorm(vmin=-0.30, vcenter=0.0, vmax=0.30)
    charge_cmap = plt.get_cmap("RdBu_r")
    delta_cmap = plt.get_cmap("RdBu")

    fig, axes = plt.subplots(3, 2, figsize=(14.2, 15.2), constrained_layout=False)
    fig.suptitle("Local Bader charge map at the active site: *OH to *O", fontsize=20, y=0.985)

    draw_panel(
        axes[0, 0], CASES["undoped_OH"], CASES["undoped_OH"].charge,
        charge_norm, charge_cmap, "Undoped  |  *OH", False,
    )
    draw_panel(
        axes[0, 1], CASES["Al16_OH"], CASES["Al16_OH"].charge,
        charge_norm, charge_cmap, "Al16  |  *OH", False,
    )
    draw_panel(
        axes[1, 0], CASES["undoped_O"], CASES["undoped_O"].charge,
        charge_norm, charge_cmap, "Undoped  |  *O", False,
    )
    draw_panel(
        axes[1, 1], CASES["Al16_O"], CASES["Al16_O"].charge,
        charge_norm, charge_cmap, "Al16  |  *O", False,
    )
    draw_panel(
        axes[2, 0], CASES["undoped_OH"], undoped_delta,
        delta_norm, delta_cmap, r"Undoped  |  electron transfer  $\Delta N=N_{*O}-N_{*OH}$", True,
    )
    draw_panel(
        axes[2, 1], CASES["Al16_OH"], al16_delta,
        delta_norm, delta_cmap, r"Al16  |  electron transfer  $\Delta N=N_{*O}-N_{*OH}$", True,
    )

    fig.subplots_adjust(left=0.07, right=0.91, bottom=0.075, top=0.945, hspace=0.34, wspace=0.25)
    charge_bar_ax = fig.add_axes([0.925, 0.405, 0.015, 0.52])
    charge_bar = fig.colorbar(plt.cm.ScalarMappable(norm=charge_norm, cmap=charge_cmap), cax=charge_bar_ax)
    charge_bar.set_label("Bader net charge q (|e|)\nred: electron deficient; blue: electron rich", fontsize=9)
    charge_bar.ax.tick_params(labelsize=8)
    delta_bar_ax = fig.add_axes([0.925, 0.095, 0.015, 0.22])
    delta_bar = fig.colorbar(plt.cm.ScalarMappable(norm=delta_norm, cmap=delta_cmap), cax=delta_bar_ax)
    delta_bar.set_label(r"electron change $\Delta N$ (e)" + "\nred: loss; blue: gain", fontsize=9)
    delta_bar.ax.tick_params(labelsize=8)

    legend = [
        Line2D([0], [0], marker="o", color="none", markerfacecolor="white", markeredgecolor=EDGE_COLOR[e],
               markeredgewidth=1.5, markersize=9 if e != "H" else 6, label=e)
        for e in ("Co", "Al", "O", "H")
    ]
    fig.legend(handles=legend, loc="lower center", ncol=4, frameon=False, bbox_to_anchor=(0.48, 0.018), fontsize=9)
    fig.text(
        0.48,
        0.048,
        "Fixed geometries. Colors are atom-integrated Bader charges, not a continuous charge-density isosurface. "
        "Only atoms within 5.2 A of the active Co are shown.",
        ha="center",
        fontsize=9.2,
        color="#4f5965",
    )
    fig.savefig(OUT, dpi=220, facecolor="white")
    print(OUT)


if __name__ == "__main__":
    main()
