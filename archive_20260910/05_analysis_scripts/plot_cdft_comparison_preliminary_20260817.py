from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


OUT = Path(__file__).resolve().parent
UNDOPED = "#4D4D4D"
AL16 = "#D55E00"
GRID = "#D9D9D9"

states = ["OH", "O", "OOH"]
undoped_charge = [-1.356, -1.574, -1.281]
al16_charge = [-1.458, -1.470, -1.379]
undoped_spin = [3.215, 2.394, 3.176]
al16_spin = [3.224, 2.776, 3.146]

labels = [
    "OH\nCo N-1",
    "OH\nCo N+1",
    "OH\nfragment N+1",
    "O\nCo N-1",
    "O\nCo N+1",
]
undoped_energy = np.array([4.913867, 4.397179, 3.216547, 5.255932, 4.822150])
al16_energy = np.array([4.889379, 4.454942, 3.771411, 5.146837, 4.141331])
undoped_status = ["valid", "cleanup pending", "valid", "cleanup pending", "valid"]


def style_axis(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#808080")
    ax.spines["bottom"].set_color("#808080")
    ax.tick_params(colors="#303030", labelsize=9)
    ax.grid(axis="y", color=GRID, linewidth=0.7, alpha=0.7)
    ax.set_axisbelow(True)


def annotate_points(ax, x, values, color, offset):
    for xpos, value in zip(x, values):
        ax.annotate(
            f"{value:.3f}",
            (xpos, value),
            xytext=(0, offset),
            textcoords="offset points",
            ha="center",
            va="bottom" if offset >= 0 else "top",
            fontsize=8,
            color=color,
        )


def main():
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 9,
            "axes.titleweight": "bold",
            "axes.labelsize": 10,
            "axes.titlesize": 11,
            "legend.fontsize": 8.5,
            "svg.fonttype": "none",
        }
    )

    fig = plt.figure(figsize=(13.6, 5.6), constrained_layout=False)
    gs = fig.add_gridspec(
        1, 3, width_ratios=[0.92, 0.92, 2.3], left=0.06, right=0.985,
        bottom=0.27, top=0.84, wspace=0.36
    )
    x_state = np.arange(len(states))

    ax1 = fig.add_subplot(gs[0, 0])
    ax1.plot(x_state, undoped_charge, "o-", color=UNDOPED, lw=1.8, ms=6, label="Undoped")
    ax1.plot(x_state, al16_charge, "s-", color=AL16, lw=1.8, ms=5.8, label="Al16")
    annotate_points(ax1, x_state, undoped_charge, UNDOPED, 7)
    annotate_points(ax1, x_state, al16_charge, AL16, -9)
    ax1.set_xticks(x_state, states)
    ax1.set_ylim(-1.68, -1.15)
    ax1.set_ylabel("Co Hirshfeld charge / e")
    ax1.set_title("A  Baseline Co charge", loc="left")
    style_axis(ax1)
    ax1.legend(frameon=False, loc="lower center", bbox_to_anchor=(0.5, 0.01), ncol=2)

    ax2 = fig.add_subplot(gs[0, 1])
    ax2.plot(x_state, undoped_spin, "o-", color=UNDOPED, lw=1.8, ms=6, label="Undoped")
    ax2.plot(x_state, al16_spin, "s-", color=AL16, lw=1.8, ms=5.8, label="Al16")
    annotate_points(ax2, x_state, undoped_spin, UNDOPED, 7)
    annotate_points(ax2, x_state, al16_spin, AL16, -9)
    ax2.set_xticks(x_state, states)
    ax2.set_ylim(2.15, 3.42)
    ax2.set_ylabel("Co local spin population / e")
    ax2.set_title("B  Baseline Co spin", loc="left")
    style_axis(ax2)
    ax2.legend(frameon=False, loc="lower center", bbox_to_anchor=(0.5, 0.01), ncol=2)

    ax3 = fig.add_subplot(gs[0, 2])
    x = np.arange(len(labels))
    width = 0.35
    bars_u = []
    for i, (value, status) in enumerate(zip(undoped_energy, undoped_status)):
        if status == "valid":
            bar = ax3.bar(
                x[i] - width / 2, value, width, color=UNDOPED,
                edgecolor=UNDOPED, linewidth=1.0
            )[0]
        else:
            bar = ax3.bar(
                x[i] - width / 2, value, width, color="white",
                edgecolor=UNDOPED, linewidth=1.2, hatch="////"
            )[0]
        bars_u.append(bar)
    bars_a = ax3.bar(
        x + width / 2, al16_energy, width, color=AL16,
        edgecolor=AL16, linewidth=1.0
    )
    for bar, value in zip(bars_u, undoped_energy):
        ax3.text(bar.get_x() + bar.get_width() / 2, value + 0.08, f"{value:.2f}",
                 ha="center", va="bottom", fontsize=7.7, color=UNDOPED)
    for bar, value in zip(bars_a, al16_energy):
        ax3.text(bar.get_x() + bar.get_width() / 2, value + 0.08, f"{value:.2f}",
                 ha="center", va="bottom", fontsize=7.7, color=AL16)
    for i, (u, a) in enumerate(zip(undoped_energy, al16_energy)):
        ax3.text(i, max(u, a) + 0.38, f"Al-U {a-u:+.2f}", ha="center",
                 va="bottom", fontsize=7.4, color="#333333")
    ax3.set_xticks(x, labels)
    ax3.set_ylim(0, 6.15)
    ax3.set_ylabel(r"Constraint penalty  $\Delta E_{\mathrm{cDFT}}$ / eV")
    ax3.set_title("C  Current matched cDFT localization penalties", loc="left")
    style_axis(ax3)
    from matplotlib.patches import Patch
    handles = [
        Patch(facecolor=UNDOPED, edgecolor=UNDOPED, label="Undoped: clean valid"),
        Patch(facecolor="white", edgecolor=UNDOPED, hatch="////", label="Undoped: cleanup pending"),
        Patch(facecolor=AL16, edgecolor=AL16, label="Al16: clean valid"),
    ]
    ax3.legend(handles=handles, frameon=False, loc="upper center",
               bbox_to_anchor=(0.5, -0.17), ncol=3)

    fig.suptitle(
        "Preliminary charge/spin and cDFT comparison: undoped vs Al16",
        x=0.06, ha="left", fontsize=14, fontweight="bold"
    )
    fig.text(
        0.06, 0.035,
        "cDFT values are fixed-geometry localization penalties relative to each unconstrained baseline; "
        "they are not OER reaction-step free energies. Hatched bars are physically converged but await "
        "a clean DBCSR termination.\nModels: historical accepted undoped Co32 vs chemically valid Al16 Co40; "
        "use the comparison for trends, not absolute formal oxidation-state assignment.",
        ha="left", va="bottom", fontsize=8.2, color="#404040", wrap=True
    )

    stem = OUT / "cdft_undoped_vs_al16_preliminary_20260817"
    fig.savefig(stem.with_suffix(".png"), dpi=240, facecolor="white")
    fig.savefig(stem.with_suffix(".svg"), facecolor="white")
    fig.savefig(stem.with_suffix(".pdf"), facecolor="white")
    plt.close(fig)

    rows = ["panel\tstate\tconstraint\tsystem\tvalue\tunit\tstatus"]
    for state, value in zip(states, undoped_charge):
        rows.append(f"A\t{state}\tbaseline_charge\tundoped\t{value:.6f}\te\tvalid")
    for state, value in zip(states, al16_charge):
        rows.append(f"A\t{state}\tbaseline_charge\tAl16\t{value:.6f}\te\tvalid")
    for state, value in zip(states, undoped_spin):
        rows.append(f"B\t{state}\tbaseline_spin\tundoped\t{value:.6f}\te\tvalid")
    for state, value in zip(states, al16_spin):
        rows.append(f"B\t{state}\tbaseline_spin\tAl16\t{value:.6f}\te\tvalid")
    constraints = ["OH_Co_Nm1", "OH_Co_Np1", "OH_fragment_Np1", "O_Co_Nm1", "O_Co_Np1"]
    for constraint, value, status in zip(constraints, undoped_energy, undoped_status):
        rows.append(f"C\t{constraint.split('_')[0]}\t{constraint}\tundoped\t{value:.6f}\teV\t{status}")
    for constraint, value in zip(constraints, al16_energy):
        rows.append(f"C\t{constraint.split('_')[0]}\t{constraint}\tAl16\t{value:.6f}\teV\tvalid")
    stem.with_suffix(".tsv").write_text("\n".join(rows) + "\n", encoding="ascii")


if __name__ == "__main__":
    main()
