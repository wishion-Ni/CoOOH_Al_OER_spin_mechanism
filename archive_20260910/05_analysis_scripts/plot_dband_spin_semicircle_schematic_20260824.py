from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch
from matplotlib.lines import Line2D


ROOT = Path(__file__).resolve().parent
CASES = (
    {
        "title": "Undoped CoOOH",
        "up": -5.53471957,
        "down": -0.14743267,
        "total": -2.89479383,
        "panel": "a",
    },
    {
        "title": "Al-doped CoOOH",
        "up": -5.55880641,
        "down": 0.02690972,
        "total": -2.74421091,
        "panel": "b",
    },
)
UP_COLOR = "#2A6FBB"
DOWN_COLOR = "#D64A32"
UP_HALF_WIDTH = 1.70
DOWN_HALF_WIDTH = 1.85


def half_ellipse(center: float, half_width: float, points: int = 500):
    energy = np.linspace(center - half_width, center + half_width, points)
    density = np.sqrt(np.clip(1.0 - ((energy - center) / half_width) ** 2, 0, None))
    return density, energy


def main() -> None:
    plt.rcParams.update({"font.size": 9, "axes.linewidth": 0.85, "figure.dpi": 180})
    fig, axes = plt.subplots(1, 2, figsize=(7.1, 4.25), sharex=True, sharey=True)

    for ax, case in zip(axes, CASES):
        up_density, up_energy = half_ellipse(case["up"], UP_HALF_WIDTH)
        down_density, down_energy = half_ellipse(case["down"], DOWN_HALF_WIDTH)

        ax.plot(-up_density, up_energy, color=UP_COLOR, lw=1.8)
        ax.fill_betweenx(up_energy, -up_density, 0, color=UP_COLOR, alpha=0.26, linewidth=0)
        ax.plot(down_density, down_energy, color=DOWN_COLOR, lw=1.8)
        ax.fill_betweenx(down_energy, 0, down_density, color=DOWN_COLOR, alpha=0.24, linewidth=0)

        ax.axhline(0, color="#202020", lw=1.0, ls=":")
        ax.hlines(case["up"], -1.08, 0, color=UP_COLOR, lw=1.25, ls="--")
        ax.hlines(case["down"], 0, 1.08, color=DOWN_COLOR, lw=1.25, ls="--")
        ax.axhline(case["total"], color="#202020", lw=1.15, ls="-.")

        ax.text(-1.04, case["up"] + 0.10, rf"$\epsilon_d^\uparrow$={case['up']:.2f}",
                color=UP_COLOR, ha="left", va="bottom", fontsize=8.5)
        ax.text(1.04, case["down"] - 0.10, rf"$\epsilon_d^\downarrow$={case['down']:.2f}",
                color=DOWN_COLOR, ha="right", va="top", fontsize=8.5)
        ax.text(0.0, case["total"] + 0.12, rf"$\epsilon_d$={case['total']:.3f} eV",
                color="#202020", ha="center", va="bottom", fontsize=8.5)
        ax.text(1.06, 0.18, r"$E_F$", color="#202020", ha="right", va="bottom", fontsize=8.5)
        ax.text(0.02, 0.97, case["panel"], transform=ax.transAxes, fontsize=11,
                fontweight="bold", ha="left", va="top")

        ax.set_title(case["title"], fontsize=10)
        ax.set_xlim(-1.15, 1.15)
        ax.set_ylim(-7.7, 2.2)
        ax.set_xticks([-0.8, 0, 0.8], ["majority", "0", "minority"])
        ax.set_xlabel("Spin-resolved d-state density (schematic)")
        ax.spines[["top", "right"]].set_visible(False)
        ax.tick_params(direction="out", width=0.8, length=3)

    axes[0].set_ylabel(r"Energy relative to $E_F$ (eV)")
    handles = [
        Patch(facecolor=UP_COLOR, edgecolor=UP_COLOR, alpha=0.35, label="majority spin"),
        Patch(facecolor=DOWN_COLOR, edgecolor=DOWN_COLOR, alpha=0.35, label="minority spin"),
        Line2D([0], [0], color="#202020", lw=1.15, ls="-.", label=r"spin-summed $\epsilon_d$"),
    ]
    fig.legend(handles=handles, frameon=False, ncol=3, loc="upper center",
               bbox_to_anchor=(0.5, 0.995), fontsize=8.5)
    fig.subplots_adjust(left=0.10, right=0.985, bottom=0.17, top=0.80, wspace=0.15)
    fig.text(
        0.5,
        0.025,
        "Spin-resolved semi-elliptical d-band schematic; centers integrated from active-Co 3d PDOS (-8 to +4 eV)",
        ha="center",
        fontsize=8,
        color="#444444",
    )
    output = ROOT / "d_band_center_spin_semicircle_schematic_20260824.png"
    fig.savefig(output, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(output)


if __name__ == "__main__":
    main()
