from pathlib import Path
import csv

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.gridspec import GridSpecFromSubplotSpec


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "cdft_oh_to_o_charge_spin_20260820.tsv"
CONSTRAINTS = ROOT / "cdft_oh_to_o_constraints_20260820.tsv"
OUT = ROOT / "cdft_oh_to_o_mechanism_20260820"

COLORS = {"Undoped": "#0072B2", "Al16": "#D55E00"}
SYSTEMS = ["Undoped", "Al16"]
SPECIES = ["Co", "O"]


def read_table(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


rows = read_table(DATA)
constraints = {row["system"]: row for row in read_table(CONSTRAINTS)}
state = {
    (row["system"], row["state"]): {
        "Co_pop": float(row["co_population_e"]),
        "O_pop": float(row["o_population_e"]),
        "Co_spin": float(row["co_spin_muB"]),
        "O_spin": float(row["o_spin_muB"]),
    }
    for row in rows
}


def delta(system, key):
    return state[(system, "O")][key] - state[(system, "OH")][key]


plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 9,
        "axes.titlesize": 10,
        "axes.labelsize": 9,
        "xtick.labelsize": 8.5,
        "ytick.labelsize": 8.5,
        "legend.fontsize": 8,
        "axes.linewidth": 0.8,
        "xtick.major.width": 0.8,
        "ytick.major.width": 0.8,
        "svg.fonttype": "none",
        "pdf.fonttype": 42,
    }
)

fig = plt.figure(figsize=(8.2, 6.7), constrained_layout=False)
outer = fig.add_gridspec(
    2, 2, left=0.09, right=0.98, bottom=0.11, top=0.93, wspace=0.32, hspace=0.42
)
ax_a = fig.add_subplot(outer[0, 0])
ax_b = fig.add_subplot(outer[0, 1])
ax_c = fig.add_subplot(outer[1, 0])
inner = GridSpecFromSubplotSpec(1, 2, subplot_spec=outer[1, 1], wspace=0.68)
ax_d1 = fig.add_subplot(inner[0, 0])
ax_d2 = fig.add_subplot(inner[0, 1])


def style_axis(ax, grid=True):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    if grid:
        ax.grid(axis="y", color="#D9D9D9", linewidth=0.65, alpha=0.8)
        ax.set_axisbelow(True)


# (a) Electron redistribution from *OH to *O.
x = np.arange(len(SPECIES))
width = 0.34
for i, system in enumerate(SYSTEMS):
    values = [delta(system, "Co_pop"), delta(system, "O_pop")]
    bars = ax_a.bar(
        x + (i - 0.5) * width,
        values,
        width,
        color=COLORS[system],
        edgecolor="white",
        linewidth=0.6,
        label=system,
        zorder=3,
    )
    for bar, value in zip(bars, values):
        offset = 0.022 if value >= 0 else -0.030
        va = "bottom" if value >= 0 else "top"
        ax_a.text(
            bar.get_x() + bar.get_width() / 2,
            value + offset,
            f"{value:+.3f}",
            ha="center",
            va=va,
            fontsize=7.7,
            color="#222222",
        )
ax_a.axhline(0, color="#333333", linewidth=0.8)
ax_a.set_xticks(x, ["Active Co", "Adsorbate O"])
ax_a.set_ylim(-0.58, 0.32)
ax_a.set_ylabel(r"$\Delta$ Hirshfeld population (e)")
ax_a.set_title(r"(a) Charge redistribution, $\ast$OH $\rightarrow$ $\ast$O", loc="left", fontweight="bold")
ax_a.legend(frameon=False, ncol=2, loc="upper right", handlelength=1.2)
ax_a.text(
    x[0] + width / 2,
    0.105,
    "Co charge\nbuffered",
    ha="center",
    va="bottom",
    fontsize=7.7,
    color=COLORS["Al16"],
)
style_axis(ax_a)


# (b) Absolute local-spin trajectories.
state_x = np.array([0.0, 1.0])
markers = {"Co": "o", "O": "D"}
linestyles = {"Co": "-", "O": "--"}
for system in SYSTEMS:
    for species in SPECIES:
        values = [state[(system, "OH")][f"{species}_spin"], state[(system, "O")][f"{species}_spin"]]
        ax_b.plot(
            state_x,
            values,
            color=COLORS[system],
            marker=markers[species],
            markersize=5.2,
            linewidth=1.6,
            linestyle=linestyles[species],
            label=f"{system} {species}",
            zorder=3,
        )
ax_b.axhline(0, color="#333333", linewidth=0.8)
ax_b.set_xticks(state_x, [r"$\ast$OH", r"$\ast$O"])
ax_b.set_xlim(-0.12, 1.12)
ax_b.set_ylim(-0.75, 3.6)
ax_b.set_ylabel(r"Hirshfeld local spin ($\mu_{B}$)")
ax_b.set_title("(b) Local-spin evolution", loc="left", fontweight="bold")
ax_b.annotate(
    "O spin sign reversal",
    xy=(1.0, state[("Al16", "O")]["O_spin"]),
    xytext=(0.48, -0.61),
    color=COLORS["Al16"],
    fontsize=7.8,
    ha="center",
    arrowprops={"arrowstyle": "->", "color": COLORS["Al16"], "lw": 0.9},
)
ax_b.legend(frameon=False, ncol=2, loc="upper right", columnspacing=0.9, handlelength=2.0)
style_axis(ax_b)


# (c) Quantitative partition of the spin response.
for i, system in enumerate(SYSTEMS):
    values = [delta(system, "Co_spin"), delta(system, "O_spin")]
    bars = ax_c.bar(
        x + (i - 0.5) * width,
        values,
        width,
        color=COLORS[system],
        edgecolor="white",
        linewidth=0.6,
        zorder=3,
    )
    for bar, value in zip(bars, values):
        ax_c.text(
            bar.get_x() + bar.get_width() / 2,
            value - 0.045,
            f"{value:+.3f}",
            ha="center",
            va="top",
            fontsize=7.7,
            color="#222222",
        )
ax_c.axhline(0, color="#333333", linewidth=0.8)
ax_c.set_xticks(x, ["Active Co", "Adsorbate O"])
ax_c.set_ylim(-0.98, 0.12)
ax_c.set_ylabel(r"$\Delta$ local spin ($\mu_{B}$)")
ax_c.set_title("(c) Spin-change partition", loc="left", fontweight="bold")
style_axis(ax_c)


# (d) Independent constrained-state fingerprints.
penalty = [float(constraints[s]["o_co_mp2_penalty_eV"]) for s in SYSTEMS]
frag_delta = [
    float(constraints[s]["o_fragment_nm1_spin_muB"])
    - float(constraints[s]["o_fragment_baseline_spin_muB"])
    for s in SYSTEMS
]

for ax, values, ylabel, title, ylim in [
    (ax_d1, penalty, "Energy (eV)", r"Co-only $M+2$", (0, 4.7)),
    (ax_d2, frag_delta, r"$\Delta$ spin ($\mu_{B}$)", r"Co+O $N-1$", (-0.75, 1.18)),
]:
    bars = ax.bar(
        np.arange(2),
        values,
        width=0.62,
        color=[COLORS[s] for s in SYSTEMS],
        edgecolor="white",
        linewidth=0.6,
        zorder=3,
    )
    ax.axhline(0, color="#333333", linewidth=0.8)
    ax.set_xticks(np.arange(2), ["Undoped", "Al16"], rotation=20, ha="right")
    ax.set_ylim(*ylim)
    ax.set_ylabel(ylabel)
    ax.set_title(title, fontsize=9)
    for bar, value in zip(bars, values):
        offset = 0.09 if value >= 0 else -0.08
        va = "bottom" if value >= 0 else "top"
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            value + offset,
            f"{value:+.3f}" if ax is ax_d2 else f"{value:.3f}",
            ha="center",
            va=va,
            fontsize=7.7,
        )
    style_axis(ax)

fig.text(
    0.545,
    0.486,
    r"(d) Constrained-state fingerprints for $\ast$O",
    ha="left",
    va="bottom",
    fontsize=10,
    fontweight="bold",
)

fig.suptitle(
    r"cDFT evidence: Al redirects the $\ast$OH $\rightarrow$ $\ast$O spin response",
    x=0.52,
    y=0.982,
    fontsize=12,
    fontweight="bold",
)
fig.text(
    0.09,
    0.035,
    "Fixed-geometry comparison. Historical undoped Co32 and Al16 Co40 active sites are not geometrically identical.",
    fontsize=7.6,
    color="#555555",
)

fig.savefig(OUT.with_suffix(".png"), dpi=400, bbox_inches="tight", facecolor="white")
fig.savefig(OUT.with_suffix(".pdf"), bbox_inches="tight", facecolor="white")
fig.savefig(OUT.with_suffix(".svg"), bbox_inches="tight", facecolor="white")
plt.close(fig)
