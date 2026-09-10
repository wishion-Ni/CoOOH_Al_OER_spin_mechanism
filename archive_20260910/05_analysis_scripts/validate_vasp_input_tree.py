#!/usr/bin/env python3
"""Validate a VASP input tree before Slurm submission."""

from __future__ import annotations

import argparse
import math
import re
from pathlib import Path


def parse_poscar(path: Path):
    lines = [line.strip() for line in path.read_text().splitlines() if line.strip()]
    scale = float(lines[1])
    lattice = [
        tuple(scale * float(value) for value in lines[index].split()[:3])
        for index in range(2, 5)
    ]
    species = lines[5].split()
    counts = [int(value) for value in lines[6].split()]
    cursor = 7
    if lines[cursor].lower().startswith("s"):
        cursor += 1
    direct = lines[cursor].lower().startswith("d")
    cursor += 1
    symbols = []
    coordinates = []
    for symbol, count in zip(species, counts):
        for _ in range(count):
            values = tuple(float(value) for value in lines[cursor].split()[:3])
            cursor += 1
            if not direct:
                raise ValueError(f"{path}: validator expects Direct coordinates")
            symbols.append(symbol)
            coordinates.append(values)
    return lattice, species, counts, symbols, coordinates


def cart(frac, lattice):
    return tuple(
        sum(frac[j] * lattice[j][i] for j in range(3))
        for i in range(3)
    )


def minimum_distance(lattice, symbols, coordinates):
    best = None
    pair = None
    for i in range(len(coordinates)):
        for j in range(i):
            delta = [coordinates[i][axis] - coordinates[j][axis] for axis in range(3)]
            delta = [value - round(value) for value in delta]
            distance = math.sqrt(sum(value * value for value in cart(delta, lattice)))
            if best is None or distance < best:
                best = distance
                pair = (symbols[j], j + 1, symbols[i], i + 1)
    return best, pair


def potcar_species(path: Path):
    titles = []
    for line in path.read_text(errors="ignore").splitlines():
        if "TITEL" in line:
            match = re.search(r"PAW_PBE\s+([A-Za-z]+)", line)
            if match:
                titles.append(match.group(1))
    return titles


def incar_value(path: Path, key: str):
    pattern = re.compile(rf"^\s*{re.escape(key)}\s*=\s*(.*?)\s*(?:[#!].*)?$", re.I)
    for line in path.read_text().splitlines():
        match = pattern.match(line)
        if match:
            return match.group(1).strip()
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    failures = []
    required = {
        "ENCUT": "520",
        "IVDW": "11",
        "ISPIN": "2",
        "EDIFFG": "-0.02",
        "LREAL": ".FALSE.",
        "ISYM": "0",
    }

    jobs = [
        line.strip()
        for line in (args.root / "jobs.list").read_text().splitlines()
        if line.strip()
    ]
    for relative in jobs:
        directory = args.root / relative
        lattice, species, counts, symbols, coordinates = parse_poscar(directory / "POSCAR")
        atom_count = sum(counts)
        titles = potcar_species(directory / "POTCAR")
        min_distance, pair = minimum_distance(lattice, symbols, coordinates)
        if titles != species:
            failures.append(f"{relative}: POTCAR {titles} != POSCAR {species}")
        if min_distance < 0.70:
            failures.append(f"{relative}: collision {pair} at {min_distance:.4f} A")
        if relative.startswith(("undoped/", "Al16_adjacent/")):
            for key, expected in required.items():
                actual = incar_value(directory / "INCAR", key)
                if actual is None or actual.upper() != expected.upper():
                    failures.append(f"{relative}: {key}={actual}, expected {expected}")
            magmom = incar_value(directory / "INCAR", "MAGMOM")
            if magmom is None or len(magmom.split()) != atom_count:
                failures.append(
                    f"{relative}: MAGMOM count "
                    f"{0 if magmom is None else len(magmom.split())} != {atom_count}"
                )
            if relative.startswith("Al16_adjacent/"):
                al_count = counts[species.index("Al")]
                metal_count = counts[species.index("Co")] + al_count
                fraction = al_count / metal_count
                if abs(fraction - 1.0 / 6.0) > 1e-10:
                    failures.append(f"{relative}: Al fraction {fraction}")
        print(
            f"{relative:28s} atoms={atom_count:3d} "
            f"species={','.join(species):9s} min={min_distance:.4f}A {pair}"
        )

    if failures:
        print("\nFAILED")
        for failure in failures:
            print(f"- {failure}")
        raise SystemExit(1)
    print(f"\nPASS: {len(jobs)} jobs validated")


if __name__ == "__main__":
    main()
