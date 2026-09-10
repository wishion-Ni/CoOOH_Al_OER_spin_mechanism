from __future__ import print_function

import os

import build_corrected_adsorbates_20260819 as build


def nearest_co(oxygen, coords, lattice):
    return min(
        (build.distance_mic(oxygen, coord, lattice), index + 1)
        for index, coord in enumerate(coords["Co"])
    )


def main():
    lattice, _, _, bare = build.read_poscar(os.path.join(build.SOURCE, "bare", "CONTCAR"))
    _, _, _, bare_seed = build.read_poscar(os.path.join(build.SOURCE, "bare", "POSCAR"))
    for state in ("OH", "O", "OOH_o03"):
        _, _, _, relaxed = build.read_poscar(os.path.join(build.SOURCE, state, "CONTCAR"))
        _, _, _, seed = build.read_poscar(os.path.join(build.SOURCE, state, "POSCAR"))
        base = bare_seed if state == "OOH_o03" else bare
        source = seed if state == "OOH_o03" else relaxed
        extras = build.state_extras(base, source, lattice)
        print("STATE", state, "EXTRA_O", len(extras["O"]), "EXTRA_H", len(extras["H"]))
        for index, oxygen in enumerate(extras["O"]):
            closest = nearest_co(oxygen, source, lattice)
            co1 = build.distance_mic(oxygen, source["Co"][0], lattice)
            print("O", index + 1, "nearest_Co", closest[1], "distance", closest[0], "Co1_distance", co1)


if __name__ == "__main__":
    main()
