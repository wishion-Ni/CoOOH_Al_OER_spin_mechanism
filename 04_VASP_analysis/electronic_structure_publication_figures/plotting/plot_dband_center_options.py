from __future__ import annotations

from pathlib import Path
import csv

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "source_data"
FIGURES = ROOT / "figures"

ACTIVE = SOURCE / "V06_activeCo_dcenter_values.csv"
FRAMEWORK = SOURCE / "V06_framework_dcenter_values.csv"
SHIFT = SOURCE / "V06_shift_summary.csv"

PRISTINE = "#374151"
AL = "#2A9D8F"
TEXT = "#1F2937"

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 9,
    "axes.linewidth": 0.8,
    "axes.edgecolor": "#202020",
    "xtick.direction": "out",
    "ytick.direction": "out",
    "xtick.major.width": 0.8,
    "ytick.major.width": 0.8,
    "xtick.major.size": 3.2,
    "ytick.major.size": 3.2,
    "svg.fonttype": "none",
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
})

SYSTEM_LABEL = {
    "Undoped CoOOH": "Pristine CoOOH",
    "Al-doped CoOOH": "Al-substituted CoOOH",
}
SYSTEM_COLOR = {
    "Undoped CoOOH": PRISTINE,
    "Al-doped CoOOH": AL,
}


def read_csv(path: Path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def full_frame(ax):
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_linewidth(0.8)
        spine.set_color("#202020")
    ax.tick_params(labelsize=8.3)


def save_all(fig, stem: str):
    FIGURES.mkdir(parents=True, exist_ok=True)
    base = FIGURES / stem
    fig.savefig(base.with_suffix(".png"), dpi=600, facecolor="white")
    fig.savefig(base.with_suffix(".tif"), dpi=600, facecolor="white",
                pil_kwargs={"compression": "tiff_adobe_deflate"})
    fig.savefig(base.with_suffix(".pdf"), facecolor="white")
    fig.savefig(base.with_suffix(".svg"), facecolor="white")
    fig.savefig(base.with_suffix(".eps"), facecolor="white")
    plt.close(fig)


def select(rows, material: str, state: str, window: str = "occupied"):
    for row in rows:
        if row["material"] == material and row["state"] == state and row["window"] == window:
            return row
    raise KeyError((material, state, window))


def build_shift_summary(active_rows, framework_rows):
    components = [
        ("Active Co total", "d_center_eV"),
        ("Active Co spin-up", "d_center_up_eV"),
        ("Active Co spin-down", "d_center_down_eV"),
    ]
    output = []
    for material in ("Undoped CoOOH", "Al-doped CoOOH"):
        oh = select(active_rows, material, "OH")
        o = select(active_rows, material, "O")
        for label, key in components:
            output.append({
                "material": material,
                "component": label,
                "window": "occupied",
                "delta_epsilon_d_eV": float(o[key]) - float(oh[key]),
            })
        fw_oh = select(framework_rows, material, "OH")
        fw_o = select(framework_rows, material, "O")
        output.append({
            "material": material,
            "component": "Framework Co average",
            "window": "occupied",
            "delta_epsilon_d_eV": float(fw_o["framework_d_center_eV"]) - float(fw_oh["framework_d_center_eV"]),
        })
    with SHIFT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["material", "component", "window", "delta_epsilon_d_eV"])
        writer.writeheader()
        for row in output:
            writer.writerow({**row, "delta_epsilon_d_eV": f"{row['delta_epsilon_d_eV']:.8f}"})
    return output


def plot_absolute(active_rows):
    fig, ax = plt.subplots(figsize=(4.85, 3.45), dpi=180)
    fig.subplots_adjust(left=0.18, right=0.78, bottom=0.18, top=0.95)
    x = np.array([0.0, 1.0])
    for material in ("Undoped CoOOH", "Al-doped CoOOH"):
        vals = [float(select(active_rows, material, state)["d_center_eV"]) for state in ("OH", "O")]
        c = SYSTEM_COLOR[material]
        ax.plot(x, vals, color=c, lw=1.8, zorder=2)
        ax.scatter([0], [vals[0]], facecolor="white", edgecolor=c, s=38, linewidth=1.3, zorder=3)
        ax.scatter([1], [vals[1]], facecolor=c, edgecolor=c, marker="s", s=34, linewidth=1.0, zorder=3)
        ax.text(0, vals[0]-0.018, f"{vals[0]:.3f}", color=c, ha="center", va="top", fontsize=8.0)
        ax.text(1, vals[1]+0.018, f"{vals[1]:.3f}", color=c, ha="center", va="bottom", fontsize=8.0)
        ax.text(0.50, np.mean(vals)+0.018, f"Δ={vals[1]-vals[0]:+.3f} eV", color=c,
                ha="center", va="bottom", fontsize=8.0)
        ax.text(1.08, vals[1], SYSTEM_LABEL[material], color=c, ha="left", va="center", fontsize=8.2)
    ax.set_xticks([0, 1], ["*OH", "*O"])
    ax.set_ylabel(r"Occupied active-Co 3d centroid, $\epsilon_d-E_F$ (eV)", fontsize=9.2)
    ax.set_xlim(-0.12, 1.58)
    ax.set_ylim(-5.18, -4.60)
    full_frame(ax)
    save_all(fig, "V06a_dband_center_absolute")


def plot_shift(shift_rows):
    fig, ax = plt.subplots(figsize=(5.35, 3.55), dpi=180)
    fig.subplots_adjust(left=0.22, right=0.97, bottom=0.20, top=0.94)
    comps = ["Active Co total", "Active Co spin-up", "Active Co spin-down", "Framework Co average"]
    labels = ["total 3d", r"spin $\uparrow$", r"spin $\downarrow$", "framework avg"]
    y = np.arange(len(comps))[::-1]
    data = {(r["material"], r["component"]): float(r["delta_epsilon_d_eV"]) for r in shift_rows}
    for ypos, comp in zip(y, comps):
        vp = data[("Undoped CoOOH", comp)]
        va = data[("Al-doped CoOOH", comp)]
        ax.plot([vp, va], [ypos, ypos], color="#9CA3AF", lw=1.15, zorder=1)
        ax.scatter(vp, ypos, facecolor="white", edgecolor=PRISTINE, s=36, linewidth=1.3, zorder=3)
        ax.scatter(va, ypos, facecolor=AL, edgecolor=AL, marker="s", s=33, linewidth=1.0, zorder=3)
        ax.text(vp-0.007, ypos+0.14, f"{vp:+.3f}", color=PRISTINE, ha="right", va="bottom", fontsize=7.8)
        ax.text(va+0.007, ypos-0.14, f"{va:+.3f}", color=AL, ha="left", va="top", fontsize=7.8)
    ax.text(0.02, 0.98, "○  Pristine CoOOH", transform=ax.transAxes, color=PRISTINE,
            ha="left", va="top", fontsize=8.0)
    ax.text(0.42, 0.98, "■  Al-substituted CoOOH", transform=ax.transAxes, color=AL,
            ha="left", va="top", fontsize=8.0)
    ax.axvline(0, color="#4B5563", lw=0.85, ls="--")
    ax.set_yticks(y, labels)
    ax.set_xlabel(r"$\Delta\epsilon_d = \epsilon_d(*O)-\epsilon_d(*OH)$ (eV)", fontsize=9.2)
    ax.set_xlim(-0.14, 0.27)
    ax.set_ylim(-0.62, 3.58)
    full_frame(ax)
    save_all(fig, "V06b_dband_center_shift_summary")


def semiellipse(energy, center, halfwidth):
    z = (energy-center)/halfwidth
    x = np.zeros_like(energy)
    mask = np.abs(z) <= 1.0
    x[mask] = np.sqrt(1.0-z[mask]**2)
    return x


def plot_schematic(active_rows):
    fig, axes = plt.subplots(1, 2, figsize=(6.2, 3.75), dpi=180, sharey=True)
    fig.subplots_adjust(left=0.12, right=0.98, bottom=0.18, top=0.93, wspace=0.16)
    e = np.linspace(-6.6, -3.5, 600)
    halfwidth = 0.95  # schematic only; not fitted to PDOS
    for ax, material in zip(axes, ("Undoped CoOOH", "Al-doped CoOOH")):
        c = SYSTEM_COLOR[material]
        oh = float(select(active_rows, material, "OH")["d_center_eV"])
        o = float(select(active_rows, material, "O")["d_center_eV"])
        dos_oh = semiellipse(e, oh, halfwidth)
        dos_o = semiellipse(e, o, halfwidth)
        ax.fill_betweenx(e, -dos_oh, 0, color=c, alpha=0.14, linewidth=0)
        ax.plot(-dos_oh, e, color=c, lw=1.35)
        ax.fill_betweenx(e, 0, dos_o, color=c, alpha=0.42, linewidth=0)
        ax.plot(dos_o, e, color=c, lw=1.35)
        ax.plot([-0.96, -0.08], [oh, oh], color=c, lw=1.05, ls="--")
        ax.plot([0.08, 0.96], [o, o], color=c, lw=1.05, ls="--")
        ax.axvline(0, color="#9CA3AF", lw=0.7)
        ax.text(0.28, 0.93, "*OH", transform=ax.transAxes, color=c, ha="center", va="top", fontsize=8.2)
        ax.text(0.72, 0.93, "*O", transform=ax.transAxes, color=c, ha="center", va="top", fontsize=8.2)
        ax.text(-0.93, oh-0.04, f"{oh:.3f}", color=c, ha="left", va="top", fontsize=7.7)
        ax.text(0.93, o+0.04, f"{o:.3f}", color=c, ha="right", va="bottom", fontsize=7.7)
        ax.text(0.04, 0.05, SYSTEM_LABEL[material], transform=ax.transAxes, color=c,
                ha="left", va="bottom", fontsize=8.6)
        ax.text(0.96, 0.05, f"Δε$_d$={o-oh:+.3f} eV", transform=ax.transAxes, color=c,
                ha="right", va="bottom", fontsize=8.0)
        ax.set_xlim(-1.12, 1.12)
        ax.set_ylim(-6.6, -3.5)
        ax.set_xticks([])
        full_frame(ax)
    axes[0].set_ylabel(r"Energy relative to $E_F$ (eV)", fontsize=9.2)
    fig.text(0.55, 0.055, "Schematic semi-elliptic Co 3d DOS envelope", ha="center", fontsize=8.3, color=TEXT)
    save_all(fig, "V06c_dband_center_schematic")


def main():
    active = read_csv(ACTIVE)
    framework = read_csv(FRAMEWORK)
    shifts = build_shift_summary(active, framework)
    plot_absolute(active)
    plot_shift(shifts)
    plot_schematic(active)
    print("Rendered V06a/V06b/V06c d-band-center presentation options.")


if __name__ == "__main__":
    main()
