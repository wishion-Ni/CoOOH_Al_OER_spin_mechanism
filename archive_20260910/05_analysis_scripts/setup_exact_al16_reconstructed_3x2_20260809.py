from __future__ import print_function

import math
import os
import shutil


ROOT = "sfs/CoOH/cp2k/Al16/oer/spin_config_scan_site03_5OH_current_20260714"
SOURCE = os.path.join(ROOT, "vasp_jacs6c06054_reconstructed_undoped_20260727", "terminal_site03")
OUTPUT = os.path.join(ROOT, "vasp_jacs6c06054_reconstructed_exact_Al16_3x2_20260809")
AL_POTCAR = os.path.join(ROOT, "vasp_jacs6c06054_rebuild_20260727", "Al16_adjacent", "bare", "POTCAR")
UNDOPED_POTCAR = os.path.join(SOURCE, "bare", "POTCAR")
NX, NY = 3, 2
ACTIVE_COPY = (1, 0)
ACTIVE_CO_LOCAL = 0
STATES = ("bare", "OH", "O", "OOH_o03")


def vec_add(a, b):
    return [a[k] + b[k] for k in range(3)]


def vec_scale(a, value):
    return [a[k] * value for k in range(3)]


def dot_frac(frac, lattice):
    out = [0.0, 0.0, 0.0]
    for i in range(3):
        out = vec_add(out, vec_scale(lattice[i], frac[i]))
    return out


def distance_mic(frac_a, frac_b, lattice):
    raw = [frac_a[k] - frac_b[k] for k in range(3)]
    best = 1.0e99
    for ia in (-1, 0, 1):
        for ib in (-1, 0, 1):
            for ic in (-1, 0, 1):
                delta = [raw[0] + ia, raw[1] + ib, raw[2] + ic]
                cart = dot_frac(delta, lattice)
                value = math.sqrt(sum(component * component for component in cart))
                best = min(best, value)
    return best


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
    mode = lines[cursor].lower()
    if not mode.startswith("d"):
        raise RuntimeError("Only Direct coordinates are supported: " + path)
    cursor += 1
    coords = {}
    for symbol, count in zip(symbols, counts):
        coords[symbol] = []
        for _ in range(count):
            coords[symbol].append([float(value) for value in lines[cursor].split()[:3]])
            cursor += 1
    return lattice, symbols, counts, coords


def transform(frac, ix, iy):
    wrapped = [value % 1.0 for value in frac]
    return [(wrapped[0] + ix) / NX, (wrapped[1] + iy) / NY, wrapped[2]]


def state_extras(base, state, lattice):
    result = {}
    for symbol in ("O",):
        n_extra = len(state[symbol]) - len(base[symbol])
        if n_extra < 0:
            raise RuntimeError("State has fewer atoms than bare for " + symbol)
        if not n_extra:
            result[symbol] = []
            continue
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
        if len(result[symbol]) != n_extra:
            raise RuntimeError("Failed to identify extras for " + symbol)
    n_extra_h = len(state["H"]) - len(base["H"])
    if n_extra_h < 0:
        raise RuntimeError("State has fewer atoms than bare for H")
    if n_extra_h:
        if not result["O"]:
            raise RuntimeError("Cannot assign adsorbate H without extra O")
        ranked_h = sorted(
            state["H"],
            key=lambda coord: min(distance_mic(coord, oxygen, lattice) for oxygen in result["O"]),
        )
        result["H"] = ranked_h[:n_extra_h]
    else:
        result["H"] = []
    return result


def choose_al_sites(co_entries, active_frac, lattice):
    candidates = [entry for entry in co_entries if entry[2] != ACTIVE_CO_LOCAL]
    seed = min(candidates, key=lambda entry: distance_mic(entry[3], active_frac, lattice))
    selected = [seed]
    while len(selected) < 10:
        remaining = [entry for entry in candidates if entry not in selected]
        selected.append(max(
            remaining,
            key=lambda entry: min(distance_mic(entry[3], chosen[3], lattice) for chosen in selected),
        ))
    return selected


def min_pair(coords_by_symbol, lattice):
    atoms = []
    for symbol in coords_by_symbol:
        for coord in coords_by_symbol[symbol]:
            atoms.append((symbol, coord))
    best = (1.0e9, "", "")
    for i in range(len(atoms)):
        for j in range(i + 1, len(atoms)):
            value = distance_mic(atoms[i][1], atoms[j][1], lattice)
            if value < best[0]:
                best = (value, atoms[i][0], atoms[j][0])
    return best


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


def write_incar(path, title, symbols, counts):
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
""".format(
        title=title,
        magmom=" ".join(magmom),
        ldau_l=" ".join(ldau_l),
        ldau_u=" ".join(ldau_u),
        ldau_j=" ".join("0" for _ in symbols),
    )
    open(path, "w").write(text)


def write_kpoints(path):
    open(path, "w").write("Matched density for 3x2 reconstructed supercell\n0\nMonkhorst-Pack\n2 2 1\n0 0 0\n")


bare_lattice, _, _, bare = read_poscar(os.path.join(SOURCE, "bare", "CONTCAR"))
_, _, _, bare_seed = read_poscar(os.path.join(SOURCE, "bare", "POSCAR"))
state_coords = {}
seed_coords = {}
for state in STATES:
    state_coords[state] = read_poscar(os.path.join(SOURCE, state, "CONTCAR"))[3]
    seed_coords[state] = read_poscar(os.path.join(SOURCE, state, "POSCAR"))[3]
background_oh = state_extras(bare, state_coords["OH"], bare_lattice)

super_lattice = [vec_scale(bare_lattice[0], NX), vec_scale(bare_lattice[1], NY), bare_lattice[2]]
base_super = {"Co": [], "H": [], "O": []}
co_entries = []
for ix in range(NX):
    for iy in range(NY):
        for local, coord in enumerate(bare["Co"]):
            transformed = transform(coord, ix, iy)
            co_entries.append((ix, iy, local, transformed))
            base_super["Co"].append(transformed)
        for symbol in ("H", "O"):
            for coord in bare[symbol]:
                base_super[symbol].append(transform(coord, ix, iy))

active_entry = [entry for entry in co_entries if entry[:3] == (ACTIVE_COPY[0], ACTIVE_COPY[1], ACTIVE_CO_LOCAL)][0]
active_frac = active_entry[3]
al_entries = choose_al_sites(co_entries, active_frac, super_lattice)
al_coords = [entry[3] for entry in al_entries]

if not os.path.isdir(OUTPUT):
    os.makedirs(OUTPUT)

manifest = open(os.path.join(OUTPUT, "model_manifest.tsv"), "w")
manifest.write("branch\tstate\tcomposition\tactive_copy\tactive_Co_local\tnearest_Al_A\tmin_pair_A\tmin_pair_elements\n")

jobs = []
for branch in ("undoped_control", "Al16_adjacent"):
    for state in STATES:
        coords = {symbol: list(values) for symbol, values in base_super.items()}
        if state == "OOH_o03":
            active_extras = state_extras(bare_seed, seed_coords[state], bare_lattice)
        else:
            active_extras = state_extras(bare, state_coords[state], bare_lattice)
        for ix in range(NX):
            for iy in range(NY):
                extras = active_extras if (ix, iy) == ACTIVE_COPY else background_oh
                for symbol in ("H", "O"):
                    coords[symbol].extend(transform(value, ix, iy) for value in extras[symbol])

        if branch == "Al16_adjacent":
            al_keys = set(tuple(round(value, 12) for value in coord) for coord in al_coords)
            co_coords = [coord for coord in coords["Co"] if tuple(round(value, 12) for value in coord) not in al_keys]
            coords = {"Co": co_coords, "Al": al_coords, "H": coords["H"], "O": coords["O"]}
            symbols = ["Co", "Al", "H", "O"]
            potcar = AL_POTCAR
            nearest_al = min(distance_mic(active_frac, coord, super_lattice) for coord in al_coords)
        else:
            symbols = ["Co", "H", "O"]
            potcar = UNDOPED_POTCAR
            nearest_al = -1.0

        workdir = os.path.join(OUTPUT, branch, state)
        if not os.path.isdir(workdir):
            os.makedirs(workdir)
        title = "JACS 6c06054 reconstructed 3x2 %s %s" % (branch, state)
        write_poscar(os.path.join(workdir, "POSCAR"), title, super_lattice, symbols, coords)
        counts = [len(coords[symbol]) for symbol in symbols]
        write_incar(os.path.join(workdir, "INCAR"), title, symbols, counts)
        write_kpoints(os.path.join(workdir, "KPOINTS"))
        shutil.copyfile(potcar, os.path.join(workdir, "POTCAR"))
        pair = min_pair(coords, super_lattice)
        composition = "".join("%s%d" % (symbol, len(coords[symbol])) for symbol in symbols)
        manifest.write("%s\t%s\t%s\t%d,%d\t%d\t%.6f\t%.6f\t%s-%s\n" % (
            branch, state, composition, ACTIVE_COPY[0], ACTIVE_COPY[1], ACTIVE_CO_LOCAL + 1,
            nearest_al, pair[0], pair[1], pair[2],
        ))
        jobs.append(os.path.relpath(workdir, OUTPUT))

manifest.close()

dopants = open(os.path.join(OUTPUT, "dopant_manifest.tsv"), "w")
dopants.write("selection\tcopy_x\tcopy_y\tlocal_Co_1based\tdistance_to_active_Co_A\n")
for index, entry in enumerate(al_entries):
    dopants.write("%d\t%d\t%d\t%d\t%.6f\n" % (
        index + 1, entry[0], entry[1], entry[2] + 1,
        distance_mic(entry[3], active_frac, super_lattice),
    ))
dopants.close()

open(os.path.join(OUTPUT, "jobs.list"), "w").write("\n".join(jobs) + "\n")
open(os.path.join(OUTPUT, "METHOD.txt"), "w").write(
    "Exact 16.7 at% Al reconstructed comparison after strict undoped literature validation.\n"
    "The Co10 reconstructed cell is expanded 3x2 to 60 metal sites; 10 non-active Co are replaced by Al.\n"
    "One central site is reactive and the other five replicated vacancies are restored as OH, giving matched low coverage.\n"
    "A same-size undoped control is generated. Active Co is retained; the first Al is the nearest non-active Co and the remaining Al sites are max-min distributed.\n"
    "Electronic protocol: spin PBE+U Co Ueff=4.5 eV, IVDW=11, ENCUT=520 eV, 2x2x1 density-matched mesh, 20 A vacuum, ISMEAR=1, force below 0.02 eV/A.\n"
    "States: bare, OH, O, and the validated site03 OOH_o03 geometry. No thermochemical fitting.\n"
)

slurm = """#!/bin/bash
#SBATCH --job-name=Al16_recon_3x2
#SBATCH --nodes=1
#SBATCH --ntasks=40
#SBATCH --partition=n40
#SBATCH --array=0-7%2
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
export LD_LIBRARY_PATH="$HOME/intel/oneapi/mkl/latest/lib/intel64:$HOME/intel/oneapi/compiler/latest/linux/compiler/lib/intel64_lin:${LD_LIBRARY_PATH:-}"
ulimit -s unlimited
"$HOME/intel/oneapi/mpi/2021.11/bin/mpirun" -n "$SLURM_NTASKS" "$VASP_HOME/vasp_std" > vasp.out 2>&1
"""
open(os.path.join(OUTPUT, "vasp_array.slurm"), "w").write(slurm)

print("OUTPUT", OUTPUT)
print("JOBS", len(jobs))
print("AL_SITES", [(entry[0], entry[1], entry[2] + 1) for entry in al_entries])
print("ACTIVE_NEAREST_AL_A", min(distance_mic(active_frac, coord, super_lattice) for coord in al_coords))
