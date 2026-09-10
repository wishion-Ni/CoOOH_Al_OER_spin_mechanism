from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


ROOT = Path(__file__).resolve().parent
PNG = ROOT / "ligand_field_spin_selective_Al_mechanism_20260831.png"
PDF = ROOT / "ligand_field_spin_selective_Al_mechanism_20260831.pdf"


plt.rcParams.update(
    {
        "font.family": "serif",
        "font.serif": ["Times New Roman", "DejaVu Serif"],
        "font.size": 9.2,
        "axes.titlesize": 10.5,
        "axes.labelsize": 9.2,
        "legend.fontsize": 8.3,
        "figure.dpi": 180,
        "savefig.dpi": 300,
        "axes.spines.top": False,
        "axes.spines.right": False,
    }
)


COLORS = {
    "co": "#3A78A1",
    "al": "#CC79A7",
    "o": "#D55E00",
    "up": "#D55E00",
    "down": "#0072B2",
    "gray": "#6B7280",
    "light": "#F3F4F6",
    "ink": "#222222",
}


def atom(ax, x, y, label, color, size=580):
    ax.scatter(x, y, s=size, color=color, edgecolor="white", linewidth=1.3, zorder=4)
    ax.scatter(x - 0.035, y + 0.05, s=size * 0.17, color="white", alpha=0.35, linewidth=0, zorder=5)
    ax.text(x, y - 0.01, label, ha="center", va="center", color="white", weight="bold", zorder=6)


def site_schematic(ax, x0, neighbor, title):
    y = 0.84
    atom(ax, x0, y, "Co", COLORS["co"])
    atom(ax, x0 + 0.18, y, "O", COLORS["o"], size=430)
    atom(
        ax,
        x0 + 0.36,
        y,
        neighbor,
        COLORS["co"] if neighbor == "Co" else COLORS["al"],
    )
    ax.plot([x0 + 0.045, x0 + 0.135], [y, y], color=COLORS["ink"], lw=2.0, zorder=2)
    ax.plot([x0 + 0.225, x0 + 0.315], [y, y], color=COLORS["ink"], lw=2.0, zorder=2)
    ax.text(x0 + 0.18, 0.985, title, ha="center", va="top", fontsize=10.2, weight="bold")

    if neighbor == "Co":
        arrow = FancyArrowPatch(
            (x0 + 0.035, 0.69),
            (x0 + 0.325, 0.69),
            connectionstyle="arc3,rad=-0.28",
            arrowstyle="<->",
            mutation_scale=10,
            lw=1.9,
            color=COLORS["up"],
        )
        ax.add_patch(arrow)
        ax.text(x0 + 0.18, 0.59, r"O-mediated $d$-$p$-$d$ exchange", ha="center", color=COLORS["up"], fontsize=8.1)
    else:
        ax.plot(
            [x0 + 0.04, x0 + 0.32],
            [0.69, 0.69],
            color=COLORS["gray"],
            lw=1.2,
            ls="--",
        )
        ax.text(
            x0 + 0.18,
            0.59,
            "weak magnetic exchange\n(Al has no near-$E_F$ 3d states)",
            ha="center",
            color=COLORS["gray"],
            fontsize=8.1,
        )


def draw_levels(ax, center, system):
    width = 0.055
    spin_x = [center - 0.07, center + 0.07]
    spin_labels = [r"spin 1 ($\uparrow$)", r"spin 2 ($\downarrow$)"]
    spin_colors = [COLORS["up"], COLORS["down"]]

    for spin_index, (x, spin_label, color) in enumerate(zip(spin_x, spin_labels, spin_colors)):
        t2g = np.array([0.18, 0.205, 0.23])
        eg = np.array([0.355, 0.39])
        if system == "control" and spin_index == 0:
            t2g += np.array([-0.018, 0.0, 0.018])
            eg += np.array([-0.025, 0.025])
        if system == "Al16" and spin_index == 0:
            t2g += np.array([-0.006, 0.0, 0.006])
            eg += np.array([-0.008, 0.008])
        for energy in t2g:
            ax.plot([x - width, x + width], [energy, energy], color=color, lw=1.6)
        for energy in eg:
            ax.plot([x - width, x + width], [energy, energy], color=color, lw=1.6)
        ax.text(x, 0.115, spin_label, ha="center", va="top", color=color, fontsize=7.8)

    ax.text(center - 0.15, 0.205, r"$t_{2g}$-like", ha="right", va="center", fontsize=7.6)
    ax.text(center - 0.15, 0.372, r"$e_g$-like", ha="right", va="center", fontsize=7.6)
    ax.annotate(
        "",
        xy=(center - 0.145, 0.35),
        xytext=(center - 0.145, 0.235),
        arrowprops=dict(arrowstyle="<->", lw=0.9, color=COLORS["gray"]),
    )
    ax.text(center - 0.16, 0.292, r"$\Delta_{CF}$", ha="right", va="center", fontsize=7.3, color=COLORS["gray"])

    if system == "control":
        response = 0.095
        text = "large majority-spin\nreorganization"
    else:
        response = 0.040
        text = "buffered majority-spin\nreorganization"
    x_arrow = center - 0.07
    ax.annotate(
        "",
        xy=(x_arrow + response, 0.455),
        xytext=(x_arrow - response, 0.455),
        arrowprops=dict(arrowstyle="<->", lw=2.2 if system == "control" else 1.2, color=COLORS["up"]),
    )
    ax.text(center, 0.495, text, ha="center", va="bottom", fontsize=7.7, color=COLORS["up"])


def panel_a(ax):
    ax.set_xlim(0, 1)
    ax.set_ylim(0.06, 1.02)
    ax.axis("off")
    ax.text(0.0, 1.03, "(a) Local ligand-field / exchange picture", fontsize=10.5, weight="bold", va="bottom")

    left_box = FancyBboxPatch(
        (0.015, 0.075), 0.46, 0.91, boxstyle="round,pad=0.012,rounding_size=0.018", facecolor="#FFF7F2", edgecolor="#E5B8A4", lw=0.9
    )
    right_box = FancyBboxPatch(
        (0.525, 0.075), 0.46, 0.91, boxstyle="round,pad=0.012,rounding_size=0.018", facecolor="#F5F7FA", edgecolor="#BDC7D3", lw=0.9
    )
    ax.add_patch(left_box)
    ax.add_patch(right_box)

    site_schematic(ax, 0.07, "Co", "Undoped: Co-O-Co")
    site_schematic(ax, 0.58, "Al", "Al16: Co-O-Al")
    draw_levels(ax, 0.25, "control")
    draw_levels(ax, 0.76, "Al16")
def panel_b(ax):
    labels = [r"spin 1 ($\uparrow$)", r"spin 2 ($\downarrow$)"]
    control = np.array([0.56027, 0.90463])
    al16 = np.array([0.20887, 0.90347])
    x = np.arange(2)
    width = 0.34
    bars_1 = ax.bar(x - width / 2, control, width, label="Undoped", color="#8FA9BE", edgecolor="white", linewidth=0.6)
    bars_2 = ax.bar(x + width / 2, al16, width, label="Al16", color=COLORS["al"], edgecolor="white", linewidth=0.6)
    for bars in (bars_1, bars_2):
        for bar in bars:
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.025, f"{bar.get_height():.3f}", ha="center", va="bottom", fontsize=7.8)
    ax.set_xticks(x, labels)
    ax.set_ylabel(r"Co-O bond strengthening, $-\Delta$ICOHP (eV)")
    ax.set_ylim(0, 1.08)
    ax.set_title("(b) Spin-resolved *OH to *O bonding response", loc="left", weight="bold", pad=8)
    ax.legend(frameon=False, loc="upper left")
    ax.grid(axis="y", color="#D1D5DB", lw=0.6, alpha=0.55)
    ax.text(
        0.985,
        0.955,
        "Al suppresses spin 1 by 62.7%; spin 2 changes by only 0.1%",
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=8.0,
        color=COLORS["ink"],
        bbox=dict(facecolor="white", edgecolor="none", alpha=0.82, pad=1.2),
    )


def panel_c(ax):
    labels = ["Undoped", "Al16"]
    values = [0.107, 0.033]
    bars = ax.bar(labels, values, width=0.55, color=["#8FA9BE", COLORS["al"]], edgecolor="white", linewidth=0.6)
    for bar, value in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, value + 0.004, f"{value:.3f}", ha="center", va="bottom", fontsize=8.2)
    ax.set_ylabel(r"$|\Delta m_{Co}|$ ($\mu_B$)")
    ax.set_ylim(0, 0.135)
    ax.set_title("(c) Active-Co spin buffering", loc="left", weight="bold", pad=8)
    ax.grid(axis="y", color="#D1D5DB", lw=0.6, alpha=0.55)
    ax.text(0.5, 0.124, "69% smaller Co moment change", ha="center", va="center", fontsize=8.0)


def panel_d(ax):
    ax.axis("off")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_title("(d) Mechanistic interpretation", loc="left", weight="bold", pad=8)
    boxes = [
        (0.14, 0.77, 0.72, 0.14, "Co -> Al neighbor substitution", "#F5E6EF"),
        (0.14, 0.57, 0.72, 0.14, "weaker O-mediated magnetic exchange", "#EEF2F6"),
        (0.14, 0.37, 0.72, 0.14, "spin-1 Co-O response is buffered", "#FFF1E8"),
        (0.14, 0.17, 0.72, 0.14, "oxidation/spin response remains O-centered", "#F8F1E7"),
    ]
    for x, y, w, h, text, color in boxes:
        patch = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.012,rounding_size=0.018", facecolor=color, edgecolor="#AAB2BD", lw=0.8)
        ax.add_patch(patch)
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=8.2)
    arrows = [
        ((0.5, 0.77), (0.5, 0.71)),
        ((0.5, 0.57), (0.5, 0.51)),
        ((0.5, 0.37), (0.5, 0.31)),
    ]
    for start, end in arrows:
        ax.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=11, lw=1.25, color=COLORS["gray"]))
    ax.text(
        0.5,
        0.015,
        "Inference: lower Co-centered electronic reorganization.\n"
        "Potential lowering still requires the CHE series.",
        ha="center",
        va="bottom",
        fontsize=7.7,
        color=COLORS["gray"],
    )


def main():
    fig = plt.figure(figsize=(12.8, 7.1))
    grid = fig.add_gridspec(2, 3, width_ratios=[1.55, 1.0, 0.90], height_ratios=[1.0, 0.72], wspace=0.40, hspace=0.38)
    ax_a = fig.add_subplot(grid[:, 0])
    ax_b = fig.add_subplot(grid[0, 1:])
    ax_c = fig.add_subplot(grid[1, 1])
    ax_d = fig.add_subplot(grid[1, 2])

    panel_a(ax_a)
    panel_b(ax_b)
    panel_c(ax_c)
    panel_d(ax_d)

    fig.suptitle(
        "Al substitution selectively buffers the majority-spin Co-O response",
        fontsize=13.0,
        y=1.01,
        weight="bold",
    )
    fig.text(
        0.5,
        -0.015,
        "Quantitative bars: validated spin-resolved LOBSTER ICOHP and Bader local moments. "
        "Ligand-field levels are qualitative distorted-octahedral groups; individual d-orbital assignment is not implied.",
        ha="center",
        fontsize=8.1,
        color=COLORS["gray"],
    )
    fig.savefig(PNG, bbox_inches="tight", facecolor="white")
    fig.savefig(PDF, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(PNG)
    print(PDF)


if __name__ == "__main__":
    main()
