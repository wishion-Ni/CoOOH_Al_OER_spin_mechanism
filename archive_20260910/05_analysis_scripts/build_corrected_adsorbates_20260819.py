from __future__ import print_function

import math
import os
import shutil


ROOT = "sfs/CoOH/cp2k/Al16/oer/spin_config_scan_site03_5OH_current_20260714"
SOURCE = os.path.join(ROOT, "vasp_jacs6c06054_reconstructed_undoped_20260727", "terminal_site03")
PARENT = os.path.join(ROOT, "vasp_jacs6c06054_reconstructed_exact_Al16_3x2_20260809")
OUTPUT = os.path.join(PARENT, "corrected_adsorbates_20260819")
PRECONV = os.path.join(OUTPUT, "electronic_preconverge")
AL_POTCAR = os.path.join(ROOT, "vasp_jacs6c06054_rebuild_20260727", "Al16_adjacent", "bare", "POTCAR")
UNDOPED_POTCAR = os.path.join(SOURCE, "bare", "POTCAR")
NX, NY = 3, 2
ACTIVE_COPY = (1, 0)
ACTIVE_CO_LOCAL = 0
STATES = ("OH", "O", "OOH_o03")
BRANCHES = ("Al16_adjacent", "undoped_control")


def fail(message):
    raise RuntimeError(message)


def vec_add(first, second):
    return [first[index] + second[index] for index in range(3)]


def vec_sub(first, second):
    return [first[index] - second[index] for index in range(3)]


def vec_scale(vector, value):
    return [component * value for component in vector]


def dot_frac(frac, lattice):
    result = [0.0, 0.0, 0.0]
    for index in range(3):
        result = vec_add(result, vec_scale(lattice[index], frac[index]))
    return result


def norm(vector):
    return math.sqrt(sum(component * component for component in vector))


def nearest_image(frac, reference, lattice):
    best = None
    for shift_x in (-2, -1, 0, 1, 2):
        for shift_y in (-2, -1, 0, 1, 2):
            for shift_z in (-1, 0, 1):
                candidate = [
                    frac[0] + shift_x,
                    frac[1] + shift_y,
                    frac[2] + shift_z,
                ]
                value = norm(dot_frac(vec_sub(candidate, reference), lattice))
                if best is None or value < best[0]:
                    best = (value, candidate)
    return best[1]


def distance_mic(first, second, lattice):
    image = nearest_image(second, first, lattice)
    return norm(dot_frac(vec_sub(image, first), lattice))


def read_poscar(path):
    lines = open(path).read().splitlines()
    scale = float(lines[1].split()[0])
    lattice = []
    for index in range(2, 5):
        lattice.append([float(value) * scale for value in lines[index].split()[:3]])
    symbols = lines[5].split()
    counts = [int(value) for value in lines[6].split()]
    cursor = 7
    if lines[cursor].lower().startswith("s"):
        cursor += 1
    if not lines[cursor].lower().startswith("d"):
        fail("Only Direct coordinates are supported: " + path)
    cursor += 1
    coords = {}
    for symbol, count in zip(symbols, counts):
        coords[symbol] = []
        for _ in range(count):
            coords[symbol].append([float(value) for value in lines[cursor].split()[:3]])
            cursor += 1
    return lattice, symbols, counts, coords


def transform_base(frac, copy_x, copy_y):
    wrapped = [value % 1.0 for value in frac]
    return [(wrapped[0] + copy_x) / NX, (wrapped[1] + copy_y) / NY, wrapped[2]]


def transform_unwrapped(frac, copy_x, copy_y):
    return [(frac[0] + copy_x) / NX, (frac[1] + copy_y) / NY, frac[2]]


def state_extras(base, state, lattice):
    result = {}
    for symbol in ("O",):
        extra_count = len(state[symbol]) - len(base[symbol])
        if extra_count < 0:
            fail("State has fewer atoms than bare for " + symbol)
        pairs = []
        for base_index, base_coord in enumerate(base[symbol]):
            for state_index, state_coord in enumerate(state[symbol]):
                pairs.append((distance_mic(base_coord, state_coord, lattice), base_index, state_index))
        pairs.sort()
        used_base = set()
        used_state = set()
        for _, base_index, state_index in pairs:
            if base_index in used_base or state_index in used_state:
                continue
            used_base.add(base_index)
            used_state.add(state_index)
            if len(used_base) == len(base[symbol]):
                break
        result[symbol] = [coord for index, coord in enumerate(state[symbol]) if index not in used_state]
        if len(result[symbol]) != extra_count:
            fail("Failed to identify extras for " + symbol)

    extra_h_count = len(state["H"]) - len(base["H"])
    if extra_h_count < 0:
        fail("State has fewer atoms than bare for H")
    if extra_h_count:
        ranked_h = sorted(
            state["H"],
            key=lambda coord: min(distance_mic(coord, oxygen, lattice) for oxygen in result["O"]),
        )
        result["H"] = ranked_h[:extra_h_count]
    else:
        result["H"] = []
    return result


def place_adsorbate_group(extras, source_active_co, target_active_co, lattice):
    if not extras["O"]:
        return {"O": [], "H": []}

    anchor_index = min(
        range(len(extras["O"])),
        key=lambda index: distance_mic(source_active_co, extras["O"][index], lattice),
    )
    source_oxygen_images = [None] * len(extras["O"])
    source_anchor = nearest_image(extras["O"][anchor_index], source_active_co, lattice)
    source_oxygen_images[anchor_index] = source_anchor
    target_anchor = vec_add(target_active_co, vec_sub(source_anchor, source_active_co))
    target_oxygen = [None] * len(extras["O"])
    target_oxygen[anchor_index] = target_anchor

    for index, oxygen in enumerate(extras["O"]):
        if index == anchor_index:
            continue
        source_image = nearest_image(oxygen, source_anchor, lattice)
        source_oxygen_images[index] = source_image
        target_oxygen[index] = vec_add(target_anchor, vec_sub(source_image, source_anchor))

    target_hydrogen = []
    for hydrogen in extras["H"]:
        oxygen_index = min(
            range(len(extras["O"])),
            key=lambda index: distance_mic(hydrogen, extras["O"][index], lattice),
        )
        source_hydrogen = nearest_image(hydrogen, source_oxygen_images[oxygen_index], lattice)
        target_hydrogen.append(
            vec_add(target_oxygen[oxygen_index], vec_sub(source_hydrogen, source_oxygen_images[oxygen_index]))
        )
    return {"O": target_oxygen, "H": target_hydrogen}


def place_adsorbate_group_super(extras, source_active_co, target_active_super, lattice):
    source_group = place_adsorbate_group(extras, source_active_co, source_active_co, lattice)
    result = {"O": [], "H": []}
    for symbol in ("O", "H"):
        for source_coord in source_group[symbol]:
            delta = vec_sub(source_coord, source_active_co)
            result[symbol].append(
                vec_add(target_active_super, [delta[0] / NX, delta[1] / NY, delta[2]])
            )
    return result


def choose_al_sites(co_entries, active_frac, lattice):
    candidates = [entry for entry in co_entries if entry[2] != ACTIVE_CO_LOCAL]
    seed = min(candidates, key=lambda entry: distance_mic(entry[3], active_frac, lattice))
    selected = [seed]
    while len(selected) < 10:
        remaining = [entry for entry in candidates if entry not in selected]
        selected.append(
            max(
                remaining,
                key=lambda entry: min(distance_mic(entry[3], chosen[3], lattice) for chosen in selected),
            )
        )
    return selected


def locate_coord(coords, target, lattice):
    distance, index = min(
        (distance_mic(coord, target, lattice), index) for index, coord in enumerate(coords)
    )
    if distance > 1.0e-7:
        fail("Could not locate mapped coordinate; closest %.9f A" % distance)
    return index


def global_index(symbols, coords, symbol, local_zero_based):
    offset = 0
    for current in symbols:
        if current == symbol:
            return offset + local_zero_based + 1
        offset += len(coords[current])
    fail("Missing symbol " + symbol)


def nearest_atom(origin, allowed_symbols, symbols, coords, lattice, excluded=None):
    excluded = set(excluded or [])
    candidates = []
    offset = 0
    for symbol in symbols:
        for local_index, coord in enumerate(coords[symbol]):
            index = offset + local_index + 1
            if symbol in allowed_symbols and index not in excluded:
                candidates.append((distance_mic(origin, coord, lattice), index, symbol, coord))
        offset += len(coords[symbol])
    if not candidates:
        fail("No candidates for nearest-atom search")
    return min(candidates)


def write_poscar(path, title, lattice, symbols, coords):
    handle = open(path, "w")
    handle.write(title + "\n1.0\n")
    for vector in lattice:
        handle.write("  %18.12f %18.12f %18.12f\n" % tuple(vector))
    handle.write("  " + "  ".join(symbols) + "\n")
    handle.write("  " + "  ".join(str(len(coords[symbol])) for symbol in symbols) + "\n")
    handle.write("Direct\n")
    for symbol in symbols:
        for frac in coords[symbol]:
            handle.write("  %18.14f %18.14f %18.14f\n" % tuple(frac))
    handle.close()


def write_preconverge_incar(path, title, symbols, counts):
    magmom = []
    for symbol, count in zip(symbols, counts):
        magmom.extend((["3.0"] if symbol == "Co" else ["0.0"]) * count)
    ldau_l = ["2" if symbol == "Co" else "-1" for symbol in symbols]
    ldau_u = ["4.5" if symbol == "Co" else "0" for symbol in symbols]
    text = """SYSTEM = {title}
ISTART = 0
ICHARG = 2
ISPIN = 2
MAGMOM = {magmom}
LDAU = .TRUE.
LDAUTYPE = 2
LDAUL = {ldau_l}
LDAUU = {ldau_u}
LDAUJ = {ldau_j}
LMAXMIX = 4
GGA = PE
IVDW = 11
ENCUT = 520
PREC = Accurate
EDIFF = 1E-4
NELM = 200
NELMIN = 8
ALGO = Fast
ISMEAR = 1
SIGMA = 0.20
IBRION = -1
NSW = 0
ISIF = 2
LREAL = Auto
ADDGRID = .TRUE.
LASPH = .TRUE.
LWAVE = .TRUE.
LCHARG = .TRUE.
ISYM = 0
NCORE = 4
KPAR = 2
NELMDL = -12
AMIX = 0.20
BMIX = 0.0001
AMIX_MAG = 0.80
BMIX_MAG = 0.0001
""".format(
        title=title,
        magmom=" ".join(magmom),
        ldau_l=" ".join(ldau_l),
        ldau_u=" ".join(ldau_u),
        ldau_j=" ".join("0" for _ in symbols),
    )
    open(path, "w").write(text)


def write_kpoints(path):
    open(path, "w").write(
        "Matched density for corrected 3x2 reconstructed supercell\n"
        "0\nMonkhorst-Pack\n2 2 1\n0 0 0\n"
    )


def validate_case(branch, state, symbols, coords, active_frac, adjacent_frac, active_group, lattice):
    active_local = locate_coord(coords["Co"], active_frac, lattice)
    active_index = global_index(symbols, coords, "Co", active_local)
    adjacent_symbol = "Al" if branch == "Al16_adjacent" else "Co"
    adjacent_local = locate_coord(coords[adjacent_symbol], adjacent_frac, lattice)
    adjacent_index = global_index(symbols, coords, adjacent_symbol, adjacent_local)

    oxygen_local = [locate_coord(coords["O"], coord, lattice) for coord in active_group["O"]]
    oxygen_indices = [global_index(symbols, coords, "O", index) for index in oxygen_local]
    anchor_local = min(
        oxygen_local,
        key=lambda index: distance_mic(active_frac, coords["O"][index], lattice),
    )
    anchor = coords["O"][anchor_local]
    anchor_index = global_index(symbols, coords, "O", anchor_local)
    co_o = distance_mic(active_frac, anchor, lattice)
    nearest_metal = nearest_atom(anchor, set(("Co", "Al")), symbols, coords, lattice)
    if nearest_metal[1] != active_index:
        fail(
            "%s/%s designated Co%d but nearest metal is %s%d"
            % (branch, state, active_index, nearest_metal[2], nearest_metal[1])
        )
    if not 1.45 <= co_o <= 2.30:
        fail("%s/%s invalid Co-O %.6f A" % (branch, state, co_o))

    oo = -1.0
    if state == "OOH_o03":
        if len(oxygen_local) != 2:
            fail("OOH does not contain two active oxygens")
        other_local = [index for index in oxygen_local if index != anchor_local][0]
        oo = distance_mic(anchor, coords["O"][other_local], lattice)
        if not 1.10 <= oo <= 1.70:
            fail("%s/%s invalid O-O %.6f A" % (branch, state, oo))
    else:
        nearest_other_o = nearest_atom(anchor, set(("O",)), symbols, coords, lattice, excluded=[anchor_index])
        if nearest_other_o[0] < 1.65:
            fail("%s/%s unintended O-O %.6f A" % (branch, state, nearest_other_o[0]))

    oh = -1.0
    hydrogen_indices = []
    if active_group["H"]:
        hydrogen_local = [locate_coord(coords["H"], coord, lattice) for coord in active_group["H"]]
        hydrogen_indices = [global_index(symbols, coords, "H", index) for index in hydrogen_local]
        oh = min(
            distance_mic(coords["H"][h_index], coords["O"][o_index], lattice)
            for h_index in hydrogen_local
            for o_index in oxygen_local
        )
        if not 0.75 <= oh <= 1.25:
            fail("%s/%s invalid active O-H %.6f A" % (branch, state, oh))

    expected_active = 16 if branch == "Al16_adjacent" else 21
    expected_adjacent = 51 if branch == "Al16_adjacent" else 23
    if active_index != expected_active or adjacent_index != expected_adjacent:
        fail(
            "%s/%s atom mapping active %d/%d adjacent %d/%d"
            % (branch, state, active_index, expected_active, adjacent_index, expected_adjacent)
        )

    composition = "".join("%s%d" % (symbol, len(coords[symbol])) for symbol in symbols)
    expected = {
        ("Al16_adjacent", "OH"): "Co50Al10H144O144",
        ("Al16_adjacent", "O"): "Co50Al10H143O144",
        ("Al16_adjacent", "OOH_o03"): "Co50Al10H144O145",
        ("undoped_control", "OH"): "Co60H144O144",
        ("undoped_control", "O"): "Co60H143O144",
        ("undoped_control", "OOH_o03"): "Co60H144O145",
    }[(branch, state)]
    if composition != expected:
        fail("%s/%s composition %s != %s" % (branch, state, composition, expected))

    return (
        composition,
        active_index,
        adjacent_index,
        distance_mic(active_frac, adjacent_frac, lattice),
        ",".join(str(index) for index in oxygen_indices),
        ",".join(str(index) for index in hydrogen_indices) if hydrogen_indices else "NA",
        co_o,
        oo,
        oh,
        "%s%d" % (nearest_metal[2], nearest_metal[1]),
        nearest_metal[0],
        "valid_intended_site",
    )


def validate_background_groups(branch, symbols, coords, groups, targets, lattice):
    for copy_key in sorted(groups):
        group = groups[copy_key]
        target = targets[copy_key]
        target_local = locate_coord(coords["Co"], target, lattice)
        target_index = global_index(symbols, coords, "Co", target_local)
        anchor = min(group["O"], key=lambda oxygen: distance_mic(target, oxygen, lattice))
        co_o = distance_mic(target, anchor, lattice)
        nearest_metal = nearest_atom(anchor, set(("Co", "Al")), symbols, coords, lattice)
        if nearest_metal[1] != target_index or not 1.45 <= co_o <= 2.30:
            fail(
                "%s background OH %s expected Co%d, nearest %s%d, Co-O %.6f A"
                % (branch, str(copy_key), target_index, nearest_metal[2], nearest_metal[1], co_o)
            )
        oxygen_local = [locate_coord(coords["O"], oxygen, lattice) for oxygen in group["O"]]
        oxygen_indices = [global_index(symbols, coords, "O", index) for index in oxygen_local]
        nearest_other = nearest_atom(
            anchor, set(("O",)), symbols, coords, lattice, excluded=oxygen_indices
        )
        if nearest_other[0] < 1.65:
            fail("%s background OH %s unintended O-O %.6f A" % (branch, str(copy_key), nearest_other[0]))
        oh = min(distance_mic(anchor, hydrogen, lattice) for hydrogen in group["H"])
        if not 0.75 <= oh <= 1.25:
            fail("%s background OH %s invalid O-H %.6f A" % (branch, str(copy_key), oh))


def write_slurm(path):
    open(path, "w").write(
        """#!/bin/bash
#SBATCH --job-name=Al16_fix_preSCF
#SBATCH --nodes=1
#SBATCH --ntasks=40
#SBATCH --partition=n40
#SBATCH --array=0-5%2
#SBATCH --output=array_%A_%a.stdout
#SBATCH --error=array_%A_%a.stderr

set -eo pipefail
ROOT_DIR=${SLURM_SUBMIT_DIR:?SLURM_SUBMIT_DIR_is_not_set}
WORKDIR=$(sed -n "$((SLURM_ARRAY_TASK_ID + 1))p" "$ROOT_DIR/preconverge_jobs.list")
cd "$ROOT_DIR/$WORKDIR"
if [ -f OUTCAR ] && grep -q "General timing and accounting informations" OUTCAR; then
  echo "Already complete: $WORKDIR"
  exit 0
fi
VASP_HOME=/apps/vasp/6.3.0_vtst_optcell_vaspsol/O3
if [ -f "$HOME/intel/oneapi/setvars.sh" ]; then
  source "$HOME/intel/oneapi/setvars.sh" --force
fi
export LD_LIBRARY_PATH="$HOME/intel/oneapi/mkl/latest/lib/intel64:$HOME/intel/oneapi/compiler/latest/linux/compiler/lib/intel64_lin:${LD_LIBRARY_PATH:-}"
ulimit -s unlimited
"$HOME/intel/oneapi/mpi/2021.11/bin/mpirun" -n "$SLURM_NTASKS" "$VASP_HOME/vasp_std" > vasp.out 2>&1
"""
    )


def main():
    if os.path.exists(OUTPUT):
        fail("Refusing to replace existing correction root: " + OUTPUT)

    bare_lattice, _, _, bare = read_poscar(os.path.join(SOURCE, "bare", "CONTCAR"))
    _, _, _, bare_seed = read_poscar(os.path.join(SOURCE, "bare", "POSCAR"))
    state_coords = {}
    seed_coords = {}
    for state in ("OH", "O", "OOH_o03"):
        state_coords[state] = read_poscar(os.path.join(SOURCE, state, "CONTCAR"))[3]
        seed_coords[state] = read_poscar(os.path.join(SOURCE, state, "POSCAR"))[3]

    base_nonmetal = {"H": [], "O": []}
    for copy_x in range(NX):
        for copy_y in range(NY):
            for symbol in ("H", "O"):
                base_nonmetal[symbol].extend(
                    transform_base(coord, copy_x, copy_y) for coord in bare[symbol]
                )
    background_extras = state_extras(bare, state_coords["OH"], bare_lattice)
    background_groups = {}
    background_targets = {}
    for copy_x in range(NX):
        for copy_y in range(NY):
            if (copy_x, copy_y) == ACTIVE_COPY:
                continue
            target = transform_base(bare["Co"][ACTIVE_CO_LOCAL], copy_x, copy_y)
            background_targets[(copy_x, copy_y)] = target
            background_groups[(copy_x, copy_y)] = place_adsorbate_group_super(
                background_extras,
                state_coords["OH"]["Co"][ACTIVE_CO_LOCAL],
                target,
                bare_lattice,
            )

    os.makedirs(PRECONV)
    jobs = []
    audit_rows = []
    for state in STATES:
        if state == "OOH_o03":
            active_extras = state_extras(bare_seed, seed_coords[state], bare_lattice)
            source_active = seed_coords[state]["Co"][ACTIVE_CO_LOCAL]
        else:
            active_extras = state_extras(bare, state_coords[state], bare_lattice)
            source_active = state_coords[state]["Co"][ACTIVE_CO_LOCAL]
        for branch in BRANCHES:
            bare_path = os.path.join(PARENT, branch, "bare", "POSCAR")
            super_lattice, symbols, _, base_coords = read_poscar(bare_path)
            coords = {}
            for symbol in symbols:
                if symbol in ("H", "O"):
                    coords[symbol] = list(base_nonmetal[symbol])
                else:
                    coords[symbol] = list(base_coords[symbol])
            for copy_key in sorted(background_groups):
                for symbol in ("H", "O"):
                    coords[symbol].extend(background_groups[copy_key][symbol])
            expected_active = 16 if branch == "Al16_adjacent" else 21
            expected_adjacent = 51 if branch == "Al16_adjacent" else 23
            elements = []
            positions = []
            for symbol in symbols:
                for coord in coords[symbol]:
                    elements.append(symbol)
                    positions.append(coord)
            if elements[expected_active - 1] != "Co":
                fail("%s active atom %d is not Co" % (branch, expected_active))
            expected_adjacent_symbol = "Al" if branch == "Al16_adjacent" else "Co"
            if elements[expected_adjacent - 1] != expected_adjacent_symbol:
                fail("%s adjacent atom %d is not %s" % (branch, expected_adjacent, expected_adjacent_symbol))
            active_frac = positions[expected_active - 1]
            adjacent_frac = positions[expected_adjacent - 1]
            active_group_super = place_adsorbate_group_super(
                active_extras, source_active, active_frac, bare_lattice
            )
            for symbol in ("H", "O"):
                coords[symbol].extend(active_group_super[symbol])

            validate_background_groups(
                branch, symbols, coords, background_groups, background_targets, super_lattice
            )

            audit = validate_case(
                branch, state, symbols, coords, active_frac, adjacent_frac, active_group_super, super_lattice
            )
            workdir = os.path.join(PRECONV, branch, state)
            os.makedirs(workdir)
            title = "corrected preconverge %s/%s" % (branch, state)
            write_poscar(os.path.join(workdir, "POSCAR"), title, super_lattice, symbols, coords)
            counts = [len(coords[symbol]) for symbol in symbols]
            write_preconverge_incar(os.path.join(workdir, "INCAR"), title, symbols, counts)
            shutil.copyfile(os.path.join(PARENT, branch, "bare", "KPOINTS"), os.path.join(workdir, "KPOINTS"))
            shutil.copyfile(os.path.join(PARENT, branch, "bare", "POTCAR"), os.path.join(workdir, "POTCAR"))
            jobs.append(os.path.relpath(workdir, OUTPUT))
            audit_rows.append((branch, state) + audit)

    with open(os.path.join(OUTPUT, "construction_audit.tsv"), "w") as handle:
        handle.write(
            "branch\tstate\tcomposition\tactive_Co_index\tadjacent_index\tadjacent_distance_A\t"
            "active_O_indices\tactive_H_indices\tCo_O_A\tO_O_A\tO_H_A\tnearest_metal_to_O\t"
            "nearest_metal_distance_A\tstatus\n"
        )
        for row in audit_rows:
            handle.write("\t".join(str(value) for value in row[:-6]))
            handle.write("\t%.6f\t%.6f\t%.6f\t%s\t%.6f\t%s\n" % row[-6:])

    with open(os.path.join(OUTPUT, "preconverge_jobs.list"), "w") as handle:
        handle.write("\n".join(jobs) + "\n")
    write_slurm(os.path.join(OUTPUT, "preconverge_array.slurm"))
    with open(os.path.join(OUTPUT, "scheduler_manifest.tsv"), "w") as handle:
        handle.write("date\tevent\tjob_id\tpartition\tranks\tarray_limit\tnotes\n")
        handle.write(
            "2026-08-19\tcancel_invalid_construction\t"
            "110989_2,111001_3,111004_4,111049_5,111005_6,111088_7,111172_3-7\t"
            "mixed\tmixed\tNA\tuser_authorized;periodic_wrapping_error;old_outputs_preserved\n"
        )
    with open(os.path.join(OUTPUT, "METHOD.txt"), "w") as handle:
        handle.write(
            "Corrected molecule-aware reconstruction for the six OH/O/OOH Al16-control states.\n"
            "Adsorbate Co-O, O-O, and O-H displacement vectors are unwrapped as one group relative to the source active Co, then translated to the designated 3x2 active Co.\n"
            "Every state must pass composition, atom-index, Co-O, O-O/O-H, nearest-metal, and adjacent-site checks before submission.\n"
            "This first stage is electronic preconvergence only and is not used for energies or forces. Valid seeds will start strict ALGO=Normal, LREAL=FALSE, EDIFF=1E-6 relaxations with force below 0.02 eV/A.\n"
        )
    shutil.copyfile(__file__, os.path.join(OUTPUT, "build_corrected_adsorbates.py"))
    print("OUTPUT", OUTPUT)
    print("JOBS", len(jobs))
    for row in audit_rows:
        print("\t".join(str(value) for value in row))


if __name__ == "__main__":
    main()
