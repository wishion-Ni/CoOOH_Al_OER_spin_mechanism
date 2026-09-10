#!/usr/bin/env python3
"""Plot the T01 OER free-energy staircase from the long-format CSV."""

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

    fig, ax = plt.subplots(figsize=(7.2, 4.8), dpi=220)
    x = [0, 1, 2, 3, 4]
    for system, frame in data.groupby("system", sort=False):
        frame = frame.sort_values("step")
        if len(frame) != 5 or abs(frame.iloc[0].dG_eV) > 1e-8 or abs(frame.iloc[-1].dG_eV - 4.92) > 1e-6:
            raise ValueError(f"Invalid endpoint or length for {system}")
        y = frame["dG_eV"].to_numpy()
        ax.plot(x, y, marker="o", ms=5, lw=2.0, color=COLORS[system], label=LABELS[system])

    ax.set_xticks(x, ["*", "*OH", "*O", "*OOH", "O2"])
    ax.set_ylabel(r"Cumulative $\Delta G$ (eV, U = 0 V)")
    ax.set_xlabel("OER reaction coordinate")
    ax.axhline(0, color="#888888", lw=0.8)
    ax.grid(axis="y", color="#dddddd", lw=0.7)
    ax.legend(frameon=False, fontsize=8, loc="upper left")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, bbox_inches="tight")


if __name__ == "__main__":
    main()
