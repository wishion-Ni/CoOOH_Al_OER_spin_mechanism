from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parent
ANALYSIS_SCRIPT = ROOT / "analyze_pdos_dcenter_20260824.py"
WINDOW = (-8.0, 4.0)


def load_analysis_module():
    spec = importlib.util.spec_from_file_location("pdos_analysis", ANALYSIS_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import {ANALYSIS_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main() -> None:
    analysis = load_analysis_module()
    data = analysis.load_cases()
    cases = (
        ("undoped_OH", "Undoped CoOOH", "#4D4D4D", "a"),
        ("Al16_OH", "Al-doped CoOOH", "#D14934", "b"),
    )

    prepared = []
    ymax = 0.0
    for key, title, color, panel in cases:
        energy = data[key]["energy"]
        up, down = data[key]["co_active"]
        dos = analysis.smooth(up + down, sigma_points=1.1)
        center, weight = analysis.centroid(energy, up + down, *WINDOW)
        prepared.append((energy, dos, center, weight, title, color, panel))
        mask = (energy >= WINDOW[0]) & (energy <= WINDOW[1])
        ymax = max(ymax, float(dos[mask].max()))

    plt.rcParams.update({"font.size": 9, "axes.linewidth": 0.85, "figure.dpi": 180})
    fig, axes = plt.subplots(1, 2, figsize=(7.3, 3.25), sharex=True, sharey=True)
    for ax, item in zip(axes, prepared):
        energy, dos, center, weight, title, color, panel = item
        mask = (energy >= WINDOW[0]) & (energy <= WINDOW[1])
        occupied = mask & (energy <= 0.0)
        unoccupied = mask & (energy > 0.0)
        ax.plot(energy[mask], dos[mask], color=color, lw=1.55)
        ax.fill_between(energy[occupied], 0, dos[occupied], color=color, alpha=0.24,
                        linewidth=0)
        ax.fill_between(energy[unoccupied], 0, dos[unoccupied], color=color, alpha=0.08,
                        linewidth=0)
        ax.axvline(0, color="#202020", lw=0.9, ls=":")
        ax.axvline(center, color=color, lw=1.35, ls="--")
        ax.annotate(
            rf"$\epsilon_d$ = {center:.3f} eV",
            xy=(center, ymax * 0.62),
            xytext=(center + 0.45, ymax * 0.82),
            arrowprops={"arrowstyle": "-|>", "color": color, "lw": 0.9},
            color=color,
            fontsize=9,
        )
        ax.text(0.02, 0.96, panel, transform=ax.transAxes, ha="left", va="top",
                fontsize=11, fontweight="bold")
        ax.set_title(title, fontsize=10)
        ax.set_xlim(*WINDOW)
        ax.set_ylim(0, ymax * 1.08)
        ax.set_xlabel(r"Energy relative to $E_F$ (eV)")
        ax.spines[["top", "right"]].set_visible(False)
        ax.tick_params(direction="out", width=0.8, length=3)
    axes[0].set_ylabel(r"Active-Co 3d PDOS (states eV$^{-1}$)")
    fig.subplots_adjust(left=0.10, right=0.985, bottom=0.18, top=0.86, wspace=0.16)
    fig.text(
        0.5,
        0.02,
        r"$\epsilon_d=\int E\rho_d(E)dE/\int\rho_d(E)dE$; integration window: -8 to +4 eV",
        ha="center",
        fontsize=8,
        color="#404040",
    )
    output = ROOT / "d_band_center_standard_pdos_20260824.png"
    fig.savefig(output, dpi=300, bbox_inches="tight")
    plt.close(fig)

    summary = ROOT / "d_band_center_standard_pdos_20260824.tsv"
    with summary.open("w", encoding="ascii", newline="\n") as handle:
        handle.write("material\tstate\tprojection\tEmin_eV\tEmax_eV\td_center_eV\td_weight\n")
        for _, _, center, weight, title, _, _ in prepared:
            handle.write(f"{title}\tOH\tactive_Co_3d_spin_sum\t{WINDOW[0]:.3f}\t"
                         f"{WINDOW[1]:.3f}\t{center:.8f}\t{weight:.8f}\n")
    print(output)
    print(summary)


if __name__ == "__main__":
    main()
