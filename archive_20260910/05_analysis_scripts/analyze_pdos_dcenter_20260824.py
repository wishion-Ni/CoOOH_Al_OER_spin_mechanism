from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parent
INPUT = ROOT / "pdos_oh_o_inputs_20260824"


@dataclass(frozen=True)
class Case:
    key: str
    material: str
    state: str
    active_co: int
    active_o: int


CASES = (
    Case("undoped_OH", "Undoped CoOOH", "OH", 21, 348),
    Case("undoped_O", "Undoped CoOOH", "O", 21, 347),
    Case("Al16_OH", "Al-doped CoOOH", "OH", 16, 348),
    Case("Al16_O", "Al-doped CoOOH", "O", 16, 347),
)


def read_poscar_species(path: Path) -> tuple[list[str], list[int]]:
    lines = path.read_text(encoding="ascii").splitlines()
    species = lines[5].split()
    counts = [int(value) for value in lines[6].split()]
    if len(species) != len(counts):
        raise ValueError(f"Species/count mismatch in {path}")
    return species, counts


def species_indices(species: list[str], counts: list[int]) -> dict[str, list[int]]:
    result: dict[str, list[int]] = {}
    start = 1
    for symbol, count in zip(species, counts):
        result[symbol] = list(range(start, start + count))
        start += count
    return result


def read_doscar(path: Path) -> tuple[float, np.ndarray, np.ndarray]:
    with path.open("r", encoding="ascii") as handle:
        natoms = int(handle.readline().split()[0])
        for _ in range(4):
            handle.readline()
        header = handle.readline().split()
        nedos = int(header[2])
        efermi = float(header[3])
        for _ in range(nedos):
            handle.readline()
        energy = None
        projected = np.empty((natoms, nedos, 18), dtype=float)
        for atom in range(natoms):
            atom_header = handle.readline()
            if not atom_header:
                raise ValueError(f"Missing atom block {atom + 1} in {path}")
            block = np.array(
                [[float(value) for value in handle.readline().split()] for _ in range(nedos)]
            )
            if block.shape[1] != 19:
                raise ValueError(f"Expected 19-column spin LORBIT=11 DOS, got {block.shape}")
            if energy is None:
                energy = block[:, 0] - efermi
            projected[atom] = block[:, 1:]
    assert energy is not None
    return efermi, energy, projected


def orbital_sum(pdos: np.ndarray, atom_indices: list[int], orbital: str) -> tuple[np.ndarray, np.ndarray]:
    rows = pdos[np.array(atom_indices) - 1]
    if orbital == "p":
        up_columns = (2, 4, 6)
        down_columns = (3, 5, 7)
    elif orbital == "d":
        up_columns = (8, 10, 12, 14, 16)
        down_columns = (9, 11, 13, 15, 17)
    else:
        raise ValueError(orbital)
    up = rows[:, :, up_columns].sum(axis=(0, 2))
    down = rows[:, :, down_columns].sum(axis=(0, 2))
    return up, down


def smooth(y: np.ndarray, sigma_points: float = 1.1) -> np.ndarray:
    radius = max(2, int(4 * sigma_points))
    x = np.arange(-radius, radius + 1)
    kernel = np.exp(-0.5 * (x / sigma_points) ** 2)
    kernel /= kernel.sum()
    return np.convolve(y, kernel, mode="same")


def centroid(energy: np.ndarray, dos: np.ndarray, lower: float, upper: float) -> tuple[float, float]:
    mask = (energy >= lower) & (energy <= upper)
    weight = np.trapezoid(dos[mask], energy[mask])
    if weight <= 1e-12:
        raise ValueError("Zero d-DOS weight")
    center = np.trapezoid(energy[mask] * dos[mask], energy[mask]) / weight
    return float(center), float(weight)


def load_cases() -> dict[str, dict[str, object]]:
    result: dict[str, dict[str, object]] = {}
    for case in CASES:
        case_dir = INPUT / case.key
        species, counts = read_poscar_species(case_dir / "POSCAR")
        indices = species_indices(species, counts)
        efermi, energy, pdos = read_doscar(case_dir / "DOSCAR")
        co_up, co_down = orbital_sum(pdos, indices["Co"], "d")
        o_up, o_down = orbital_sum(pdos, indices["O"], "p")
        act_co_up, act_co_down = orbital_sum(pdos, [case.active_co], "d")
        act_o_up, act_o_down = orbital_sum(pdos, [case.active_o], "p")
        result[case.key] = {
            "case": case,
            "efermi": efermi,
            "energy": energy,
            "co_global": (co_up / len(indices["Co"]), co_down / len(indices["Co"])),
            "o_global": (o_up / len(indices["O"]), o_down / len(indices["O"])),
            "co_active": (act_co_up, act_co_down),
            "o_active": (act_o_up, act_o_down),
        }
    return result


def style_axis(ax: plt.Axes, ylabel: str) -> None:
    ax.axhline(0, color="#333333", lw=0.7)
    ax.axvline(0, color="#333333", lw=0.8, ls=":")
    ax.set_xlim(-8, 4)
    ax.set_ylabel(ylabel)
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(direction="out", width=0.8, length=3)


def plot_pdos(data: dict[str, dict[str, object]]) -> Path:
    plt.rcParams.update({"font.size": 9, "axes.linewidth": 0.8, "figure.dpi": 180})
    fig, axes = plt.subplots(2, 2, figsize=(8.1, 6.1), sharex=True, constrained_layout=True)
    rows = (("undoped_OH", "Undoped CoOOH"), ("Al16_OH", "Al-doped CoOOH"))
    colors = {"Co": "#1768AC", "O": "#C63C32"}
    for row, (key, title) in enumerate(rows):
        item = data[key]
        energy = item["energy"]
        ax = axes[row, 0]
        for label, field in (("Co 3d", "co_global"), ("O 2p", "o_global")):
            up, down = item[field]
            color = colors[label.split()[0]]
            ax.plot(energy, smooth(up), color=color, lw=1.25, label=label)
            ax.plot(energy, -smooth(down), color=color, lw=1.0)
        style_axis(ax, "PDOS / atom (states eV$^{-1}$)")
        ax.set_title(f"{title}: framework-averaged", loc="left", fontsize=10)
        if row == 0:
            ax.legend(frameon=False, ncol=2, loc="upper left")

        ax = axes[row, 1]
        for label, field in (("Active Co 3d", "co_active"), ("O$_{ads}$ 2p", "o_active")):
            up, down = item[field]
            color = colors["Co" if label.startswith("Active") else "O"]
            ax.plot(energy, smooth(up), color=color, lw=1.25, label=label)
            ax.plot(energy, -smooth(down), color=color, lw=1.0)
        style_axis(ax, "Local PDOS (states eV$^{-1}$)")
        ax.set_title(f"{title}: active *OH site", loc="left", fontsize=10)
        if row == 0:
            ax.legend(frameon=False, ncol=2, loc="upper left")

    axes[1, 0].set_xlabel("Energy relative to $E_F$ (eV)")
    axes[1, 1].set_xlabel("Energy relative to $E_F$ (eV)")
    fig.text(0.995, 0.5, "spin-up: positive; spin-down: negative", rotation=90,
             va="center", ha="right", fontsize=8, color="#444444")
    output = ROOT / "pdos_cooh_undoped_al16_preliminary_20260824.png"
    fig.savefig(output, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return output


def analyze_centers(data: dict[str, dict[str, object]]) -> tuple[Path, Path, Path]:
    rows = []
    for case in CASES:
        item = data[case.key]
        energy = item["energy"]
        up, down = item["co_active"]
        total = up + down
        for label, lower, upper in (("occupied", -8.0, 0.0), ("extended", -8.0, 4.0)):
            center, weight = centroid(energy, total, lower, upper)
            up_center, up_weight = centroid(energy, up, lower, upper)
            down_center, down_weight = centroid(energy, down, lower, upper)
            rows.append((case.material, case.state, case.active_co, label, lower, upper,
                         center, weight, up_center, up_weight, down_center, down_weight))
    tsv = ROOT / "d_band_center_oh_o_20260824.tsv"
    with tsv.open("w", encoding="ascii", newline="\n") as handle:
        handle.write("material\tstate\tactive_co_index\twindow\tEmin_eV\tEmax_eV\t"
                     "d_center_eV\td_weight\td_center_up_eV\td_weight_up\t"
                     "d_center_down_eV\td_weight_down\n")
        for row in rows:
            handle.write("\t".join(str(value) if isinstance(value, (str, int)) else f"{value:.8f}"
                                   for value in row) + "\n")

    framework_tsv = ROOT / "d_band_center_framework_oh_o_20260824.tsv"
    with framework_tsv.open("w", encoding="ascii", newline="\n") as handle:
        handle.write("material\tstate\twindow\tEmin_eV\tEmax_eV\t"
                     "framework_d_center_eV\tframework_d_weight_per_Co\n")
        for case in CASES:
            item = data[case.key]
            energy = item["energy"]
            up, down = item["co_global"]
            for label, lower, upper in (("occupied", -8.0, 0.0), ("extended", -8.0, 4.0)):
                center, weight = centroid(energy, up + down, lower, upper)
                handle.write(f"{case.material}\t{case.state}\t{label}\t{lower:.8f}\t"
                             f"{upper:.8f}\t{center:.8f}\t{weight:.8f}\n")

    occupied = [row for row in rows if row[3] == "occupied"]
    extended = [row for row in rows if row[3] == "extended"]
    x = np.array([0, 1])
    width = 0.34
    colors = {"Undoped CoOOH": "#555555", "Al-doped CoOOH": "#D04A35"}
    fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.65))
    for ax, subset, title in zip(
        axes,
        (occupied, extended),
        ("Occupied Co-3d center: -8 to 0 eV", "Extended Co-3d center: -8 to +4 eV"),
    ):
        for offset, material in zip((-width / 2, width / 2), colors):
            values = [next(row[6] for row in subset if row[0] == material and row[1] == state)
                      for state in ("OH", "O")]
            ax.bar(x + offset, values, width=width, color=colors[material], label=material)
            for xpos, value in zip(x + offset, values):
                ax.text(xpos, value + 0.06, f"{value:.2f}", ha="center", va="bottom", fontsize=8)
        ax.set_xticks(x, ("*OH", "*O"))
        ax.set_ylabel(r"$\epsilon_d-E_F$ (eV)")
        ax.set_title(title, loc="left", fontsize=9.5)
        ax.spines[["top", "right"]].set_visible(False)
        ax.axhline(0, color="#333333", lw=0.7)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, frameon=False, fontsize=8, ncol=2,
               loc="upper center", bbox_to_anchor=(0.5, 0.985))
    fig.subplots_adjust(left=0.10, right=0.98, bottom=0.15, top=0.78, wspace=0.28)
    output = ROOT / "d_band_center_oh_o_preliminary_20260824.png"
    fig.savefig(output, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return output, tsv, framework_tsv


def main() -> None:
    data = load_cases()
    pdos_png = plot_pdos(data)
    center_png, center_tsv, framework_tsv = analyze_centers(data)
    print(pdos_png)
    print(center_png)
    print(center_tsv)
    print(framework_tsv)


if __name__ == "__main__":
    main()
