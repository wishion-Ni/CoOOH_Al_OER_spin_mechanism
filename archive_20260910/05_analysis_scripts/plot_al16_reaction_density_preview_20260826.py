from __future__ import annotations

import struct
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from skimage.measure import marching_cubes


ROOT = Path(__file__).resolve().parent
RAW = ROOT / "Al16_O_minus_OH_ds2.raw"
O_POSCAR = ROOT / "Al16_O_at_OHgeom_POSCAR"
OH_POSCAR = ROOT / "Al16_OH_formal_POSCAR"
OUTPUT = ROOT / "Al16_reaction_density_preview_20260826.png"
ISOVALUE = 0.020

COLORS = {
    "Co": "#5074B8",
    "Al": "#B9B4C7",
    "O": "#D94941",
    "H": "#F5F5F5",
    "gain": "#F2B134",
    "loss": "#26A6C7",
}


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
    atom_symbols = []
    for symbol, count in zip(symbols, counts):
        atom_symbols.extend([symbol] * count)
    return lattice, coordinates, atom_symbols


def read_density(path: Path):
    with path.open("rb") as handle:
        if handle.read(8) != b"CHGDIFF1":
            raise ValueError("unexpected density file magic")
        version, downsample, nx, ny, nz = struct.unpack("<5i", handle.read(20))
        if version != 1:
            raise ValueError(f"unsupported density version {version}")
        lattice = np.fromfile(handle, dtype="<f8", count=9).reshape(3, 3)
        volume = float(np.fromfile(handle, dtype="<f8", count=1)[0])
        density = np.fromfile(handle, dtype="<f4", count=nx * ny * nz).reshape(nz, ny, nx)
    return density, lattice, volume, downsample


def minimal_offset(frac: np.ndarray, origin: np.ndarray) -> np.ndarray:
    offset = frac - origin
    return offset - np.round(offset)


def extract_crop(density, lattice, center, atom_fracs, margin_angstrom):
    nz, ny, nx = density.shape
    dims = np.array([nx, ny, nz], dtype=int)
    center_index = np.rint(center * dims).astype(int)
    offsets = np.array([minimal_offset(frac, center) for frac in atom_fracs])
    lattice_lengths = np.linalg.norm(lattice, axis=1)
    fractional_margin = margin_angstrom / lattice_lengths
    low = np.floor((offsets.min(axis=0) - fractional_margin) * dims).astype(int)
    high = np.ceil((offsets.max(axis=0) + fractional_margin) * dims).astype(int) + 1
    x_offsets = np.arange(low[0], high[0])
    y_offsets = np.arange(low[1], high[1])
    z_offsets = np.arange(low[2], high[2])
    x_indices = (center_index[0] + x_offsets) % nx
    y_indices = (center_index[1] + y_offsets) % ny
    z_indices = (center_index[2] + z_offsets) % nz
    crop = density[np.ix_(z_indices, y_indices, x_indices)]
    return crop, center_index, (x_offsets, y_offsets, z_offsets), dims


def mesh_for_level(crop, level, center_index, offsets, dims, lattice):
    vertices, faces, _, _ = marching_cubes(crop, level=level, allow_degenerate=False)
    x_offsets, y_offsets, z_offsets = offsets
    fractional = np.column_stack(
        (
            (center_index[0] + x_offsets[0] + vertices[:, 2]) / dims[0],
            (center_index[1] + y_offsets[0] + vertices[:, 1]) / dims[1],
            (center_index[2] + z_offsets[0] + vertices[:, 0]) / dims[2],
        )
    )
    center_fractional = center_index / dims
    cartesian = (fractional - center_fractional) @ lattice
    return cartesian, faces


def atom_cartesian(frac, center, lattice):
    return minimal_offset(frac, center) @ lattice


def add_atom(ax, position, symbol, size=150, alpha=1.0, edge="#202020"):
    ax.scatter(
        [position[0]], [position[1]], [position[2]],
        s=size, color=COLORS[symbol], edgecolors=edge, linewidths=0.55,
        depthshade=True, alpha=alpha, zorder=20,
    )


def add_bond(ax, first, second, dashed=False, alpha=0.9):
    ax.plot(
        [first[0], second[0]], [first[1], second[1]], [first[2], second[2]],
        color="#6B6B6B", lw=2.0, ls="--" if dashed else "-", alpha=alpha, zorder=8,
    )


def equalize(ax, points, pad=0.8):
    points = np.asarray(points)
    center = 0.5 * (points.min(axis=0) + points.max(axis=0))
    radius = 0.5 * np.max(points.max(axis=0) - points.min(axis=0)) + pad
    ax.set_xlim(center[0] - radius, center[0] + radius)
    ax.set_ylim(center[1] - radius, center[1] + radius)
    ax.set_zlim(center[2] - radius, center[2] + radius)
    ax.set_box_aspect((1, 1, 1))


def draw_panel(ax, density, lattice, reaction_frac, hydroxyl_frac, selected, bonds, labels, title, view):
    active_o = reaction_frac[346]
    atom_fracs = [reaction_frac[index - 1] for index in selected if index > 0]
    atom_fracs.append(hydroxyl_frac[203])
    crop, center_index, offsets, dims = extract_crop(density, lattice, active_o, atom_fracs, 1.6)

    positive_vertices, positive_faces = mesh_for_level(
        crop, ISOVALUE, center_index, offsets, dims, lattice
    )
    negative_vertices, negative_faces = mesh_for_level(
        -crop, ISOVALUE, center_index, offsets, dims, lattice
    )
    ax.add_collection3d(
        Poly3DCollection(
            positive_vertices[positive_faces], facecolor=COLORS["gain"], edgecolor="none", alpha=0.38,
            zorder=1,
        )
    )
    ax.add_collection3d(
        Poly3DCollection(
            negative_vertices[negative_faces], facecolor=COLORS["loss"], edgecolor="none", alpha=0.34,
            zorder=1,
        )
    )

    positions = {index: atom_cartesian(reaction_frac[index - 1], active_o, lattice) for index in selected}
    ghost_h = atom_cartesian(hydroxyl_frac[203], hydroxyl_frac[347], lattice)
    positions[204] = ghost_h
    for first, second, dashed in bonds:
        add_bond(ax, positions[first], positions[second], dashed=dashed)
    for index in selected:
        symbol = "Co" if index <= 50 else "Al" if index <= 60 else "H" if index <= 203 else "O"
        add_atom(ax, positions[index], symbol, size=250 if symbol in ("Co", "Al") else 175)
        if index in labels:
            position = positions[index]
            ax.text(position[0], position[1], position[2] + 0.28, labels[index], fontsize=7.2,
                    ha="center", color="#202020", zorder=30)
    add_atom(ax, ghost_h, "H", size=125, alpha=0.65, edge="#666666")
    ax.text(ghost_h[0], ghost_h[1], ghost_h[2] + 0.30, "H removed", fontsize=7.5,
            ha="center", color="#303030", zorder=30)

    equalize(ax, np.array(list(positions.values())), pad=1.0)
    ax.view_init(elev=view[0], azim=view[1])
    ax.set_proj_type("ortho")
    ax.set_axis_off()
    ax.set_title(title, fontsize=10, pad=4)


def main():
    density, raw_lattice, _, downsample = read_density(RAW)
    lattice, reaction_frac, _ = read_poscar(O_POSCAR)
    hydroxyl_lattice, hydroxyl_frac, _ = read_poscar(OH_POSCAR)
    if not np.allclose(raw_lattice, lattice) or not np.allclose(lattice, hydroxyl_lattice):
        raise ValueError("lattice mismatch")

    fig = plt.figure(figsize=(8.2, 4.4), dpi=180)
    ax1 = fig.add_subplot(121, projection="3d", computed_zorder=False)
    ax2 = fig.add_subplot(122, projection="3d", computed_zorder=False)
    draw_panel(
        ax1, density, lattice, reaction_frac, hydroxyl_frac,
        selected=[16, 347],
        bonds=[(16, 347, False), (347, 204, True)],
        labels={16: "Co", 347: r"O$_{ads}$"},
        title="Active Co-O site",
        view=(18, -60),
    )
    draw_panel(
        ax2, density, lattice, reaction_frac, hydroxyl_frac,
        selected=[16, 51, 116, 258, 259, 347],
        bonds=[
            (16, 347, False), (347, 204, True), (16, 258, False),
            (51, 258, False), (51, 259, False), (259, 116, False),
        ],
        labels={16: "Co", 51: "Al", 258: r"O$_{bridge}$", 259: r"O$_{OH}$", 347: r"O$_{ads}$"},
        title="O$_{ads}$-Co-O$_{bridge}$-Al-OH framework",
        view=(17, -64),
    )

    handles = [
        Line2D([0], [0], marker="o", color="none", markerfacecolor=COLORS["gain"],
               markersize=8, label="electron accumulation"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor=COLORS["loss"],
               markersize=8, label="electron depletion"),
    ]
    fig.legend(handles=handles, loc="upper center", ncol=2, frameon=False, bbox_to_anchor=(0.5, 0.985))
    fig.suptitle("Al-doped CoOOH: reaction-induced charge-density difference", y=0.895, fontsize=12)
    fig.text(
        0.5, 0.045,
        r"$\Delta\rho=\rho(*O@OH_{geom})-\rho(*OH@OH_{geom})$; "
        rf"isosurface = $\pm${ISOVALUE:.3f} e $\AA^{{-3}}$; grid downsample = {downsample}",
        ha="center", fontsize=8.2, color="#333333",
    )
    fig.text(
        0.5, 0.015,
        "Single-system preview; continuous density difference, not atom-integrated Bader charge.",
        ha="center", fontsize=7.5, color="#666666",
    )
    fig.subplots_adjust(left=0.01, right=0.99, bottom=0.09, top=0.82, wspace=0.00)
    fig.savefig(OUTPUT, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(OUTPUT)


if __name__ == "__main__":
    main()
