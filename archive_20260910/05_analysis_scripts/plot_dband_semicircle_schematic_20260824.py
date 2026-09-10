from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parent
CASES = (
    ("Undoped CoOOH", -2.89479383, "#555555", "a"),
    ("Al-doped CoOOH", -2.74421091, "#D14934", "b"),
)
BAND_HALF_WIDTH = 2.15


def semicircle(center: float, half_width: float, points: int = 500):
    energy = np.linspace(center - half_width, center + half_width, points)
    density = np.sqrt(np.clip(1.0 - ((energy - center) / half_width) ** 2, 0, None))
    return density, energy


def main() -> None:
    plt.rcParams.update({"font.size": 9, "axes.linewidth": 0.85, "figure.dpi": 180})
    fig, axes = plt.subplots(1, 2, figsize=(6.8, 3.55), sharey=True)
    ymax = 0.8
    ymin = -5.5
    undoped_center = CASES[0][1]

    for ax, (title, center, color, panel) in zip(axes, CASES):
        density, energy = semicircle(center, BAND_HALF_WIDTH)
        ax.plot(density, energy, color=color, lw=1.8)
        ax.fill_betweenx(energy, 0, density, color=color, alpha=0.25, linewidth=0)
        ax.axhline(0, color="#202020", lw=1.0, ls=":")
        ax.axhline(center, color=color, lw=1.5, ls="--")
        ax.text(0.04, center + 0.12, rf"$\epsilon_d$ = {center:.3f} eV",
                color=color, fontsize=9, ha="left", va="bottom")
        ax.text(1.08, 0.12, r"$E_F$", color="#202020", fontsize=9,
                ha="right", va="bottom")
        ax.text(0.04, 0.96, panel, transform=ax.transAxes, fontsize=11,
                fontweight="bold", ha="left", va="top")
        ax.set_title(title, fontsize=10)
        ax.set_xlim(0, 1.15)
        ax.set_ylim(ymin, ymax)
        ax.set_xlabel("d-state density (schematic)")
        ax.set_xticks([])
        ax.spines[["top", "right"]].set_visible(False)
        ax.tick_params(direction="out", width=0.8, length=3)

    axes[0].set_ylabel(r"Energy relative to $E_F$ (eV)")
    axes[1].axhline(undoped_center, color="#777777", lw=0.9, ls=":")
    axes[1].annotate(
        r"$\Delta\epsilon_d=+0.151$ eV",
        xy=(1.04, CASES[1][1]),
        xytext=(1.04, undoped_center - 0.55),
        arrowprops={"arrowstyle": "-|>", "color": CASES[1][2], "lw": 1.1},
        color=CASES[1][2],
        ha="right",
        va="top",
        fontsize=9,
    )
    fig.subplots_adjust(left=0.11, right=0.985, bottom=0.19, top=0.82, wspace=0.18)
    fig.text(0.5, 0.03,
             "Semi-elliptical d-band schematic; centers taken from spin-summed active-Co 3d PDOS",
             ha="center", fontsize=8, color="#444444")
    output = ROOT / "d_band_center_semicircle_schematic_20260824.png"
    fig.savefig(output, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(output)


if __name__ == "__main__":
    main()
