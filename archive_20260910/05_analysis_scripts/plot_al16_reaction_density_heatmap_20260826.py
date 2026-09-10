from __future__ import annotations

import struct
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import TwoSlopeNorm
from scipy.ndimage import map_coordinates


ROOT = Path(__file__).resolve().parent
RAW = ROOT / "Al16_O_minus_OH_ds2.raw"
O_POSCAR = ROOT / "Al16_O_at_OHgeom_POSCAR"
OH_POSCAR = ROOT / "Al16_OH_formal_POSCAR"
OUTPUT = ROOT / "Al16_reaction_density_heatmap_preview_20260826.png"


def read_poscar(path: Path):
    lines = path.read_text().splitlines()
    scale = float(lines[1].split()[0])
    lattice = np.array([[float(value) for value in lines[row].split()[:3]] for row in range(2, 5)]) * scale
    symbols = lines[5].split()
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


def read_density(path: Path):
    with path.open("rb") as handle:
        if handle.read(8) != b"CHGDIFF1":
            raise ValueError("unexpected density file")
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


def main():
    density, raw_lattice, _, downsample = read_density(RAW)
    lattice, reaction_frac = read_poscar(O_POSCAR)
    hydroxyl_lattice, hydroxyl_frac = read_poscar(OH_POSCAR)
    if not np.allclose(raw_lattice, lattice) or not np.allclose(lattice, hydroxyl_lattice):
        raise ValueError("lattice mismatch")

    active_o = reaction_frac[346]
    # Reaction-POSCAR indices after removing active H204.
    site_indices = {
        r"O$_{ads}$": 347,
        "Co": 16,
        r"O$_{bridge}$": 258,
        "Al": 51,
        r"O$_{OH}$": 259,
        r"H$_{OH}$": 116,
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
    chain_direction = site_cart[r"O$_{OH}$"] - site_cart[r"O$_{ads}$"]
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
    u_min, v_min = uv.min(axis=0) - np.array([2.0, 1.8])
    u_max, v_max = uv.max(axis=0) + np.array([2.0, 1.8])
    u = np.linspace(u_min, u_max, 520)
    v = np.linspace(v_min, v_max, 360)
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
    plane_density = map_coordinates(density, coordinates, order=1, mode="wrap").reshape(v.size, u.size)

    limit = 0.050
    levels = np.linspace(-limit, limit, 101)
    fig, ax = plt.subplots(figsize=(8.0, 4.7), dpi=180)
    image = ax.contourf(
        uu, vv, np.clip(plane_density, -limit, limit), levels=levels,
        cmap="RdBu_r", norm=TwoSlopeNorm(vmin=-limit, vcenter=0.0, vmax=limit), extend="both",
    )
    ax.contour(uu, vv, plane_density, levels=[-0.020, 0.020],
               colors=["#167D9A", "#B8322A"], linewidths=0.75, linestyles=["--", "-"])

    bonds = [
        (r"O$_{ads}$", "Co"),
        ("Co", r"O$_{bridge}$"),
        (r"O$_{bridge}$", "Al"),
        ("Al", r"O$_{OH}$"),
        (r"O$_{OH}$", r"H$_{OH}$"),
    ]
    for first, second in bonds:
        p1, p2 = projected[first], projected[second]
        ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color="#222222", lw=1.1, alpha=0.75)
    h_removed = projected["H removed"]
    o_ads = projected[r"O$_{ads}$"]
    ax.plot([h_removed[0], o_ads[0]], [h_removed[1], o_ads[1]], color="#333333", lw=1.0, ls="--")

    offsets = {
        r"O$_{ads}$": (0.02, 0.18),
        "Co": (0.02, 0.18),
        r"O$_{bridge}$": (0.03, 0.18),
        "Al": (0.02, 0.18),
        r"O$_{OH}$": (0.02, 0.18),
        r"H$_{OH}$": (0.02, -0.30),
    }
    for label, position in projected.items():
        if label == "H removed":
            continue
        dx, dy = offsets[label]
        ax.scatter(position[0], position[1], s=15, color="#111111", zorder=6)
        ax.text(position[0] + dx, position[1] + dy, label, ha="center", va="bottom", fontsize=8.5,
                color="#111111", bbox=dict(facecolor="white", edgecolor="none", alpha=0.62, pad=0.8))
    ax.scatter(h_removed[0], h_removed[1], s=38, marker="x", linewidths=1.3, color="#222222", zorder=7)
    ax.text(h_removed[0], h_removed[1] + 0.22, "removed H", ha="center", va="bottom", fontsize=8.3,
            bbox=dict(facecolor="white", edgecolor="none", alpha=0.62, pad=0.8))

    colorbar = fig.colorbar(image, ax=ax, pad=0.025, fraction=0.046)
    colorbar.set_label(r"$\Delta\rho$ (e $\AA^{-3}$)")
    colorbar.set_ticks([-0.05, -0.025, 0, 0.025, 0.05])
    ax.set_xlabel("In-plane coordinate (Å)")
    ax.set_ylabel("In-plane coordinate (Å)")
    ax.set_aspect("equal")
    ax.set_title("Al-doped CoOOH: reaction-induced charge redistribution", fontsize=11.5, pad=10)
    ax.text(
        0.015, 0.018,
        r"$\Delta\rho=\rho(*O@OH_{geom})-\rho(*OH@OH_{geom})$" + f"  |  grid downsample = {downsample}",
        transform=ax.transAxes, fontsize=8.0, color="#222222",
        bbox=dict(facecolor="white", edgecolor="#999999", alpha=0.82, boxstyle="square,pad=0.25"),
    )
    fig.tight_layout()
    fig.savefig(OUTPUT, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(OUTPUT)


if __name__ == "__main__":
    main()
