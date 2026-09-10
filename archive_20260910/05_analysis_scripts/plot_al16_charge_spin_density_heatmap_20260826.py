from __future__ import annotations

import struct
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import TwoSlopeNorm
from scipy.ndimage import map_coordinates


ROOT = Path(__file__).resolve().parent
CHARGE_RAW = ROOT / "Al16_O_minus_OH_ds2.raw"
SPIN_RAW = ROOT / "Al16_O_minus_OH_spin_ds2.raw"
O_POSCAR = ROOT / "Al16_O_at_OHgeom_POSCAR"
OH_POSCAR = ROOT / "Al16_OH_formal_POSCAR"
OUTPUT = ROOT / "Al16_reaction_charge_spin_channels_heatmap_preview_20260826.png"


def read_poscar(path: Path):
    lines = path.read_text().splitlines()
    scale = float(lines[1].split()[0])
    lattice = np.array([[float(value) for value in lines[row].split()[:3]] for row in range(2, 5)]) * scale
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


def draw_framework(ax, projected):
    bonds = [
        (r"O$_{ads}$", "Co"),
        ("Co", r"O$_{bridge}$"),
        (r"O$_{bridge}$", "Al"),
    ]
    for first, second in bonds:
        p1, p2 = projected[first], projected[second]
        ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color="#202020", lw=1.0, alpha=0.76)

    h_removed = projected["H removed"]
    o_ads = projected[r"O$_{ads}$"]
    ax.plot([h_removed[0], o_ads[0]], [h_removed[1], o_ads[1]], color="#333333", lw=0.9, ls="--")

    offsets = {
        r"O$_{ads}$": (0.02, 0.18),
        "Co": (0.02, 0.18),
        r"O$_{bridge}$": (0.03, 0.18),
        "Al": (0.02, 0.18),
    }
    for label, position in projected.items():
        if label == "H removed":
            continue
        dx, dy = offsets[label]
        ax.scatter(position[0], position[1], s=12, color="#111111", zorder=6)
        ax.text(
            position[0] + dx,
            position[1] + dy,
            label,
            ha="center",
            va="bottom",
            fontsize=8.0,
            color="#111111",
            bbox=dict(facecolor="white", edgecolor="none", alpha=0.64, pad=0.6),
        )
    ax.scatter(h_removed[0], h_removed[1], s=34, marker="x", linewidths=1.2, color="#222222", zorder=7)
    ax.text(
        h_removed[0],
        h_removed[1] + 0.22,
        "removed H",
        ha="center",
        va="bottom",
        fontsize=7.8,
        bbox=dict(facecolor="white", edgecolor="none", alpha=0.64, pad=0.6),
    )


def main():
    charge, charge_lattice, _, charge_ds = read_density(CHARGE_RAW, b"CHGDIFF1")
    spin, spin_lattice, _, spin_ds = read_density(SPIN_RAW, b"MAGDIFF1")
    lattice, reaction_frac = read_poscar(O_POSCAR)
    hydroxyl_lattice, hydroxyl_frac = read_poscar(OH_POSCAR)
    if not (
        np.allclose(charge_lattice, spin_lattice)
        and np.allclose(lattice, hydroxyl_lattice)
        and np.allclose(lattice, charge_lattice)
        and charge.shape == spin.shape
        and charge_ds == spin_ds
    ):
        raise ValueError("charge/spin grid or lattice mismatch")

    active_o = reaction_frac[346]
    site_indices = {
        r"O$_{ads}$": 347,
        "Co": 16,
        r"O$_{bridge}$": 258,
        "Al": 51,
    }
    site_cart = {
        label: minimum_image(reaction_frac[index - 1], active_o) @ lattice
        for label, index in site_indices.items()
    }
    removed_h = minimum_image(hydroxyl_frac[203], hydroxyl_frac[347]) @ lattice

    framework = np.array([site_cart[label] for label in site_indices])
    plane_center = framework.mean(axis=0)
    _, _, vh = np.linalg.svd(framework - plane_center, full_matrices=False)
    axis_u, axis_v = vh[0], vh[1]
    chain_direction = site_cart["Al"] - site_cart[r"O$_{ads}$"]
    if np.dot(axis_u, chain_direction) < 0:
        axis_u = -axis_u
    if np.dot(np.cross(axis_u, axis_v), vh[2]) < 0:
        axis_v = -axis_v

    projected = {
        label: np.array([np.dot(position - plane_center, axis_u), np.dot(position - plane_center, axis_v)])
        for label, position in site_cart.items()
    }
    projected["H removed"] = np.array(
        [np.dot(removed_h - plane_center, axis_u), np.dot(removed_h - plane_center, axis_v)]
    )
    uv = np.array(list(projected.values()))
    u_min, v_min = uv.min(axis=0) - np.array([1.15, 1.15])
    u_max, v_max = uv.max(axis=0) + np.array([1.15, 1.15])
    u = np.linspace(u_min, u_max, 520)
    v = np.linspace(v_min, v_max, 360)
    uu, vv, charge_plane = sample_plane(charge, lattice, active_o, plane_center, axis_u, axis_v, u, v)
    _, _, spin_plane = sample_plane(spin, lattice, active_o, plane_center, axis_u, axis_v, u, v)
    spin_up_plane = 0.5 * (charge_plane + spin_plane)
    spin_down_plane = 0.5 * (charge_plane - spin_plane)

    fig, axes = plt.subplots(2, 2, figsize=(11.7, 8.0), dpi=180, sharex=True, sharey=True)
    specifications = [
        (charge_plane, 0.050, "RdBu_r", r"$\Delta\rho$ (e $\AA^{-3}$)",
         r"(a) Charge-density response", [-0.020, 0.020], ["#167D9A", "#B8322A"]),
        (spin_plane, 0.080, "PuOr", r"$\Delta m$ ($\mu_B$ $\AA^{-3}$)",
         r"(b) Magnetization-density response", [-0.030, 0.030], ["#C77C12", "#5B2C83"]),
        (spin_up_plane, 0.050, "RdBu_r", r"$\Delta\rho^\uparrow$ (e $\AA^{-3}$)",
         r"(c) Spin-up charge response", [-0.020, 0.020], ["#167D9A", "#B8322A"]),
        (spin_down_plane, 0.050, "RdBu_r", r"$\Delta\rho^\downarrow$ (e $\AA^{-3}$)",
         r"(d) Spin-down charge response", [-0.020, 0.020], ["#167D9A", "#B8322A"]),
    ]
    for ax, (field, limit, cmap, colorbar_label, title, contour_levels, contour_colors) in zip(
        axes.ravel(), specifications
    ):
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
        ax.contour(
            uu,
            vv,
            field,
            levels=contour_levels,
            colors=contour_colors,
            linewidths=0.72,
            linestyles=["--", "-"],
        )
        draw_framework(ax, projected)
        colorbar = fig.colorbar(image, ax=ax, pad=0.018, fraction=0.046)
        colorbar.set_label(colorbar_label)
        colorbar.set_ticks([-limit, -limit / 2, 0, limit / 2, limit])
        ax.set_xlabel("In-plane coordinate (Å)")
        ax.set_aspect("equal")
        ax.set_title(title, fontsize=11.2, pad=9)

    axes[0, 0].set_ylabel("In-plane coordinate (Å)")
    axes[1, 0].set_ylabel("In-plane coordinate (Å)")
    fig.suptitle("Al-doped CoOOH: *OH to *O response at fixed geometry", fontsize=12.2, y=1.01)
    fig.text(
        0.5,
        -0.01,
        r"$\Delta\rho=\rho(*O@OH_{geom})-\rho(*OH@OH_{geom})$;  "
        r"$\Delta m=m(*O@OH_{geom})-m(*OH@OH_{geom})$;  "
        r"$\Delta\rho^{\uparrow,\downarrow}=(\Delta\rho\pm\Delta m)/2$;  "
        f"grid downsample = {charge_ds}",
        ha="center",
        fontsize=8.4,
    )
    fig.tight_layout(w_pad=1.4)
    fig.savefig(OUTPUT, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(OUTPUT)
    print(f"charge_plane_range={charge_plane.min():.8f},{charge_plane.max():.8f}")
    print(f"spin_plane_range={spin_plane.min():.8f},{spin_plane.max():.8f}")
    print(f"spin_up_plane_range={spin_up_plane.min():.8f},{spin_up_plane.max():.8f}")
    print(f"spin_down_plane_range={spin_down_plane.min():.8f},{spin_down_plane.max():.8f}")


if __name__ == "__main__":
    main()
