from __future__ import print_function

import hashlib
import os

import deploy_lobster_preconverged_20260819 as vasp


ROOT = (
    "sfs/CoOH/cp2k/Al16/oer/spin_config_scan_site03_5OH_current_20260714/"
    "vasp_jacs6c06054_reconstructed_exact_Al16_3x2_20260809"
)
CORRECTED = os.path.join(ROOT, "corrected_adsorbates_20260819")


def fail(message):
    raise RuntimeError(message)


def digest(path):
    value = hashlib.sha256()
    with open(path, "rb") as handle:
        while True:
            block = handle.read(1024 * 1024)
            if not block:
                break
            value.update(block)
    return value.hexdigest()


def composition(elements):
    order = []
    counts = {}
    for element in elements:
        if element not in counts:
            order.append(element)
            counts[element] = 0
        counts[element] += 1
    return "".join("%s%d" % (element, counts[element]) for element in order)


def parse_incar(path):
    tags = {}
    for line in open(path):
        clean = line.split("#", 1)[0].split("!", 1)[0].strip()
        if "=" not in clean:
            continue
        key, value = clean.split("=", 1)
        tags[key.strip().upper()] = value.strip()
    return tags


def nearest_metal(origin, elements, positions, cell):
    return min(
        (vasp.distance(origin, position, cell), index + 1, elements[index])
        for index, position in enumerate(positions)
        if elements[index] in ("Co", "Al")
    )


def minimum_pair(elements, positions, cell):
    best = None
    for first in range(len(positions)):
        for second in range(first + 1, len(positions)):
            value = vasp.distance(positions[first], positions[second], cell)
            if best is None or value < best[0]:
                best = (value, first + 1, elements[first], second + 1, elements[second])
    return best


def main():
    audit = []
    with open(os.path.join(CORRECTED, "construction_audit.tsv")) as handle:
        header = handle.readline().rstrip().split("\t")
        for line in handle:
            values = line.rstrip().split("\t")
            audit.append(dict(zip(header, values)))

    rows = []
    for record in audit:
        branch = record["branch"]
        state = record["state"]
        case = os.path.join(CORRECTED, "electronic_preconverge", branch, state)
        for filename in ("POSCAR", "POTCAR", "KPOINTS", "INCAR"):
            path = os.path.join(case, filename)
            if not os.path.isfile(path) or os.path.getsize(path) == 0:
                fail("missing input %s/%s/%s" % (branch, state, filename))

        cell, elements, positions = vasp.read_poscar(os.path.join(case, "POSCAR"))
        if composition(elements) != record["composition"]:
            fail("composition mismatch %s/%s" % (branch, state))
        active = int(record["active_Co_index"])
        adjacent = int(record["adjacent_index"])
        oxygen = [int(value) for value in record["active_O_indices"].split(",")]
        hydrogen = [] if record["active_H_indices"] == "NA" else [
            int(value) for value in record["active_H_indices"].split(",")
        ]
        if elements[active - 1] != "Co":
            fail("active index is not Co %s/%s" % (branch, state))
        expected_adjacent = "Al" if branch == "Al16_adjacent" else "Co"
        if elements[adjacent - 1] != expected_adjacent:
            fail("adjacent index mismatch %s/%s" % (branch, state))
        if any(elements[index - 1] != "O" for index in oxygen):
            fail("active oxygen index mismatch %s/%s" % (branch, state))
        if any(elements[index - 1] != "H" for index in hydrogen):
            fail("active hydrogen index mismatch %s/%s" % (branch, state))

        co_o = min(vasp.distance(positions[active - 1], positions[index - 1], cell) for index in oxygen)
        anchor = min(oxygen, key=lambda index: vasp.distance(positions[active - 1], positions[index - 1], cell))
        nearest = nearest_metal(positions[anchor - 1], elements, positions, cell)
        if nearest[1] != active or not 1.45 <= co_o <= 2.30:
            fail("site validation failed %s/%s" % (branch, state))

        oo = -1.0
        if state == "OOH_o03":
            oo = vasp.distance(positions[oxygen[0] - 1], positions[oxygen[1] - 1], cell)
            if not 1.10 <= oo <= 1.70:
                fail("OOH bond failed %s/%s" % (branch, state))
        non_group_o = [
            index + 1 for index, element in enumerate(elements)
            if element == "O" and index + 1 not in oxygen
        ]
        nearest_non_group_o = min(
            vasp.distance(positions[group_index - 1], positions[other_index - 1], cell)
            for group_index in oxygen
            for other_index in non_group_o
        )
        if nearest_non_group_o < 1.65:
            fail("unintended O-O contact %s/%s %.6f" % (branch, state, nearest_non_group_o))

        oh = -1.0
        if hydrogen:
            oh = min(
                vasp.distance(positions[h_index - 1], positions[o_index - 1], cell)
                for h_index in hydrogen for o_index in oxygen
            )
            if not 0.75 <= oh <= 1.25:
                fail("O-H validation failed %s/%s" % (branch, state))

        bare = os.path.join(ROOT, branch, "bare")
        bare_cell, bare_elements, bare_positions = vasp.read_poscar(os.path.join(bare, "POSCAR"))
        metal_count = sum(1 for element in bare_elements if element in ("Co", "Al"))
        metal_shift = max(
            vasp.distance(positions[index], bare_positions[index], cell)
            for index in range(metal_count)
        )
        if metal_shift > 1.0e-8:
            fail("metal framework changed %s/%s %.9f" % (branch, state, metal_shift))
        if digest(os.path.join(case, "POTCAR")) != digest(os.path.join(bare, "POTCAR")):
            fail("POTCAR mismatch %s/%s" % (branch, state))
        if digest(os.path.join(case, "KPOINTS")) != digest(os.path.join(bare, "KPOINTS")):
            fail("KPOINTS mismatch %s/%s" % (branch, state))

        tags = parse_incar(os.path.join(case, "INCAR"))
        required = {
            "ISTART": "0",
            "ICHARG": "2",
            "EDIFF": "1E-4",
            "ALGO": "Fast",
            "IBRION": "-1",
            "NSW": "0",
            "LREAL": "Auto",
            "ENCUT": "520",
        }
        for key, expected in required.items():
            if tags.get(key, "").lower() != expected.lower():
                fail("INCAR %s mismatch %s/%s" % (key, branch, state))

        closest = minimum_pair(elements, positions, cell)
        if closest[0] < 0.65:
            fail("atomic overlap %s/%s %.6f" % (branch, state, closest[0]))
        rows.append(
            (
                branch,
                state,
                len(elements),
                active,
                adjacent,
                co_o,
                oo,
                oh,
                nearest_non_group_o,
                metal_shift,
                closest[0],
                "%s%d-%s%d" % (closest[2], closest[1], closest[4], closest[3]),
                "independent_valid",
            )
        )

    output = os.path.join(CORRECTED, "independent_validation.tsv")
    with open(output, "w") as handle:
        handle.write(
            "branch\tstate\tatoms\tactive_Co\tadjacent\tCo_O_A\tO_O_A\tO_H_A\t"
            "nearest_non_group_O_A\tmax_metal_shift_A\tminimum_pair_A\tminimum_pair\tstatus\n"
        )
        for row in rows:
            handle.write("\t".join(str(value) for value in row[:5]))
            handle.write("\t%.6f\t%.6f\t%.6f\t%.6f\t%.9f\t%.6f\t%s\t%s\n" % row[5:])
    print(output)
    for row in rows:
        print("\t".join(str(value) for value in row))


if __name__ == "__main__":
    main()
