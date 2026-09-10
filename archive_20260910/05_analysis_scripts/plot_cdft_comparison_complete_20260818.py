from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


OUT = Path(__file__).resolve().parent
STEM = OUT / "cdft_undoped_vs_al16_complete_20260818"
UNDOPED = "#3F3F3F"
AL16 = "#C84C2F"
GRID = "#D8D8D8"

states = ["OH", "O", "OOH"]
undoped_charge = np.array([-1.356, -1.574, -1.281])
al16_charge = np.array([-1.458, -1.470, -1.379])
undoped_spin = np.array([3.215, 2.394, 3.176])
al16_spin = np.array([3.224, 2.776, 3.146])

constraints = ["OH N-1", "OH N+1", "O N-1", "O N+1", "OOH N-1", "OOH N+1"]
undoped_co = np.array([4.913867, 4.397178, 5.255931, 4.822150, 5.269218, 4.315024])
al16_co = np.array([4.889379, 4.454942, 5.146837, 4.141331, 5.080396, 4.165019])
undoped_fragment = np.array([3.102077, 3.216547, 3.311917, 3.657029, 3.240959, 2.590033])
al16_fragment = np.array([3.385023, 3.771411, 3.389370, 3.389767, 2.873528, 2.697286])


def style_axis(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#777777")
    ax.spines["bottom"].set_color("#777777")
    ax.grid(axis="y", color=GRID, linewidth=0.7, alpha=0.75)
    ax.set_axisbelow(True)
    ax.tick_params(labelsize=9, colors="#303030")


def point_labels(ax, x, values, color, offset):
    for xpos, value in zip(x, values):
        ax.annotate(
            f"{value:.3f}",
            (xpos, value),
            xytext=(0, offset),
            textcoords="offset points",
            ha="center",
            va="bottom" if offset > 0 else "top",
            fontsize=8,
            color=color,
        )


def paired_bars(ax, labels, undoped, al16, title, ylim):
    x = np.arange(len(labels))
    width = 0.36
    left = ax.bar(x - width / 2, undoped, width, color=UNDOPED, label="Undoped")
    right = ax.bar(x + width / 2, al16, width, color=AL16, label="Al16")
    for bars, values, color in ((left, undoped, UNDOPED), (right, al16, AL16)):
        for bar, value in zip(bars, values):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                value + 0.055,
                f"{value:.2f}",
                ha="center",
                va="bottom",
                fontsize=7.2,
                color=color,
            )
    for xpos, u, a in zip(x, undoped, al16):
        ax.text(
            xpos,
            max(u, a) + 0.30,
            f"Al-U {a-u:+.2f}",
            ha="center",
            va="bottom",
            fontsize=7.1,
            color="#333333",
        )
    ax.set_xticks(x, [label.replace(" ", "\n") for label in labels])
    ax.set_ylim(*ylim)
    ax.set_ylabel(r"Constraint penalty  $\Delta E_{\mathrm{cDFT}}$ / eV")
    ax.set_title(title, loc="left")
    style_axis(ax)


def main():
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 9,
            "axes.titleweight": "bold",
            "axes.titlesize": 11,
            "axes.labelsize": 10,
            "legend.fontsize": 8.5,
            "svg.fonttype": "none",
        }
    )
    fig, axes = plt.subplots(2, 2, figsize=(13.8, 9.0))
    fig.subplots_adjust(left=0.075, right=0.985, bottom=0.12, top=0.90, hspace=0.38, wspace=0.24)

    x = np.arange(len(states))
    ax = axes[0, 0]
    ax.plot(x, undoped_charge, "o-", color=UNDOPED, lw=1.8, ms=6, label="Undoped")
    ax.plot(x, al16_charge, "s-", color=AL16, lw=1.8, ms=5.8, label="Al16")
    point_labels(ax, x, undoped_charge, UNDOPED, 7)
    point_labels(ax, x, al16_charge, AL16, -10)
    ax.set_xticks(x, states)
    ax.set_ylim(-1.70, -1.14)
    ax.set_ylabel("Co Hirshfeld charge / e")
    ax.set_title("A  Unconstrained Co charge", loc="left")
    style_axis(ax)
    ax.legend(frameon=False, ncol=2, loc="lower center")

    ax = axes[0, 1]
    ax.plot(x, undoped_spin, "o-", color=UNDOPED, lw=1.8, ms=6, label="Undoped")
    ax.plot(x, al16_spin, "s-", color=AL16, lw=1.8, ms=5.8, label="Al16")
    point_labels(ax, x, undoped_spin, UNDOPED, 7)
    point_labels(ax, x, al16_spin, AL16, -10)
    ax.set_xticks(x, states)
    ax.set_ylim(2.10, 3.43)
    ax.set_ylabel("Co local spin population / e")
    ax.set_title("B  Unconstrained Co spin", loc="left")
    style_axis(ax)
    ax.legend(frameon=False, ncol=2, loc="lower center")

    paired_bars(axes[1, 0], constraints, undoped_co, al16_co, "C  Co-only charge localization", (0, 6.05))
    paired_bars(
        axes[1, 1], constraints, undoped_fragment, al16_fragment,
        "D  Co + adsorbate fragment localization", (0, 4.55)
    )

    fig.suptitle(
        "Complete fixed-geometry cDFT comparison: undoped vs Al16",
        x=0.075,
        ha="left",
        fontsize=15,
        fontweight="bold",
    )
    from matplotlib.patches import Patch

    fig.legend(
        handles=[
            Patch(facecolor=UNDOPED, label="Undoped"),
            Patch(facecolor=AL16, label="Al16"),
        ],
        frameon=False,
        ncol=2,
        loc="upper right",
        bbox_to_anchor=(0.985, 0.96),
    )
    fig.text(
        0.075,
        0.025,
        "N-1 removes one electron (hole localization); N+1 adds one electron. Values are localization penalties relative to each "
        "unconstrained state, not OER step free energies. Models are historical accepted undoped Co32 and chemically valid Al16 Co40; "
        "local sites are not identical, so use differences as mechanistic trends rather than formal oxidation states.",
        ha="left",
        va="bottom",
        fontsize=8.2,
        color="#404040",
        wrap=True,
    )
    fig.savefig(STEM.with_suffix(".png"), dpi=240, facecolor="white")
    fig.savefig(STEM.with_suffix(".svg"), facecolor="white")
    fig.savefig(STEM.with_suffix(".pdf"), facecolor="white")
    plt.close(fig)

    rows = ["state\tconstraint_scope\tdirection\tundoped_eV\tAl16_eV\tAl_minus_undoped_eV\tstatus"]
    for label, u, a in zip(constraints, undoped_co, al16_co):
        state, direction = label.split()
        rows.append(f"{state}\tCo-only\t{direction}\t{u:.6f}\t{a:.6f}\t{a-u:+.6f}\tvalid")
    for label, u, a in zip(constraints, undoped_fragment, al16_fragment):
        state, direction = label.split()
        rows.append(f"{state}\tCo+adsorbate\t{direction}\t{u:.6f}\t{a:.6f}\t{a-u:+.6f}\tvalid")
    rows.extend(
        [
            "O\tCo-only-spin\tM-2\t0.869876\tNA\tNA\tAl16_rejected_spin_branch_discontinuity",
            "O\tCo-only-spin\tM+2\t2.899188\t4.036604\t+1.137416\tvalid",
        ]
    )
    STEM.with_suffix(".tsv").write_text("\n".join(rows) + "\n", encoding="ascii")

    report = """# Complete undoped vs Al16 cDFT comparison

## Completion

- Undoped matched scans: 14/14 clean valid.
- Al16 charge scans: complete and valid.
- Al16 O Co-only M-2: rejected because the constrained solution changed spin branch discontinuously; it is not fitted or imputed.

## Main OER-relevant N-1 result

For a Co+adsorbate fragment, Al16 changes the hole-localization penalty by:

- OH: +0.282946 eV (harder).
- O: +0.077453 eV (slightly harder).
- OOH: -0.367431 eV (easier).

Al therefore does not act as a uniform electron-withdrawing dopant across the cycle. Its clearest effect is selective stabilization of the late OOH-associated oxidized fragment.

## Redox localization

Co-only N-1 costs 4.89-5.27 eV, whereas Co+adsorbate N-1 costs 2.87-3.39 eV. The lower fragment penalties support delocalized Co-O ligand-hole accommodation rather than integer Co-only oxidation.

The unconstrained O state shows the largest spin response to Al: Co spin changes from 2.394 to 2.776, while the adsorbate O spin changes sign in the baseline population analysis. This is consistent with redistribution of spin density over the Co-O unit.

## Spin constraint

The newly completed undoped O M-2 state has a penalty of 0.869876 eV and reaches Co spin 0.394038 for a target of 0.394000. Undoped O M+2 costs 2.899188 eV; Al16 O M+2 costs 4.036604 eV. The Al16 M-2 branch is not comparable because it was rejected for branch discontinuity.

## Scope

These are fixed-geometry cDFT localization energies, not CHE free-energy steps or kinetic barriers. The undoped Co32 and Al16 Co40 local sites are chemically accepted but not geometrically identical. Formal oxidation states require joint interpretation of charge, spin, DFT+U occupation and cDFT energetics.
"""
    STEM.with_suffix(".md").write_text(report, encoding="ascii")


if __name__ == "__main__":
    main()
