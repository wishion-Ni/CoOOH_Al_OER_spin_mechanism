#!/usr/bin/env python3
"""Render publication-oriented COHP/ICOHP and PDOS figures from validated TSVs.

The script intentionally uses only the synchronized, geometry-validated datasets in
04_VASP_analysis/electronic_structure_publication_data.

Main outputs
------------
V01a_COHP_four_state.*
    Spin-summed -pCOHP for Coact-Oads and Coact-Obridge across the four formal states.
V01b_ICOHP_Coact_Oads_summary.*
    Integrated -ICOHP change for the key Coact-Oads bond from *OH to *O.
V02a_PDOS_four_state.*
    Spin-resolved local PDOS (Coact 3d, Oads 2p, Obridge 2p), with spin-down mirrored.

Supplementary outputs
---------------------
V01c_COHP_all_bonds_four_state.*
    Adds neighbor-Obridge to the COHP comparison.
V01d_ICOHP_all_bonds_summary.*
    All validated bond-integrated -ICOHP values.
V02b_PDOS_frontier_zoom.*
    Frontier-region zoom of V02a.

No raw band-index tracking or orbital-symmetry assignment is performed here.
"""

from __future__ import annotations

from pathlib import Path
import csv
import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

ROOT = Path.cwd()
DATA = ROOT / "04_VASP_analysis" / "electronic_structure_publication_data"
OUT = ROOT / "04_VASP_analysis" / "electronic_structure_publication_figures"
FIG = OUT / "figures"
PLOT_READY = OUT / "source_data"
NOTES = OUT / "notes"
for p in (FIG, PLOT_READY, NOTES):
    p.mkdir(parents=True, exist_ok=True)

# Project-wide palette already used in the theory figure packages.
SYSTEM_COLORS = {"pristine": "#374151", "Al16": "#2A9D8F"}
PAIR_COLORS = {
    "Coact-Oads": "#1F5A94",
    "Coact-Obridge": "#D97706",
    "neighbor-Obridge": "#7A7A7A",
}
PDOS_COLORS = {
    "Coact d": "#374151",
    "Oads p": "#C65F2E",
    "Obridge p": "#2A9D8F",
}

STATE_SPECS = [
    ("pristine", "*OH", "pristine_OH", "Pristine *OH"),
    ("pristine", "*O", "pristine_O", "Pristine *O"),
    ("Al16", "*OH", "Al16_OH", "Al-substituted *OH"),
    ("Al16", "*O", "Al16_O", "Al-substituted *O"),
]

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 8.0,
    "axes.labelsize": 8.8,
    "axes.titlesize": 8.7,
    "xtick.labelsize": 7.6,
    "ytick.labelsize": 7.6,
    "legend.fontsize": 7.0,
    "axes.linewidth": 0.9,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "savefig.transparent": False,
})


def style_ax(ax):
    for sp in ax.spines.values():
        sp.set_visible(True)
        sp.set_linewidth(0.9)
    ax.tick_params(direction="out", width=0.8, length=3.0, pad=2.5)
    ax.axhline(0, color="0.55", lw=0.65, zorder=0)
    ax.axvline(0, color="0.35", lw=0.75, ls=(0, (3, 2)), zorder=0)


def save_all(fig, stem: str):
    for ext in ("png", "tif", "pdf", "svg", "eps"):
        kwargs = {"bbox_inches": "tight", "facecolor": "white"}
        if ext in ("png", "tif"):
            kwargs["dpi"] = 600
        fig.savefig(FIG / f"{stem}.{ext}", **kwargs)


def load_cohp(system: str, state: str, shard: str) -> pd.DataFrame:
    p = DATA / "COHP" / "source_data" / f"cohp_curves_{shard}.tsv"
    df = pd.read_csv(p, sep="\t")
    # Strictly use synchronized columns; fail loudly if format changes.
    req = {"system", "state", "pair_role", "energy_eV_rel_EF", "spin", "minus_pCOHP"}
    missing = req - set(df.columns)
    if missing:
        raise RuntimeError(f"Missing COHP columns in {p}: {sorted(missing)}")
    df = df[(df["system"] == system) & (df["state"] == state)].copy()
    return df


def total_cohp(df: pd.DataFrame) -> pd.DataFrame:
    # Sum spin channels at each energy for each validated bond.
    out = (
        df.groupby(["pair_role", "energy_eV_rel_EF"], as_index=False)["minus_pCOHP"]
        .sum()
        .rename(columns={"minus_pCOHP": "minus_pCOHP_total"})
    )
    return out


def plot_cohp_four_state(include_neighbor: bool, stem: str, xlim=(-6.0, 3.0)):
    pair_roles = ["Coact-Oads", "Coact-Obridge"]
    if include_neighbor:
        pair_roles.append("neighbor-Obridge")

    prepared = []
    ymax = 0.0
    for system, state, shard, label in STATE_SPECS:
        t = total_cohp(load_cohp(system, state, shard))
        t = t[t["pair_role"].isin(pair_roles)].copy()
        t = t[(t["energy_eV_rel_EF"] >= xlim[0]) & (t["energy_eV_rel_EF"] <= xlim[1])]
        t["system"] = system
        t["state"] = state
        prepared.append((label, t))
        if len(t):
            ymax = max(ymax, float(np.nanmax(np.abs(t["minus_pCOHP_total"].to_numpy()))))

    combined = pd.concat([x[1] for x in prepared], ignore_index=True)
    combined.to_csv(PLOT_READY / f"{stem}_plot_ready.csv", index=False)
    ylim = max(0.5, 1.08 * ymax)

    fig, axes = plt.subplots(2, 2, figsize=(7.05, 5.15), sharex=True, sharey=True)
    axes = axes.ravel()
    ls = {"Coact-Oads": "-", "Coact-Obridge": "--", "neighbor-Obridge": ":"}
    lw = {"Coact-Oads": 1.45, "Coact-Obridge": 1.15, "neighbor-Obridge": 1.05}
    pretty = {
        "Coact-Oads": r"Co$_{act}$-O$_{ads}$",
        "Coact-Obridge": r"Co$_{act}$-O$_{bridge}$",
        "neighbor-Obridge": r"Neighbor-O$_{bridge}$",
    }

    for ax, (label, d) in zip(axes, prepared):
        for role in pair_roles:
            s = d[d["pair_role"] == role].sort_values("energy_eV_rel_EF")
            ax.plot(
                s["energy_eV_rel_EF"], s["minus_pCOHP_total"],
                color=PAIR_COLORS[role], ls=ls[role], lw=lw[role], label=pretty[role],
            )
        ax.set_title(label, pad=4)
        ax.set_xlim(*xlim)
        ax.set_ylim(-ylim, ylim)
        style_ax(ax)

    axes[2].set_xlabel(r"$E-E_F$ (eV)")
    axes[3].set_xlabel(r"$E-E_F$ (eV)")
    axes[0].set_ylabel(r"$-\mathrm{pCOHP}$")
    axes[2].set_ylabel(r"$-\mathrm{pCOHP}$")
    axes[0].legend(frameon=False, loc="upper left", handlelength=2.5, borderaxespad=0.35)
    fig.tight_layout(pad=0.75, w_pad=0.75, h_pad=0.75)
    save_all(fig, stem)
    plt.close(fig)


def plot_icohp_key_bond():
    p = DATA / "COHP" / "source_data" / "icohp_summary.tsv"
    df = pd.read_csv(p, sep="\t")
    df.to_csv(PLOT_READY / "V01_ICOHP_validated_summary.csv", index=False)
    d = df[df["pair_role"] == "Coact-Oads"].copy()

    fig, ax = plt.subplots(figsize=(3.55, 3.05))
    x = np.arange(2, dtype=float)
    width = 0.32
    state_order = ["*OH", "*O"]
    state_hatch = {"*OH": "", "*O": "//"}

    for i, system in enumerate(["pristine", "Al16"]):
        vals = []
        for state in state_order:
            row = d[(d["system"] == system) & (d["state"] == state)]
            if len(row) != 1:
                raise RuntimeError(f"Expected one ICOHP row for {system} {state} Coact-Oads")
            vals.append(float(row.iloc[0]["minus_ICOHP_total_eV"]))
        offs = (-width/2 if i == 0 else width/2)
        bars = ax.bar(
            x + offs, vals, width=width * 0.92,
            color=SYSTEM_COLORS[system], alpha=0.9,
            label=("Pristine" if system == "pristine" else "Al-substituted"),
            edgecolor="white", linewidth=0.55,
        )
        for j, b in enumerate(bars):
            if state_order[j] == "*O":
                b.set_hatch("//")
            ax.text(b.get_x()+b.get_width()/2, b.get_height()+0.055, f"{vals[j]:.2f}",
                    ha="center", va="bottom", fontsize=6.8)
        delta = vals[1] - vals[0]
        xpos = x[1] + offs
        ax.text(xpos, max(vals) + 0.35, f"Δ={delta:+.2f}", ha="center", va="bottom",
                fontsize=6.8, color=SYSTEM_COLORS[system])

    ax.set_xticks(x, ["*OH", "*O"])
    ax.set_ylabel(r"$-\mathrm{ICOHP}$ (eV)")
    ax.set_ylim(0, max(3.9, float(d["minus_ICOHP_total_eV"].max()) + 0.7))
    for sp in ax.spines.values():
        sp.set_visible(True); sp.set_linewidth(0.9)
    ax.tick_params(direction="out", width=0.8, length=3)
    ax.legend(frameon=False, loc="upper left", handlelength=1.4)
    fig.tight_layout(pad=0.55)
    save_all(fig, "V01b_ICOHP_Coact_Oads_summary")
    plt.close(fig)


def plot_icohp_all_bonds():
    p = DATA / "COHP" / "source_data" / "icohp_summary.tsv"
    df = pd.read_csv(p, sep="\t")
    roles = ["Coact-Oads", "Coact-Obridge", "neighbor-Obridge"]
    labels = [r"Co$_{act}$-O$_{ads}$", r"Co$_{act}$-O$_{bridge}$", r"Neighbor-O$_{bridge}$"]
    x = np.arange(len(roles), dtype=float)
    fig, ax = plt.subplots(figsize=(4.35, 3.0))
    sys_off = {"pristine": -0.16, "Al16": 0.16}
    state_off = {"*OH": -0.045, "*O": 0.045}

    for i, role in enumerate(roles):
        for system in ["pristine", "Al16"]:
            xx, yy = [], []
            for state in ["*OH", "*O"]:
                row = df[(df["pair_role"] == role) & (df["system"] == system) & (df["state"] == state)]
                if len(row) != 1:
                    continue
                xv = x[i] + sys_off[system] + state_off[state]
                yv = float(row.iloc[0]["minus_ICOHP_total_eV"])
                xx.append(xv); yy.append(yv)
                if state == "*OH":
                    ax.scatter(xv, yv, s=29, facecolors="white", edgecolors=SYSTEM_COLORS[system], linewidth=1.05, zorder=3)
                else:
                    ax.scatter(xv, yv, s=29, color=SYSTEM_COLORS[system], edgecolor="white", linewidth=0.45, zorder=3)
            if len(xx) == 2:
                ax.plot(xx, yy, color=SYSTEM_COLORS[system], lw=1.15, zorder=2)

    ax.set_xticks(x, labels)
    ax.set_ylabel(r"$-\mathrm{ICOHP}$ (eV)")
    ax.set_ylim(0.85, 3.95)
    for sp in ax.spines.values():
        sp.set_visible(True); sp.set_linewidth(0.9)
    ax.tick_params(direction="out", width=0.8, length=3)
    handles = [
        Line2D([0], [0], color=SYSTEM_COLORS["pristine"], lw=2, label="Pristine"),
        Line2D([0], [0], color=SYSTEM_COLORS["Al16"], lw=2, label="Al-substituted"),
        Line2D([0], [0], marker="o", color="0.45", markerfacecolor="white", lw=0, markersize=4.8, label="*OH"),
        Line2D([0], [0], marker="s", color="none", markerfacecolor="0.45", lw=0, markersize=4.8, label="*O"),
    ]
    ax.legend(handles=handles, frameon=False, loc="upper left", handlelength=1.4, labelspacing=0.3)
    fig.tight_layout(pad=0.55)
    save_all(fig, "V01d_ICOHP_all_bonds_summary")
    plt.close(fig)


def load_pdos(system: str, state: str, shard: str) -> pd.DataFrame:
    p = DATA / "PDOS" / "source_data" / f"pdos_curves_{shard}.tsv"
    df = pd.read_csv(p, sep="\t")
    req = {"system", "state", "energy_eV_rel_EF", "spin", "site_role", "orbital", "dos"}
    missing = req - set(df.columns)
    if missing:
        raise RuntimeError(f"Missing PDOS columns in {p}: {sorted(missing)}")
    return df[(df["system"] == system) & (df["state"] == state)].copy()


def aggregate_local_pdos(df: pd.DataFrame) -> pd.DataFrame:
    pieces = []
    specs = [
        ("Coact", lambda s: s.astype(str).str.startswith("d"), "Coact d"),
        ("Oads", lambda s: s.astype(str).str.startswith("p"), "Oads p"),
        ("Obridge", lambda s: s.astype(str).str.startswith("p"), "Obridge p"),
    ]
    for role, orbital_filter, out_label in specs:
        sub = df[(df["site_role"] == role) & orbital_filter(df["orbital"])].copy()
        agg = sub.groupby(["energy_eV_rel_EF", "spin"], as_index=False)["dos"].sum()
        agg["projection"] = out_label
        pieces.append(agg)
    out = pd.concat(pieces, ignore_index=True)
    return out


def plot_pdos_four_state(stem: str, xlim=(-6.0, 3.0)):
    prepared = []
    ymax = 0.0
    for system, state, shard, label in STATE_SPECS:
        a = aggregate_local_pdos(load_pdos(system, state, shard))
        a = a[(a["energy_eV_rel_EF"] >= xlim[0]) & (a["energy_eV_rel_EF"] <= xlim[1])].copy()
        a["system"] = system
        a["state"] = state
        prepared.append((label, a))
        if len(a):
            ymax = max(ymax, float(np.nanmax(np.abs(a["dos"].to_numpy()))))

    combined = pd.concat([x[1] for x in prepared], ignore_index=True)
    combined.to_csv(PLOT_READY / f"{stem}_plot_ready.csv", index=False)
    ylim = max(0.5, 1.08 * ymax)

    fig, axes = plt.subplots(2, 2, figsize=(7.05, 5.15), sharex=True, sharey=True)
    axes = axes.ravel()
    projections = ["Coact d", "Oads p", "Obridge p"]

    for ax, (label, d) in zip(axes, prepared):
        for proj in projections:
            for spin, ls in [("up", "-"), ("down", "--")]:
                s = d[(d["projection"] == proj) & (d["spin"] == spin)].sort_values("energy_eV_rel_EF")
                y = s["dos"].to_numpy(dtype=float)
                if spin == "down":
                    y = -y
                ax.plot(s["energy_eV_rel_EF"], y, color=PDOS_COLORS[proj], lw=1.15 if spin == "up" else 1.0,
                        ls=ls, alpha=0.98)
        ax.set_title(label, pad=4)
        ax.set_xlim(*xlim)
        ax.set_ylim(-ylim, ylim)
        style_ax(ax)

    axes[2].set_xlabel(r"$E-E_F$ (eV)")
    axes[3].set_xlabel(r"$E-E_F$ (eV)")
    axes[0].set_ylabel("PDOS (states/eV)")
    axes[2].set_ylabel("PDOS (states/eV)")
    handles = [
        Line2D([0], [0], color=PDOS_COLORS[p], lw=1.5, label=p) for p in projections
    ] + [
        Line2D([0], [0], color="0.35", lw=1.2, ls="-", label="spin up"),
        Line2D([0], [0], color="0.35", lw=1.2, ls="--", label="spin down (mirrored)"),
    ]
    axes[0].legend(handles=handles, frameon=False, loc="upper left", handlelength=2.2, borderaxespad=0.35)
    fig.tight_layout(pad=0.75, w_pad=0.75, h_pad=0.75)
    save_all(fig, stem)
    plt.close(fig)


def write_notes():
    text = """# COHP / PDOS publication-figure notes

## Dataset status

All curves are generated from the synchronized four-state package and validated geometry mapping.
The COHP panels use only distance-validated pairs from the current structures.

LOBSTER quality in the synchronized records has absolute charge spilling below 2% in both spin
channels for all four states. The pristine *OH run also reports a 1-of-8 k-point orthonormalization
warning; it should be disclosed in the methods/SI and checked against `bandOverlaps.lobster` if a
more quantitative claim depends on fine spectral detail.

## Figure interpretation

- `V01a`: spin-summed -pCOHP; positive values denote bonding contributions and negative values
  antibonding contributions. The main panel deliberately emphasizes Coact-Oads and Coact-Obridge.
- `V01b`: integrated -ICOHP for Coact-Oads. It quantifies the occupied bond-strengthening response
  on going from *OH to *O but is not a reaction free energy or barrier.
- `V01c/V01d`: supplementary all-bond context including neighbor-Obridge. In Al16 the neighbor bond
  is Al-Obridge, so its magnitude should not be compared as though it were the same chemical bond as
  neighboring Co-Obridge in pristine CoOOH.
- `V02a/V02b`: local PDOS only. Coact 3d and O 2p components are summed over their component
  orbitals. Spin-down is mirrored solely for visualization. Do not infer formal oxidation states from
  PDOS peak areas alone.

## Mechanistic boundary

These figures support changes in Co-O covalency and O-rich frontier-state participation. They do not
by themselves establish an exact emitted-electron spin, a unique raw-band correspondence across
structures, an integer high-spin/low-spin transition, or a formal oxidation-state assignment.
"""
    (NOTES / "figure_note.md").write_text(text, encoding="utf-8")

    cap = """# Suggested captions

**V01a | Bond-resolved COHP across the *OH -> *O conversion.** Spin-summed -pCOHP for the
geometry-validated Coact-Oads and Coact-Obridge pairs in pristine and Al-substituted CoOOH. The
Fermi level is set to 0 eV; positive -pCOHP denotes bonding and negative -pCOHP antibonding
contributions.

**V01b | Integrated Coact-Oads bonding response.** Integrated -ICOHP of the active Co-Oads bond
for *OH and *O. The *OH -> *O increase is larger in pristine CoOOH than in Al-substituted CoOOH,
consistent with a stronger occupied-bond rehybridization response at the pristine active Co site.

**V02a | Local spin-resolved PDOS across *OH -> *O.** Projected density of states of Coact 3d,
adsorbate O 2p, and bridging O 2p states in pristine and Al-substituted CoOOH. Spin-down components
are mirrored for visualization and all energies are referenced to the Fermi level.
"""
    (NOTES / "suggested_captions.md").write_text(cap, encoding="utf-8")


def main():
    plot_cohp_four_state(False, "V01a_COHP_four_state")
    plot_icohp_key_bond()
    plot_cohp_four_state(True, "V01c_COHP_all_bonds_four_state")
    plot_icohp_all_bonds()
    plot_pdos_four_state("V02a_PDOS_four_state", (-6.0, 3.0))
    plot_pdos_four_state("V02b_PDOS_frontier_zoom", (-2.5, 1.0))
    write_notes()
    print(f"Rendered publication figures to {FIG}")


if __name__ == "__main__":
    main()
