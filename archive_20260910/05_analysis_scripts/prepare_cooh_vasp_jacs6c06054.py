#!/usr/bin/env python3
"""Prepare paired undoped/Al16 CoOOH(0001) VASP OER calculations."""

from __future__ import annotations

import argparse
import math
import shutil
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Atom:
    symbol: str
    cart: tuple[float, float, float]
    layer: int = 0


def vec_add(a, b):
    return tuple(x + y for x, y in zip(a, b))


def vec_sub(a, b):
    return tuple(x - y for x, y in zip(a, b))


def vec_scale(a, scale):
    return tuple(scale * x for x in a)


def norm(a):
    return math.sqrt(sum(x * x for x in a))


def unit(a):
    length = norm(a)
    return tuple(x / length for x in a)


def matvec(frac, lattice):
    return tuple(
        frac[0] * lattice[0][i]
        + frac[1] * lattice[1][i]
        + frac[2] * lattice[2][i]
        for i in range(3)
    )


def parse_poscar(path: Path):
    lines = [line.strip() for line in path.read_text().splitlines() if line.strip()]
    scale = float(lines[1])
    lattice = [
        tuple(scale * float(value) for value in lines[index].split()[:3])
        for index in range(2, 5)
    ]
    symbols = lines[5].split()
    counts = [int(value) for value in lines[6].split()]
    cursor = 7
    if lines[cursor].lower().startswith("s"):
        cursor += 1
    direct = lines[cursor].lower().startswith("d")
    cursor += 1
    atoms = []
    for symbol, count in zip(symbols, counts):
        for _ in range(count):
            values = tuple(float(value) for value in lines[cursor].split()[:3])
            cursor += 1
            cart = matvec(values, lattice) if direct else values
            atoms.append(Atom(symbol, cart))
    return lattice, atoms


def periodic_xy_distance(a, b, lattice):
    best = None
    for i in (-1, 0, 1):
        for j in (-1, 0, 1):
            shift = vec_add(vec_scale(lattice[0], i), vec_scale(lattice[1], j))
            delta = vec_sub(vec_add(a, shift), b)
            distance = norm(delta)
            if best is None or distance < best:
                best = distance
    return best


def build_slab(source: Path):
    lattice, source_atoms = parse_poscar(source)
    nx, ny = 2, 2
    slab_lattice = [
        vec_scale(lattice[0], nx),
        vec_scale(lattice[1], ny),
        (0.0, 0.0, 1.0),
    ]
    unwrapped = []
    for atom in source_atoms:
        fractional_z = atom.cart[2] / lattice[2][2]
        if fractional_z < 0.2:
            fractional_z += 1.0
        unwrapped.append(Atom(atom.symbol, (atom.cart[0], atom.cart[1], fractional_z * lattice[2][2])))

    atoms = []
    for i in range(nx):
        for j in range(ny):
            shift = vec_add(vec_scale(lattice[0], i), vec_scale(lattice[1], j))
            for atom in unwrapped:
                atoms.append(Atom(atom.symbol, vec_add(atom.cart, shift)))

    min_z = min(atom.cart[2] for atom in atoms)
    max_z = max(atom.cart[2] for atom in atoms)
    vacuum = 20.0
    shift_z = 0.5 * vacuum - min_z
    atoms = [
        Atom(atom.symbol, (atom.cart[0], atom.cart[1], atom.cart[2] + shift_z))
        for atom in atoms
    ]
    slab_lattice[2] = (0.0, 0.0, max_z - min_z + vacuum)

    co_z = sorted({round(atom.cart[2], 6) for atom in atoms if atom.symbol == "Co"})
    for atom in atoms:
        if atom.symbol == "Co":
            atom.layer = min(range(len(co_z)), key=lambda idx: abs(atom.cart[2] - co_z[idx]))

    top_co = max((atom for atom in atoms if atom.symbol == "Co"), key=lambda atom: atom.cart[2])
    top_layer = [atom for atom in atoms if atom.symbol == "Co" and atom.layer == top_co.layer]
    center = vec_scale(vec_add(slab_lattice[0], slab_lattice[1]), 0.5)
    active = min(top_layer, key=lambda atom: periodic_xy_distance(atom.cart, center, slab_lattice))

    top_oxygen = [
        atom
        for atom in atoms
        if atom.symbol == "O" and 0.2 < atom.cart[2] - active.cart[2] < 2.5
    ]
    terminal_o = min(
        top_oxygen,
        key=lambda atom: periodic_xy_distance(atom.cart, active.cart, slab_lattice),
    )
    hydrogens = [atom for atom in atoms if atom.symbol == "H"]
    terminal_h = min(
        hydrogens,
        key=lambda atom: periodic_xy_distance(atom.cart, terminal_o.cart, slab_lattice),
    )
    if periodic_xy_distance(terminal_h.cart, terminal_o.cart, slab_lattice) > 1.3:
        raise RuntimeError("Could not identify the terminal O-H group")

    base = [atom for atom in atoms if atom is not terminal_o and atom is not terminal_h]
    return slab_lattice, base, active, terminal_o, terminal_h


def make_states(base, terminal_o, terminal_h, lattice):
    states = {
        "bare": list(base),
        "OH": list(base) + [Atom("O", terminal_o.cart), Atom("H", terminal_h.cart)],
        "O": list(base) + [Atom("O", terminal_o.cart)],
    }
    a_hat = unit(lattice[0])
    b_hat = unit(lattice[1])
    z_hat = (0.0, 0.0, 1.0)
    for index, tangent in enumerate((a_hat, b_hat, unit(vec_sub(b_hat, a_hat))), start=1):
        oo_axis = unit(vec_add(vec_scale(tangent, 0.52), vec_scale(z_hat, 0.85)))
        oh_axis = unit(vec_add(vec_scale(tangent, -0.35), vec_scale(z_hat, 0.94)))
        distal_o = vec_add(terminal_o.cart, vec_scale(oo_axis, 1.35))
        distal_h = vec_add(distal_o, vec_scale(oh_axis, 0.98))
        states[f"OOH_o{index:02d}"] = list(base) + [
            Atom("O", terminal_o.cart),
            Atom("O", distal_o),
            Atom("H", distal_h),
        ]
    return states


def dope_al16(atoms, active, lattice):
    metals = [atom for atom in atoms if atom.symbol == "Co"]
    same_layer = [atom for atom in metals if atom.layer == active.layer and atom is not active]
    adjacent = min(
        same_layer,
        key=lambda atom: periodic_xy_distance(atom.cart, active.cart, lattice),
    )
    other_layers = [atom for atom in metals if atom.layer != active.layer]
    remote = max(
        other_layers,
        key=lambda atom: periodic_xy_distance(atom.cart, active.cart, lattice),
    )
    dopants = {id(adjacent), id(remote)}
    doped = [
        Atom("Al" if id(atom) in dopants else atom.symbol, atom.cart, atom.layer)
        for atom in atoms
    ]
    return doped, (adjacent.cart, remote.cart)


def fractional(cart, lattice):
    a, b, c = lattice
    det = a[0] * b[1] - a[1] * b[0]
    x = (cart[0] * b[1] - cart[1] * b[0]) / det
    y = (a[0] * cart[1] - a[1] * cart[0]) / det
    z = cart[2] / c[2]
    return x % 1.0, y % 1.0, z


def write_poscar(path, title, lattice, atoms, species):
    ordered = [atom for symbol in species for atom in atoms if atom.symbol == symbol]
    counts = [sum(atom.symbol == symbol for atom in atoms) for symbol in species]
    lines = [title, "1.0"]
    lines.extend("  " + "  ".join(f"{value:20.12f}" for value in vector) for vector in lattice)
    lines.append("  " + "  ".join(species))
    lines.append("  " + "  ".join(str(value) for value in counts))
    lines.append("Direct")
    for atom in ordered:
        lines.append("  " + "  ".join(f"{value:18.12f}" for value in fractional(atom.cart, lattice)))
    path.write_text("\n".join(lines) + "\n")


def magnetic_moments(atoms, species):
    ordered = [atom for symbol in species for atom in atoms if atom.symbol == symbol]
    values = []
    for atom in ordered:
        if atom.symbol == "Co":
            values.append("3.0" if atom.layer % 2 == 0 else "-3.0")
        else:
            values.append("0.0")
    return " ".join(values)


def write_surface_incar(path, title, atoms, species):
    ldau_l = ["2" if symbol == "Co" else "-1" for symbol in species]
    ldau_u = ["4.5" if symbol == "Co" else "0" for symbol in species]
    zeros = ["0" for _ in species]
    text = f"""SYSTEM = {title}
ISTART = 0
ICHARG = 2
ISPIN = 2
MAGMOM = {magnetic_moments(atoms, species)}
LDAU = .TRUE.
LDAUTYPE = 2
LDAUL = {' '.join(ldau_l)}
LDAUU = {' '.join(ldau_u)}
LDAUJ = {' '.join(zeros)}
LMAXMIX = 4
GGA = PE
IVDW = 11
ENCUT = 520
PREC = Accurate
EDIFF = 1E-6
NELM = 240
NELMIN = 6
ALGO = Normal
ISMEAR = 0
SIGMA = 0.05
IBRION = 2
NSW = 300
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
    path.write_text(text)


def write_kpoints(path, mesh=(4, 3, 1)):
    path.write_text(
        "JACS 6c06054 reported surface mesh\n"
        "0\n"
        "Monkhorst-Pack\n"
        f"{mesh[0]} {mesh[1]} {mesh[2]}\n"
        "0 0 0\n"
    )


def write_gas(root, gas_potcars):
    molecules = {
        "gas_H2": (
            ["H"],
            [Atom("H", (10.0, 10.0, 9.63)), Atom("H", (10.0, 10.0, 10.37))],
        ),
        "gas_H2O": (
            ["H", "O"],
            [
                Atom("H", (10.76, 10.0, 10.59)),
                Atom("H", (9.24, 10.0, 10.59)),
                Atom("O", (10.0, 10.0, 10.0)),
            ],
        ),
    }
    lattice = [(20.0, 0.0, 0.0), (0.0, 20.0, 0.0), (0.0, 0.0, 20.0)]
    for name, (species, atoms) in molecules.items():
        directory = root / name
        directory.mkdir(parents=True, exist_ok=True)
        write_poscar(directory / "POSCAR", name, lattice, atoms, species)
        shutil.copy2(gas_potcars[name], directory / "POTCAR")
        (directory / "KPOINTS").write_text("Gamma only\n0\nGamma\n1 1 1\n0 0 0\n")
        (directory / "INCAR").write_text(
            f"""SYSTEM = {name}
ISTART = 0
ICHARG = 2
ISPIN = 1
GGA = PE
IVDW = 11
ENCUT = 520
PREC = Accurate
EDIFF = 1E-7
NELM = 200
ALGO = Normal
ISMEAR = 0
SIGMA = 0.02
IBRION = 2
NSW = 100
ISIF = 2
EDIFFG = -0.01
LREAL = .FALSE.
ADDGRID = .TRUE.
LASPH = .TRUE.
LWAVE = .FALSE.
LCHARG = .FALSE.
ISYM = 0
NCORE = 4
"""
        )


def write_job_files(root, directories):
    (root / "jobs.list").write_text("\n".join(str(path.relative_to(root)) for path in directories) + "\n")
    (root / "vasp_array.slurm").write_text(
        f"""#!/bin/bash
#SBATCH --job-name=CoOH_VASP_JACS
#SBATCH --nodes=1
#SBATCH --ntasks=28
#SBATCH --partition=n28
#SBATCH --array=0-{len(directories) - 1}%3
#SBATCH --output=array_%A_%a.stdout
#SBATCH --error=array_%A_%a.stderr

set -eo pipefail
ROOT="$(pwd)"
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
    parser.add_argument("--undoped-potcar", type=Path, required=True)
    parser.add_argument("--doped-potcar", type=Path, required=True)
    parser.add_argument("--h2-potcar", type=Path, required=True)
    parser.add_argument("--h2o-potcar", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    args.output.mkdir(parents=True, exist_ok=False)
    lattice, base, active, terminal_o, terminal_h = build_slab(args.source)
    states = make_states(base, terminal_o, terminal_h, lattice)
    jobs = []
    manifest = [
        "system\tstate\tformula\tactive_Co_x_A\tactive_Co_y_A\tactive_Co_z_A\tdopant_positions_A"
    ]

    for system in ("undoped", "Al16_adjacent"):
        for state, atoms in states.items():
            dopant_text = "none"
            if system == "Al16_adjacent":
                atoms, dopants = dope_al16(atoms, active, lattice)
                dopant_text = ";".join(",".join(f"{value:.6f}" for value in position) for position in dopants)
                species = ["Co", "Al", "H", "O"]
                potcar = args.doped_potcar
            else:
                species = ["Co", "H", "O"]
                potcar = args.undoped_potcar
            directory = args.output / system / state
            directory.mkdir(parents=True)
            title = f"{system} CoOOH(0001) {state}; JACS 6c06054 protocol"
            write_poscar(directory / "POSCAR", title, lattice, atoms, species)
            write_surface_incar(directory / "INCAR", title, atoms, species)
            write_kpoints(directory / "KPOINTS")
            shutil.copy2(potcar, directory / "POTCAR")
            jobs.append(directory)
            formula = " ".join(
                f"{symbol}{sum(atom.symbol == symbol for atom in atoms)}" for symbol in species
            )
            manifest.append(
                f"{system}\t{state}\t{formula}\t"
                f"{active.cart[0]:.6f}\t{active.cart[1]:.6f}\t{active.cart[2]:.6f}\t{dopant_text}"
            )

    write_gas(
        args.output,
        {"gas_H2": args.h2_potcar, "gas_H2O": args.h2o_potcar},
    )
    jobs.extend((args.output / "gas_H2", args.output / "gas_H2O"))
    write_job_files(args.output, jobs)
    (args.output / "manifest.tsv").write_text("\n".join(manifest) + "\n")
    (args.output / "METHOD.txt").write_text(
        "Reference: JACS 2026, DOI 10.1021/jacs.6c06054 and its SI.\n"
        "Reported settings reproduced: spin-polarized PBE+U (Co Ueff=4.5 eV), "
        "D3 zero damping (IVDW=11), ENCUT=520 eV, force threshold 0.02 eV/A, "
        "4x3x1 surface k mesh, and 20 A vacuum.\n"
        "Model: three-layer 2x2 CoOOH(0001) slab generated from the existing "
        "CoOOH bulk cell. The terminal surface OH on one lattice Co is removed "
        "to define *, then restored/replaced by OH, O, or OOH. Al16_adjacent "
        "contains 2 Al among 12 metal sites (16.7 at%) while retaining Co as "
        "the active center.\n"
        "Literature validation target: undoped lattice Co site PDS O->OOH and "
        "thermodynamic overpotential 4.41 V. This target is a validation check, "
        "not a fitting constraint.\n"
    )
    print(f"Prepared {len(jobs)} jobs in {args.output}")
    print(f"Active Co: {active.cart}")
    print(f"Removed terminal O-H: O={terminal_o.cart}, H={terminal_h.cart}")


if __name__ == "__main__":
    main()
