from pathlib import Path

import matplotlib.pyplot as plt


OUT = Path(__file__).with_name("vasp_oer_all_existing_preliminary_20260809.png")
X = [0, 1, 2, 3, 4]

series = [
    ("Strict undoped site03", [0.0, 1.531782, 3.887188, 4.360700, 4.920000], "#166534", "-", 3.0),
    ("Strict undoped site01 (partial)", [0.0, 1.495844, 3.910498], "#7c3aed", "--", 2.0),
    ("Strict undoped site02 (partial)", [0.0, 1.689660, 3.897229], "#0f766e", ":", 2.2),
    ("Undoped lattice screen", [0.0, -1.325944, 0.285246, 3.246172, 4.920000], "#c2410c", "-", 2.2),
    ("Al16 lattice screen", [0.0, 0.166564, 1.102971, 2.224078, 4.920000], "#2563eb", "-", 2.2),
]

fig, ax = plt.subplots(figsize=(12, 7.6), dpi=160)
fig.patch.set_facecolor("white")
ax.set_facecolor("white")

for label, values, color, linestyle, width in series:
    xs = X[: len(values)]
    ax.step(xs, values, where="mid", label=label, color=color, linestyle=linestyle, linewidth=width)
    ax.scatter(xs, values, s=24 if len(values) == 5 else 18, color=color, zorder=3)
    if len(values) < 5:
        ax.plot([2.0, 2.82], [values[-1], values[-1]], color=color, linestyle=linestyle, linewidth=1.2, alpha=0.7)
        ax.scatter([3.0], [values[-1]], marker="x", s=65, linewidths=2, color=color, zorder=4)

ax.set_xlim(-0.25, 4.25)
ax.set_ylim(-1.5, 5.25)
ax.set_xticks(X, ["*", "*OH", "*O", "*OOH", "O$_2$ + *"])
ax.set_ylabel("Cumulative $\\Delta G$ (eV)")
ax.set_title("All current VASP OER pathways", loc="left", fontsize=16, fontweight="bold", pad=20)
ax.text(
    0.0,
    1.02,
    "Preliminary electronic CHE at U = 0 V; invalid structures excluded; no ZPE or thermal correction",
    transform=ax.transAxes,
    fontsize=9.5,
    color="#596273",
)
ax.grid(axis="y", color="#d9dee7", linewidth=0.8)
ax.spines[["top", "right"]].set_visible(False)
ax.spines[["left", "bottom"]].set_color("#283241")
ax.tick_params(colors="#394456")

legend = ax.legend(loc="upper left", bbox_to_anchor=(1.015, 1.0), frameon=False, fontsize=9.5)
for text in legend.get_texts():
    text.set_color("#172033")

ax.text(1.02, 0.54, "Electronic CHE summary", transform=ax.transAxes, fontsize=10.5, fontweight="bold")
ax.text(1.02, 0.49, "Strict site03: $\\eta$ = 1.125 V", transform=ax.transAxes, fontsize=9)
ax.text(1.02, 0.455, "PDS: *OH to *O", transform=ax.transAxes, fontsize=8.5, color="#596273")
ax.text(1.02, 0.39, "Undoped lattice: $\\eta$ = 1.731 V", transform=ax.transAxes, fontsize=9)
ax.text(1.02, 0.355, "PDS: *O to *OOH", transform=ax.transAxes, fontsize=8.5, color="#596273")
ax.text(1.02, 0.29, "Al16 lattice: $\\eta$ = 1.466 V", transform=ax.transAxes, fontsize=9)
ax.text(1.02, 0.255, "PDS: *OOH to O$_2$ + *", transform=ax.transAxes, fontsize=8.5, color="#596273")
ax.text(1.02, 0.17, "Partial curves have no valid OOH", transform=ax.transAxes, fontsize=8.5, color="#596273")
ax.text(1.02, 0.135, "and no limiting potential.", transform=ax.transAxes, fontsize=8.5, color="#596273")

fig.text(
    0.075,
    0.018,
    "VASP references: H2 job 110942_12; H2O job 110942_13. Jobs 110953/110954 are supplying strict site03 vibrational corrections.",
    fontsize=8,
    color="#596273",
)
fig.subplots_adjust(left=0.08, right=0.72, top=0.88, bottom=0.12)
fig.savefig(OUT, bbox_inches="tight", facecolor="white")
