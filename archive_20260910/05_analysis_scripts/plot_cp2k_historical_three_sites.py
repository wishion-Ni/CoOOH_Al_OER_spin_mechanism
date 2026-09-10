from pathlib import Path

import matplotlib.pyplot as plt


OUT = Path(__file__).resolve().parent
SYSTEMS = {
    "Undoped Co32": {
        "steps": [1.199993, 1.793143, 1.534211, 0.392652],
        "color": "#222222",
        "marker": "o",
    },
    "Al16 Co7_adjAl": {
        "steps": [1.403097, 1.524802, 0.871955, 1.120146],
        "color": "#C43C39",
        "marker": "s",
    },
    "Al16 Al47 active site": {
        "steps": [2.382189, -1.011081, 2.217542, 1.331350],
        "color": "#187D72",
        "marker": "^",
    },
}
STATES = ["*", "*OH", "*O", "*OOH", "* + O2"]


def levels(steps):
    values = [0.0]
    for step in steps:
        values.append(values[-1] + step)
    return values


def write_tsv():
    lines = ["system\tstate_index\tstate\tcumulative_E_eV\tstep_dE_eV"]
    for name, spec in SYSTEMS.items():
        cumulative = levels(spec["steps"])
        for i, state in enumerate(STATES):
            step = "" if i == 0 else f"{spec['steps'][i - 1]:.6f}"
            lines.append(f"{name}\t{i}\t{state}\t{cumulative[i]:.6f}\t{step}")
    (OUT / "cp2k_historical_undoped_co7_al47_staircase.tsv").write_text(
        "\n".join(lines) + "\n", encoding="ascii"
    )


def draw():
    fig, ax = plt.subplots(figsize=(10.8, 6.8), constrained_layout=True)
    offsets = [-0.18, 0.0, 0.18]
    for (name, spec), offset in zip(SYSTEMS.items(), offsets):
        cumulative = levels(spec["steps"])
        x = [i + offset for i in range(len(STATES))]
        half_width = 0.24
        for i, energy in enumerate(cumulative):
            ax.plot(
                [x[i] - half_width, x[i] + half_width],
                [energy, energy],
                linewidth=2.8,
                color=spec["color"],
                label=name if i == 0 else None,
                zorder=2,
            )
        for i in range(len(cumulative) - 1):
            ax.plot(
                [x[i] + half_width, x[i + 1] - half_width],
                [cumulative[i], cumulative[i + 1]],
                linewidth=2.1,
                color=spec["color"],
                zorder=2,
            )
        ax.scatter(
            x,
            cumulative,
            s=57,
            marker=spec["marker"],
            color=spec["color"],
            edgecolor="white",
            linewidth=0.8,
            zorder=3,
        )
        for i, step in enumerate(spec["steps"]):
            mid_x = (x[i] + half_width + x[i + 1] - half_width) / 2
            mid_y = (cumulative[i] + cumulative[i + 1]) / 2
            ax.annotate(
                f"{step:.2f}",
                (mid_x, mid_y),
                xytext=(0, 7 if step >= 0 else -12),
                textcoords="offset points",
                ha="center",
                va="center",
                fontsize=8.5,
                color=spec["color"],
                fontweight="semibold",
                bbox={"boxstyle": "square,pad=0.16", "fc": "white", "ec": "none", "alpha": 0.82},
            )

    ax.axhline(0, color="#777777", linewidth=0.8)
    ax.set_xticks(range(len(STATES)), STATES)
    ax.set_xlim(-0.5, 4.5)
    ax.set_ylim(-0.35, 5.35)
    ax.set_ylabel("Cumulative electronic OER energy (eV)")
    ax.set_xlabel("AEM intermediate at U = 0 V")
    ax.set_title("Historical CP2K OER electronic-energy staircase")
    ax.grid(axis="y", color="#D8D8D8", linewidth=0.8, alpha=0.75)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(loc="upper left", frameon=False, ncols=1)
    fig.text(
        0.5,
        0.005,
        "Step labels are electronic Delta E (eV). Historical comparison only; no vibrational correction is applied.",
        ha="center",
        fontsize=8.5,
        color="#555555",
    )
    fig.savefig(OUT / "cp2k_historical_undoped_co7_al47_staircase.svg")
    fig.savefig(OUT / "cp2k_historical_undoped_co7_al47_staircase.png", dpi=220)


if __name__ == "__main__":
    write_tsv()
    draw()
