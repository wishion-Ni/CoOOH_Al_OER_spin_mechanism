from pathlib import Path

import matplotlib.pyplot as plt


STEPS = [1.755822390, 2.030710620, 0.669871268, 0.463595722]
LABELS = ["*", "OH*", "O*", "OOH*", "* + O2"]
U_EQ = 1.23


def cumulative(values):
    result = [0.0]
    for value in values:
        result.append(result[-1] + value)
    return result


levels_0 = cumulative(STEPS)
levels_eq = [value - index * U_EQ for index, value in enumerate(levels_0)]

out_dir = Path(__file__).parent
with (out_dir / "strict_site03_vasp_298p15K_staircase.tsv").open("w", encoding="ascii") as handle:
    handle.write("state\telectrons\tdG_U0_eV\tdG_U1.23_eV\n")
    for index, label in enumerate(LABELS):
        handle.write(f"{label}\t{index}\t{levels_0[index]:.9f}\t{levels_eq[index]:.9f}\n")

plt.rcParams.update({"font.size": 10, "font.family": "DejaVu Sans"})
fig, ax = plt.subplots(figsize=(8.0, 5.2), constrained_layout=True)

colors = {"U=0 V": "#1f5a94", "U=1.23 V": "#b33c2e"}
for legend, levels in (("U=0 V", levels_0), ("U=1.23 V", levels_eq)):
    color = colors[legend]
    for index, level in enumerate(levels):
        ax.hlines(level, index - 0.34, index + 0.34, color=color, linewidth=2.4)
        if index < len(levels) - 1:
            ax.plot([index + 0.34, index + 0.66], [level, levels[index + 1]], color=color, linewidth=1.2)

for index, step in enumerate(STEPS):
    weight = "bold" if index == 1 else "normal"
    ax.text(index + 0.5, (levels_0[index] + levels_0[index + 1]) / 2,
            f"{step:.2f}", ha="center", va="center", color="#1f1f1f", fontweight=weight,
            bbox={"facecolor": "white", "edgecolor": "none", "pad": 1.0, "alpha": 0.85})

ax.text(0.02, 0.97,
        "Strict undoped site03, VASP PBE+U, 298.15 K, 1 bar\n"
        "PDS: OH* -> O*   UL = 2.031 V   eta = 0.801 V\n"
        "Literature target eta ~1.00 V; deviation -0.20 V",
        transform=ax.transAxes, ha="left", va="top", fontsize=9,
        bbox={"facecolor": "white", "edgecolor": "#777777", "pad": 5.0})
ax.text(4.32, levels_0[-1] + 0.07, "U=0 V", color=colors["U=0 V"], ha="right", va="bottom")
ax.text(4.32, levels_eq[-1] + 0.07, "U=1.23 V", color=colors["U=1.23 V"], ha="right", va="bottom")

ax.set_xticks(range(len(LABELS)), LABELS)
ax.set_ylabel("Relative free energy (eV)")
ax.set_xlim(-0.45, 4.45)
ax.set_ylim(-0.25, 5.25)
ax.grid(axis="y", color="#d7d7d7", linewidth=0.7)
ax.spines[["top", "right"]].set_visible(False)
fig.savefig(out_dir / "strict_site03_vasp_298p15K_staircase.png", dpi=220)
fig.savefig(out_dir / "strict_site03_vasp_298p15K_staircase.svg")
