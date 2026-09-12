from __future__ import annotations

import csv
from pathlib import Path

import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1] / "04_VASP_analysis/electronic_structure_publication_data"


def read(path):
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def read_curve_set(directory, stem):
    combined = directory / (stem + ".tsv")
    paths = [combined] if combined.exists() else sorted(directory.glob(stem + "_*.tsv"))
    result = []
    for path in paths:
        result.extend(read(path))
    return result


def main():
    out = ROOT / "previews"
    out.mkdir(parents=True, exist_ok=True)
    cohp = read_curve_set(ROOT / "COHP/source_data", "cohp_curves")
    pdos = read_curve_set(ROOT / "PDOS/source_data", "pdos_curves")
    states = [("pristine", "*OH"), ("pristine", "*O"), ("Al16", "*OH"), ("Al16", "*O")]
    fig, axes = plt.subplots(2, 2, figsize=(10, 7), sharex=True, sharey=True)
    for ax, (system, state) in zip(axes.flat, states):
        for spin, color in (("up", "#1565c0"), ("down", "#c62828")):
            rs = [r for r in cohp if r["system"] == system and r["state"] == state and r["pair_role"] == "Coact-Oads" and r["spin"] == spin]
            rs.sort(key=lambda r: float(r["energy_eV_rel_EF"]))
            ax.plot([float(r["energy_eV_rel_EF"]) for r in rs], [float(r["minus_pCOHP"]) for r in rs], color=color, lw=0.8, label=spin)
        ax.axvline(0, color="0.2", lw=0.6)
        ax.axhline(0, color="0.6", lw=0.5)
        ax.set_title("%s %s" % (system, state))
        ax.set_xlim(-8, 1.8)
        ax.legend(frameon=False, fontsize=8)
    fig.supxlabel("E - EF (eV)")
    fig.supylabel("-pCOHP (bonding positive)")
    fig.tight_layout()
    fig.savefig(out / "cohp_sanity_preview.png", dpi=180)
    plt.close(fig)

    fig, axes = plt.subplots(2, 2, figsize=(10, 7), sharex=True, sharey=True)
    for ax, (system, state) in zip(axes.flat, states):
        for role, orbital, color in (("Coact", "d", "#1565c0"), ("Oads", "p", "#c62828")):
            rs = [r for r in pdos if r["system"] == system and r["state"] == state and r["site_role"] == role and r["orbital"].startswith(orbital)]
            by_e = {}
            for r in rs:
                by_e.setdefault((float(r["energy_eV_rel_EF"]), r["spin"]), 0.0)
                by_e[(float(r["energy_eV_rel_EF"]), r["spin"])] += float(r["dos"])
            for spin, sign, ls in (("up", 1, "-"), ("down", -1, "--")):
                pts = sorted((e, sign * v) for (e, s), v in by_e.items() if s == spin)
                ax.plot([p[0] for p in pts], [p[1] for p in pts], color=color, ls=ls, lw=0.8, label=role + " " + spin)
        ax.axvline(0, color="0.2", lw=0.6)
        ax.set_title("%s %s" % (system, state))
        ax.set_xlim(-8, 4)
        ax.legend(frameon=False, fontsize=7)
    fig.supxlabel("E - EF (eV)")
    fig.supylabel("PDOS; down mirrored")
    fig.tight_layout()
    fig.savefig(out / "pdos_sanity_preview.png", dpi=180)
    plt.close(fig)


if __name__ == "__main__":
    main()

