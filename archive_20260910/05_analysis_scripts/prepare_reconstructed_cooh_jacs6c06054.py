#!/usr/bin/env python3
"""Build the reconstructed Co(OH)2-Cl terminal-site model from Co8Co2.xsf."""

from __future__ import annotations

import argparse
import math
import shutil
from dataclasses import dataclass
from pathlib import Path


ATOMIC_SYMBOLS = {1: "H", 8: "O", 17: "Cl", 27: "Co"}


@dataclass
class Atom:
    symbol: str
    cart: tuple[float, float, float]
    tag: str = ""


def add(a, b):
    return tuple(x + y for x, y in zip(a, b))


def subtract(a, b):
    return tuple(x - y for x, y in zip(a, b))


def scale(a, factor):
    return tuple(factor * x for x in a)


def length(a):
    return math.sqrt(sum(x * x for x in a))


def normalize(a):
    value = length(a)
    return tuple(x / value for x in a)


def cross(a, b):
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def inverse_fractional(cart, lattice):
    a, b, c = lattice
    volume = dot(a, cross(b, c))
    return (
        dot(cart, cross(b, c)) / volume,
        dot(cart, cross(c, a)) / volume,
        dot(cart, cross(a, b)) / volume,
    )


def parse_xsf(path: Path):
    lines = path.read_text().splitlines()
    vector_index = next(i for i, line in enumerate(lines) if line.strip() == "PRIMVEC")
    lattice = [
        tuple(float(value) for value in lines[vector_index + offset].split()[:3])
        for offset in range(1, 4)
    ]
    coord_index = next(i for i, line in enumerate(lines) if line.strip() == "PRIMCOORD")
    count = int(lines[coord_index + 1].split()[0])
    atoms = []
    for line in lines[coord_index + 2 : coord_index + 2 + count]:
        values = line.split()
        atoms.append(
            Atom(
                ATOMIC_SYMBOLS[int(values[0])],
                tuple(float(value) for value in values[1:4]),
            )
        )
    return lattice, atoms


def minimum_image_vector(origin, target, lattice):
    best = None
    best_vector = None
    for i in (-1, 0, 1):
        for j in (-1, 0, 1):
            shifted = add(target, add(scale(lattice[0], i), scale(lattice[1], j)))
            vector = subtract(shifted, origin)
            distance = length(vector)
            if best is None or distance < best:
                best = distance
                best_vector = vector
    return best_vector


def reconstruct(lattice, atoms):
    cobalt = [atom for atom in atoms if atom.symbol == "Co"]
    terminal_cobalt = sorted(cobalt, key=lambda atom: atom.cart[2])
    bottom_co, top_co = terminal_cobalt[0], terminal_cobalt[-1]
    if abs(abs(top_co.cart[2]) - 1.86270304) > 0.05:
        raise RuntimeError("Unexpected Co8Co2.xsf terminal cobalt geometry")

    reconstructed = [Atom(atom.symbol, atom.cart, atom.tag) for atom in atoms if atom.symbol != "Cl"]
    added_top = []
    for label, center, outward_sign in (
        ("bottom", bottom_co, -1.0),
        ("top", top_co, 1.0),
    ):
        oxygen = [atom for atom in atoms if atom.symbol == "O"]
        neighbors = sorted(
            (
                (length(minimum_image_vector(center.cart, atom.cart, lattice)), atom)
                for atom in oxygen
            ),
            key=lambda item: item[0],
        )[:3]
        if any(distance > 2.15 for distance, _ in neighbors):
            raise RuntimeError(f"Could not identify three lattice O neighbors for {label} Co")

        missing = []
        for site_index, (distance, atom) in enumerate(neighbors, start=1):
            existing_vector = minimum_image_vector(center.cart, atom.cart, lattice)
            oxygen_cart = add(center.cart, scale(normalize(existing_vector), -distance))
            hydrogen_cart = add(oxygen_cart, (0.0, 0.0, 0.98 * outward_sign))
            oxygen_atom = Atom("O", oxygen_cart, f"{label}_terminal_O_{site_index}")
            hydrogen_atom = Atom("H", hydrogen_cart, f"{label}_terminal_H_{site_index}")
            reconstructed.extend((oxygen_atom, hydrogen_atom))
            missing.append((oxygen_atom, hydrogen_atom))
        if label == "top":
            added_top = sorted(
                missing,
                key=lambda pair: math.atan2(
                    pair[0].cart[1] - center.cart[1],
                    pair[0].cart[0] - center.cart[0],
                ),
            )

    counts = {symbol: sum(atom.symbol == symbol for atom in reconstructed) for symbol in ("Co", "H", "O")}
    if counts != {"Co": 10, "H": 24, "O": 24}:
        raise RuntimeError(f"Wrong reconstructed composition: {counts}")

    minimum_z = min(atom.cart[2] for atom in reconstructed)
    maximum_z = max(atom.cart[2] for atom in reconstructed)
    shift_z = 10.0 - minimum_z
    shifted = [
        Atom(atom.symbol, (atom.cart[0], atom.cart[1], atom.cart[2] + shift_z), atom.tag)
        for atom in reconstructed
    ]
    shifted_top = []
    for oxygen_atom, hydrogen_atom in added_top:
        shifted_top.append(
            (
                next(atom for atom in shifted if atom.tag == oxygen_atom.tag),
                next(atom for atom in shifted if atom.tag == hydrogen_atom.tag),
            )
        )
    shifted_top_co = next(
        atom
        for atom in shifted
        if atom.symbol == "Co" and abs(atom.cart[2] - (top_co.cart[2] + shift_z)) < 1.0e-6
    )
    slab_lattice = [lattice[0], lattice[1], (0.0, 0.0, maximum_z - minimum_z + 20.0)]
    return slab_lattice, shifted, shifted_top_co, shifted_top


def make_site_states(reconstructed, active_oh, lattice):
    active_o, active_h = active_oh
    bare = [atom for atom in reconstructed if atom is not active_o and atom is not active_h]
    states = {
        "bare": list(bare),
        "OH": list(reconstructed),
        "O": list(bare) + [Atom("O", active_o.cart, "adsorbate_O")],
    }
    z_axis = (0.0, 0.0, 1.0)
    tangents = (
        normalize(lattice[0]),
        normalize(lattice[1]),
        normalize(subtract(lattice[1], lattice[0])),
    )
    for orientation, tangent in enumerate(tangents, start=1):
        oo_axis = normalize(add(scale(z_axis, 0.82), scale(tangent, 0.57)))
        oh_axis = normalize(add(scale(z_axis, 0.94), scale(tangent, -0.34)))
        distal_o = add(active_o.cart, scale(oo_axis, 1.35))
        distal_h = add(distal_o, scale(oh_axis, 0.98))
        states[f"OOH_o{orientation:02d}"] = list(bare) + [
            Atom("O", active_o.cart, "adsorbate_proximal_O"),
            Atom("O", distal_o, "adsorbate_distal_O"),
            Atom("H", distal_h, "adsorbate_H"),
        ]
    return states


def write_poscar(path, title, lattice, atoms):
    species = ["Co", "H", "O"]
    ordered = [atom for symbol in species for atom in atoms if atom.symbol == symbol]
    counts = [sum(atom.symbol == symbol for atom in atoms) for symbol in species]
    lines = [title, "1.0"]
    lines.extend("  " + "  ".join(f"{value:20.12f}" for value in vector) for vector in lattice)
    lines.append("  " + "  ".join(species))
    lines.append("  " + "  ".join(str(value) for value in counts))
    lines.append("Direct")
    for atom in ordered:
        fractional = inverse_fractional(atom.cart, lattice)
        lines.append("  " + "  ".join(f"{value % 1.0:18.12f}" for value in fractional))
    path.write_text("\n".join(lines) + "\n")


def write_incar(path, title, atoms):
    magmom = " ".join("3.0" if atom.symbol == "Co" else "0.0" for symbol in ("Co", "H", "O") for atom in atoms if atom.symbol == symbol)
    path.write_text(
        f"""SYSTEM = {title}
ISTART = 0
ICHARG = 2
ISPIN = 2
MAGMOM = {magmom}
LDAU = .TRUE.
LDAUTYPE = 2
LDAUL = 2 -1 -1
LDAUU = 4.5 0 0
LDAUJ = 0 0 0
LMAXMIX = 4
GGA = PE
IVDW = 11
ENCUT = 520
PREC = Accurate
EDIFF = 1E-6
NELM = 300
NELMIN = 8
ALGO = Normal
ISMEAR = 1
SIGMA = 0.20
IBRION = 2
NSW = 360
ISIF = 2
EDIFFG = -0.02
LREAL = .FALSE.
ADDGRID = .TRUE.
LASPH = .TRUE.
LWAVE = .TRUE.
LCHARG = .TRUE.
ISYM = 0
NCORE = 4
"""
    )


def minimum_distance(atoms, lattice):
    best = (float("inf"), None)
    for i, first in enumerate(atoms):
        for j in range(i + 1, len(atoms)):
            second = atoms[j]
            vector = minimum_image_vector(first.cart, second.cart, lattice)
            distance = length(vector)
            if distance < best[0]:
                best = (distance, (i + 1, first.symbol, j + 1, second.symbol))
    return best


def write_jobs(root, jobs):
    (root / "jobs.list").write_text("\n".join(str(job.relative_to(root)) for job in jobs) + "\n")
    (root / "vasp_array.slurm").write_text(
        f"""#!/bin/bash
#SBATCH --job-name=CoOH_recon_JACS
#SBATCH --nodes=1
#SBATCH --ntasks=28
#SBATCH --partition=n28
#SBATCH --array=0-{len(jobs) - 1}%3
#SBATCH --output=array_%A_%a.stdout
#SBATCH --error=array_%A_%a.stderr

set -eo pipefail
WORKDIR="$(sed -n "$((SLURM_ARRAY_TASK_ID + 1))p" jobs.list)"
cd "$WORKDIR"
if [ -f OUTCAR ] && grep -q "General timing and accounting informations" OUTCAR; then
  echo "Already complete: $WORKDIR"
  exit 0
fi
VASP_HOME=/apps/vasp/6.3.0_vtst_optcell_vaspsol/O3
if [ -f "$HOME/intel/oneapi/setvars.sh" ]; then
  source "$HOME/intel/oneapi/setvars.sh" --force
fi
export LD_LIBRARY_PATH="$HOME/intel/oneapi/mkl/latest/lib/intel64:$HOME/intel/oneapi/compiler/latest/linux/compiler/lib/intel64_lin:${{LD_LIBRARY_PATH:-}}"
ulimit -s unlimited
"$HOME/intel/oneapi/mpi/2021.11/bin/mpirun" -n "$SLURM_NTASKS" "$VASP_HOME/vasp_std" > vasp.out 2>&1
"""
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--potcar", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    source_lattice, source_atoms = parse_xsf(args.source)
    lattice, reconstructed, active_co, active_oh_sites = reconstruct(source_lattice, source_atoms)
    args.output.mkdir(parents=True, exist_ok=False)

    jobs = []
    manifest = [
        "site\tstate\tformula\tactive_Co_x_A\tactive_Co_y_A\tactive_Co_z_A\t"
        "active_O_x_A\tactive_O_y_A\tactive_O_z_A\tminimum_distance_A\tminimum_pair"
    ]
    for site_index, active_oh in enumerate(active_oh_sites, start=1):
        states = make_site_states(reconstructed, active_oh, lattice)
        for state_name, atoms in states.items():
            directory = args.output / f"terminal_site{site_index:02d}" / state_name
            directory.mkdir(parents=True)
            title = f"JACS 6c06054 reconstructed Co10(OH)23 terminal site {site_index} {state_name}"
            write_poscar(directory / "POSCAR", title, lattice, atoms)
            write_incar(directory / "INCAR", title, atoms)
            (directory / "KPOINTS").write_text(
                "JACS 6c06054 reconstructed surface mesh\n0\nMonkhorst-Pack\n4 3 1\n0 0 0\n"
            )
            shutil.copy2(args.potcar, directory / "POTCAR")
            jobs.append(directory)
            counts = {symbol: sum(atom.symbol == symbol for atom in atoms) for symbol in ("Co", "H", "O")}
            minimum, pair = minimum_distance(atoms, lattice)
            active_o = active_oh[0]
            manifest.append(
                f"site{site_index:02d}\t{state_name}\t"
                f"Co{counts['Co']} H{counts['H']} O{counts['O']}\t"
                f"{active_co.cart[0]:.6f}\t{active_co.cart[1]:.6f}\t{active_co.cart[2]:.6f}\t"
                f"{active_o.cart[0]:.6f}\t{active_o.cart[1]:.6f}\t{active_o.cart[2]:.6f}\t"
                f"{minimum:.6f}\t{pair}"
            )

    write_jobs(args.output, jobs)
    (args.output / "manifest.tsv").write_text("\n".join(manifest) + "\n")
    (args.output / "METHOD.txt").write_text(
        "Exact source coordinates: Co8Co2.xsf from Oestreicher et al., "
        "Inorg. Chem. 2019, DOI 10.1021/acs.inorgchem.9b01252, as cited by "
        "JACS 2026 DOI 10.1021/jacs.6c06054.\n"
        "The two Cl atoms are removed. For each original tetrahedral terminal "
        "Co, three OH groups are added opposite its three lattice Co-O bonds, "
        "giving Co10(OH)24. One of the three top terminal OH groups is removed "
        "to form each Co10(OH)23 active-site branch.\n"
        "Reported VASP protocol: spin-polarized PBE+U (Co Ueff=4.5 eV), D3 "
        "zero damping, ENCUT=520 eV, 4x3x1 k mesh, 20 A vacuum, forces below "
        "0.02 eV/A, and first-order Methfessel-Paxton smearing.\n"
        "Validation targets from Figure 5/S28: reconstructed terminal sites "
        "approximately 0.60, 0.71, and 1.00 V overpotential; PDS OH->O.\n"
    )
    print(f"Prepared {len(jobs)} reconstructed terminal-site jobs in {args.output}")


if __name__ == "__main__":
    main()
