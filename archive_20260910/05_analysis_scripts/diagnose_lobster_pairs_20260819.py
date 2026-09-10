from __future__ import print_function

import os

import deploy_lobster_preconverged_20260819 as deployment


BASE_O_COUNT = 138


def main():
    for branch, state, active_index, adjacent_index in deployment.CASES:
        if state == "bare":
            continue
        path = os.path.join(deployment.SOURCE, branch, state, "POSCAR")
        cell, elements, positions = deployment.read_poscar(path)
        oxygen_indices = [index for index, element in enumerate(elements, 1) if element == "O"]
        active_local = BASE_O_COUNT + 3
        expected_active = [oxygen_indices[active_local - 1]]
        if state == "OOH_o03":
            expected_active.append(oxygen_indices[active_local])
        print("---%s/%s designated Co%d adjacent %s%d---" % (
            branch, state, active_index, elements[adjacent_index - 1], adjacent_index
        ))
        for oxygen_index in expected_active:
            active_distance = deployment.distance(
                positions[active_index - 1], positions[oxygen_index - 1], cell
            )
            metal_distance, nearest_metal = deployment.nearest_index(
                oxygen_index, {"Co", "Al"}, elements, positions, cell
            )
            print(
                "constructed active-extra O%d: designated Co-O %.6f; nearest %s%d %.6f"
                % (
                    oxygen_index,
                    active_distance,
                    elements[nearest_metal - 1],
                    nearest_metal,
                    metal_distance,
                )
            )
        if len(expected_active) == 2:
            print(
                "constructed active O-O %.6f"
                % deployment.distance(
                    positions[expected_active[0] - 1], positions[expected_active[1] - 1], cell
                )
            )
        if state != "OOH_o03":
            continue
        oxygen = sorted(
            (
                deployment.distance(positions[active_index - 1], positions[index - 1], cell),
                index,
            )
            for index, element in enumerate(elements, 1)
            if element == "O"
        )
        print("nearest oxygens to designated active Co%d:" % active_index)
        for co_distance, oxygen_index in oxygen[:16]:
            oo_distance, nearest_o = deployment.nearest_index(
                oxygen_index, {"O"}, elements, positions, cell, excluded=[oxygen_index]
            )
            oh_distance, nearest_h = deployment.nearest_index(
                oxygen_index, {"H"}, elements, positions, cell
            )
            print(
                "O%d Co-O %.6f nearest O%d %.6f nearest H%d %.6f"
                % (oxygen_index, co_distance, nearest_o, oo_distance, nearest_h, oh_distance)
            )
        close_pairs = []
        for offset, first in enumerate(oxygen_indices):
            for second in oxygen_indices[offset + 1:]:
                value = deployment.distance(positions[first - 1], positions[second - 1], cell)
                if value < 2.0:
                    close_pairs.append((value, first, second))
        print("O-O pairs below 2.0 A:", sorted(close_pairs)[:20])


if __name__ == "__main__":
    main()
