from __future__ import annotations

from pathlib import Path
import csv

import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from mpl_toolkits.axes_grid1.inset_locator import inset_axes

from plot_diff_density_subfigures import (
    BASE,
    CASES,
    read_field,
    read_overlay,
    save_figure,
    style_axis,
)


ANNOTATIONS = {
    "charge_density": {
        "legend": "cDFT-Hirshfeld ΔN",
        "values": {
            "pristine": {"Co(act)": "+0.219 e", "Oads": "−0.464 e"},
            "Al16": {"Co(act)": "+0.012 e", "Oads": "−0.427 e"},
        },
        "color": "#D55E00",
    },
    "magnetization": {
        "legend": "cDFT-Hirshfeld Δm",
        "values": {
            "pristine": {"Co(act)": "−0.821 μB", "Oads": "−0.070 μB"},
            "Al16": {"Co(act)": "−0.448 μB", "Oads": "−0.744 μB"},
        },
        "color": "#0072B2",
    },
    "spin_up": {
        "legend": "LOBSTER Oads 2p ΔN↑",
        "values": {
            "pristine": {"Oads": "+0.160 e"},
            "Al16": {"Oads": "+0.220 e"},
        },
        "color": "#D55E00",
    },
    "spin_down": {
        "legend": "LOBSTER Oads 2p ΔN↓",
        "values": {
            "pristine": {"Oads": "−0.660 e"},
            "Al16": {"Oads": "−0.680 e"},
        },
        "color": "#0072B2",
    },
}


def load_annotations():
    source = Path('artifacts/mechanism_validation_bundle/03_cp2k_spin_resolved_changes.tsv')
    columns = dict(charge_density='delta_N_total', magnetization='delta_spin_muB',
                   spin_up='delta_N_up', spin_down='delta_N_down')
    with source.open(encoding='utf-8', newline='') as handle:
        data = [row for row in csv.DictReader(handle, delimiter='\t')
                if row['method_partition'] == 'Hirshfeld']
    assert len(data) == 8
    for name, column in columns.items():
        config = ANNOTATIONS[name]
        config['values'] = {'pristine': {}, 'Al16': {}}
        for row in data:
            role = {'Coact': 'Co(act)', 'Oads': 'Oads', 'Obridge': 'Obridge',
                    'neighbor': 'Al' if row['system'] == 'Al16' else 'Co(adj)'}[row['atom_role']]
            unit = 'μB' if name == 'magnetization' else 'e'
            config['values'][row['system']][role] = f"{float(row[column]):+.3f} {unit}".replace('-', '−')
    return source


def add_evidence(ax, system, points, map_name):
    config = ANNOTATIONS[map_name]
    for previous in list(ax.texts):
        previous.remove()
    offsets = {
        "Co(act)": (0, 9),
        "Oads": (0, -10),
        "Obridge": (0, 9),
        "Co(adj)": (0, -10),
        "Al": (0, -10),
    }
    names = {'Co(act)': r'Co$_{act}$', 'Oads': r'O$_{ads}$',
             'Obridge': r'O$_{br}$', 'Co(adj)': r'Co$_{adj}$', 'Al': 'Al'}
    for label, value in config["values"][system].items():
        x, y, _ = points[label]
        text = ax.annotate(
            names[label] + '\n' + value,
            (x, y),
            xytext=offsets[label],
            textcoords="offset points",
            ha="center",
            va="bottom" if offsets[label][1] > 0 else "top",
            fontsize=7.2,
            color=config["color"],
            zorder=11,
        )
        text.set_path_effects([pe.withStroke(linewidth=2.3, foreground="white")])



def render_pair(fig, axes, overlay, map_name, map_spec):
    loaded = [(system, case_name, label, *read_field(map_name, case_name)) for system, case_name, label in CASES]
    image = None
    for ax, (system, case_name, label, x, y, field) in zip(axes, loaded):
        image = style_axis(
            ax,
            x,
            y,
            field,
            map_spec[1],
            map_spec[3],
            map_spec[4],
            map_spec[5],
            overlay[system],
            label,
        )
        add_evidence(ax, system, overlay[system], map_name)
    return image


def main():
    source = load_annotations()
    overlay = read_overlay()
    map_specs = {
        "charge_density": ("charge_density", "Charge density difference", r"$\Delta\rho$", "e Å$^{-3}$", 0.050, "RdBu_r"),
        "magnetization": ("magnetization", "Magnetization difference", r"$\Delta m$", "μ$_B$ Å$^{-3}$", 0.080, "PuOr"),
        "spin_up": ("spin_up", "Spin-up density difference", r"$\Delta\rho_\uparrow$", "e Å$^{-3}$", 0.050, "RdBu_r"),
        "spin_down": ("spin_down", "Spin-down density difference", r"$\Delta\rho_\downarrow$", "e Å$^{-3}$", 0.050, "RdBu_r"),
    }
    out_dir = Path("artifacts/diff_density_four_atom_preview_20260915")
    out_dir.mkdir(parents=True, exist_ok=True)
    with (out_dir / 'annotation_provenance.txt').open('w', encoding='utf-8') as handle:
        handle.write(f'Atomic labels: CP2K cDFT baseline Hirshfeld populations from {source}.\n'
                     'All differences: O minus OH. Positive delta N means electron gain.\n'
                     'Background: VASP reaction-density maps; atomic labels are a separate CP2K analysis, not integrals of the displayed VASP field.\n'
                     'Spin channels retain the source convention; no cross-code spin-axis alignment is claimed.\n'
                     'Source rounding can cause up/down sum or difference residuals up to 0.001 electron or muB.\n')

    contact, axes = plt.subplots(4, 2, figsize=(8.6, 13.6), dpi=200, sharex=False, sharey=False)
    for row, map_name in zip(axes, map_specs):
        render_pair(contact, list(row), overlay, map_name, map_specs[map_name])
        row[0].set_title(map_specs[map_name][2], loc="left", fontsize=8.4, weight="bold", pad=4)
        row[1].set_title(map_specs[map_name][2], loc="left", fontsize=8.4, weight="bold", pad=4)
        for ax in row:
            ax.set_box_aspect(0.56)
    contact.subplots_adjust(left=0.07, right=0.94, bottom=0.05, top=0.97, wspace=0.36, hspace=0.42)
    contact.savefig(out_dir / "four_map_contact_sheet.png", dpi=600, bbox_inches="tight", facecolor="white")
    contact.savefig(out_dir / "four_map_contact_sheet.pdf", bbox_inches="tight", facecolor="white")
    plt.close(contact)

    for map_name, map_spec in map_specs.items():
        paired, pair_axes = plt.subplots(1, 2, figsize=(7.2, 3.95), dpi=200, sharex=True, sharey=True, gridspec_kw={"wspace": 0.08})
        image = render_pair(paired, pair_axes, overlay, map_name, map_spec)
        cax = inset_axes(pair_axes[1], width="3.8%", height="86%", loc="center left", bbox_to_anchor=(1.04, 0.0, 1.0, 1.0), bbox_transform=pair_axes[1].transAxes, borderpad=0)
        cbar = paired.colorbar(image, cax=cax)
        limit = map_spec[4]
        cbar.set_ticks([-limit, 0.0, limit])
        cbar.ax.tick_params(labelsize=8.0, length=3)
        cbar.set_label(map_spec[3], fontsize=8.8, labelpad=5)
        paired.subplots_adjust(left=0.075, right=0.86, bottom=0.13, top=0.99)
        save_figure(paired, out_dir / f"{map_name}_difference_with_evidence")

    print(out_dir)


if __name__ == "__main__":
    main()
