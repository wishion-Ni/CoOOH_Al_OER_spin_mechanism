from __future__ import print_function

import os

import deploy_lobster_preconverged_20260819 as deployment


BASE_O_COUNT = 138


def active_adsorbate_oxygen_indices(state, active_index, elements, positions, cell):
    if state == "bare":
        return []
    oxygen_indices = [index for index, element in enumerate(elements, 1) if element == "O"]
    extra_oxygen = oxygen_indices[BASE_O_COUNT:]
    proximal = min(
        extra_oxygen,
        key=lambda index: deployment.distance(
            positions[active_index - 1], positions[index - 1], cell
        ),
    )
    if state != "OOH_o03":
        return [proximal]
    distal = min(
        [index for index in oxygen_indices if index != proximal],
        key=lambda index: deployment.distance(
            positions[proximal - 1], positions[index - 1], cell
        ),
    )
    return [proximal, distal]


def append_pair(rows, role, first, second, elements, positions, cell):
    pair_distance = deployment.distance(positions[first - 1], positions[second - 1], cell)
    rows.append((role, first, second, pair_distance))
    return pair_distance


def main():
    if not os.path.isdir(deployment.DEST):
        deployment.fail("deployment root missing: %s" % deployment.DEST)
    all_rows = []

    for branch, state, active_index, adjacent_index in deployment.CASES:
        source = os.path.join(deployment.SOURCE, branch, state)
        case = os.path.join(deployment.DEST, branch, state)
        cell, elements, positions = deployment.read_poscar(os.path.join(source, "POSCAR"))
        expected_adjacent = "Al" if branch == "Al16_adjacent" else "Co"
        pairs = []
        adsorbate_oxygen = active_adsorbate_oxygen_indices(
            state, active_index, elements, positions, cell
        )

        if state == "bare":
            framework_distance, framework_oxygen = deployment.nearest_index(
                active_index, {"O"}, elements, positions, cell
            )
            pairs.append(("Co-Oframework", active_index, framework_oxygen, framework_distance))
        elif state in ("OH", "O"):
            ads_oxygen = adsorbate_oxygen[0]
            co_o = append_pair(pairs, "Co-Oads", active_index, ads_oxygen, elements, positions, cell)
            if not 1.4 < co_o < 2.6:
                nearest_co_distance, nearest_co = deployment.nearest_index(
                    ads_oxygen, {"Co"}, elements, positions, cell
                )
                deployment.fail(
                    "implausible Co-Oads %.6f in %s/%s; O%d nearest Co%d %.6f"
                    % (co_o, branch, state, ads_oxygen, nearest_co, nearest_co_distance)
                )
            if state == "OH":
                oh_distance, ads_h = deployment.nearest_index(
                    ads_oxygen, {"H"}, elements, positions, cell
                )
                if not 0.8 < oh_distance < 1.2:
                    deployment.fail("implausible adsorbate O-H %.6f in %s/%s" % (oh_distance, branch, state))
                pairs.append(("Oads-Hads", ads_oxygen, ads_h, oh_distance))
        else:
            first_o, second_o = adsorbate_oxygen
            first_co = deployment.distance(positions[active_index - 1], positions[first_o - 1], cell)
            second_co = deployment.distance(positions[active_index - 1], positions[second_o - 1], cell)
            proximal, distal = (first_o, second_o) if first_co <= second_co else (second_o, first_o)
            co_o = append_pair(pairs, "Co-Oads", active_index, proximal, elements, positions, cell)
            oo = append_pair(pairs, "Oads-Odistal", proximal, distal, elements, positions, cell)
            if not 1.4 < co_o < 2.6 or not 1.1 < oo < 1.8:
                deployment.fail(
                    "implausible OOH geometry Co-O %.6f O-O %.6f in %s/%s"
                    % (co_o, oo, branch, state)
                )
            oh_distance, ads_h = deployment.nearest_index(
                distal, {"H"}, elements, positions, cell
            )
            if 0.8 < oh_distance < 1.2:
                pairs.append(("Odistal-Hads", distal, ads_h, oh_distance))

        hydroxyl = deployment.find_hydroxyl_oxygen(
            adjacent_index, elements, positions, cell, excluded=adsorbate_oxygen
        )
        if hydroxyl is not None:
            metal_o_distance, hydroxyl_oxygen, hydroxyl_h, hydroxyl_oh_distance = hydroxyl
            pairs.append((expected_adjacent + "-OH", adjacent_index, hydroxyl_oxygen, metal_o_distance))
            pairs.append(("OH-H", hydroxyl_oxygen, hydroxyl_h, hydroxyl_oh_distance))

        bridge = deployment.find_bridge(
            active_index, adjacent_index, elements, positions, cell, excluded=adsorbate_oxygen
        )
        _, _, bridge_oxygen, active_o_distance, adjacent_o_distance = bridge
        if active_o_distance > 2.7 or adjacent_o_distance > 2.7:
            deployment.fail("no plausible Co-O-M bridge in %s/%s" % (branch, state))
        pairs.append(("Co-Obridge", active_index, bridge_oxygen, active_o_distance))
        pairs.append((expected_adjacent + "-Obridge", adjacent_index, bridge_oxygen, adjacent_o_distance))

        deployment.write_lobsterin(os.path.join(case, "lobsterin"), pairs)
        with open(os.path.join(case, "PAIR_INFO.tsv"), "w") as handle:
            handle.write("role\tatom1\telement1\tatom2\telement2\tdistance_A\n")
            for role, first, second, pair_distance in pairs:
                row = (
                    branch,
                    state,
                    role,
                    first,
                    elements[first - 1],
                    second,
                    elements[second - 1],
                    pair_distance,
                )
                all_rows.append(row)
                handle.write(
                    "%s\t%d\t%s\t%d\t%s\t%.6f\n"
                    % (role, first, elements[first - 1], second, elements[second - 1], pair_distance)
                )

    with open(os.path.join(deployment.DEST, "pair_manifest.tsv"), "w") as handle:
        handle.write("branch\tstate\trole\tatom1\telement1\tatom2\telement2\tdistance_A\n")
        for row in all_rows:
            handle.write("\t".join(str(value) for value in row[:-1]) + "\t%.6f\n" % row[-1])

    for row in all_rows:
        print("\t".join(str(value) for value in row[:-1]) + "\t%.6f" % row[-1])


if __name__ == "__main__":
    main()
