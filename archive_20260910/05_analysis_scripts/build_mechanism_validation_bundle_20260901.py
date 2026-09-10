from __future__ import annotations

import csv
import json
import math
import re
import shutil
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "mechanism_validation_bundle"
SRC = ROOT / "mechanism_validation_sources_20260901"
PDOS_ROOT = ROOT / "pdos_oh_o_inputs_20260824"
COHP_ROOT = ROOT / "cohp_oh_o_inputs_20260824"
GROSS_ROOT = ROOT / "lobster_grosspop_oh_o_20260826"

UP = "#D55E00"
DOWN = "#0072B2"
GREEN = "#009E73"
GRAY = "#5B6573"
PURPLE = "#CC79A7"


def rel(path: Path) -> str:
    try:
        return path.relative_to(ROOT.parent).as_posix()
    except ValueError:
        return path.as_posix()


def write_tsv(path: Path, rows: list[dict], fields: list[str] | None = None) -> None:
    if fields is None:
        fields = list(rows[0]) if rows else []
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def fmt(value, digits=6):
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return value


def min_image(delta: np.ndarray, cell: np.ndarray) -> np.ndarray:
    frac = np.linalg.solve(cell.T, delta)
    frac -= np.round(frac)
    return frac @ cell


def distance(a: np.ndarray, b: np.ndarray, cell: np.ndarray) -> float:
    return float(np.linalg.norm(min_image(b - a, cell)))


def parse_cp2k_input(path: Path):
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    cell = np.zeros((3, 3), dtype=float)
    atoms: list[tuple[str, np.ndarray]] = []
    in_coord = False
    for line in lines:
        fields = line.split()
        if len(fields) == 4 and fields[0] in {"A", "B", "C"}:
            cell[{"A": 0, "B": 1, "C": 2}[fields[0]]] = [float(v) for v in fields[1:]]
        if fields[:1] == ["&COORD"]:
            in_coord = True
            continue
        if in_coord and len(fields) >= 2 and fields[0].upper() == "&END":
            break
        if in_coord and len(fields) == 4 and re.fullmatch(r"[A-Za-z]+", fields[0]):
            atoms.append((fields[0], np.array([float(v) for v in fields[1:]], dtype=float)))
    return cell, atoms


def parse_cp2k_populations(path: Path):
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    mull: dict[int, dict] = {}
    hirsh: dict[int, dict] = {}
    mode = None
    for line in lines:
        if "Mulliken Population Analysis" in line:
            mode = "mull"
            continue
        if "Hirshfeld Charges" in line:
            mode = "hirsh"
            continue
        if mode == "mull":
            match = re.match(
                r"^\s*(\d+)\s+([A-Za-z]+)\s+\d+\s+([-+0-9.Ee]+)\s+([-+0-9.Ee]+)\s+([-+0-9.Ee]+)\s+([-+0-9.Ee]+)\s*$",
                line,
            )
            if match:
                idx, elem, up, down, charge, spin = match.groups()
                mull[int(idx)] = {
                    "element": elem,
                    "N_up": float(up),
                    "N_down": float(down),
                    "N_total": float(up) + float(down),
                    "charge": float(charge),
                    "spin": float(spin),
                }
        elif mode == "hirsh":
            match = re.match(
                r"^\s*(\d+)\s+([A-Za-z]+)\s+\d+\s+([-+0-9.Ee]+)\s+([-+0-9.Ee]+)\s+([-+0-9.Ee]+)\s+([-+0-9.Ee]+)\s+([-+0-9.Ee]+)\s*$",
                line,
            )
            if match:
                idx, elem, refq, up, down, spin, charge = match.groups()
                hirsh[int(idx)] = {
                    "element": elem,
                    "N_up": float(up),
                    "N_down": float(down),
                    "N_total": float(up) + float(down),
                    "charge": float(charge),
                    "spin": float(spin),
                    "reference_charge": float(refq),
                }
    if not mull or not hirsh:
        raise ValueError(f"Population sections not parsed from {path}")
    return {"Mulliken": mull, "Hirshfeld": hirsh}


def identify_cp2k_bridge(cell, atoms, co_idx: int, oads_idx: int, prefer_al: bool):
    co = atoms[co_idx - 1][1]
    candidates = []
    for oi, (element, opos) in enumerate(atoms, start=1):
        if element != "O" or oi == oads_idx:
            continue
        dco = distance(co, opos, cell)
        if dco > 2.45:
            continue
        for mi, (melem, mpos) in enumerate(atoms, start=1):
            if mi == co_idx or melem not in {"Co", "Al"}:
                continue
            dm = distance(mpos, opos, cell)
            if dm <= 2.45:
                penalty = 0 if (prefer_al and melem == "Al") else (2 if prefer_al else 0)
                candidates.append((penalty, dco + dm, oi, mi, melem, dco, dm))
    if not candidates:
        return None
    return min(candidates)


def parse_poscar(path: Path):
    lines = path.read_text(encoding="ascii", errors="replace").splitlines()
    scale = float(lines[1].split()[0])
    cell = np.array([[float(v) for v in lines[i].split()[:3]] for i in range(2, 5)]) * scale
    elements = lines[5].split()
    counts = [int(v) for v in lines[6].split()]
    cursor = 7
    if lines[cursor].strip().lower().startswith("s"):
        cursor += 1
    direct = lines[cursor].strip().lower().startswith("d")
    cursor += 1
    raw = np.array([[float(v) for v in lines[cursor + i].split()[:3]] for i in range(sum(counts))])
    coords = raw @ cell if direct else raw * scale
    atom_elements = [element for element, count in zip(elements, counts) for _ in range(count)]
    return cell, atom_elements, coords


def parse_doscar(path: Path):
    with path.open("r", encoding="ascii") as handle:
        natoms = int(handle.readline().split()[0])
        for _ in range(4):
            handle.readline()
        header = handle.readline().split()
        nedos = int(header[2])
        efermi = float(header[3])
        for _ in range(nedos):
            handle.readline()
        projected = np.empty((natoms, nedos, 18), dtype=float)
        energy = None
        for atom in range(natoms):
            handle.readline()
            block = np.array([[float(v) for v in handle.readline().split()] for _ in range(nedos)])
            if block.shape[1] != 19:
                raise ValueError(f"Expected spin-resolved LORBIT=11 DOSCAR: {path}")
            if energy is None:
                energy = block[:, 0] - efermi
            projected[atom] = block[:, 1:]
    return energy, projected


D_ORBS = {"dxy": (8, 9), "dyz": (10, 11), "dz2": (12, 13), "dxz": (14, 15), "dx2-y2": (16, 17)}
P_ORBS = {"py": (2, 3), "pz": (4, 5), "px": (6, 7)}
S_ORBS = {"s": (0, 1)}


def atom_orbital(projected, atom_index, columns):
    atom = projected[atom_index - 1]
    return atom[:, columns[0]], atom[:, columns[1]]


def orbital_sum(projected, atom_index, orbital_map):
    up = np.zeros(projected.shape[1])
    down = np.zeros_like(up)
    for cols in orbital_map.values():
        u, d = atom_orbital(projected, atom_index, cols)
        up += u
        down += d
    return up, down


@dataclass
class CohpCase:
    energy: np.ndarray
    spin1: np.ndarray
    spin2: np.ndarray
    icohp: list[tuple[float, float, float]]
    spilling: tuple[float, float]
    source: Path


def parse_cohp(folder: Path) -> CohpCase:
    lines = (folder / "COHPCAR.lobster").read_text(encoding="ascii").splitlines()
    ncurves, nspin, nedos = [int(v) for v in lines[1].split()[:3]]
    data_start = 3 + (ncurves - 1)
    data = np.array([[float(v) for v in line.split()] for line in lines[data_start : data_start + nedos]])
    spin1 = data[:, 1 + 2]
    spin2 = data[:, 1 + 2 * ncurves + 2]
    icohp = []
    for line in (folder / "ICOHPLIST.lobster").read_text(encoding="ascii").splitlines():
        fields = line.split()
        if fields and fields[0].isdigit() and len(fields) >= 6:
            icohp.append((float(fields[3]), float(fields[-2]), float(fields[-1])))
    spills = []
    for line in (folder / "lobsterout").read_text(encoding="ascii").splitlines():
        if "abs. charge spilling:" in line:
            spills.append(float(line.split()[-1].rstrip("%")))
    return CohpCase(data[:, 0], spin1, spin2, icohp, tuple(spills[:2]), folder / "COHPCAR.lobster")


def parse_grosspop_total(path: Path, atom_index: int):
    lines = path.read_text(encoding="ascii").splitlines()
    start = None
    for i, line in enumerate(lines):
        if re.match(rf"^\s*{atom_index}\s+[A-Za-z]+\s+", line):
            start = i
            break
    if start is None:
        raise ValueError(f"Atom {atom_index} absent in {path}")
    for line in lines[start : start + 20]:
        if re.match(r"^\s*total\s+", line):
            values = [float(v) for v in line.split()[1:5]]
            return {"Mulliken_up": values[0], "Loewdin_up": values[1], "Mulliken_down": values[2], "Loewdin_down": values[3]}
    raise ValueError(f"Total line absent for atom {atom_index} in {path}")


def clean_axes(ax):
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(direction="out", length=3)


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    cp2k_cases = {
        ("pristine", "*OH"): {"stem": "undoped_OH", "Coact": 32, "Oads": 212, "H": 211, "prefer_al": False},
        ("pristine", "*O"): {"stem": "undoped_O", "Coact": 32, "Oads": 211, "H": None, "prefer_al": False},
        ("Al16", "*OH"): {"stem": "Al16_OH", "Coact": 48, "Oads": 222, "H": 221, "prefer_al": True},
        ("Al16", "*O"): {"stem": "Al16_O", "Coact": 48, "Oads": 221, "H": None, "prefer_al": True},
    }
    vasp_cases = {
        ("pristine", "*OH"): {"key": "undoped_OH", "Coact": 21, "Oads": 348, "H": 204, "Obridge": 259, "neighbor": 23, "neighbor_element": "Co"},
        ("pristine", "*O"): {"key": "undoped_O", "Coact": 21, "Oads": 347, "H": None, "Obridge": 258, "neighbor": 23, "neighbor_element": "Co"},
        ("Al16", "*OH"): {"key": "Al16_OH", "Coact": 16, "Oads": 348, "H": 204, "Obridge": 259, "neighbor": 51, "neighbor_element": "Al"},
        ("Al16", "*O"): {"key": "Al16_O", "Coact": 16, "Oads": 347, "H": None, "Obridge": 258, "neighbor": 51, "neighbor_element": "Al"},
    }

    cp2k_data = {}
    mapping_rows = []
    stable_cp2k_framework = {
        "pristine": {"Obridge": 205, "neighbor": 45, "neighbor_element": "Co"},
        "Al16": {"Obridge": 205, "neighbor": 32, "neighbor_element": "Al"},
    }
    for (system, state), meta in cp2k_cases.items():
        inp = SRC / f"cp2k_{meta['stem']}_baseline.inp"
        out = SRC / f"cp2k_{meta['stem']}_baseline.out"
        cell, atoms = parse_cp2k_input(inp)
        pops = parse_cp2k_populations(out)
        framework = stable_cp2k_framework[system]
        ob_idx = framework["Obridge"]
        neighbor_idx = framework["neighbor"]
        neighbor_element = framework["neighbor_element"]
        d_co_ob = distance(atoms[meta["Coact"] - 1][1], atoms[ob_idx - 1][1], cell)
        d_n_ob = distance(atoms[neighbor_idx - 1][1], atoms[ob_idx - 1][1], cell)
        if d_co_ob > 2.45 or d_n_ob > 2.45:
            raise RuntimeError(f"Stable CP2K framework mapping broke for {system} {state}")
        d_co_oads = distance(atoms[meta["Coact"] - 1][1], atoms[meta["Oads"] - 1][1], cell)
        meta.update({"Obridge": ob_idx, "neighbor": neighbor_idx, "neighbor_element": neighbor_element})
        cp2k_data[(system, state)] = {"meta": meta, "cell": cell, "atoms": atoms, "pops": pops, "out": out, "inp": inp}
        mapping_rows.append({
            "method": "CP2K", "system": system, "state": state, "directory": rel(inp.parent),
            "Coact_index": meta["Coact"], "Oads_index": meta["Oads"], "H_index": fmt(meta["H"]),
            "Obridge_index": ob_idx, "neighbor_index": neighbor_idx, "neighbor_element": neighbor_element,
            "Coact_Oads_distance_A": fmt(d_co_oads), "Coact_Obridge_distance_A": fmt(d_co_ob),
            "neighbor_Obridge_distance_A": fmt(d_n_ob),
            "geometry_match_quality": "related but not strictly identical to VASP",
            "notes": "Shared framework O and neighbor selected in *OH, then tracked by stable atom index into *O; CP2K and VASP use different cells/models and active-site indices.",
        })

    vasp_geom = {}
    for (system, state), meta in vasp_cases.items():
        poscar = PDOS_ROOT / meta["key"] / "POSCAR"
        cell, elements, coords = parse_poscar(poscar)
        d1 = distance(coords[meta["Coact"] - 1], coords[meta["Oads"] - 1], cell)
        d2 = distance(coords[meta["Coact"] - 1], coords[meta["Obridge"] - 1], cell)
        d3 = distance(coords[meta["neighbor"] - 1], coords[meta["Obridge"] - 1], cell)
        vasp_geom[(system, state)] = (cell, elements, coords)
        mapping_rows.append({
            "method": "VASP", "system": system, "state": state, "directory": rel(poscar.parent),
            "Coact_index": meta["Coact"], "Oads_index": meta["Oads"], "H_index": fmt(meta["H"]),
            "Obridge_index": meta["Obridge"], "neighbor_index": meta["neighbor"], "neighbor_element": meta["neighbor_element"],
            "Coact_Oads_distance_A": fmt(d1), "Coact_Obridge_distance_A": fmt(d2), "neighbor_Obridge_distance_A": fmt(d3),
            "geometry_match_quality": "identical fixed geometry within each matched pristine/Al pair",
            "notes": "Validated formal static mapping; *O index shifts after removal of H204. Cross-method geometry is related, not identical.",
        })
    write_tsv(OUT / "00_structure_mapping.tsv", mapping_rows)

    absolute_rows = []
    roles = ["Coact", "Oads", "Obridge", "neighbor"]
    for (system, state), data in cp2k_data.items():
        for partition, table in data["pops"].items():
            for role in roles:
                idx = data["meta"][role]
                value = table[idx]
                absolute_rows.append({
                    "system": system, "state": state, "atom_role": role, "atom_index": idx,
                    "element": value["element"], "method_partition": partition,
                    "N_total": fmt(value["N_total"]), "N_up": fmt(value["N_up"]), "N_down": fmt(value["N_down"]),
                    "charge_e": fmt(value["charge"]), "spin_muB": fmt(value["spin"]), "source_file": rel(data["out"]),
                })
    write_tsv(OUT / "01_cp2k_absolute_populations.tsv", absolute_rows)

    ligand_md = """# CP2K ligand-field interpretation

## Result

The active Co is best described as a **strongly covalent, spin-polarized Co-O center**. A high-spin-like d6 picture is a useful qualitative starting point, but not a literal integer oxidation-state assignment.

- CP2K local Co moments are 3.20-3.25 muB in *OH and 2.39-2.88 muB in *O, depending on material and partition. These values are compatible with substantial exchange polarization and broadly HS-like behavior, but are smaller than the spin-only 4 muB limit of an ideal localized S=2 center.
- Mulliken Co populations near 16.1-16.3 valence electrons and strongly partition-dependent Hirshfeld charges show that Co-O covalency invalidates a strict ionic d6 count.
- Oxidation changes both Co and O populations and spin; it is therefore safer to draw exchange-split Co-O hybrid manifolds than isolated atomic Co d levels.
- The Al-substituted *O state retains a larger Co moment than pristine *O, consistent with reduced Co-centered spin accommodation in the CP2K model.

## Safe manuscript wording

"The active site is a strongly covalent, high-spin-like Co-O unit with pronounced exchange splitting; formal d6 notation is used only as a ligand-field guide."

Source: `01_cp2k_absolute_populations.tsv` from the four validated CP2K baseline outputs.
"""
    (OUT / "02_cp2k_ligand_field_interpretation.md").write_text(ligand_md, encoding="utf-8")

    change_rows = []
    for system in ("pristine", "Al16"):
        oh = cp2k_data[(system, "*OH")]
        oo = cp2k_data[(system, "*O")]
        for partition in ("Mulliken", "Hirshfeld"):
            for role in roles:
                a = oh["pops"][partition][oh["meta"][role]]
                b = oo["pops"][partition][oo["meta"][role]]
                change_rows.append({
                    "system": system, "atom_role": role,
                    "OH_atom_index": oh["meta"][role], "O_atom_index": oo["meta"][role],
                    "method_partition": partition,
                    "OH_N_up": fmt(a["N_up"]), "O_N_up": fmt(b["N_up"]), "delta_N_up": fmt(b["N_up"] - a["N_up"]),
                    "OH_N_down": fmt(a["N_down"]), "O_N_down": fmt(b["N_down"]), "delta_N_down": fmt(b["N_down"] - a["N_down"]),
                    "OH_N_total": fmt(a["N_total"]), "O_N_total": fmt(b["N_total"]), "delta_N_total": fmt(b["N_total"] - a["N_total"]),
                    "OH_spin_muB": fmt(a["spin"]), "O_spin_muB": fmt(b["spin"]), "delta_spin_muB": fmt(b["spin"] - a["spin"]),
                    "source_files": f"{rel(oh['out'])};{rel(oo['out'])}",
                })
    write_tsv(OUT / "03_cp2k_spin_resolved_changes.tsv", change_rows)

    constraint_src = ROOT / "cdft_undoped_vs_al16_complete_20260818.tsv"
    constraint_rows = []
    with constraint_src.open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            row["source_file"] = rel(constraint_src)
            row["quantity_type"] = "cDFT constraint penalty; not CHE energy or barrier"
            constraint_rows.append(row)
    write_tsv(OUT / "04_cp2k_cdft_constraints.tsv", constraint_rows)
    cdft_md = """# CP2K cDFT interpretation

1. **Ligand/Co-O holes are favored over Co-only holes.** Existing N-1 penalties are about 4.89-5.27 eV for Co-only constraints but 2.87-3.39 eV for Co+adsorbate constraints. This supports an O-rich, covalent hole rather than a purely Co-localized oxidation.
2. **Al makes Co-centered spin accommodation harder in the *O state.** The valid Co-only M+2 penalty increases from 2.899188 eV (pristine) to 4.036604 eV (Al16), a +1.137416 eV difference.
3. **Al suppresses the CP2K Co-centered charge response.** Hirshfeld Delta N(Coact) is +0.219 e in pristine but +0.012 e in Al16; Mulliken gives +0.147192 and +0.050237 e, respectively. The magnitude is partition dependent, but the suppression trend is consistent.
4. **O is the dominant redox center.** Hirshfeld Delta N(Oads) is -0.464 e (pristine) and -0.427 e (Al16). In Al16 the Oads local spin changes from +0.336 to -0.408 muB in CP2K.
5. The Al16 M-2 branch was rejected because of a discontinuous spin branch and cannot be used.

These values are cDFT localization/spin penalties. They are not CHE reaction free energies, kinetic barriers, or applied potentials.
"""
    (OUT / "04_cp2k_cdft_interpretation.md").write_text(cdft_md, encoding="utf-8")

    frontier_cp2k_rows = []
    for system in ("pristine", "Al16"):
        data = cp2k_data[(system, "*OH")]
        frontier_cp2k_rows.append({
            "system": system, "state": "*OH", "frontier_window": "HOMO-2 eV to LUMO+0.5 eV requested",
            "MO_eigenvalues_available": "NO", "spin_resolved_PDOS_available": "NO",
            "Oads_2p_weight": "", "Coact_3d_weight": "", "neighbor_weight": "",
            "interpretation": "Existing baseline output contains populations but no MO eigenvalue list, PDOS, LDOS, or orbital projections; defer symmetry and bonding character to VASP/LOBSTER.",
            "source_file": rel(data["out"]),
        })
    write_tsv(OUT / "05_cp2k_frontier_states.tsv", frontier_cp2k_rows)
    fig, ax = plt.subplots(figsize=(7.2, 3.2), dpi=180)
    ax.axis("off")
    ax.text(0.5, 0.72, "CP2K frontier-state projection not available", ha="center", va="center", fontsize=15, weight="bold")
    ax.text(0.5, 0.43, "Validated baseline outputs contain Mulliken/Hirshfeld populations\nbut no MO eigenvalues, PDOS or orbital-resolved LDOS.", ha="center", va="center", fontsize=11)
    ax.text(0.5, 0.16, "No new SCF was run. Orbital symmetry and bonding are deferred to VASP/LOBSTER.", ha="center", va="center", fontsize=9.5, color=GRAY)
    fig.savefig(OUT / "05_cp2k_frontier_states.png", dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)

    pdos_loaded = {}
    pdos_rows = []
    frontier_features = {}
    for system, key in (("pristine", "undoped_OH"), ("Al16", "Al16_OH")):
        meta = vasp_cases[(system, "*OH")]
        dos_path = PDOS_ROOT / key / "DOSCAR"
        energy, projected = parse_doscar(dos_path)
        pdos_loaded[system] = (energy, projected)
        role_specs = [
            ("Coact", meta["Coact"], D_ORBS),
            ("Oads", meta["Oads"], P_ORBS),
            ("Obridge", meta["Obridge"], P_ORBS),
            ("neighbor", meta["neighbor"], D_ORBS if meta["neighbor_element"] == "Co" else {**S_ORBS, **P_ORBS, **D_ORBS}),
        ]
        mask = (energy >= -2.0) & (energy <= 0.5)
        for role, idx, orbital_map in role_specs:
            for orbital, cols in orbital_map.items():
                up, down = atom_orbital(projected, idx, cols)
                for i in np.where(mask)[0]:
                    pdos_rows.append({
                        "system": system, "state": "*OH", "energy_minus_EF_eV": fmt(float(energy[i])),
                        "atom_role": role, "atom_index": idx, "element": vasp_geom[(system, "*OH")][1][idx - 1],
                        "orbital_global_axis": orbital, "spin": "up", "PDOS_states_per_eV": fmt(float(up[i])), "source_file": rel(dos_path),
                    })
                    pdos_rows.append({
                        "system": system, "state": "*OH", "energy_minus_EF_eV": fmt(float(energy[i])),
                        "atom_role": role, "atom_index": idx, "element": vasp_geom[(system, "*OH")][1][idx - 1],
                        "orbital_global_axis": orbital, "spin": "down", "PDOS_states_per_eV": fmt(float(down[i])), "source_file": rel(dos_path),
                    })
        o_up, o_down = orbital_sum(projected, meta["Oads"], P_ORBS)
        peak_mask = (energy >= -1.0) & (energy <= 0.0)
        peak_i = np.where(peak_mask)[0][np.argmax(o_down[peak_mask])]
        co_up, co_down = orbital_sum(projected, meta["Coact"], D_ORBS)
        ob_up, ob_down = orbital_sum(projected, meta["Obridge"], P_ORBS)
        nmap = D_ORBS if meta["neighbor_element"] == "Co" else {**S_ORBS, **P_ORBS, **D_ORBS}
        n_up, n_down = orbital_sum(projected, meta["neighbor"], nmap)
        frontier_features[system] = {
            "peak_energy_eV": float(energy[peak_i]), "Oads_p_down": float(o_down[peak_i]), "Oads_p_up": float(o_up[peak_i]),
            "Coact_d_down": float(co_down[peak_i]), "Coact_d_up": float(co_up[peak_i]),
            "Obridge_p_down": float(ob_down[peak_i]), "neighbor_down": float(n_down[peak_i]),
            "definition": "largest Oads p spin-down PDOS peak in -1 to 0 eV; spectral proxy, not an isolated eigenstate",
            "source_file": rel(dos_path),
        }
    write_tsv(OUT / "06_vasp_frontier_pdos.tsv", pdos_rows)

    for system, filename, title in (("pristine", "06_vasp_frontier_pdos_pristine.png", "Pristine CoOOH *OH"), ("Al16", "06_vasp_frontier_pdos_Al.png", "Al-substituted CoOOH *OH")):
        energy, projected = pdos_loaded[system]
        meta = vasp_cases[(system, "*OH")]
        o = orbital_sum(projected, meta["Oads"], P_ORBS)
        co = orbital_sum(projected, meta["Coact"], D_ORBS)
        ob = orbital_sum(projected, meta["Obridge"], P_ORBS)
        nmap = D_ORBS if meta["neighbor_element"] == "Co" else {**S_ORBS, **P_ORBS, **D_ORBS}
        nn = orbital_sum(projected, meta["neighbor"], nmap)
        fig, axes = plt.subplots(2, 2, figsize=(10.2, 6.2), dpi=180, sharey="row")
        for col, (lo, hi, label) in enumerate(((-2.0, 0.5, "frontier window"), (-1.0, 0.2, "near-EF detail"))):
            ax = axes[0, col]
            ax.plot(energy, o[0], color=UP, lw=1.6, label="Oads 2p up")
            ax.plot(energy, -o[1], color=DOWN, lw=1.6, label="Oads 2p down")
            ax.plot(energy, co[0], color=GREEN, lw=1.2, ls="--", label="Coact 3d up")
            ax.plot(energy, -co[1], color=PURPLE, lw=1.2, ls="--", label="Coact 3d down")
            ax.axvline(0, color="black", lw=0.8)
            ax.axvline(frontier_features[system]["peak_energy_eV"], color=GRAY, lw=0.9, ls=":")
            ax.axhline(0, color="black", lw=0.6)
            ax.set_xlim(lo, hi)
            ax.set_title(label)
            clean_axes(ax)
            ax = axes[1, col]
            ax.plot(energy, ob[0], color=UP, lw=1.5, label="Obridge 2p up")
            ax.plot(energy, -ob[1], color=DOWN, lw=1.5, label="Obridge 2p down")
            nlabel = "Coadj 3d" if system == "pristine" else "Al s+p+d"
            ax.plot(energy, nn[0], color=GREEN, lw=1.2, ls="--", label=f"{nlabel} up")
            ax.plot(energy, -nn[1], color=PURPLE, lw=1.2, ls="--", label=f"{nlabel} down")
            ax.axvline(0, color="black", lw=0.8)
            ax.axvline(frontier_features[system]["peak_energy_eV"], color=GRAY, lw=0.9, ls=":")
            ax.axhline(0, color="black", lw=0.6)
            ax.set_xlim(lo, hi)
            ax.set_xlabel(r"$E-E_F$ (eV)")
            clean_axes(ax)
        axes[0, 0].set_ylabel("PDOS (up / -down)")
        axes[1, 0].set_ylabel("PDOS (up / -down)")
        axes[0, 0].legend(frameon=False, fontsize=7, ncol=2)
        axes[1, 0].legend(frameon=False, fontsize=7, ncol=2)
        fig.suptitle(f"Spin-resolved frontier PDOS: {title}", fontsize=13)
        fig.text(0.5, 0.01, "Global VASP orbital axes; dotted line marks the Oads spin-down peak proxy.", ha="center", fontsize=8.5, color=GRAY)
        fig.tight_layout(rect=(0, 0.035, 1, 0.95))
        fig.savefig(OUT / filename, dpi=300, bbox_inches="tight", facecolor="white")
        plt.close(fig)

    cohp_cases = {}
    cohp_rows = []
    frontier_cohp_summary = {}
    for system, key in (("pristine", "undoped_OH"), ("Al16", "Al16_OH")):
        case = parse_cohp(COHP_ROOT / key)
        cohp_cases[(system, "*OH")] = case
        peak = frontier_features[system]["peak_energy_eV"]
        local = (case.energy >= peak - 0.12) & (case.energy <= peak + 0.12)
        selected_minus = -case.spin2
        total_minus = -(case.spin1 + case.spin2)
        vals = selected_minus[local]
        pos_frac = float(np.mean(vals > 0))
        neg_frac = float(np.mean(vals < 0))
        local_mean = float(np.mean(vals))
        total_local_mean = float(np.mean(total_minus[local]))
        if abs(local_mean) < 0.01:
            classification = "approximately nonbonding"
        elif pos_frac >= 0.75:
            classification = "weakly bonding" if abs(local_mean) < 0.10 else "bonding"
        elif neg_frac >= 0.75:
            classification = "weakly antibonding" if abs(local_mean) < 0.10 else "antibonding"
        else:
            classification = "mixed bonding/antibonding"
        frontier_cohp_summary[system] = {
            "peak_energy_eV": peak, "selected_spin": "spin2/down", "local_half_width_eV": 0.12,
            "mean_minus_COHP_selected_spin": local_mean, "mean_minus_COHP_total_pair_both_spins": total_local_mean,
            "positive_fraction": pos_frac, "negative_fraction": neg_frac, "classification": classification,
            "source_file": rel(case.source),
        }
        mask = (case.energy >= -2.0) & (case.energy <= 0.5)
        for i in np.where(mask)[0]:
            for spin, values in (("spin1/up", -case.spin1), ("spin2/down", -case.spin2)):
                cohp_rows.append({
                    "system": system, "state": "*OH", "energy_minus_EF_eV": fmt(float(case.energy[i])), "spin": spin,
                    "minus_COHP": fmt(float(values[i])), "frontier_peak_proxy_eV": fmt(peak),
                    "selected_frontier_spin": "spin2/down", "local_mean_minus_COHP_selected_spin": fmt(local_mean),
                    "local_mean_minus_COHP_total_pair_both_spins": fmt(total_local_mean), "frontier_classification": classification,
                    "sign_convention": "positive -COHP = bonding; negative -COHP = antibonding",
                    "source_file": rel(case.source),
                })
    write_tsv(OUT / "07_frontier_cohp.tsv", cohp_rows)

    for system, filename, title in (("pristine", "07_frontier_cohp_pristine.png", "Pristine *OH"), ("Al16", "07_frontier_cohp_Al.png", "Al16 *OH")):
        case = cohp_cases[(system, "*OH")]
        peak = frontier_features[system]["peak_energy_eV"]
        fig, axes = plt.subplots(1, 2, figsize=(9.6, 3.8), dpi=180, sharey=True)
        for ax, (lo, hi, label) in zip(axes, ((-2.0, 0.5, "frontier window"), (-1.0, 0.2, "near-EF detail"))):
            ax.plot(case.energy, -case.spin1, color=UP, lw=1.6, label="spin 1 / up")
            ax.plot(case.energy, -case.spin2, color=DOWN, lw=1.6, label="spin 2 / down")
            ax.axhline(0, color="black", lw=0.7)
            ax.axvline(0, color="black", lw=0.8, ls="--")
            ax.axvline(peak, color=GRAY, lw=1, ls=":", label="Oads-down peak proxy")
            ax.set_xlim(lo, hi)
            ax.set_title(label)
            ax.set_xlabel(r"$E-E_F$ (eV)")
            clean_axes(ax)
        axes[0].set_ylabel(r"$-\mathrm{COHP}$ (bonding $>0$)")
        axes[0].legend(frameon=False, fontsize=8)
        fig.suptitle(f"Coact-Oads spin-2 frontier COHP: {title} ({frontier_cohp_summary[system]['classification']})", fontsize=12)
        fig.tight_layout(rect=(0, 0, 1, 0.93))
        fig.savefig(OUT / filename, dpi=300, bbox_inches="tight", facecolor="white")
        plt.close(fig)

    symmetry_rows = []
    for system in ("pristine", "Al16"):
        meta = vasp_cases[(system, "*OH")]
        cell, _, coords = vasp_geom[(system, "*OH")]
        vector = min_image(coords[meta["Oads"] - 1] - coords[meta["Coact"] - 1], cell)
        unit = vector / np.linalg.norm(vector)
        max_axis = max(abs(unit))
        symmetry_rows.append({
            "system": system, "state": "*OH", "Coact_Oads_vector_A": ",".join(f"{v:.6f}" for v in vector),
            "unit_vector_global_xyz": ",".join(f"{v:.6f}" for v in unit), "max_abs_axis_cosine": fmt(float(max_axis)),
            "minority_spin_assignment": "method-dependent: VASP/LOBSTER spin-down; CP2K Al Oads loss is alpha-dominant", "confidence_minority": "LOW",
            "Oads_character": "Oads 2p-rich spectral feature", "confidence_Oads": "HIGH",
            "Coact_character": "Coact 3d overlaps the frontier window", "confidence_Coact": "MEDIUM",
            "bonding_character": frontier_cohp_summary[system]["classification"], "confidence_bonding": "MEDIUM",
            "sigma_pi": "not assigned from global axes", "confidence_sigma_pi": "LOW",
            "eg_t2g": "not assigned in distorted covalent surface geometry", "confidence_eg_t2g": "LOW",
            "safe_label": "O-rich spin-polarized Co-O frontier state", "source_files": f"{rel(PDOS_ROOT / meta['key'] / 'POSCAR')};{rel(COHP_ROOT / meta['key'] / 'COHPCAR.lobster')}",
        })
    write_tsv(OUT / "08_orbital_symmetry_assignment.tsv", symmetry_rows)
    symmetry_md = """# Orbital-symmetry assignment

The Coact-Oads bond vector was evaluated in the global VASP cell, but the available PDOS labels remain global Cartesian projections. No local-axis rotation or orbital-resolved p-d COHP exists in the present data.

Therefore:

- Oads 2p-rich character: **high confidence**.
- Coact 3d admixture: **medium confidence**.
- Co-O bonding character near the selected spectral feature: **medium confidence**, from total pair COHP.
- universal minority-spin assignment: **low confidence/method dependent**, because CP2K and VASP/LOBSTER disagree on the dominant spin channel of Oads electron loss.
- sigma/pi and eg/t2g labels: **low confidence; not assigned**.

Safe label for the manuscript diagram: **O-rich spin-polarized Co-O frontier state**. This is deliberately less specific than "minority-spin eg*/sigma*".
"""
    (OUT / "08_orbital_symmetry_assignment.md").write_text(symmetry_md, encoding="utf-8")

    all_cohp = {}
    summary_src = ROOT / "cohp_oh_to_o_academic_summary_20260824.tsv"
    for system, material, prefix in (("pristine", "Undoped", "undoped"), ("Al16", "Al16", "Al16")):
        for state, suffix in (("*OH", "OH"), ("*O", "O")):
            all_cohp[(system, state)] = parse_cohp(COHP_ROOT / f"{prefix}_{suffix}")
    rehyb_rows = []
    for system in ("pristine", "Al16"):
        oh = all_cohp[(system, "*OH")]
        oo = all_cohp[(system, "*O")]
        d1 = -(oo.icohp[0][1] - oh.icohp[0][1])
        d2 = -(oo.icohp[0][2] - oh.icohp[0][2])
        rehyb_rows.append({
            "system": system, "pair": "Coact-Oads", "OH_ICOHP_spin1_eV": fmt(oh.icohp[0][1]), "O_ICOHP_spin1_eV": fmt(oo.icohp[0][1]),
            "delta_minus_ICOHP_spin1_eV": fmt(d1), "OH_ICOHP_spin2_eV": fmt(oh.icohp[0][2]), "O_ICOHP_spin2_eV": fmt(oo.icohp[0][2]),
            "delta_minus_ICOHP_spin2_eV": fmt(d2), "delta_minus_ICOHP_total_eV": fmt(d1 + d2),
            "interpretation": "positive Delta(-ICOHP) = occupied Co-O bond strengthening; spin-dependent covalency rehybridization, not majority-electron transfer",
            "source_files": f"{rel(oh.source)};{rel(oo.source)};{rel(summary_src)}",
        })
    write_tsv(OUT / "09_spin_rehybridization.tsv", rehyb_rows)
    fig, ax = plt.subplots(figsize=(6.2, 4.2), dpi=180)
    x = np.arange(2)
    d1s = [float(r["delta_minus_ICOHP_spin1_eV"]) for r in rehyb_rows]
    d2s = [float(r["delta_minus_ICOHP_spin2_eV"]) for r in rehyb_rows]
    ax.bar(x, d1s, width=0.58, color=UP, label="spin 1 / up")
    ax.bar(x, d2s, width=0.58, bottom=d1s, color=DOWN, label="spin 2 / down")
    for i, total in enumerate(np.array(d1s) + np.array(d2s)):
        ax.text(i, total + 0.035, f"{total:.3f} eV", ha="center", fontsize=9)
    ax.set_xticks(x, ["Pristine", "Al16"])
    ax.set_ylabel(r"$\Delta(-ICOHP)$, *O - *OH (eV)")
    ax.set_title("Spin-dependent Coact-Oads bond rehybridization")
    ax.legend(frameon=False)
    clean_axes(ax)
    fig.tight_layout()
    fig.savefig(OUT / "09_spin_rehybridization.png", dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)

    neighbor_rows = []
    for system in ("pristine", "Al16"):
        energy, projected = pdos_loaded[system]
        meta = vasp_cases[(system, "*OH")]
        nmap = D_ORBS if meta["neighbor_element"] == "Co" else {**S_ORBS, **P_ORBS, **D_ORBS}
        nup, ndown = orbital_sum(projected, meta["neighbor"], nmap)
        mask = (energy >= -2.0) & (energy <= 0.5)
        neighbor_rows.append({
            "system": system, "quantity": "neighbor frontier PDOS integral", "atom_role": "Coadj" if system == "pristine" else "Al",
            "spin1_value": fmt(float(np.trapezoid(nup[mask], energy[mask]))), "spin2_value": fmt(float(np.trapezoid(ndown[mask], energy[mask]))),
            "total_value": fmt(float(np.trapezoid((nup + ndown)[mask], energy[mask]))), "units": "states in -2.0 to +0.5 eV",
            "interpretation": "magnetic Co 3d frontier weight" if system == "pristine" else "Al s+p+d projection; Al local moment is approximately zero",
            "source_file": rel(PDOS_ROOT / meta["key"] / "DOSCAR"),
        })
        oh = all_cohp[(system, "*OH")]
        oo = all_cohp[(system, "*O")]
        for pair_idx, label in ((3, "Coact-Obridge"), (4, "neighbor-Obridge")):
            d1 = -(oo.icohp[pair_idx][1] - oh.icohp[pair_idx][1])
            d2 = -(oo.icohp[pair_idx][2] - oh.icohp[pair_idx][2])
            neighbor_rows.append({
                "system": system, "quantity": "bond rehybridization", "atom_role": label,
                "spin1_value": fmt(d1), "spin2_value": fmt(d2), "total_value": fmt(d1 + d2), "units": "Delta(-ICOHP) eV",
                "interpretation": "positive = bond strengthening; near-zero neighbor-framework response for Al",
                "source_file": f"{rel(oh.source)};{rel(oo.source)}",
            })
    write_tsv(OUT / "10_neighbor_Co_vs_Al.tsv", neighbor_rows)
    fig, axes = plt.subplots(1, 2, figsize=(9.8, 4.0), dpi=180)
    for system, color, label in (("pristine", GREEN, "Coadj 3d"), ("Al16", PURPLE, "Al s+p+d")):
        energy, projected = pdos_loaded[system]
        meta = vasp_cases[(system, "*OH")]
        nmap = D_ORBS if meta["neighbor_element"] == "Co" else {**S_ORBS, **P_ORBS, **D_ORBS}
        up, down = orbital_sum(projected, meta["neighbor"], nmap)
        axes[0].plot(energy, up, color=color, lw=1.6, label=f"{label} up")
        axes[0].plot(energy, -down, color=color, lw=1.2, ls="--", label=f"{label} down")
    axes[0].axvline(0, color="black", lw=0.8)
    axes[0].axhline(0, color="black", lw=0.6)
    axes[0].set_xlim(-2, 0.5)
    axes[0].set_xlabel(r"$E-E_F$ (eV)")
    axes[0].set_ylabel("PDOS (up / -down)")
    axes[0].set_title("Neighbor states on one energy scale")
    axes[0].legend(frameon=False, fontsize=7)
    clean_axes(axes[0])
    labels = ["Coact-O\npristine", "Coact-O\nAl16", "neighbor-O\npristine", "neighbor-O\nAl16"]
    vals = []
    for role, system in (("Coact-Obridge", "pristine"), ("Coact-Obridge", "Al16"), ("neighbor-Obridge", "pristine"), ("neighbor-Obridge", "Al16")):
        vals.append(float(next(r["total_value"] for r in neighbor_rows if r["system"] == system and r["atom_role"] == role)))
    axes[1].bar(np.arange(4), vals, color=[GREEN, PURPLE, GREEN, PURPLE])
    axes[1].axhline(0, color="black", lw=0.7)
    axes[1].set_xticks(np.arange(4), labels)
    axes[1].set_ylabel(r"$\Delta(-ICOHP)$ (eV)")
    axes[1].set_title("Bridge-bond response, *O - *OH")
    clean_axes(axes[1])
    fig.tight_layout()
    fig.savefig(OUT / "10_neighbor_Co_vs_Al.png", dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)

    audit_rows = []
    for system in ("pristine", "Al16"):
        for partition in ("Mulliken", "Hirshfeld"):
            for state in ("*OH", "*O"):
                data = cp2k_data[(system, state)]
                v = data["pops"][partition][data["meta"]["Oads"]]
                audit_rows.append({
                    "method": "CP2K", "partition": partition, "system": system, "state": state, "Oads_index": data["meta"]["Oads"],
                    "N_up": fmt(v["N_up"]), "N_down": fmt(v["N_down"]), "N_total": fmt(v["N_total"]), "local_spin_muB": fmt(v["spin"]),
                    "charge_e": fmt(v["charge"]), "spin_axis_note": "same global alpha-beta convention; active Co spin is positive",
                    "source_file": rel(data["out"]),
                })
        for state, suffix, idx in (("*OH", "OH", 348), ("*O", "O", 347)):
            gp_path = GROSS_ROOT / f"{'undoped' if system == 'pristine' else 'Al16'}_{suffix}_GROSSPOP.lobster"
            gp = parse_grosspop_total(gp_path, idx)
            for partition in ("Mulliken", "Loewdin"):
                up = gp[f"{partition}_up"]
                down = gp[f"{partition}_down"]
                audit_rows.append({
                    "method": "LOBSTER", "partition": partition, "system": system, "state": state, "Oads_index": idx,
                    "N_up": fmt(up), "N_down": fmt(down), "N_total": fmt(up + down), "local_spin_muB": fmt(up - down),
                    "charge_e": "", "spin_axis_note": "VASP/LOBSTER spin 1/up minus spin 2/down",
                    "source_file": rel(gp_path),
                })
    vasp_support = {
        ("pristine", "*OH"): (0.159, -0.618730), ("pristine", "*O"): (0.813, -0.358038),
        ("Al16", "*OH"): (0.328, -0.650293), ("Al16", "*O"): (1.028, -0.426088),
    }
    mech_source = ROOT / "cooh_al16_oh_to_o_mechanism_data_for_image_ai_20260831.md"
    for (system, state), (moment, charge) in vasp_support.items():
        audit_rows.append({
            "method": "VASP+Bader", "partition": "OUTCAR local moment + Bader charge", "system": system, "state": state,
            "Oads_index": vasp_cases[(system, state)]["Oads"], "N_up": "", "N_down": "", "N_total": "",
            "local_spin_muB": fmt(moment), "charge_e": fmt(charge), "spin_axis_note": "Bader charge is not a spin partition; OUTCAR moment remains positive",
            "source_file": rel(mech_source),
        })
    write_tsv(OUT / "11_O_spin_reversal_audit.tsv", audit_rows)
    audit_md = """# Oads spin-reversal audit

## Classification

**CP2K PARTITION-ROBUST BUT NOT VASP-ROBUST**

## CP2K primary result

- In Al16, Oads changes from +0.339262 to -0.462897 muB (Mulliken) and from +0.336 to -0.408 muB (Hirshfeld).
- Both CP2K partitions therefore support a local Oads spin-polarization reversal.
- Hirshfeld Oads changes from N_alpha/N_beta = 3.318/2.981 in *OH to 2.732/3.140 in *O. The dominant electron loss is alpha relative to the positive Co spin axis; beta gains population.
- Pristine Oads does not reverse sign and loses both alpha and beta population more evenly.

## VASP/LOBSTER supporting result

- VASP local Oads moments remain positive: pristine +0.159 to +0.813 muB; Al16 +0.328 to +1.028 muB.
- LOBSTER Oads 2p populations indicate spin-down loss with spin-up gain, not the CP2K alpha-dominant loss.
- This is not a simple global spin-axis sign inversion because active Co has the same positive orientation in both descriptions.

## Why the methods can differ

The CP2K and VASP structures are related but not identical, use different cells/local sites, basis/projection definitions, and population partitions. Local spin assigned to an oxygen basin or atom-centered basis is not an observable invariant. The sign reversal is robust inside CP2K across Mulliken and Hirshfeld, but not across methods.

## Manuscript use

Use CP2K to support an Al-induced O-centered spin reorganization and disclose the CP2K local sign reversal as method dependent. Do not draw a universal removed minority-spin electron or claim a method-independent O spin reversal.
"""
    (OUT / "11_O_spin_reversal_audit.md").write_text(audit_md, encoding="utf-8")

    claims = [
        ("M1", "Active Co is strongly spin-polarized / HS-like.", "Co moments 3.20-3.25 muB in *OH; strongly covalent HS-like center.", "VASP moments near 3 muB support strong polarization.", "Strongly covalent high-spin-like Co-O; not strict ionic d6.", "HIGH", "YES", "Integer d6/S=2 is only a qualitative starting point."),
        ("M2", "Exchange splitting makes frontier spins inequivalent.", "Large local Co spin and unequal alpha/beta populations.", "Spin-resolved PDOS/COHP are strongly inequivalent.", "Exchange-split Co-O manifold.", "HIGH", "YES", "Exact orbital ordering is not available from CP2K."),
        ("M3", "The redox-active occupied frontier state is minority-spin.", "Al CP2K Oads loss is alpha-dominant, not beta/minority relative to positive Co.", "LOBSTER Oads 2p loss is spin-down dominated.", "Spin channel is method dependent; use O-rich spin-polarized frontier state.", "LOW", "NO", "CP2K and VASP/LOBSTER disagree."),
        ("M4", "The redox-active state has dominant Oads 2p character.", "Oads is dominant electron-loss site in both CP2K partitions.", "Oads p feature dominates the selected near-EF proxy and loses most projected population.", "O-rich/ligand-hole-like oxidation.", "HIGH", "YES", "PDOS peak is a spectral proxy, not a single MO."),
        ("M5", "It has significant Co 3d hybridization.", "Co population/spin respond and Co+adsorbate hole is cheaper than Co-only hole.", "Co 3d overlaps Oads 2p near EF; Co-O COHP is finite.", "Covalent Co-O frontier manifold.", "MEDIUM", "YES", "No local-axis orbital decomposition."),
        ("M6", "It has a definite Co-O bonding character.", "No CP2K orbital-resolved frontier COHP/PDOS.", f"Pristine: {frontier_cohp_summary['pristine']['classification']}; Al16: {frontier_cohp_summary['Al16']['classification']} near the Oads-down peak proxy.", "Use the system-specific spin2 pair-total COHP classification only.", "MEDIUM", "QUALIFIED", "Feature selection and pair-total COHP do not isolate one p-d molecular orbital."),
        ("M7", "It is eg*/sigma*-like or t2g*/pi*-like.", "Not available.", "Global orbital axes and no orbital-resolved p-d COHP prevent secure assignment.", "Do not assign eg/t2g or sigma/pi.", "LOW", "NO", "Requires local-axis projection/orbital-resolved COHP."),
        ("M8", "Oxidation strengthens Coact-Oads.", "Co-O distance/orbital energy not directly quantified in CP2K cDFT populations.", "Delta(-ICOHP) = +1.46490 eV pristine and +1.11234 eV Al16.", "Coact-Oads strengthens in both systems.", "HIGH", "YES", "ICOHP is a bonding metric, not a barrier."),
        ("M9", "Oxidation produces spin-dependent orbital rehybridization.", "Alpha/beta populations change differently on Co and O.", "Spin-resolved ICOHP and orbital populations reorganize differently.", "Spin-dependent covalency rehybridization.", "HIGH", "YES", "Do not call it majority-electron transfer."),
        ("M10", "Material-dependent rehybridization occurs predominantly in majority spin.", "CP2K is not orbital-bond resolved and does not establish this channel universally.", "Difference in bond strengthening is 0.35140 eV in spin1 and 0.00116 eV in spin2.", "VASP/LOBSTER-specific majority-spin bonding response.", "MEDIUM", "QUALIFIED", "Supporting-method result; CP2K spin-channel assignment differs."),
        ("M11", "Neighboring Co provides low-energy magnetic d-state coupling.", "Mapped neighboring Co has finite spin/population response.", "Coadj 3d PDOS is spin polarized near EF and bridge COHP responds.", "Neighbor Co can provide a magnetic d-state relaxation channel.", "MEDIUM", "QUALIFIED", "Direct causal isolation would require targeted orbital perturbation."),
        ("M12", "Al lacks an equivalent low-energy magnetic d manifold.", "Mapped Al has near-zero local spin.", "Al local moment is about 0.003 muB and lacks Co-like magnetic 3d PDOS.", "Al removes the neighboring magnetic Co channel.", "HIGH", "YES", "Al still has strong, largely invariant Al-O bonding."),
        ("M13", "Al suppresses Co-centered orbital/spin accommodation.", "Co Delta N is +0.219 to +0.012 e (Hirshfeld) and M+2 penalty rises by 1.137416 eV.", "Co moment drop is reduced and spin1 Co-O strengthening is smaller.", "Al buffers/suppresses Co-centered response.", "HIGH", "YES", "Absolute charge magnitudes depend on partition."),
        ("M14", "The oxidized state is more O-centered with Al.", "Oads remains main redox center while Co response is strongly suppressed.", "Bader and LOBSTER show O-centered spin/population response with smaller Co d net change.", "Al favors ligand/O-centered accommodation.", "HIGH", "YES", "VASP Bader Co charge differences are small; CP2K is primary."),
        ("M15", "Oads spin polarization reverses in Al16.", "Yes in both CP2K Mulliken and Hirshfeld.", "No in VASP OUTCAR/LOBSTER sign.", "CP2K partition-robust but not VASP-robust.", "MEDIUM", "QUALIFIED", "Disclose model and partition dependence."),
    ]
    cp2k_claim_values = {
        "M1": "mCo(*OH) pristine=3.254625/3.215, Al16=3.204646/3.224 muB (Mulliken/Hirshfeld)",
        "M2": "Coact *OH local spin pristine=3.215, Al16=3.224 muB (Hirshfeld)",
        "M3": "Al16 Oads Hirshfeld Delta N_alpha=-0.586, Delta N_beta=+0.159 e; active Co spin remains positive",
        "M4": "Hirshfeld Delta N(Oads)=-0.464 e pristine, -0.427 e Al16",
        "M5": "N-1 penalty: Co-only=4.889-5.269 eV; Co+adsorbate=2.874-3.390 eV",
        "M6": "null: no CP2K orbital-resolved frontier COHP/PDOS",
        "M7": "null: no bond-aligned CP2K orbital projection",
        "M8": "null: CP2K population analysis does not provide ICOHP",
        "M9": "Al16 Oads Delta N_alpha=-0.586, Delta N_beta=+0.159 e (Hirshfeld)",
        "M10": "null: CP2K output is not orbital-bond resolved",
        "M11": "Mapped CP2K neighbor is Co45 (pristine) or Al32 (Al16); see absolute populations",
        "M12": "Al32 is the mapped neighboring atom; its local spin is small relative to Co",
        "M13": "Hirshfeld Delta N(Coact)=+0.219 e pristine vs +0.012 e Al16; Co-only M+2 penalty=2.899188 vs 4.036604 eV",
        "M14": "Hirshfeld Delta N(Oads)=-0.464/-0.427 e while Delta N(Coact)=+0.219/+0.012 e (pristine/Al16)",
        "M15": "Al16 Oads m=+0.339262 to -0.462897 muB Mulliken; +0.336 to -0.408 muB Hirshfeld",
    }
    vasp_claim_values = {
        "M1": "VASP mCoact(*OH)=2.941 muB pristine, 3.140 muB Al16",
        "M2": "spin-resolved PDOS and COHP channels are unequal near EF",
        "M3": "LOBSTER Oads 2p Delta N_up=+0.160/+0.220 and Delta N_down=-0.660/-0.680 e (pristine/Al16)",
        "M4": "largest Oads spin-down PDOS peak in -1..0 eV occurs at -0.096633 eV pristine and -0.109159 eV Al16",
        "M5": "finite Coact 3d PDOS at the Oads peak and ICOHP(*OH)=-1.92767/-1.93011 eV",
        "M6": f"spin2 local mean -COHP={frontier_cohp_summary['pristine']['mean_minus_COHP_selected_spin']:.6f} pristine ({frontier_cohp_summary['pristine']['classification']}), {frontier_cohp_summary['Al16']['mean_minus_COHP_selected_spin']:.6f} Al16 ({frontier_cohp_summary['Al16']['classification']})",
        "M7": "null: global VASP axes; no bond-aligned orbital-resolved p-d COHP",
        "M8": "Delta(-ICOHP)=+1.46490 eV pristine, +1.11234 eV Al16",
        "M9": "Delta(-ICOHP) spin1/spin2=+0.56027/+0.90463 eV pristine; +0.20887/+0.90347 eV Al16",
        "M10": "pristine-Al difference in Delta(-ICOHP)=0.35140 eV spin1 and 0.00116 eV spin2",
        "M11": "Coadj frontier PDOS integral=2.449529 states (-2..+0.5 eV); Coact-Obridge Delta(-ICOHP)=+0.070270 eV",
        "M12": "Al frontier s+p+d integral=0.012442 states and mAl about 0.003 muB",
        "M13": "Delta mCoact=-0.107 muB pristine vs -0.033 muB Al16; spin1 Delta(-ICOHP)=+0.56027 vs +0.20887 eV",
        "M14": "Bader Delta N(Oads)=-0.260692/-0.224205 e; LOBSTER Co 3d Delta N=+0.08/+0.04 e (pristine/Al16)",
        "M15": "VASP Oads m=+0.328 to +1.028 muB in Al16; no sign reversal",
    }
    evidence_rows = []
    for cid, pred, cp, va, pref, conf, safe, caveat in claims:
        evidence_rows.append({
            "claim_id": cid, "chemical_ligand_field_prediction": pred, "CP2K_evidence": cp,
            "CP2K_values": cp2k_claim_values[cid], "VASP_LOBSTER_evidence": va,
            "VASP_LOBSTER_values": vasp_claim_values[cid], "preferred_interpretation": pref,
            "confidence": conf, "safe_for_main_figure": safe, "caveat": caveat,
        })
    write_tsv(OUT / "12_mechanism_evidence_matrix.tsv", evidence_rows)

    diagram_md = """# Safe orbital diagram specification

## Mandatory drawing rule

Draw **exchange-split, covalent Co-O hybrid manifolds**, not a strict ionic Co d6 crystal-field diagram. Do not invent exact eg/t2g or sigma/pi labels. Use the generic label **O-rich spin-polarized Co-O frontier state**.

## Four panels

### Pristine *OH

1. Lower occupied Co-O bonding manifold, both spins occupied. Evidence: VASP PDOS + finite bonding COHP; occupancy arrows are schematic, not integer orbital counts.
2. O-rich occupied frontier manifold near EF with Co 3d admixture. Evidence: VASP Oads 2p and Coact 3d PDOS overlap; CP2K favors Co+adsorbate over Co-only holes.
   - VASP/LOBSTER spin-2 peak proxy: approximately nonbonding with respect to Coact-Oads; local mean -COHP = -0.001402 in +/-0.12 eV.
3. Neighbor-Co 3d/O-2p/Co-3d relaxation channel adjacent to the active manifold. Evidence: Coadj spin-polarized PDOS and bridge COHP.

### Pristine *O

1. Show one electron removed from the O-rich frontier manifold, but label the removed spin **method dependent**: CP2K and VASP/LOBSTER do not agree.
2. Show stronger Coact-Oads bonding after oxidation: Delta(-ICOHP) = +1.46490 eV (spin1 +0.56027; spin2 +0.90463 eV).
3. Show CP2K redistribution: Hirshfeld Delta N(Coact)=+0.219 e, Delta N(Oads)=-0.464 e; Delta m(Coact)=-0.821 muB.

### Al16 *OH

1. Same covalent exchange-split Co-O manifold.
   - VASP/LOBSTER spin-2 peak proxy: weakly antibonding with respect to Coact-Oads; local mean -COHP = -0.030390 in +/-0.12 eV.
2. Replace the neighboring magnetic Co level bundle with a high/weakly magnetic Al state label: Al has no equivalent low-energy magnetic Co-3d manifold and local moment about 0.003 muB.
3. Keep Al-O framework as a thin structural support, not a redox orbital.

### Al16 *O

1. Remove one electron from the O-rich frontier manifold with the same method-dependent spin annotation.
2. Show weaker total Co-O bond strengthening than pristine: Delta(-ICOHP)=+1.11234 eV (spin1 +0.20887; spin2 +0.90347 eV), 0.35256 eV less than pristine and almost entirely a spin1 bonding difference.
3. Show suppressed Co response from CP2K: Hirshfeld Delta N(Coact)=+0.012 e versus +0.219 e pristine; Co-only M+2 penalty is 4.036604 versus 2.899188 eV.
4. Show O-centered response: Hirshfeld Delta N(Oads)=-0.427 e and CP2K local spin +0.336 to -0.408 muB. Add a dagger: "local sign reversal is CP2K partition-robust but not VASP-robust."

## Electron-arrow justification

- Use arrows only to indicate exchange polarization and oxidation of an O-rich covalent manifold.
- Do not label the removed electron universally as minority spin. CP2K Al Oads loses alpha population while VASP/LOBSTER loses spin-down O 2p population.
- Do not draw a literal integer d6 occupation or exact orbital degeneracies.

## Safe one-sentence mechanism

Al substitution removes a neighboring magnetic Co-3d relaxation channel, raises the cost of Co-centered spin accommodation, and leaves *OH-to-*O oxidation more ligand/O-centered while reducing the spin1 contribution to Co-O bond strengthening.
"""
    (OUT / "13_safe_orbital_diagram.md").write_text(diagram_md, encoding="utf-8")

    additional_md = """# Minimal additional calculation request (not executed)

## Unresolved questions

1. Is the chemically redox-active CP2K frontier state alpha or beta, and what are its Oads/Coact/neighbor weights?
2. Is the selected near-EF Co-O feature sigma-like or pi-like in a bond-aligned local coordinate system?
3. Can total pair COHP be decomposed into specific Co d - O p interactions at the frontier feature?

## Why existing data are insufficient

The four CP2K baseline outputs contain populations but no MO eigenvalues or PDOS. VASP PDOS uses global axes, and existing LOBSTER COHP is pair-total rather than orbital-resolved. CP2K and VASP also disagree on the dominant spin channel of Oads electron loss.

## Requested Tier 1 / 1.5 work

- CP2K PDOS/MO post-processing from existing converged restart/WFN files, if those files exist: atom/orbital/spin projections for Coact, Oads, Obridge and neighbor in HOMO-2 to LUMO+0.5 eV. No new SCF.
- Orbital-resolved LOBSTER COHP rerun from existing WAVECAR/vasprun.xml using bond-aligned p-d pair definitions or equivalent local-axis analysis. No VASP rerun and no ionic relaxation.

Expected cost: post-processing only, likely minutes to hours and negligible relative to the completed statics. Expected outputs: CP2K PDOS/MO projection and orbital-resolved p-d COHP. Do not launch without explicit approval and confirmation that existing restart/WFN files are available.
"""
    (OUT / "14_minimal_additional_calculation_request.md").write_text(additional_md, encoding="utf-8")

    summary = {
        "model_mapping": {"rows": mapping_rows, "cross_method_comparability": "related but not strictly identical"},
        "cp2k_primary": {
            "ligand_field_state": {"label": "strongly covalent spin-polarized high-spin-like Co-O", "strict_ionic_d6": False, "source_file": "02_cp2k_ligand_field_interpretation.md"},
            "absolute_populations": {"units": {"N": "electrons", "charge": "e", "spin": "muB"}, "rows": absolute_rows},
            "oh_to_o_spin_changes": {"units": {"N": "electrons", "spin": "muB"}, "rows": change_rows},
            "cdft": {"quantity": "constraint penalty, not CHE energy or barrier", "units": "eV", "rows": constraint_rows},
            "frontier_states": {"available": False, "reason": "No MO eigenvalues, PDOS, LDOS, or orbital projections in existing baseline outputs", "source_files": [rel(cp2k_data[(s, '*OH')]['out']) for s in ('pristine', 'Al16')]},
        },
        "vasp_lobster_support": {
            "frontier_pdos": {"feature_definition": frontier_features, "units": {"energy": "eV relative to EF", "PDOS": "states/eV"}, "source_file": "06_vasp_frontier_pdos.tsv"},
            "frontier_cohp": {"sign_convention": "positive -COHP is bonding", "classification": frontier_cohp_summary, "source_file": "07_frontier_cohp.tsv"},
            "orbital_symmetry": {"safe_label": "O-rich spin-polarized Co-O frontier state", "sigma_pi": None, "eg_t2g": None, "source_file": "08_orbital_symmetry_assignment.tsv"},
            "spin_rehybridization": {"units": "Delta(-ICOHP), eV", "rows": rehyb_rows, "source_file": "09_spin_rehybridization.tsv"},
            "neighbor_co_vs_al": {"rows": neighbor_rows, "source_file": "10_neighbor_Co_vs_Al.tsv"},
        },
        "spin_reversal_audit": {"classification": "CP2K PARTITION-ROBUST BUT NOT VASP-ROBUST", "source_file": "11_O_spin_reversal_audit.md", "rows": audit_rows},
        "mechanistic_claims": [
            {"claim": row["chemical_ligand_field_prediction"], "cp2k_support": row["CP2K_evidence"], "cp2k_values": row["CP2K_values"], "vasp_support": row["VASP_LOBSTER_evidence"], "vasp_values": row["VASP_LOBSTER_values"], "confidence": row["confidence"], "safe_for_main_figure": row["safe_for_main_figure"] == "YES", "safe_for_main_figure_status": row["safe_for_main_figure"]}
            for row in evidence_rows
        ],
        "safe_orbital_diagram": {"safe_label": "O-rich spin-polarized Co-O frontier state", "specification_file": "13_safe_orbital_diagram.md", "universal_minority_spin_label": False, "exact_eg_t2g_label": False},
        "unresolved_questions": [
            "CP2K frontier spin/orbital weights are absent from existing outputs.",
            "Dominant Oads electron-loss spin channel disagrees between CP2K and VASP/LOBSTER.",
            "Local sigma/pi and eg/t2g assignment requires bond-aligned orbital projections.",
        ],
    }
    (OUT / "mechanism_validation_for_chatgpt.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    readme = """# Mechanism validation bundle

This bundle implements `chatgpt-request.md` using only existing validated CP2K, VASP, Bader and LOBSTER results. No new electronic-structure calculation was launched.

## Method hierarchy

- CP2K cDFT, Mulliken/Hirshfeld populations and local spin are primary for the charge/spin mechanism.
- VASP PDOS and LOBSTER COHP/populations provide supporting orbital and bond analysis.
- Values from the methods are not averaged. Disagreements are reported explicitly.

## Main supported result

Al substitution suppresses Co-centered charge/spin accommodation in CP2K, removes a neighboring magnetic Co-3d relaxation channel, and reduces the spin1 contribution to Coact-Oads bond strengthening. Oxidation remains O-rich/ligand-hole-like.

## Main limitation

The exact spin label of the removed frontier electron is not method robust: CP2K Al Oads loss is alpha dominated and reverses the local Oads spin sign, while VASP/LOBSTER indicates spin-down O-2p loss without a sign reversal. The safe orbital label is therefore **O-rich spin-polarized Co-O frontier state**.

For the VASP spin-2 Oads peak proxy, the corresponding Coact-Oads COHP is approximately nonbonding in pristine *OH and weakly antibonding in Al16 *OH. This is a selected spin-channel, pair-total COHP classification, not an exact molecular-orbital assignment.

## Start here

1. `mechanism_validation_for_chatgpt.json`
2. `12_mechanism_evidence_matrix.tsv`
3. `13_safe_orbital_diagram.md`
4. `11_O_spin_reversal_audit.md`

## Data provenance

All extracted rows contain source paths. CP2K/VASP structures are related but not strictly identical; fixed-geometry VASP pristine/Al pairs are internally matched. `05_cp2k_frontier_states.png` intentionally documents missing CP2K orbital output instead of fabricating a frontier diagram.
"""
    (OUT / "README.md").write_text(readme, encoding="utf-8")

    zip_path = ROOT / "mechanism_validation_bundle.zip"
    if zip_path.exists():
        zip_path.unlink()
    shutil.make_archive(str(zip_path.with_suffix("")), "zip", root_dir=OUT.parent, base_dir=OUT.name)
    print(f"Wrote {OUT}")
    print(f"Wrote {zip_path}")
    print(f"Files: {len(list(OUT.iterdir()))}")


if __name__ == "__main__":
    main()
