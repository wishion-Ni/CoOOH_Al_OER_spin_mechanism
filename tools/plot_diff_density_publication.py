from __future__ import annotations

import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import TwoSlopeNorm


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "04_VASP_analysis/diff_density_publication_data"
CASES = [("pristine", "undoped_control", "Undoped CoOOH"), ("Al16", "Al16_adjacent", "Al16-substituted CoOOH")]
MAPS = [
    ("charge_density", "charge_diff", "Charge density difference", "e Angstrom^-3", 0.050, "RdBu_r"),
    ("magnetization", "magnetization_diff", "Magnetization difference", "mu_B Angstrom^-3", 0.080, "PuOr"),
    ("spin_up", "spin_up_diff", "Spin-up difference", "e Angstrom^-3", 0.050, "RdBu_r"),
    ("spin_down", "spin_down_diff", "Spin-down difference", "e Angstrom^-3", 0.050, "RdBu_r"),
]


def rows(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def atom_color(element):
    return {"Co": "#777777", "Al": "#e58f22", "O": "#c7372f"}[element]


def read_field(map_name, case_name):
    path = BASE / map_name / "source_data" / (case_name + ".tsv")
    data = rows(path)
    xs = sorted({float(row["x_A"]) for row in data})
    ys = sorted({float(row["y_A"]) for row in data})
    x_index = {value: i for i, value in enumerate(xs)}
    y_index = {value: i for i, value in enumerate(ys)}
    field = np.zeros((len(ys), len(xs)))
    for row in data:
        field[y_index[float(row["y_A"])], x_index[float(row["x_A"])]] = float(row["value"])
    return np.array(xs), np.array(ys), field


def read_overlay():
    result = {}
    for row in rows(BASE / "mapping/atom_overlay.tsv"):
        result.setdefault(row["system"], []).append(row)
    return result


def main():
    overlay = read_overlay()
    fig, axes = plt.subplots(2, 4, figsize=(15.5, 6.2), dpi=200, sharex=True, sharey=True)
    for row_index, (system, case_name, case_label) in enumerate(CASES):
        for col_index, (map_name, map_type, title, units, limit, cmap) in enumerate(MAPS):
            x, y, field = read_field(map_name, case_name)
            ax = axes[row_index, col_index]
            image = ax.contourf(
                x,
                y,
                np.clip(field, -limit, limit),
                levels=np.linspace(-limit, limit, 101),
                cmap=cmap,
                norm=TwoSlopeNorm(vmin=-limit, vcenter=0.0, vmax=limit),
                extend="both",
            )
            ax.contour(x, y, field, levels=[-0.4 * limit, 0.4 * limit], colors=["#126b8a", "#9e2e27"], linewidths=0.55)
            points = overlay[system]
            point_by_label = {p["label"]: (float(p["x_A"]), float(p["y_A"])) for p in points}
            labels = list(point_by_label)
            for first, second in zip(labels[:-1], labels[1:]):
                ax.plot([point_by_label[first][0], point_by_label[second][0]], [point_by_label[first][1], point_by_label[second][1]], color="#444444", lw=0.85, zorder=5)
            for point in points:
                xy = point_by_label[point["label"]]
                ax.scatter(xy[0], xy[1], s=42, color=atom_color(point["element"]), edgecolor="#111111", linewidth=0.5, zorder=7)
                ax.text(xy[0], xy[1] + 0.18, point["label"], ha="center", va="bottom", fontsize=7.0, zorder=8)
            if row_index == 0:
                ax.set_title(title, fontsize=9.5, pad=6)
            if col_index == 0:
                ax.set_ylabel(case_label, fontsize=8.6)
            if row_index == 1:
                ax.set_xlabel("x / Å", fontsize=8.2)
            ax.set_aspect("equal")
            ax.tick_params(labelsize=6.8)
            colorbar = fig.colorbar(image, ax=ax, pad=0.012, fraction=0.042)
            colorbar.set_ticks([-limit, 0.0, limit])
            colorbar.ax.tick_params(labelsize=6.2)
            colorbar.set_label(units, fontsize=6.7)
    fig.suptitle(r"Fixed-geometry density reconstruction for $*\mathrm{OH}\rightarrow *\mathrm{O}$", fontsize=11.2, y=1.01)
    fig.text(0.5, -0.025, r"$\Delta\rho=\rho(*\mathrm{O}@*\mathrm{OH}\ geometry)-\rho(*\mathrm{OH}@*\mathrm{OH}\ geometry)$; identical plane, limits and orientation.", ha="center", fontsize=8.0)
    fig.tight_layout(w_pad=0.65, h_pad=0.55)
    output = BASE / "figures"
    output.mkdir(parents=True, exist_ok=True)
    for extension in ("png", "tiff", "pdf", "svg"):
        kwargs = {"dpi": 600, "bbox_inches": "tight", "facecolor": "white"}
        if extension == "tiff":
            kwargs["pil_kwargs"] = {"compression": "tiff_lzw"}
        fig.savefig(output / ("diff_density_publication." + extension), **kwargs)
    plt.close(fig)
    print(output / "diff_density_publication.png")


if __name__ == "__main__":
    main()

