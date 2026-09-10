from __future__ import print_function

import os

import build_corrected_adsorbates_20260819 as build


def describe(path, target, adjacent, lattice):
    cell, symbols, _, coords = build.read_poscar(path)
    elements = []
    positions = []
    for symbol in symbols:
        for coord in coords[symbol]:
            elements.append(symbol)
            positions.append(coord)
    target_rows = sorted(
        (build.distance_mic(target, coord, cell), index + 1, elements[index])
        for index, coord in enumerate(positions)
        if elements[index] == "Co"
    )[:4]
    adjacent_rows = sorted(
        (build.distance_mic(adjacent, coord, cell), index + 1, elements[index])
        for index, coord in enumerate(positions)
        if elements[index] in ("Co", "Al")
    )[:4]
    print("PATH", path)
    print("TARGET_MATCHES", target_rows)
    print("ADJACENT_MATCHES", adjacent_rows)
    for index in (15, 16, 17, 20, 21, 22, 23, 50, 51):
        if index <= len(positions):
            print(
                "ATOM",
                index,
                elements[index - 1],
                "to_target",
                build.distance_mic(target, positions[index - 1], cell),
                "to_adjacent",
                build.distance_mic(adjacent, positions[index - 1], cell),
            )


def main():
    lattice, _, _, bare = build.read_poscar(os.path.join(build.SOURCE, "bare", "CONTCAR"))
    super_lattice = [build.vec_scale(lattice[0], build.NX), build.vec_scale(lattice[1], build.NY), lattice[2]]
    co_entries = []
    for copy_x in range(build.NX):
        for copy_y in range(build.NY):
            for local, coord in enumerate(bare["Co"]):
                co_entries.append((copy_x, copy_y, local, build.transform_base(coord, copy_x, copy_y)))
    active = [entry for entry in co_entries if entry[:3] == (1, 0, 0)][0][3]
    al_entries = build.choose_al_sites(co_entries, active, super_lattice)
    adjacent = al_entries[0][3]
    print("CONCEPT_ACTIVE", active)
    print("CONCEPT_ADJACENT", adjacent)
    print("AL_ENTRIES", [(entry[0], entry[1], entry[2] + 1) for entry in al_entries])
    paths = (
        os.path.join(build.PARENT, "Al16_adjacent", "bare", "POSCAR"),
        os.path.join(build.PARENT, "electronic_preconverge_20260810", "Al16_adjacent", "bare", "POSCAR"),
        os.path.join(build.PARENT, "electronic_preconverge_20260810", "Al16_adjacent", "bare", "CONTCAR"),
    )
    for path in paths:
        describe(path, active, adjacent, super_lattice)


if __name__ == "__main__":
    main()
