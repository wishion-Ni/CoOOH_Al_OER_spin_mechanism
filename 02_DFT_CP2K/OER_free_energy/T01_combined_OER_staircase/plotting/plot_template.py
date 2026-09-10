#!/usr/bin/env python3
"""Plot the selected historical CP2K three-site OER staircase."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


LABELS = {
    "CoOOH_pristine": "Pristine CoOOH",
    "Al16_Co7_adjAl": "Al16: Co adjacent to Al",
    "Al16_Al47_control": "Al16: Al-site control",
}
COLORS = {
    "CoOOH_pristine": "#222222",
    "Al16_Co7_adjAl": "#C43D3D",
    "Al16_Al47_control": "#2C6EAE",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path("source_data/staircase_source.csv"))
    parser.add_argument("--output", type=Path, default=Path("T01_combined_OER_staircase_comparison.png"))
    args = parser.parse_args()

    data = pd.read_csv(args.input)
    required = {"system", "state", "step", "dG_eV"}
    missing = required - set(data.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")
    if sorted(data["step"].unique()) != [0, 1, 2, 3, 4]:
        raise ValueError("Each staircase must use steps 0 through 4")

    fig, ax = plt.subplots(figsize=(10.8, 6.8), dpi=220)
    x = [0, 1, 2, 3, 4]
    offsets = [-0.18, 0.0, 0.18]
    for system, frame in data.groupby("system", sort=False):
        frame = frame.sort_values("step")
        if len(frame) != 5 or abs(frame.iloc[0].dG_eV) > 1e-8 or abs(frame.iloc[-1].dG_eV - 4.92) > 2e-6:
            raise ValueError(f"Invalid endpoint or length for {system}")
        y = frame["dG_eV"].to_numpy()
        offset = offsets[list(data.groupby("system", sort=False).groups).index(system)]
        xx = [v + offset for v in x]
        color = COLORS[system]
        for i, energy in enumerate(y):
            ax.plot([xx[i] - 0.24, xx[i] + 0.24], [energy, energy], lw=2.8, color=color,
                    label=LABELS[system] if i == 0 else None, zorder=2)
        for i in range(len(y) - 1):
            ax.plot([xx[i] + 0.24, xx[i + 1] - 0.24], [y[i], y[i + 1]], lw=2.1,
                    color=color, zorder=2)
        ax.scatter(xx, y, s=57, marker="o", color=color, edgecolor="white", linewidth=0.8, zorder=3)
        for i in range(4):
            step = y[i + 1] - y[i]
            mid_x = (xx[i] + 0.24 + xx[i + 1] - 0.24) / 2
            mid_y = (y[i] + y[i + 1]) / 2
            ax.annotate(f"{step:.2f}", (mid_x, mid_y), xytext=(0, 7 if step >= 0 else -12),
                        textcoords="offset points", ha="center", va="center", fontsize=8.5,
                        color=color, fontweight="semibold",
                        bbox={"boxstyle": "square,pad=0.16", "fc": "white", "ec": "none", "alpha": 0.82})

    ax.set_xticks(x, ["*", "*OH", "*O", "*OOH", "O2"])
    ax.set_ylabel(r"Cumulative electronic OER energy (eV)")
    ax.set_xlabel("AEM intermediate")
    ax.axhline(0, color="#888888", lw=0.8)
    ax.grid(axis="y", color="#dddddd", lw=0.7)
    ax.legend(frameon=False, fontsize=8, loc="upper left")
    ax.set_title("Historical CP2K OER electronic-energy staircase")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, bbox_inches="tight")


if __name__ == "__main__":
    main()

