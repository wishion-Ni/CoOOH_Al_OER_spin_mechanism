from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import TwoSlopeNorm
from mpl_toolkits.axes_grid1.inset_locator import inset_axes

plt.rcParams["svg.fonttype"] = "none"
plt.rcParams["path.simplify"] = True
plt.rcParams["path.simplify_threshold"] = 0.25


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "04_VASP_analysis/diff_density_publication_data"
CASES = [
    ("pristine", "undoped_control", "Undoped CoOOH"),
    ("Al16", "Al16_adjacent", "Al16-substituted CoOOH"),
]
MAPS = [
    ("charge_density", "Charge density difference", r"$\Delta\rho$", "e Å$^{-3}$", 0.050, "RdBu_r"),
    ("magnetization", "Magnetization difference", r"$\Delta m$", "μ$_B$ Å$^{-3}$", 0.080, "PuOr"),
    ("spin_up", "Spin-up density difference", r"$\Delta\rho_\uparrow$", "e Å$^{-3}$", 0.050, "RdBu_r"),
    ("spin_down", "Spin-down density difference", r"$\Delta\rho_\downarrow$", "e Å$^{-3}$", 0.050, "RdBu_r"),
]


def rows(path: Path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def read_field(map_name: str, case_name: str):
    data = rows(BASE / map_name / "source_data" / f"{case_name}.tsv")
    xs = np.array(sorted({float(row["x_A"]) for row in data}))
    ys = np.array(sorted({float(row["y_A"]) for row in data}))
    x_index = {value: i for i, value in enumerate(xs)}
    y_index = {value: i for i, value in enumerate(ys)}
    field = np.zeros((len(ys), len(xs)))
    for row in data:
        field[y_index[float(row["y_A"])], x_index[float(row["x_A"])]] = float(row["value"])
    return xs, ys, field


def read_overlay():
    result = {}
    for row in rows(BASE / "mapping/atom_overlay.tsv"):
        result.setdefault(row["system"], {})[row["label"]] = (float(row["x_A"]), float(row["y_A"]), row["element"])
    return result


def draw_framework(ax, points):
    label_map = {"Co(act)": "Co", "Oads": r"O$_{ads}$", "Obridge": r"O$_{br}$", "Co(adj)": "Co", "Al": "Al"}
    if "Co(act)" in points and "Oads" in points:
        p1, p2 = points["Co(act)"], points["Oads"]
        ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color="#1e1e1e", lw=1.35, zorder=5)
    neighbor = "Al" if "Al" in points else "Co(adj)"
    if "Obridge" in points and neighbor in points:
        p1, p2 = points["Obridge"], points[neighbor]
        ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color="#555555", lw=0.95, zorder=5)
    colors = {"Co": "#777777", "Al": "#e58f22", "O": "#c7372f", "H": "#ffffff"}
    for label, (x, y, element) in points.items():
        ax.scatter(x, y, s=44, color=colors[element], edgecolor="#111111", linewidth=0.55, zorder=7)
        ax.annotate(
            label_map[label],
            (x, y),
            xytext=(0, 8),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=8.2,
            zorder=8,
            bbox={"boxstyle": "round,pad=0.12", "facecolor": "white", "edgecolor": "none", "alpha": 0.78},
        )


def style_axis(ax, x, y, field, title, units, limit, cmap, points, case_label):
    image = ax.contourf(
        x,
        y,
        np.clip(field, -limit, limit),
        levels=np.linspace(-limit, limit, 41),
        cmap=cmap,
        norm=TwoSlopeNorm(vmin=-limit, vcenter=0.0, vmax=limit),
        extend="both",
    )
    ax.contour(x, y, field, levels=[-0.4 * limit, 0.4 * limit], colors=["#126b8a", "#9e2e27"], linewidths=0.55)
    draw_framework(ax, points)
    ax.set_xlabel("u / Å", fontsize=9.4)
    ax.set_ylabel("v / Å", fontsize=9.4)
    ax.tick_params(labelsize=8.0, length=3)
    ax.set_aspect("equal")
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_linewidth(0.8)
        spine.set_color("#222222")
    return image


def save_figure(fig, output_stem: Path):
    output_stem.parent.mkdir(parents=True, exist_ok=True)
    for extension in ("png", "tiff", "pdf", "svg"):
        kwargs = {"dpi": 600, "bbox_inches": "tight", "facecolor": "white"}
        if extension == "tiff":
            kwargs["pil_kwargs"] = {"compression": "tiff_adobe_deflate"}
        fig.savefig(output_stem.with_suffix(f".{extension}"), **kwargs)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description="Render independently usable difference-density subfigures.")
    parser.add_argument("--output-dir", type=Path, default=BASE / "figures/subfigures")
    args = parser.parse_args()
    overlay = read_overlay()

    for map_name, title, symbol, units, limit, cmap in MAPS:
        loaded = [(case[0], case[1], case[2], *read_field(map_name, case[1])) for case in CASES]

        paired, axes = plt.subplots(1, 2, figsize=(7.2, 3.65), dpi=200, sharex=True, sharey=True,
                                    gridspec_kw={"wspace": 0.08})
        image = None
        for ax, (system, case_name, case_label, x, y, field) in zip(axes, loaded):
            image = style_axis(ax, x, y, field, title, units, limit, cmap, overlay[system], case_label)
        cax = inset_axes(
            axes[1],
            width="3.8%",
            height="86%",
            loc="center left",
            bbox_to_anchor=(1.04, 0.0, 1.0, 1.0),
            bbox_transform=axes[1].transAxes,
            borderpad=0,
        )
        cbar = paired.colorbar(image, cax=cax)
        cbar.set_ticks([-limit, 0.0, limit])
        cbar.ax.tick_params(labelsize=8.0, length=3)
        cbar.set_label(units, fontsize=8.8, labelpad=5)
        paired.subplots_adjust(left=0.075, right=0.86, bottom=0.14, top=0.98)
        save_figure(paired, args.output_dir / "paired" / f"{map_name}_difference")

        for system, case_name, case_label, x, y, field in loaded:
            single, ax = plt.subplots(1, 1, figsize=(3.65, 3.55), dpi=200)
            image = style_axis(ax, x, y, field, title, units, limit, cmap, overlay[system], case_label)
            cax = inset_axes(
                ax,
                width="5.0%",
                height="86%",
                loc="center left",
                bbox_to_anchor=(1.06, 0.0, 1.0, 1.0),
                bbox_transform=ax.transAxes,
                borderpad=0,
            )
            cbar = single.colorbar(image, cax=cax)
            cbar.set_ticks([-limit, 0.0, limit])
            cbar.ax.tick_params(labelsize=7.7, length=3)
            cbar.set_label(units, fontsize=8.4, labelpad=5)
            single.subplots_adjust(left=0.16, right=0.78, bottom=0.17, top=0.98)
            save_figure(single, args.output_dir / "single_panel" / f"{map_name}_{case_name}")

    print(args.output_dir)


if __name__ == "__main__":
    main()

