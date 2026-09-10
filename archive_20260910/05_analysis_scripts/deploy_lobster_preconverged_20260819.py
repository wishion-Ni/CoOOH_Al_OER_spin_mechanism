from __future__ import print_function

import math
import os
import re
import shutil
import sys
import codecs


ROOT = (
    "sfs/CoOH/cp2k/Al16/oer/spin_config_scan_site03_5OH_current_20260714/"
    "vasp_jacs6c06054_reconstructed_exact_Al16_3x2_20260809"
)
SOURCE = os.path.join(ROOT, "electronic_preconverge_20260810")
DEST = os.path.join(
    ROOT,
    "electronic_structure_al_contribution_20260818",
    "cohp_lobster_preconverged_20260819",
)

CASES = [
    ("Al16_adjacent", "bare", 16, 51),
    ("undoped_control", "bare", 21, 23),
    ("Al16_adjacent", "OH", 16, 51),
    ("undoped_control", "OH", 21, 23),
    ("Al16_adjacent", "O", 16, 51),
    ("undoped_control", "O", 21, 23),
    ("Al16_adjacent", "OOH_o03", 16, 51),
    ("undoped_control", "OOH_o03", 21, 23),
]

REQUIRED = ["INCAR", "KPOINTS", "POSCAR", "POTCAR", "OUTCAR", "WAVECAR", "vasprun.xml"]


def fail(message):
    raise RuntimeError(message)


def read_poscar(path):
    with open(path) as handle:
        lines = [line.rstrip() for line in handle]
    scale = float(lines[1].split()[0])
    cell = []
    for index in range(2, 5):
        cell.append([float(value) * scale for value in lines[index].split()[:3]])
    symbols = lines[5].split()
    counts = [int(value) for value in lines[6].split()]
    cursor = 7
    if lines[cursor].strip().lower().startswith("s"):
        cursor += 1
    direct = lines[cursor].strip().lower().startswith("d")
    cursor += 1
    elements = []
    positions = []
    for symbol, count in zip(symbols, counts):
        for _ in range(count):
            values = [float(value) for value in lines[cursor].split()[:3]]
            cursor += 1
            if direct:
                positions.append(values)
            else:
                positions.append(cart_to_frac([value * scale for value in values], cell))
            elements.append(symbol)
    return cell, elements, positions


def inverse3(matrix):
    a, b, c = matrix[0]
    d, e, f = matrix[1]
    g, h, i = matrix[2]
    determinant = a * (e * i - f * h) - b * (d * i - f * g) + c * (d * h - e * g)
    if abs(determinant) < 1.0e-14:
        fail("singular cell")
    return [
        [(e * i - f * h) / determinant, (c * h - b * i) / determinant, (b * f - c * e) / determinant],
        [(f * g - d * i) / determinant, (a * i - c * g) / determinant, (c * d - a * f) / determinant],
        [(d * h - e * g) / determinant, (b * g - a * h) / determinant, (a * e - b * d) / determinant],
    ]


def cart_to_frac(cart, cell):
    # POSCAR lattice vectors are rows; cart = frac * cell.
    inverse = inverse3(cell)
    return [
        cart[0] * inverse[0][column]
        + cart[1] * inverse[1][column]
        + cart[2] * inverse[2][column]
        for column in range(3)
    ]


def frac_delta_to_cart(delta, cell):
    return [sum(delta[row] * cell[row][column] for row in range(3)) for column in range(3)]


def distance(first, second, cell):
    best = None
    for tx in (-1, 0, 1):
        for ty in (-1, 0, 1):
            for tz in (-1, 0, 1):
                delta = [
                    second[0] - first[0] + tx,
                    second[1] - first[1] + ty,
                    second[2] - first[2] + tz,
                ]
                cart = frac_delta_to_cart(delta, cell)
                value = math.sqrt(sum(component * component for component in cart))
                if best is None or value < best:
                    best = value
    return best


def nearest_index(origin_index, allowed, elements, positions, cell, excluded=None):
    excluded = set(excluded or [])
    candidates = []
    for index, element in enumerate(elements, 1):
        if index in excluded or element not in allowed:
            continue
        candidates.append((distance(positions[origin_index - 1], positions[index - 1], cell), index))
    if not candidates:
        fail("no candidate for atom %d" % origin_index)
    return min(candidates)


def parse_outcar(path):
    with codecs.open(path, "r", encoding="utf-8", errors="ignore") as handle:
        text = handle.read()
    if "General timing and accounting informations" not in text:
        fail("OUTCAR lacks normal VASP termination: %s" % path)
    matches = re.findall(r"NBANDS\s*=\s*(\d+)", text)
    if not matches:
        fail("NBANDS missing in %s" % path)
    nkpts = re.findall(r"NKPTS\s*=\s*(\d+)", text)
    nelect = re.findall(r"NELECT\s*=\s*([0-9.]+)", text)
    return int(matches[-1]), int(nkpts[-1]) if nkpts else -1, float(nelect[-1]) if nelect else -1.0


def recommended_orbitals(elements):
    # pbeVaspFit2015 minimal recommended valence manifold used only as a conservative pre-check.
    orbitals = {"H": 1, "O": 4, "Al": 4, "Co": 6}
    return sum(orbitals[element] for element in elements)


def find_hydroxyl_oxygen(metal_index, elements, positions, cell, excluded=None):
    excluded = set(excluded or [])
    candidates = []
    for oxygen_index, element in enumerate(elements, 1):
        if element != "O" or oxygen_index in excluded:
            continue
        h_distance, h_index = nearest_index(
            oxygen_index, {"H"}, elements, positions, cell
        )
        if h_distance > 1.25:
            continue
        metal_distance = distance(
            positions[metal_index - 1], positions[oxygen_index - 1], cell
        )
        candidates.append((metal_distance, oxygen_index, h_index, h_distance))
    if not candidates:
        return None
    return min(candidates)


def find_bridge(active_index, adjacent_index, elements, positions, cell, excluded=None):
    excluded = set(excluded or [])
    candidates = []
    for oxygen_index, element in enumerate(elements, 1):
        if element != "O" or oxygen_index in excluded:
            continue
        active_distance = distance(
            positions[active_index - 1], positions[oxygen_index - 1], cell
        )
        adjacent_distance = distance(
            positions[adjacent_index - 1], positions[oxygen_index - 1], cell
        )
        score = max(active_distance, adjacent_distance)
        candidates.append((score, active_distance + adjacent_distance, oxygen_index, active_distance, adjacent_distance))
    return min(candidates)


def atom_label(index, elements):
    return "%s%d" % (elements[index - 1], index)


def write_lobsterin(path, pairs):
    lines = [
        "COHPstartEnergy -15.0",
        "COHPendEnergy 5.0",
        "basisSet pbeVaspFit2015",
        "useRecommendedBasisFunctions",
        "gaussianSmearingWidth 0.05",
    ]
    seen = set()
    for _, first, second, _ in pairs:
        key = tuple(sorted((first, second)))
        if key in seen:
            continue
        seen.add(key)
        lines.append("cohpbetween atom %d atom %d" % (first, second))
    with open(path, "w") as handle:
        handle.write("\n".join(lines) + "\n")


def safe_symlink(source, destination):
    if os.path.lexists(destination):
        if os.path.islink(destination) and os.path.realpath(destination) == os.path.realpath(source):
            return
        fail("refusing to replace existing path: %s" % destination)
    os.symlink(os.path.relpath(source, os.path.dirname(destination)), destination)


def main():
    if os.path.exists(DEST):
        fail("deployment root already exists: %s" % DEST)
    os.makedirs(DEST)
    validation = []
    pair_rows = []
    jobs = []

    for branch, state, active_index, adjacent_index in CASES:
        source = os.path.join(SOURCE, branch, state)
        case = os.path.join(DEST, branch, state)
        os.makedirs(case)
        for filename in REQUIRED:
            source_file = os.path.join(source, filename)
            if not os.path.isfile(source_file) or os.path.getsize(source_file) == 0:
                fail("missing required source file: %s" % source_file)
            safe_symlink(source_file, os.path.join(case, filename))

        cell, elements, positions = read_poscar(os.path.join(source, "POSCAR"))
        if elements[active_index - 1] != "Co":
            fail("active atom is not Co in %s/%s" % (branch, state))
        expected_adjacent = "Al" if branch == "Al16_adjacent" else "Co"
        if elements[adjacent_index - 1] != expected_adjacent:
            fail("adjacent atom mismatch in %s/%s" % (branch, state))
        nbands, nkpts, nelect = parse_outcar(os.path.join(source, "OUTCAR"))
        min_orbitals = recommended_orbitals(elements)

        pairs = []
        excluded = []
        if state != "bare":
            ads_distance, ads_oxygen = nearest_index(
                active_index, {"O"}, elements, positions, cell
            )
            pairs.append(("Co-Oads", active_index, ads_oxygen, ads_distance))
            excluded.append(ads_oxygen)
            if state == "OOH_o03":
                oo_distance, distal_oxygen = nearest_index(
                    ads_oxygen, {"O"}, elements, positions, cell, excluded=[ads_oxygen]
                )
                pairs.append(("Oads-Odistal", ads_oxygen, distal_oxygen, oo_distance))
                excluded.append(distal_oxygen)
        else:
            framework_distance, framework_oxygen = nearest_index(
                active_index, {"O"}, elements, positions, cell
            )
            pairs.append(("Co-Oframework", active_index, framework_oxygen, framework_distance))

        hydroxyl = find_hydroxyl_oxygen(
            adjacent_index, elements, positions, cell, excluded=excluded
        )
        if hydroxyl is not None:
            metal_o_distance, hydroxyl_oxygen, hydroxyl_h, hydroxyl_oh_distance = hydroxyl
            pairs.append((expected_adjacent + "-OH", adjacent_index, hydroxyl_oxygen, metal_o_distance))
            pairs.append(("OH-H", hydroxyl_oxygen, hydroxyl_h, hydroxyl_oh_distance))

        bridge = find_bridge(
            active_index, adjacent_index, elements, positions, cell, excluded=excluded
        )
        _, _, bridge_oxygen, active_o_distance, adjacent_o_distance = bridge
        pairs.append(("Co-Obridge", active_index, bridge_oxygen, active_o_distance))
        pairs.append((expected_adjacent + "-Obridge", adjacent_index, bridge_oxygen, adjacent_o_distance))

        write_lobsterin(os.path.join(case, "lobsterin"), pairs)
        with open(os.path.join(case, "PAIR_INFO.tsv"), "w") as handle:
            handle.write("role\tatom1\telement1\tatom2\telement2\tdistance_A\n")
            for role, first, second, pair_distance in pairs:
                handle.write(
                    "%s\t%d\t%s\t%d\t%s\t%.6f\n"
                    % (role, first, elements[first - 1], second, elements[second - 1], pair_distance)
                )
                pair_rows.append(
                    (branch, state, role, first, elements[first - 1], second, elements[second - 1], pair_distance)
                )

        status = "ready_for_lobster_dry_run"
        if nbands < min_orbitals:
            status = "needs_lobster_dry_run_likely_more_NBANDS"
        validation.append(
            (
                branch,
                state,
                len(elements),
                nelect,
                nkpts,
                nbands,
                min_orbitals,
                os.path.getsize(os.path.join(source, "WAVECAR")),
                active_index,
                atom_label(active_index, elements),
                adjacent_index,
                atom_label(adjacent_index, elements),
                status,
            )
        )
        jobs.append(os.path.relpath(case, DEST))

    with open(os.path.join(DEST, "validation_manifest.tsv"), "w") as handle:
        handle.write(
            "branch\tstate\tatoms\tNELECT\tNKPTS\tNBANDS\tconservative_min_local_orbitals\t"
            "WAVECAR_bytes\tactive_index\tactive_label\tadjacent_index\tadjacent_label\tstatus\n"
        )
        for row in validation:
            handle.write("\t".join(str(value) for value in row) + "\n")

    with open(os.path.join(DEST, "pair_manifest.tsv"), "w") as handle:
        handle.write("branch\tstate\trole\tatom1\telement1\tatom2\telement2\tdistance_A\n")
        for row in pair_rows:
            handle.write("\t".join(str(value) for value in row[:-1]) + "\t%.6f\n" % row[-1])

    with open(os.path.join(DEST, "jobs.list"), "w") as handle:
        handle.write("\n".join(jobs) + "\n")

    shutil.copyfile(__file__, os.path.join(DEST, "deploy_lobster_preconverged.py"))

    with open(os.path.join(DEST, "run_lobster_array.slurm"), "w") as handle:
        handle.write(
            """#!/bin/bash
#SBATCH --job-name=cohp_preconv
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --partition=n28
#SBATCH --array=0-7%1
#SBATCH --output=array_%A_%a.stdout
#SBATCH --error=array_%A_%a.stderr

set -eu
ROOT_DIR=$(cd "$(dirname "$0")" && pwd)
CASE=$(sed -n "$((SLURM_ARRAY_TASK_ID + 1))p" "$ROOT_DIR/jobs.list")
cd "$ROOT_DIR/$CASE"

LOBSTER_BIN=${LOBSTER_BIN:-}
if [ -z "$LOBSTER_BIN" ] || [ ! -x "$LOBSTER_BIN" ]; then
  echo "BLOCKED: set LOBSTER_BIN to a licensed executable under the allowed project roots." >&2
  exit 3
fi
for file in INCAR KPOINTS POSCAR POTCAR OUTCAR WAVECAR vasprun.xml lobsterin; do
  if [ ! -s "$file" ]; then
    echo "BLOCKED: missing $file in $CASE" >&2
    exit 4
  fi
done
"$LOBSTER_BIN"
grep -q "finished" lobsterout
"""
        )

    with open(os.path.join(DEST, "README.md"), "w") as handle:
        handle.write(
            """# Preliminary LOBSTER COHP deployment

- Scope: eight normally terminated fixed-geometry VASP preconvergence states.
- Data are relative symlinks; no multi-gigabyte WAVECAR files are duplicated.
- This directory is preliminary and does not replace COHP on final strict relaxed statics.
- No LOBSTER executable or license was found under the allowed project roots at deployment time.
- Do not submit `run_lobster_array.slurm` until a licensed executable is available.
- After each dry run, validate basis selection, absolute/total charge spilling, pair mapping,
  normal LOBSTER termination, and whether NBANDS spans the selected local basis.
- `conservative_min_local_orbitals` is a pre-check only, not a substitute for LOBSTER's own basis report.
"""
        )

    print(DEST)
    for row in validation:
        print("\t".join(str(value) for value in row))


if __name__ == "__main__":
    main()
