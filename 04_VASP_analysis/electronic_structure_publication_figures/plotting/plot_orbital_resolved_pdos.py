#!/usr/bin/env python3
"""Orbital-resolved PDOS component analysis for the validated four-state OER dataset.

This script adds a second-layer electronic-structure analysis on top of the publication
PDOS overview. It deliberately favors physically traceable component extraction over
arbitrary multi-Gaussian peak fitting.

Outputs
-------
V03a_Coact_d_orbital_resolved.*
    Coact dxy, dyz, dz2, dxz, dx2-y2 PDOS in the frontier region; spin-down mirrored.
V03b_Oads_p_orbital_resolved.*
    Oads px, py, pz PDOS in the frontier region; spin-down mirrored.
V03c_OH_to_O_difference_PDOS.*
    EF-aligned spin-summed spectral difference, PDOS(*O)-PDOS(*OH), for Coact d,
    Oads p and Obridge p.
V03d_frontier_integrated_delta_weights.*
    Change in integrated local PDOS spectral weight across three frontier windows.

Tables
------
V03_frontier_integrated_weights.csv
V03_frontier_component_integrals.csv
V03_frontier_peak_candidates.csv

Interpretation boundaries are written to notes/V03_interpretation_note.md.
"""

from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

ROOT = Path.cwd()
DATA = ROOT / "04_VASP_analysis" / "electronic_structure_publication_data" / "PDOS" / "source_data"
OUT = ROOT / "04_VASP_analysis" / "electronic_structure_publication_figures"
FIG = OUT / "figures"
SRC = OUT / "source_data"
NOTES = OUT / "notes"
for p in (FIG, SRC, NOTES):
    p.mkdir(parents=True, exist_ok=True)

STATE_SPECS = [
    ("pristine", "*OH", "pristine_OH", "Pristine *OH"),
    ("pristine", "*O", "pristine_O", "Pristine *O"),
    ("Al16", "*OH", "Al16_OH", "Al-substituted *OH"),
    ("Al16", "*O", "Al16_O", "Al-substituted *O"),
]

SYSTEM_COLORS = {"pristine": "#374151", "Al16": "#2A9D8F"}
D_ORDER = ["dxy", "dyz", "dz2", "dxz", "dx2-y2"]
D_LABELS = {
    "dxy": r"$d_{xy}$",
    "dyz": r"$d_{yz}$",
    "dz2": r"$d_{z^2}$",
    "dxz": r"$d_{xz}$",
    "dx2-y2": r"$d_{x^2-y^2}$",
}
D_COLORS = {
    "dxy": "#4C78A8",
    "dyz": "#72B7B2",
    "dz2": "#F58518",
    "dxz": "#B279A2",
    "dx2-y2": "#E45756",
}
P_ORDER = ["px", "py", "pz"]
P_LABELS = {"px": r"$p_x$", "py": r"$p_y$", "pz": r"$p_z$"}
P_COLORS = {"px": "#4C78A8", "py": "#F58518", "pz": "#54A24B"}
ROLE_COLORS = {"Coact": "#374151", "Oads": "#C65F2E", "Obridge": "#2A9D8F"}
ROLE_LABELS = {"Coact": r"Co$_{act}$ 3d", "Oads": r"O$_{ads}$ 2p", "Obridge": r"O$_{bridge}$ 2p"}

FRONTIER_XLIM = (-2.5, 1.2)
WINDOWS = [(-2.0, 0.0, "occupied -2 to 0 eV"), (-1.0, 0.0, "near-EF -1 to 0 eV"), (0.0, 1.0, "unoccupied 0 to 1 eV")]

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 8.0,
    "axes.labelsize": 8.8,
    "axes.titlesize": 8.7,
    "xtick.labelsize": 7.5,
    "ytick.labelsize": 7.5,
    "legend.fontsize": 6.7,
    "axes.linewidth": 0.9,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "savefig.transparent": False,
})


def save_all(fig, stem: str):
    for ext, kw in [
        ("png", {"dpi": 600}),
        ("tif", {"dpi": 600}),
        ("pdf", {}),
        ("svg", {}),
        ("eps", {}),
    ]:
        fig.savefig(FIG / f"{stem}.{ext}", bbox_inches="tight", facecolor="white", **kw)


def style_panel(ax, xlim=FRONTIER_XLIM):
    for sp in ax.spines.values():
        sp.set_visible(True)
        sp.set_linewidth(0.9)
    ax.tick_params(direction="out", width=0.8, length=3.0, pad=2.5)
    ax.axhline(0, color="0.55", lw=0.65, zorder=0)
    ax.axvline(0, color="0.30", lw=0.75, ls=(0, (3, 2)), zorder=0)
    ax.set_xlim(*xlim)


def load_data() -> pd.DataFrame:
    dfs = []
    for system, state, key, _ in STATE_SPECS:
        fn = DATA / f"pdos_curves_{key}.tsv"
        if not fn.exists():
            raise FileNotFoundError(fn)
        d = pd.read_csv(fn, sep="\t")
        dfs.append(d)
    df = pd.concat(dfs, ignore_index=True)
    df["energy_eV_rel_EF"] = pd.to_numeric(df["energy_eV_rel_EF"], errors="coerce")
    df["dos"] = pd.to_numeric(df["dos"], errors="coerce")
    return df.dropna(subset=["energy_eV_rel_EF", "dos"])


def panel_subset(df, system, state, role, orbitals):
    return df[(df.system == system) & (df.state == state) & (df.site_role == role) & (df.orbital.isin(orbitals))].copy()


def mirrored_ylim(df, role, orbitals, xlim):
    q = df[(df.site_role == role) & (df.orbital.isin(orbitals)) & df.energy_eV_rel_EF.between(*xlim)].copy()
    if q.empty:
        return 1.0
    # Robust upper bound so a single numerical spike does not flatten every panel.
    vals = np.abs(q.dos.to_numpy(float))
    y = float(np.nanpercentile(vals, 99.7))
    return max(0.2, 1.18 * y)


def plot_orbital_panels(df, role, orbitals, labels, colors, stem, ylabel):
    fig, axes = plt.subplots(2, 2, figsize=(7.15, 5.15), sharex=True, sharey=True)
    ylim = mirrored_ylim(df, role, orbitals, FRONTIER_XLIM)
    for ax, (system, state, _, title) in zip(axes.flat, STATE_SPECS):
        sub = panel_subset(df, system, state, role, orbitals)
        for orb in orbitals:
            for spin, sign in [("up", 1.0), ("down", -1.0)]:
                s = sub[(sub.orbital == orb) & (sub.spin == spin)].sort_values("energy_eV_rel_EF")
                if s.empty:
                    continue
                ax.plot(s.energy_eV_rel_EF, sign * s.dos, color=colors[orb], lw=1.25)
        style_panel(ax)
        ax.set_ylim(-ylim, ylim)
        ax.text(0.035, 0.94, title, transform=ax.transAxes, ha="left", va="top", fontsize=8.5, fontweight="semibold")
    for ax in axes[1, :]:
        ax.set_xlabel(r"$E-E_F$ (eV)")
    for ax in axes[:, 0]:
        ax.set_ylabel(ylabel)
    handles = [Line2D([0], [0], color=colors[o], lw=1.8, label=labels[o]) for o in orbitals]
    handles += [Line2D([0], [0], color="0.2", lw=1.2, label=r"spin $\uparrow$ above / $\downarrow$ mirrored")]
    axes[0, 0].legend(handles=handles, frameon=False, loc="lower left", ncol=2, columnspacing=0.9, handlelength=1.7)
    fig.tight_layout(pad=0.7, w_pad=0.75, h_pad=0.8)
    save_all(fig, stem)
    plt.close(fig)


def summed_spectrum(df, system, state, role):
    q = df[(df.system == system) & (df.state == state) & (df.site_role == role)].copy()
    # Only the mechanism-relevant shell for each role.
    if role == "Coact":
        q = q[q.orbital.isin(D_ORDER)]
    elif role in ("Oads", "Obridge"):
        q = q[q.orbital.isin(P_ORDER)]
    g = q.groupby("energy_eV_rel_EF", as_index=False)["dos"].sum().sort_values("energy_eV_rel_EF")
    return g.energy_eV_rel_EF.to_numpy(float), g.dos.to_numpy(float)


def common_difference(df, system, role):
    e_oh, y_oh = summed_spectrum(df, system, "*OH", role)
    e_o, y_o = summed_spectrum(df, system, "*O", role)
    lo = max(e_oh.min(), e_o.min(), FRONTIER_XLIM[0])
    hi = min(e_oh.max(), e_o.max(), FRONTIER_XLIM[1])
    grid = np.linspace(lo, hi, 900)
    oh = np.interp(grid, e_oh, y_oh)
    oo = np.interp(grid, e_o, y_o)
    return grid, oo - oh


def plot_difference(df):
    fig, axes = plt.subplots(1, 2, figsize=(7.15, 3.0), sharex=True, sharey=True)
    for ax, system, title in zip(axes, ["pristine", "Al16"], ["Pristine", "Al-substituted"]):
        for role in ["Coact", "Oads", "Obridge"]:
            e, dy = common_difference(df, system, role)
            ax.plot(e, dy, color=ROLE_COLORS[role], lw=1.45, label=ROLE_LABELS[role])
        style_panel(ax)
        ax.text(0.035, 0.94, title, transform=ax.transAxes, ha="left", va="top", fontsize=8.5, fontweight="semibold")
        ax.set_xlabel(r"$E-E_F$ (eV)")
    axes[0].set_ylabel(r"$\Delta$PDOS = PDOS$_{*O}$ - PDOS$_{*OH}$")
    axes[0].legend(frameon=False, loc="upper left", bbox_to_anchor=(0.0, 0.87), handlelength=1.8)
    fig.tight_layout(pad=0.65, w_pad=0.8)
    save_all(fig, "V03c_OH_to_O_difference_PDOS")
    plt.close(fig)


def integrate_spectrum(e, y, lo, hi):
    mask = (e >= lo) & (e <= hi)
    if mask.sum() < 2:
        return np.nan
    return float(np.trapezoid(y[mask], e[mask]))


def integration_tables(df):
    rows = []
    comp_rows = []
    for system, state, _, _ in STATE_SPECS:
        for role in ["Coact", "Oads", "Obridge"]:
            e, y = summed_spectrum(df, system, state, role)
            for lo, hi, wname in WINDOWS:
                rows.append({
                    "system": system, "state": state, "site_role": role,
                    "window": wname, "Emin_eV": lo, "Emax_eV": hi,
                    "integrated_PDOS": integrate_spectrum(e, y, lo, hi),
                })
        for role, orbitals in [("Coact", D_ORDER), ("Oads", P_ORDER)]:
            for orb in orbitals:
                for spin in ["up", "down"]:
                    q = df[(df.system == system) & (df.state == state) & (df.site_role == role) & (df.orbital == orb) & (df.spin == spin)].sort_values("energy_eV_rel_EF")
                    if q.empty:
                        continue
                    e = q.energy_eV_rel_EF.to_numpy(float)
                    y = q.dos.to_numpy(float)
                    for lo, hi, wname in WINDOWS:
                        comp_rows.append({
                            "system": system, "state": state, "site_role": role,
                            "orbital": orb, "spin": spin, "window": wname,
                            "Emin_eV": lo, "Emax_eV": hi,
                            "integrated_PDOS": integrate_spectrum(e, y, lo, hi),
                        })
    sums = pd.DataFrame(rows)
    comps = pd.DataFrame(comp_rows)
    sums.to_csv(SRC / "V03_frontier_integrated_weights.csv", index=False)
    comps.to_csv(SRC / "V03_frontier_component_integrals.csv", index=False)
    return sums, comps


def plot_delta_integrals(sums):
    roles = ["Coact", "Oads", "Obridge"]
    systems = ["pristine", "Al16"]
    labels = [ROLE_LABELS[r] for r in roles]
    fig, axes = plt.subplots(1, 3, figsize=(7.45, 2.75), sharey=False)
    x = np.arange(len(roles))
    width = 0.34
    for ax, (_, _, wname) in zip(axes, WINDOWS):
        for i, system in enumerate(systems):
            vals = []
            for role in roles:
                o = sums[(sums.system == system) & (sums.state == "*O") & (sums.site_role == role) & (sums.window == wname)].integrated_PDOS.iloc[0]
                oh = sums[(sums.system == system) & (sums.state == "*OH") & (sums.site_role == role) & (sums.window == wname)].integrated_PDOS.iloc[0]
                vals.append(o - oh)
            ax.bar(x + (i - 0.5) * width, vals, width=width, color=SYSTEM_COLORS[system], alpha=0.92, edgecolor="white", linewidth=0.5)
        ax.axhline(0, color="0.35", lw=0.75)
        for sp in ax.spines.values():
            sp.set_visible(True); sp.set_linewidth(0.9)
        ax.tick_params(direction="out", width=0.8, length=3.0, pad=2.5)
        ax.set_xticks(x, labels, rotation=27, ha="right")
        ax.set_title(wname, pad=4)
    axes[0].set_ylabel(r"$\Delta$ integrated PDOS (*O - *OH)")
    handles = [
        Line2D([0], [0], color=SYSTEM_COLORS["pristine"], lw=5, label="Pristine"),
        Line2D([0], [0], color=SYSTEM_COLORS["Al16"], lw=5, label="Al-substituted"),
    ]
    axes[0].legend(handles=handles, frameon=False, loc="best")
    fig.tight_layout(pad=0.7, w_pad=0.75)
    save_all(fig, "V03d_frontier_integrated_delta_weights")
    plt.close(fig)


def peak_candidates(df):
    rows = []
    for system, state, _, _ in STATE_SPECS:
        for role, orbitals in [("Coact", D_ORDER), ("Oads", P_ORDER)]:
            for orb in orbitals:
                for spin in ["up", "down"]:
                    q = df[(df.system == system) & (df.state == state) & (df.site_role == role) & (df.orbital == orb) & (df.spin == spin) & df.energy_eV_rel_EF.between(-2.5, 1.0)].sort_values("energy_eV_rel_EF")
                    if len(q) < 3:
                        continue
                    e = q.energy_eV_rel_EF.to_numpy(float)
                    y = q.dos.to_numpy(float)
                    # Numerical local maxima only; no Gaussian/Lorentzian fit is implied.
                    idx = np.where((y[1:-1] > y[:-2]) & (y[1:-1] >= y[2:]))[0] + 1
                    if idx.size == 0:
                        continue
                    floor = max(0.03, 0.08 * float(np.nanmax(y)))
                    idx = [i for i in idx if y[i] >= floor]
                    idx = sorted(idx, key=lambda i: y[i], reverse=True)[:3]
                    for rank, i in enumerate(idx, start=1):
                        rows.append({
                            "system": system, "state": state, "site_role": role,
                            "orbital": orb, "spin": spin, "rank_by_height": rank,
                            "peak_energy_eV_rel_EF": e[i], "peak_PDOS": y[i],
                            "method": "discrete local-maximum candidate; no peak-shape fit",
                        })
    out = pd.DataFrame(rows)
    out.to_csv(SRC / "V03_frontier_peak_candidates.csv", index=False)
    return out


def write_note():
    text = """# V03 orbital-resolved PDOS interpretation note

## What these plots establish

- V03a resolves the active-Co 3d projection into the five VASP Cartesian d components.
- V03b resolves the adsorbate-O 2p projection into Cartesian px/py/pz components.
- V03c compares the spectral redistribution from *OH to *O after aligning each state's spectrum to its own Fermi level.
- V03d quantifies changes in integrated local PDOS spectral weight in selected frontier-energy windows.
- `V03_frontier_peak_candidates.csv` is an automated local-maximum inventory for inspection; it is **not** a multi-Gaussian fit and individual numerical peaks are not automatically distinct physical quasiparticle states.

## Required interpretation boundaries

1. The labels dxy/dyz/dz2/dxz/dx2-y2 and px/py/pz are the Cartesian projector components supplied by the VASP DOS output. The local Co-O coordination axes are not explicitly rotated here. Therefore do **not** make strict eg/t2g or sigma/pi assignments from these labels alone.
2. V03c is an EF-aligned **spectral difference**, not a charge-density-difference map and not a conserved electron-transfer density.
3. Integrated PDOS spectral weight is not equivalent to Bader/Hirshfeld charge or an exact orbital occupation number.
4. Because the *OH and *O calculations correspond to different electron counts and selected global spin states, the plots describe the electronic structure of the selected states; they do not independently prove the kinetic route by which the system reaches the *O spin branch.
5. Tiny negative projected-DOS values, when present, are retained rather than silently clipped; they should be treated as projection/numerical artifacts unless independently validated.
6. For the mechanism narrative, emphasize robust redistribution between Co-centered and O-centered frontier character. Exact orbital-symmetry claims require an explicit local-axis/orbital analysis.
"""
    (NOTES / "V03_interpretation_note.md").write_text(text, encoding="utf-8")


def main():
    df = load_data()
    plot_orbital_panels(
        df, "Coact", D_ORDER, D_LABELS, D_COLORS,
        "V03a_Coact_d_orbital_resolved", r"Co$_{act}$ orbital PDOS"
    )
    plot_orbital_panels(
        df, "Oads", P_ORDER, P_LABELS, P_COLORS,
        "V03b_Oads_p_orbital_resolved", r"O$_{ads}$ orbital PDOS"
    )
    plot_difference(df)
    sums, comps = integration_tables(df)
    plot_delta_integrals(sums)
    peak_candidates(df)
    write_note()
    print("Rendered V03 orbital-resolved PDOS analysis.")


if __name__ == "__main__":
    main()
