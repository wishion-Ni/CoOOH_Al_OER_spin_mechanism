from __future__ import annotations

import csv
import hashlib
import struct
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import TwoSlopeNorm
from scipy.ndimage import map_coordinates


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "artifacts/reaction_density_final_20260901"
BASE = ROOT / "04_VASP_analysis/diff_density_publication_data"

CASES = {
    "undoped_control": {
        "system": "pristine",
        "label": "Undoped CoOOH",
        "active_co": 21,
        "active_o": 347,
        "bridge_o": 258,
        "neighbor": 23,
        "neighbor_label": "Co(adj)",
    },
    "Al16_adjacent": {
        "system": "Al16",
        "label": "Al16-substituted CoOOH",
        "active_co": 16,
        "active_o": 347,
        "bridge_o": 258,
        "neighbor": 51,
        "neighbor_label": "Al",
    },
}

MAPS = {
    "charge_density": ("charge_diff", "e Angstrom^-3", "Charge density difference"),
    "magnetization": ("magnetization_diff", "mu_B Angstrom^-3", "Magnetization difference"),
    "spin_up": ("spin_up_diff", "e Angstrom^-3", "Spin-up density difference"),
    "spin_down": ("spin_down_diff", "e Angstrom^-3", "Spin-down density difference"),
}


def read_poscar(path):
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    scale = float(lines[1].split()[0])
    lattice = np.array([[float(x) for x in lines[row].split()[:3]] for row in range(2, 5)]) * scale
    elements = lines[5].split()
    counts = [int(x) for x in lines[6].split()]
    cursor = 7
    if lines[cursor].lower().startswith("s"):
        cursor += 1
    direct = lines[cursor].lower().startswith("d")
    cursor += 1
    coords = np.array([[float(x) for x in lines[cursor + i].split()[:3]] for i in range(sum(counts))])
    if not direct:
        coords = coords @ np.linalg.inv(lattice)
    species = [element for element, count in zip(elements, counts) for _ in range(count)]
    return lattice, coords, species


def read_density(path, magic):
    with path.open("rb") as handle:
        if handle.read(8) != magic:
            raise ValueError("unexpected density header: %s" % path)
        version, downsample, nx, ny, nz = struct.unpack("<5i", handle.read(20))
        if version != 1:
            raise ValueError("unsupported density version")
        lattice = np.fromfile(handle, dtype="<f8", count=9).reshape(3, 3)
        volume = float(np.fromfile(handle, dtype="<f8", count=1)[0])
        density = np.fromfile(handle, dtype="<f4", count=nx * ny * nz).reshape(nz, ny, nx)
    if density.size != nx * ny * nz:
        raise ValueError("truncated density file: %s" % path)
    return density, lattice, volume, downsample


def minimum_image(frac, origin):
    return frac - np.round(frac - origin)


def framework(case, lattice, coords, origin):
    atoms = {
        "Co(act)": case["active_co"],
        "Oads": case["active_o"],
        "Obridge": case["bridge_o"],
        case["neighbor_label"]: case["neighbor"],
    }
    return {label: minimum_image(coords[index - 1], origin) @ lattice for label, index in atoms.items()}


def sample_plane(density, lattice, active_o, plane_center, axis_u, axis_v, u, v):
    uu, vv = np.meshgrid(u, v)
    cartesian = (
        (active_o @ lattice)[None, None, :]
        + plane_center[None, None, :]
        + uu[:, :, None] * axis_u[None, None, :]
        + vv[:, :, None] * axis_v[None, None, :]
    )
    fractional = (cartesian @ np.linalg.inv(lattice)) % 1.0
    nz, ny, nx = density.shape
    sample_coords = np.vstack(
        (
            (fractional[:, :, 2] * nz).ravel(),
            (fractional[:, :, 1] * ny).ravel(),
            (fractional[:, :, 0] * nx).ravel(),
        )
    )
    sampled = map_coordinates(density, sample_coords, order=1, mode="wrap").reshape(v.size, u.size)
    return uu, vv, sampled


def write_tsv(path, x, y, values, system, map_type, units, plane_label):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(["x_A", "y_A", "value", "system", "transition", "map_type", "units", "plane_label"])
        for iy in range(values.shape[0]):
            for ix in range(values.shape[1]):
                writer.writerow(
                    [
                        "%.5f" % x[iy, ix],
                        "%.5f" % y[iy, ix],
                        "%.8g" % values[iy, ix],
                        system,
                        "*O-*OH_at_*OH_geometry",
                        map_type,
                        units,
                        plane_label,
                    ]
                )


def file_hash(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return path.stat().st_size, digest.hexdigest()


def atom_colors(label):
    if label.startswith("Co"):
        return "#777777"
    if label == "Al":
        return "#e58f22"
    if label.startswith("O"):
        return "#c7372f"
    return "#ffffff"


def draw_framework(ax, projected):
    labels = list(projected)
    for first, second in zip(labels[:-1], labels[1:]):
        p1, p2 = projected[first], projected[second]
        ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color="#444444", lw=0.85, zorder=5)
    for label, point in projected.items():
        ax.scatter(
            point[0], point[1], s=42, color=atom_colors(label), edgecolor="#111111", linewidth=0.5, zorder=7
        )
        ax.text(point[0], point[1] + 0.18, label, ha="center", va="bottom", fontsize=7.0, zorder=8)


def main():
    BASE.mkdir(parents=True, exist_ok=True)
    loaded = {}
    source_rows = []
    reference_lattice = None
    reference_shape = None
    reference_downsample = None

    for case_name, case in CASES.items():
        charge_path = SOURCE / (case_name + "_O_minus_OH_charge_ds2.raw")
        spin_path = SOURCE / (case_name + "_O_minus_OH_spin_ds2.raw")
        poscar_path = SOURCE / (case_name + "_O_at_OHgeom_POSCAR")
        charge, charge_lattice, charge_volume, charge_ds = read_density(charge_path, b"CHGDIFF1")
        spin, spin_lattice, spin_volume, spin_ds = read_density(spin_path, b"MAGDIFF1")
        lattice, coords, species = read_poscar(poscar_path)
        if not (
            np.allclose(charge_lattice, spin_lattice)
            and np.allclose(lattice, charge_lattice)
            and charge.shape == spin.shape
            and charge_ds == spin_ds
            and np.isclose(charge_volume, spin_volume)
        ):
            raise ValueError("density/grid mismatch for %s" % case_name)
        if reference_lattice is None:
            reference_lattice, reference_shape, reference_downsample = lattice, charge.shape, charge_ds
        elif not (np.allclose(reference_lattice, lattice) and reference_shape == charge.shape and reference_downsample == charge_ds):
            raise ValueError("pristine/Al16 grids are not directly comparable")
        source_rows.extend(
            [
                ["density", case["system"], "*O-*OH_at_*OH_geometry", "charge_density", str(charge_path), charge_path.name, *file_hash(charge_path)],
                ["density", case["system"], "*O-*OH_at_*OH_geometry", "magnetization", str(spin_path), spin_path.name, *file_hash(spin_path)],
                ["structure", case["system"], "*O-*OH_at_*OH_geometry", "structure", str(poscar_path), poscar_path.name, *file_hash(poscar_path)],
                ["metadata", case["system"], "*O-*OH_at_*OH_geometry", "charge_stats", str(SOURCE / (case_name + "_O_minus_OH_charge_ds2.stats")), case_name + "_O_minus_OH_charge_ds2.stats", *file_hash(SOURCE / (case_name + "_O_minus_OH_charge_ds2.stats"))],
                ["metadata", case["system"], "*O-*OH_at_*OH_geometry", "spin_stats", str(SOURCE / (case_name + "_O_minus_OH_spin_ds2.stats")), case_name + "_O_minus_OH_spin_ds2.stats", *file_hash(SOURCE / (case_name + "_O_minus_OH_spin_ds2.stats"))],
            ]
        )
        loaded[case_name] = {
            "case": case,
            "charge": charge,
            "spin": spin,
            "lattice": lattice,
            "coords": coords,
            "charge_volume": charge_volume,
            "spin_volume": spin_volume,
            "charge_integral": float(charge.sum(dtype=np.float64) * charge_volume / charge.size),
            "spin_integral": float(spin.sum(dtype=np.float64) * spin_volume / spin.size),
        }

    reference = loaded["undoped_control"]
    origin = reference["coords"][CASES["undoped_control"]["active_o"] - 1]
    reference_framework = framework(CASES["undoped_control"], reference["lattice"], reference["coords"], origin)
    points = np.array(list(reference_framework.values()))
    plane_center = points.mean(axis=0)
    _, _, vh = np.linalg.svd(points - plane_center, full_matrices=False)
    axis_u, axis_v = vh[0], vh[1]
    if np.dot(axis_u, reference_framework["Co(adj)"] - reference_framework["Oads"]) < 0:
        axis_u = -axis_u
    if np.dot(np.cross(axis_u, axis_v), vh[2]) < 0:
        axis_v = -axis_v
    projected_all = []
    for case_name, item in loaded.items():
        active_o = item["coords"][item["case"]["active_o"] - 1]
        points_case = framework(item["case"], item["lattice"], item["coords"], active_o)
        projected = {label: np.array([np.dot(point - plane_center, axis_u), np.dot(point - plane_center, axis_v)]) for label, point in points_case.items()}
        projected_all.extend(projected.values())
        item["active_o"] = active_o
        item["projected"] = projected
    projected_all = np.array(projected_all)
    u_min, v_min = projected_all.min(axis=0) - np.array([1.20, 1.10])
    u_max, v_max = projected_all.max(axis=0) + np.array([1.20, 1.10])
    u = np.linspace(u_min, u_max, 120)
    v = np.linspace(v_min, v_max, 80)
    plane_label = "PCA plane through Co(act)-Oads-Obridge-neighbor; x/y in Angstrom"
    slice_rows = []
    for case_name, item in loaded.items():
        _, _, charge_plane = sample_plane(item["charge"], item["lattice"], item["active_o"], plane_center, axis_u, axis_v, u, v)
        _, _, spin_plane = sample_plane(item["spin"], item["lattice"], item["active_o"], plane_center, axis_u, axis_v, u, v)
        fields = {
            "charge_density": charge_plane,
            "magnetization": spin_plane,
            "spin_up": 0.5 * (charge_plane + spin_plane),
            "spin_down": 0.5 * (charge_plane - spin_plane),
        }
        item["fields"] = fields
        for map_name, (map_type, units, _) in MAPS.items():
            out = BASE / map_name / "source_data" / (case_name + ".tsv")
            write_tsv(out, *np.meshgrid(u, v), fields[map_name], item["case"]["system"], map_type, units, plane_label)
            slice_rows.append([item["case"]["system"], map_name, str(out), 120, 80, "%.6f" % u_min, "%.6f" % u_max, "%.6f" % v_min, "%.6f" % v_max, units, plane_label])

    mapping_dir = BASE / "mapping"
    mapping_dir.mkdir(parents=True, exist_ok=True)
    with (mapping_dir / "state_mapping.tsv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(["system", "case_name", "state_O", "state_OH", "active_Co_index", "adsorbate_O_index", "bridge_O_index", "neighbor_index", "neighbor_label", "geometry_status"])
        for key, case in CASES.items():
            writer.writerow([case["system"], key, "*O@*OH_geometry", "*OH@*OH_geometry", case["active_co"], case["active_o"], case["bridge_o"], case["neighbor"], case["neighbor_label"], "validated existing same-geometry pair"])
    with (mapping_dir / "slice_definition.tsv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(["plane_label", "axis_u", "axis_v", "u_min_A", "u_max_A", "v_min_A", "v_max_A", "nx", "ny", "coordinate_convention", "color_limits_charge", "color_limits_magnetization", "color_limits_spin"])
        writer.writerow([plane_label, "%.8f %.8f %.8f" % tuple(axis_u), "%.8f %.8f %.8f" % tuple(axis_v), "%.6f" % u_min, "%.6f" % u_max, "%.6f" % v_min, "%.6f" % v_max, 120, 80, "x=axis_u projection; y=axis_v projection; origin at active adsorbate O", "±0.050 e Angstrom^-3", "±0.080 mu_B Angstrom^-3", "±0.050 e Angstrom^-3"])
    with (mapping_dir / "atom_overlay.tsv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(["system", "label", "x_A", "y_A", "element"])
        for key, item in loaded.items():
            for label, point in item["projected"].items():
                element = "Al" if label == "Al" else ("O" if label.startswith("O") else "Co")
                writer.writerow([item["case"]["system"], label, "%.6f" % point[0], "%.6f" % point[1], element])
    with (BASE / "source_manifest.tsv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(["dataset", "system", "transition", "map_type", "source_path", "source_file", "size_bytes", "sha256"])
        writer.writerows(source_rows)
    with (BASE / "README.md").open("w", encoding="utf-8") as handle:
        handle.write("""# Difference-density publication package\n\nThis package contains comparable fixed-*OH-geometry *O minus *OH charge and spin maps for pristine and Al16 CoOOH. The four map folders contain plot-ready TSV slices with x_A, y_A, value, system, transition, map_type, units and plane_label.\n\nThe manuscript figure is in `figures/` in PNG/TIFF/PDF/SVG formats. The slice and plotting conventions are recorded in `mapping/slice_definition.tsv`; source sizes and SHA256 values are in `source_manifest.tsv`.\n\nRun `python tools/plot_diff_density_publication.py` to regenerate the figure from the TSV slices.\n""")
    with (BASE / "PROVENANCE.md").open("w", encoding="utf-8") as handle:
        handle.write("""# Difference-density provenance\n\nNo new VASP, LOBSTER or CP2K calculation was run. The synchronized sources are the completed same-geometry reaction-density outputs under `artifacts/reaction_density_final_20260901/`: charge and magnetization binary maps plus the corresponding *O-at-*OH-geometry POSCAR files and statistics.\n\nThe source maps represent `rho(*O@*OH geometry)-rho(*OH@*OH geometry)` and `m(*O@*OH geometry)-m(*OH@*OH geometry)`. Spin-up and spin-down density differences are derived as `0.5*(Delta rho + Delta m)` and `0.5*(Delta rho - Delta m)`, using `m=rho_up-rho_down`. The full 3D fields are downsampled from 420x280x420 to 210x140x210 before the synchronized slice is sampled.\n\nThe plotted plane is a common PCA plane through active Co, adsorbate O, bridge O and the neighboring Co/Al. The displayed slice uses 120x80 points, identical orientation and identical color limits for pristine and Al16. Slice values are local densities, not Bader charges. The full-density charge integrals are approximately -1 electron for both systems; the magnetization integrals are recorded in the original statistics files.\n\nSource hashes, exact paths and metadata are recorded in `source_manifest.tsv`.\n""")
    fig = render_figure(loaded, u, v)
    fig_dir = BASE / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "tiff", "pdf", "svg"):
        kwargs = {"dpi": 600, "bbox_inches": "tight", "facecolor": "white"}
        if ext == "tiff":
            kwargs["pil_kwargs"] = {"compression": "tiff_lzw"}
        fig.savefig(fig_dir / ("diff_density_publication." + ext), **kwargs)
    plt.close(fig)
    print("SYNCED", len(slice_rows), "slices", "charge_integrals", [(k, round(v["charge_integral"], 9)) for k, v in loaded.items()])


def render_figure(loaded, u, v):
    limits = [0.050, 0.080, 0.050, 0.050]
    cmaps = ["RdBu_r", "PuOr", "RdBu_r", "RdBu_r"]
    titles = ["Charge density difference", "Magnetization difference", "Spin-up difference", "Spin-down difference"]
    units = ["e Angstrom^-3", "mu_B Angstrom^-3", "e Angstrom^-3", "e Angstrom^-3"]
    fig, axes = plt.subplots(2, 4, figsize=(15.5, 6.2), dpi=200, sharex=True, sharey=True)
    for row, key in enumerate(("undoped_control", "Al16_adjacent")):
        item = loaded[key]
        for col, map_name in enumerate(MAPS):
            ax = axes[row, col]
            limit = limits[col]
            image = ax.contourf(
                u,
                v,
                np.clip(item["fields"][map_name], -limit, limit),
                levels=np.linspace(-limit, limit, 101),
                cmap=cmaps[col],
                norm=TwoSlopeNorm(vmin=-limit, vcenter=0.0, vmax=limit),
                extend="both",
            )
            ax.contour(u, v, item["fields"][map_name], levels=[-0.4 * limit, 0.4 * limit], colors=["#126b8a", "#9e2e27"], linewidths=0.55)
            draw_framework(ax, item["projected"])
            if row == 0:
                ax.set_title(titles[col], fontsize=9.5, pad=6)
            if col == 0:
                ax.set_ylabel(item["case"]["label"], fontsize=8.6)
            if row == 1:
                ax.set_xlabel("x / Å", fontsize=8.2)
            ax.set_aspect("equal")
            ax.tick_params(labelsize=6.8)
            cbar = fig.colorbar(image, ax=ax, pad=0.012, fraction=0.042)
            cbar.set_ticks([-limit, 0.0, limit])
            cbar.ax.tick_params(labelsize=6.2)
            cbar.set_label(units[col], fontsize=6.7)
    fig.suptitle(r"Fixed-geometry density reconstruction for $*\mathrm{OH}\rightarrow *\mathrm{O}$", fontsize=11.2, y=1.01)
    fig.text(0.5, -0.025, r"$\Delta\rho=\rho(*\mathrm{O}@*\mathrm{OH}\ geometry)-\rho(*\mathrm{OH}@*\mathrm{OH}\ geometry)$; identical plane, limits and orientation.", ha="center", fontsize=8.0)
    fig.tight_layout(w_pad=0.65, h_pad=0.55)
    return fig


if __name__ == "__main__":
    main()

