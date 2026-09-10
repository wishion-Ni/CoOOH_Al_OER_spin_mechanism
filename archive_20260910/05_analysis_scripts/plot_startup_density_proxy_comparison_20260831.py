from __future__ import annotations

import struct
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import TwoSlopeNorm
from scipy.ndimage import map_coordinates


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "startup_density_proxy_comparison_20260827"
OUTPUT = ROOT / "startup_density_proxy_undoped_vs_Al16_20260831.png"


CASES = {
    "undoped_control": {
        "label": "Undoped CoOOH",
        "active_co": 21,
        "active_o": 347,
        "bridge_o": 258,
        "neighbor": 23,
        "neighbor_label": "Co(adj)",
    },
    "Al16_adjacent": {
        "label": "Al16-doped CoOOH",
        "active_co": 16,
        "active_o": 347,
        "bridge_o": 258,
        "neighbor": 51,
        "neighbor_label": "Al",
    },
}


def read_poscar(path: Path):
    lines = path.read_text().splitlines()
    scale = float(lines[1].split()[0])
    lattice = np.array(
        [[float(value) for value in lines[row].split()[:3]] for row in range(2, 5)]
    ) * scale
    counts = [int(value) for value in lines[6].split()]
    cursor = 7
    if lines[cursor].lower().startswith("s"):
        cursor += 1
    direct = lines[cursor].lower().startswith("d")
    cursor += 1
    coordinates = np.array(
        [[float(value) for value in lines[cursor + atom].split()[:3]] for atom in range(sum(counts))]
    )
    if not direct:
        coordinates = coordinates @ np.linalg.inv(lattice)
    return lattice, coordinates


def read_density(path: Path, expected_magic: bytes):
    with path.open("rb") as handle:
        magic = handle.read(8)
        if magic != expected_magic:
            raise ValueError(f"unexpected density file {path.name}: {magic!r}")
        version, downsample, nx, ny, nz = struct.unpack("<5i", handle.read(20))
        if version != 1:
            raise ValueError(f"unsupported version {version}")
        lattice = np.fromfile(handle, dtype="<f8", count=9).reshape(3, 3)
        volume = float(np.fromfile(handle, dtype="<f8", count=1)[0])
        density = np.fromfile(handle, dtype="<f4", count=nx * ny * nz).reshape(nz, ny, nx)
    if density.size != nx * ny * nz:
        raise ValueError(f"truncated density file: {path}")
    return density, lattice, volume, downsample


def minimum_image(frac, origin):
    delta = frac - origin
    return delta - np.round(delta)


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
    coordinates = np.vstack(
        (
            (fractional[:, :, 2] * nz).ravel(),
            (fractional[:, :, 1] * ny).ravel(),
            (fractional[:, :, 0] * nx).ravel(),
        )
    )
    sampled = map_coordinates(density, coordinates, order=1, mode="wrap").reshape(v.size, u.size)
    return uu, vv, sampled


def framework_for_case(case, lattice, coordinates, active_o_ref):
    labels = {
        "Oads": case["active_o"],
        "Co(act)": case["active_co"],
        "Obridge": case["bridge_o"],
        case["neighbor_label"]: case["neighbor"],
    }
    return {
        label: minimum_image(coordinates[index - 1], active_o_ref) @ lattice
        for label, index in labels.items()
    }


def draw_framework(ax, projected):
    labels = list(projected)
    for first, second in zip(labels[:-1], labels[1:]):
        p1, p2 = projected[first], projected[second]
        ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color="#222222", lw=1.0, alpha=0.8)

    colors = {
        "Oads": "#d84b42",
        "Obridge": "#d84b42",
        "Co(act)": "#3274a1",
        "Co(adj)": "#3274a1",
        "Al": "#d88db3",
    }
    for label, position in projected.items():
        ax.scatter(
            position[0],
            position[1],
            s=46,
            color=colors[label],
            edgecolor="white",
            linewidth=0.7,
            zorder=7,
        )
        ax.text(
            position[0],
            position[1] + 0.23,
            label,
            ha="center",
            va="bottom",
            fontsize=7.2,
            color="#111111",
            bbox=dict(facecolor="white", edgecolor="none", alpha=0.72, pad=0.5),
            zorder=8,
        )


def main():
    loaded = {}
    reference_lattice = None
    reference_shape = None
    downsample = None

    for case_name, case in CASES.items():
        charge, charge_lattice, charge_volume, charge_ds = read_density(
            DATA / f"{case_name}_startup_O_minus_OH_charge_ds2.raw", b"CHGDIFF1"
        )
        spin, spin_lattice, spin_volume, spin_ds = read_density(
            DATA / f"{case_name}_startup_O_minus_OH_spin_ds2.raw", b"MAGDIFF1"
        )
        lattice, coordinates = read_poscar(DATA / f"{case_name}_O_at_OHgeom_POSCAR")
        if not (
            np.allclose(charge_lattice, spin_lattice)
            and np.allclose(lattice, charge_lattice)
            and charge.shape == spin.shape
            and charge_ds == spin_ds
            and np.isclose(charge_volume, spin_volume)
        ):
            raise ValueError(f"grid/lattice mismatch for {case_name}")
        if reference_lattice is None:
            reference_lattice = lattice
            reference_shape = charge.shape
            downsample = charge_ds
        elif not (
            np.allclose(reference_lattice, lattice)
            and reference_shape == charge.shape
            and downsample == charge_ds
        ):
            raise ValueError("undoped/Al16 grids are not directly comparable")
        loaded[case_name] = {
            "case": case,
            "charge": charge,
            "spin": spin,
            "charge_integral": float(charge.sum(dtype=np.float64) * charge_volume / charge.size),
            "spin_integral": float(spin.sum(dtype=np.float64) * spin_volume / spin.size),
            "lattice": lattice,
            "coordinates": coordinates,
        }

    undoped = loaded["undoped_control"]
    active_o_ref = undoped["coordinates"][CASES["undoped_control"]["active_o"] - 1]
    undoped_framework = framework_for_case(
        CASES["undoped_control"], undoped["lattice"], undoped["coordinates"], active_o_ref
    )
    framework_points = np.array(list(undoped_framework.values()))
    plane_center = framework_points.mean(axis=0)
    _, _, vh = np.linalg.svd(framework_points - plane_center, full_matrices=False)
    axis_u, axis_v = vh[0], vh[1]
    if np.dot(axis_u, undoped_framework["Co(adj)"] - undoped_framework["Oads"]) < 0:
        axis_u = -axis_u
    if np.dot(np.cross(axis_u, axis_v), vh[2]) < 0:
        axis_v = -axis_v

    prepared = {}
    all_projected = []
    for case_name, item in loaded.items():
        case = item["case"]
        active_o = item["coordinates"][case["active_o"] - 1]
        framework = framework_for_case(case, item["lattice"], item["coordinates"], active_o)
        projected = {
            label: np.array(
                [np.dot(position - plane_center, axis_u), np.dot(position - plane_center, axis_v)]
            )
            for label, position in framework.items()
        }
        all_projected.extend(projected.values())
        prepared[case_name] = {"active_o": active_o, "projected": projected, **item}

    uv = np.array(all_projected)
    u_min, v_min = uv.min(axis=0) - np.array([1.25, 1.15])
    u_max, v_max = uv.max(axis=0) + np.array([1.25, 1.15])
    u = np.linspace(u_min, u_max, 520)
    v = np.linspace(v_min, v_max, 340)

    for item in prepared.values():
        uu, vv, charge_plane = sample_plane(
            item["charge"],
            item["lattice"],
            item["active_o"],
            plane_center,
            axis_u,
            axis_v,
            u,
            v,
        )
        _, _, spin_plane = sample_plane(
            item["spin"],
            item["lattice"],
            item["active_o"],
            plane_center,
            axis_u,
            axis_v,
            u,
            v,
        )
        item["fields"] = [
            charge_plane,
            spin_plane,
            0.5 * (charge_plane + spin_plane),
            0.5 * (charge_plane - spin_plane),
        ]

    limits = [0.050, 0.080, 0.050, 0.050]
    cmaps = ["RdBu_r", "PuOr", "RdBu_r", "RdBu_r"]
    titles = [
        r"Charge response $\Delta\rho$",
        r"Spin response $\Delta m$",
        r"Spin-up $\Delta\rho^\uparrow$",
        r"Spin-down $\Delta\rho^\downarrow$",
    ]
    units = [
        r"e $\AA^{-3}$",
        r"$\mu_B$ $\AA^{-3}$",
        r"e $\AA^{-3}$",
        r"e $\AA^{-3}$",
    ]

    fig, axes = plt.subplots(2, 4, figsize=(15.8, 6.4), dpi=180, sharex=True, sharey=True)
    case_order = ["undoped_control", "Al16_adjacent"]
    for row, case_name in enumerate(case_order):
        item = prepared[case_name]
        for column, (field, limit, cmap, title, unit) in enumerate(
            zip(item["fields"], limits, cmaps, titles, units)
        ):
            ax = axes[row, column]
            levels = np.linspace(-limit, limit, 121)
            image = ax.contourf(
                uu,
                vv,
                np.clip(field, -limit, limit),
                levels=levels,
                cmap=cmap,
                norm=TwoSlopeNorm(vmin=-limit, vcenter=0.0, vmax=limit),
                extend="both",
            )
            contour_level = 0.4 * limit
            ax.contour(
                uu,
                vv,
                field,
                levels=[-contour_level, contour_level],
                colors=["#126b8a", "#9e2e27"],
                linewidths=0.65,
                linestyles=["--", "-"],
            )
            draw_framework(ax, item["projected"])
            if row == 0:
                ax.set_title(title, fontsize=10.4, pad=8)
            if column == 0:
                ax.set_ylabel(
                    item["case"]["label"]
                    + f"\nIntegral spin response = {item['spin_integral']:+.3f} muB"
                    + "\nIn-plane coordinate (A)",
                    fontsize=9.0,
                )
            if row == 1:
                ax.set_xlabel("In-plane coordinate (A)", fontsize=8.7)
            ax.set_aspect("equal")
            ax.tick_params(labelsize=7.5)

            colorbar = fig.colorbar(image, ax=ax, pad=0.012, fraction=0.042)
            colorbar.set_ticks([-limit, 0.0, limit])
            colorbar.ax.tick_params(labelsize=7.0)
            colorbar.set_label(unit, fontsize=7.5)

    fig.suptitle(
        "Preliminary startup-density proxy: undoped vs Al16-doped CoOOH",
        fontsize=12.0,
        y=1.01,
    )
    fig.text(
        0.5,
        -0.025,
        r"Proxy = $\rho$(formal *O) - $\rho$(formal *OH); includes structural response. "
        r"Identical slice, limits and color scales. Charge channels: red positive, blue negative; "
        r"spin response: purple positive, orange negative.",
        ha="center",
        fontsize=8.3,
    )
    fig.tight_layout(w_pad=0.8, h_pad=0.7)
    fig.savefig(OUTPUT, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)

    print(OUTPUT)
    for case_name in case_order:
        print(
            f"{case_name}\tcharge_integral={prepared[case_name]['charge_integral']:.9f}"
            f"\tspin_integral={prepared[case_name]['spin_integral']:.9f}"
        )
        for title, field in zip(titles, prepared[case_name]["fields"]):
            print(
                f"{case_name}\t{title}\tmin={field.min():.8f}\tmax={field.max():.8f}"
            )


if __name__ == "__main__":
    main()
