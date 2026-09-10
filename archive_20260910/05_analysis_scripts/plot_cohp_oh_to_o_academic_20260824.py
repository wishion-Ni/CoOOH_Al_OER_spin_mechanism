from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import Patch


BASE = Path(__file__).resolve().parent / "cohp_oh_o_inputs_20260824"
OUT = Path(__file__).resolve().parent / "cohp_oh_to_o_academic_preliminary_20260824.png"
TSV = Path(__file__).resolve().parent / "cohp_oh_to_o_academic_summary_20260824.tsv"

COLORS = {"Undoped": "#555b63", "Al16": "#17866f"}
STATE_COLORS = {"*OH": "#3c78b4", "*O": "#d05b47"}
SPIN_COLORS = {"spin 1": "#d05b47", "spin 2": "#3c78b4"}
STATE_STYLE = {"*OH": (0, (5, 2.5)), "*O": "-"}


@dataclass
class CohpCase:
    material: str
    state: str
    energy: np.ndarray
    spin1: np.ndarray
    spin2: np.ndarray
    icohp_spin1: float
    icohp_spin2: float
    distance: float
    spilling1: float
    spilling2: float

    @property
    def total(self) -> np.ndarray:
        return self.spin1 + self.spin2

    @property
    def icohp_total(self) -> float:
        return self.icohp_spin1 + self.icohp_spin2


def parse_icohp(path: Path) -> tuple[float, float, float]:
    for line in path.read_text().splitlines():
        fields = line.split()
        if fields and fields[0] == "1":
            return float(fields[3]), float(fields[-2]), float(fields[-1])
    raise ValueError(f"Pair 1 not found in {path}")


def parse_spilling(path: Path) -> tuple[float, float]:
    values = []
    for line in path.read_text().splitlines():
        if "abs. charge spilling:" in line:
            values.append(float(line.split()[-1].rstrip("%")))
    if len(values) != 2:
        raise ValueError(f"Expected two spin spillings in {path}, got {values}")
    return values[0], values[1]


def parse_cohp(folder: Path, material: str, state: str) -> CohpCase:
    lines = (folder / "COHPCAR.lobster").read_text().splitlines()
    metadata = lines[1].split()
    ncurves = int(metadata[0])
    nspin = int(metadata[1])
    nedos = int(metadata[2])
    if ncurves != 6 or nspin != 2 or nedos != 401:
        raise ValueError(f"Unexpected COHPCAR dimensions in {folder}: {metadata[:3]}")
    data_start = 3 + (ncurves - 1)
    data = np.array([[float(value) for value in line.split()] for line in lines[data_start : data_start + nedos]])
    if data.shape != (nedos, 1 + 2 * ncurves * nspin):
        raise ValueError(f"Unexpected COHPCAR data shape in {folder}: {data.shape}")

    # Curve 0 is the average; curve 1 is the validated active Co-Oads pair.
    pair1_spin1 = data[:, 1 + 2]
    pair1_spin2 = data[:, 1 + 2 * ncurves + 2]
    distance, icohp1, icohp2 = parse_icohp(folder / "ICOHPLIST.lobster")
    spilling1, spilling2 = parse_spilling(folder / "lobsterout")
    return CohpCase(
        material,
        state,
        data[:, 0],
        pair1_spin1,
        pair1_spin2,
        icohp1,
        icohp2,
        distance,
        spilling1,
        spilling2,
    )


CASES = {
    ("Undoped", "*OH"): parse_cohp(BASE / "undoped_OH", "Undoped", "*OH"),
    ("Undoped", "*O"): parse_cohp(BASE / "undoped_O", "Undoped", "*O"),
    ("Al16", "*OH"): parse_cohp(BASE / "Al16_OH", "Al16", "*OH"),
    ("Al16", "*O"): parse_cohp(BASE / "Al16_O", "Al16", "*O"),
}


def plot_spectrum(ax, material: str, spin: int, panel: str) -> None:
    for state in ("*OH", "*O"):
        case = CASES[(material, state)]
        cohp = case.spin1 if spin == 1 else case.spin2
        ax.plot(
            -cohp,
            case.energy,
            color=STATE_COLORS[state],
            linestyle=STATE_STYLE[state],
            linewidth=2.45 if state == "*O" else 2.05,
            alpha=1.0,
        )
    ax.axvspan(-2.4, 0.0, color="#f3c7bf", alpha=0.16, zorder=0)
    ax.axvspan(0.0, 2.4, color="#bdd7ec", alpha=0.16, zorder=0)
    ax.axvline(0.0, color="#3f454d", linewidth=0.8)
    ax.axhline(0.0, color="#20252b", linestyle=(0, (3, 2)), linewidth=1.05)
    ax.set_xlim(-2.15, 2.15)
    ax.set_ylim(-8.0, 1.5)
    ax.set_xlabel(r"$-\mathrm{COHP}$")
    ax.set_ylabel(r"$E-E_\mathrm{F}$ (eV)")
    ax.set_title(f"({panel})  {material} | Spin {spin}", loc="left", fontsize=12.5, fontweight="bold")
    ax.grid(axis="y", color="#dfe3e6", linewidth=0.55, alpha=0.75)
    ax.text(1.95, -7.55, "bonding", color="#346b98", fontsize=8.7, ha="right")
    ax.text(-1.95, -7.55, "antibonding", color="#a64f40", fontsize=8.7, ha="left")
    ax.tick_params(direction="in", top=True, right=True)


def plot_delta_icohp(ax) -> None:
    materials = ["Undoped", "Al16"]
    delta1 = []
    delta2 = []
    totals = []
    for material in materials:
        oh = CASES[(material, "*OH")]
        o = CASES[(material, "*O")]
        d1 = o.icohp_spin1 - oh.icohp_spin1
        d2 = o.icohp_spin2 - oh.icohp_spin2
        delta1.append(d1)
        delta2.append(d2)
        totals.append(d1 + d2)

    x = np.arange(len(materials))
    ax.bar(x, delta1, width=0.56, color=SPIN_COLORS["spin 1"], edgecolor="#333940", linewidth=0.75)
    ax.bar(
        x,
        delta2,
        width=0.56,
        bottom=delta1,
        color=SPIN_COLORS["spin 2"],
        edgecolor="#333940",
        linewidth=0.75,
    )
    for xpos, total in zip(x, totals):
        ax.text(xpos, total - 0.06, f"{total:.3f}", ha="center", va="top", fontsize=10, fontweight="bold")
    ax.annotate(
        "0.353 eV less\nCo-O strengthening",
        xy=(1, totals[1]),
        xytext=(0.50, -0.34),
        arrowprops=dict(arrowstyle="->", color="#4a5057", lw=1.0),
        ha="center",
        fontsize=9.2,
        bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="#c7ccd1"),
    )
    ax.axhline(0.0, color="#333940", linewidth=0.8)
    ax.set_xticks(x, materials)
    ax.set_ylim(-1.65, 0.08)
    ax.set_ylabel(r"$\Delta\mathrm{ICOHP}=\mathrm{ICOHP}_{*O}-\mathrm{ICOHP}_{*OH}$ (eV)")
    ax.set_title("(e)  Reaction-induced ICOHP change", loc="left", fontsize=12.5, fontweight="bold")
    ax.text(0.03, 0.03, "more negative = larger bond strengthening", transform=ax.transAxes, fontsize=8.5, color="#59616a")
    ax.grid(axis="y", color="#dfe3e6", linewidth=0.55, alpha=0.75)
    ax.tick_params(direction="in", top=True, right=True)

    table_text = (
        "Total ICOHP at $E_F$ (eV)\n"
        "                *OH       *O\n"
        f"Undoped  {CASES[('Undoped', '*OH')].icohp_total:7.3f}  {CASES[('Undoped', '*O')].icohp_total:7.3f}\n"
        f"Al16       {CASES[('Al16', '*OH')].icohp_total:7.3f}  {CASES[('Al16', '*O')].icohp_total:7.3f}"
    )
    ax.text(
        0.97,
        0.97,
        table_text,
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=8.8,
        family="monospace",
        bbox=dict(boxstyle="round,pad=0.35", fc="#f7f8f8", ec="#c8cdd2"),
    )


def write_summary() -> None:
    rows = [
        "material\tstate\tdistance_A\tICOHP_spin1_eV\tICOHP_spin2_eV\tICOHP_total_eV\tspilling_spin1_percent\tspilling_spin2_percent"
    ]
    for material in ("Undoped", "Al16"):
        for state in ("*OH", "*O"):
            case = CASES[(material, state)]
            rows.append(
                f"{material}\t{state}\t{case.distance:.5f}\t{case.icohp_spin1:.5f}\t{case.icohp_spin2:.5f}\t"
                f"{case.icohp_total:.5f}\t{case.spilling1:.2f}\t{case.spilling2:.2f}"
            )
    for material in ("Undoped", "Al16"):
        oh = CASES[(material, "*OH")]
        o = CASES[(material, "*O")]
        rows.append(
            f"{material}\tDelta(O-OH)\tNA\t{o.icohp_spin1-oh.icohp_spin1:.5f}\t"
            f"{o.icohp_spin2-oh.icohp_spin2:.5f}\t{o.icohp_total-oh.icohp_total:.5f}\tNA\tNA"
        )
    TSV.write_text("\n".join(rows) + "\n")


def main() -> None:
    fig = plt.figure(figsize=(15.8, 9.2))
    grid = fig.add_gridspec(2, 3, width_ratios=(1.0, 1.0, 1.08), hspace=0.23, wspace=0.25)
    axes = [
        fig.add_subplot(grid[0, 0]),
        fig.add_subplot(grid[0, 1]),
        fig.add_subplot(grid[1, 0]),
        fig.add_subplot(grid[1, 1]),
    ]
    summary_ax = fig.add_subplot(grid[:, 2])
    plot_spectrum(axes[0], "Undoped", 1, "a")
    plot_spectrum(axes[1], "Al16", 1, "b")
    plot_spectrum(axes[2], "Undoped", 2, "c")
    plot_spectrum(axes[3], "Al16", 2, "d")
    plot_delta_icohp(summary_ax)

    state_legend = [
        Line2D([0], [0], color=STATE_COLORS["*OH"], lw=2.2, linestyle=STATE_STYLE["*OH"], label="*OH"),
        Line2D([0], [0], color=STATE_COLORS["*O"], lw=2.5, linestyle=STATE_STYLE["*O"], label="*O"),
    ]
    spin_legend = [
        Patch(facecolor=SPIN_COLORS["spin 1"], edgecolor="#333940", label="Spin 1"),
        Patch(facecolor=SPIN_COLORS["spin 2"], edgecolor="#333940", label="Spin 2"),
    ]
    first = fig.legend(handles=state_legend, loc="upper center", ncol=2, frameon=False, bbox_to_anchor=(0.31, 0.965))
    fig.add_artist(first)
    fig.legend(handles=spin_legend, loc="upper center", ncol=2, frameon=False, bbox_to_anchor=(0.83, 0.965))
    fig.suptitle(r"Spin-resolved Co-O$_{ads}$ bonding during *OH $\rightarrow$ *O", fontsize=17.5, y=0.995)
    fig.text(
        0.5,
        0.018,
        r"LOBSTER 5.1.1; $E_F=0$ eV; positive $-\mathrm{COHP}$ denotes bonding. "
        r"Identical fixed geometries for Al16/control pairs; charge spilling 0.92-1.27%.",
        ha="center",
        fontsize=9.3,
        color="#4f5861",
    )
    fig.subplots_adjust(left=0.06, right=0.985, bottom=0.09, top=0.89)
    fig.savefig(OUT, dpi=240, facecolor="white", bbox_inches="tight")
    write_summary()
    print(OUT)
    print(TSV)


if __name__ == "__main__":
    main()
