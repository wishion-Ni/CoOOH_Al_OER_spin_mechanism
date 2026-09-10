from __future__ import annotations

import csv
import itertools
import math
import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parent
STRUCTURE_ROOT = ROOT / "cohp_oh_o_inputs_20260824"
GROSSPOP_ROOT = ROOT / "lobster_grosspop_oh_o_20260826"
FRONTIER_ROOT = ROOT / "frontier_level_postprocess_20260903"
OUT = ROOT / "orbital_assignment_audit_20260903"


@dataclass(frozen=True)
class Case:
    key: str
    system: str
    material: str
    state: str
    coact: int
    neighbor: int
    oads: int
    obridge: int
    neighbor_element: str
    structure_folder: str
    grosspop_file: str


CASES = (
    Case("undoped_OH", "pristine_OH", "Pristine", "*OH", 21, 23, 348, 259, "Co", "undoped_OH", "undoped_OH_GROSSPOP.lobster"),
    Case("undoped_O", "pristine_O", "Pristine", "*O", 21, 23, 347, 258, "Co", "undoped_O", "undoped_O_GROSSPOP.lobster"),
    Case("Al16_OH", "Al16_OH", "Al16", "*OH", 16, 51, 348, 259, "Al", "Al16_OH", "Al16_OH_GROSSPOP.lobster"),
    Case("Al16_O", "Al16_O", "Al16", "*O", 16, 51, 347, 258, "Al", "Al16_O", "Al16_O_GROSSPOP.lobster"),
)


def write_tsv(path: Path, rows: list[dict[str, object]], columns: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def fmt(value: object) -> object:
    if isinstance(value, float):
        return f"{value:.8f}"
    return value


def read_poscar(path: Path) -> dict[str, object]:
    lines = path.read_text(encoding="ascii").splitlines()
    scale = float(lines[1].split()[0])
    lattice = np.array([[float(x) for x in lines[i].split()[:3]] for i in range(2, 5)]) * scale
    species = lines[5].split()
    counts = [int(x) for x in lines[6].split()]
    cursor = 7
    if lines[cursor].strip().lower().startswith("s"):
        cursor += 1
    mode = lines[cursor].strip().lower()
    cursor += 1
    coordinates = np.array(
        [[float(x) for x in lines[cursor + i].split()[:3]] for i in range(sum(counts))]
    )
    fractional = coordinates @ np.linalg.inv(lattice) if mode.startswith("c") else coordinates
    elements: list[str] = []
    for symbol, count in zip(species, counts):
        elements.extend([symbol] * count)
    return {
        "lattice": lattice,
        "species": species,
        "counts": counts,
        "fractional": fractional,
        "elements": elements,
    }


def minimum_image_vector(structure: dict[str, object], atom_a: int, atom_b: int) -> np.ndarray:
    frac = structure["fractional"]
    lattice = structure["lattice"]
    delta = frac[atom_b - 1] - frac[atom_a - 1]
    delta -= np.round(delta)
    return delta @ lattice


def oxygen_indices(structure: dict[str, object]) -> list[int]:
    return [index for index, element in enumerate(structure["elements"], start=1) if element == "O"]


def unit(vector: np.ndarray) -> np.ndarray:
    return vector / np.linalg.norm(vector)


def angle_deg(a: np.ndarray, b: np.ndarray) -> float:
    cosine = float(np.clip(np.dot(unit(a), unit(b)), -1.0, 1.0))
    return math.degrees(math.acos(cosine))


def spectator_pairings(indices: list[int]) -> list[list[tuple[int, int]]]:
    first = indices[0]
    result = []
    for partner in indices[1:]:
        remaining = [value for value in indices if value not in (first, partner)]
        result.append([(first, partner), (remaining[0], remaining[1])])
    return result


def procrustes_rotation(actual: np.ndarray, ideal: np.ndarray) -> np.ndarray:
    u, _singular, vt = np.linalg.svd(actual.T @ ideal)
    rotation = u @ vt
    if np.linalg.det(rotation) < 0:
        u[:, -1] *= -1
        rotation = u @ vt
    return rotation


def local_frame_rows(case: Case) -> list[dict[str, object]]:
    structure = read_poscar(STRUCTURE_ROOT / case.structure_folder / "POSCAR")
    vectors = {
        oxygen: minimum_image_vector(structure, case.coact, oxygen)
        for oxygen in oxygen_indices(structure)
    }
    six = sorted(vectors, key=lambda oxygen: np.linalg.norm(vectors[oxygen]))[:6]
    if case.oads not in six or case.obridge not in six:
        raise ValueError(f"Expected axial O atoms absent from six nearest O in {case.system}: {six}")
    spectators = [oxygen for oxygen in six if oxygen not in (case.oads, case.obridge)]
    pairing = max(
        spectator_pairings(spectators),
        key=lambda pairs: sum(angle_deg(vectors[a], vectors[b]) for a, b in pairs),
    )

    best = None
    for pair_order in (pairing, pairing[::-1]):
        for signs in itertools.product((1, -1), repeat=2):
            assignment: dict[int, np.ndarray] = {
                case.oads: np.array([0.0, 0.0, 1.0]),
                case.obridge: np.array([0.0, 0.0, -1.0]),
            }
            for axis_index, ((atom_a, atom_b), sign) in enumerate(zip(pair_order, signs)):
                axis = np.zeros(3)
                axis[axis_index] = float(sign)
                assignment[atom_a] = axis
                assignment[atom_b] = -axis
            ordered_atoms = [case.oads, case.obridge] + [atom for pair in pair_order for atom in pair]
            actual = np.array([unit(vectors[atom]) for atom in ordered_atoms])
            ideal = np.array([assignment[atom] for atom in ordered_atoms])
            rotation = procrustes_rotation(actual, ideal)
            fitted = actual @ rotation
            residual_angles = [angle_deg(fitted[i], ideal[i]) for i in range(6)]
            rms = math.sqrt(sum(value * value for value in residual_angles) / 6.0)
            candidate = (rms, assignment, pair_order, rotation, residual_angles, ordered_atoms)
            if best is None or candidate[0] < best[0]:
                best = candidate
    assert best is not None
    rms, assignment, pair_order, rotation, residual_angles, ordered_atoms = best
    residual_by_atom = dict(zip(ordered_atoms, residual_angles))
    trans_pairs = [(case.oads, case.obridge, "z")] + [
        (pair[0], pair[1], axis) for pair, axis in zip(pair_order, ("x", "y"))
    ]
    pair_by_atom: dict[int, tuple[str, int, float]] = {}
    for atom_a, atom_b, axis in trans_pairs:
        trans_angle = angle_deg(vectors[atom_a], vectors[atom_b])
        pair_by_atom[atom_a] = (axis, atom_b, trans_angle)
        pair_by_atom[atom_b] = (axis, atom_a, trans_angle)

    axis_global = {"x": rotation[:, 0], "y": rotation[:, 1], "z": rotation[:, 2]}
    rows: list[dict[str, object]] = []
    for oxygen in six:
        vector = vectors[oxygen]
        local = unit(vector) @ rotation
        ideal = assignment[oxygen]
        axis, trans_partner, trans_angle = pair_by_atom[oxygen]
        role = "Oads" if oxygen == case.oads else "Obridge" if oxygen == case.obridge else "spectator"
        row = {
            "system": case.system,
            "state": case.state,
            "active_Co": case.coact,
            "O_atom": oxygen,
            "role": role,
            "assigned_ideal_direction": "+" + axis if ideal[np.argmax(np.abs(ideal))] > 0 else "-" + axis,
            "distance_A": float(np.linalg.norm(vector)),
            "trans_partner": trans_partner,
            "trans_angle_deg": trans_angle,
            "fit_angular_deviation_deg": residual_by_atom[oxygen],
            "octahedral_fit_RMS_deg": rms,
            "bond_global_x": float(unit(vector)[0]),
            "bond_global_y": float(unit(vector)[1]),
            "bond_global_z": float(unit(vector)[2]),
            "bond_local_x": float(local[0]),
            "bond_local_y": float(local[1]),
            "bond_local_z": float(local[2]),
            "local_x_global_x": float(axis_global["x"][0]),
            "local_x_global_y": float(axis_global["x"][1]),
            "local_x_global_z": float(axis_global["x"][2]),
            "local_y_global_x": float(axis_global["y"][0]),
            "local_y_global_y": float(axis_global["y"][1]),
            "local_y_global_z": float(axis_global["y"][2]),
            "local_z_global_x": float(axis_global["z"][0]),
            "local_z_global_y": float(axis_global["z"][1]),
            "local_z_global_z": float(axis_global["z"][2]),
            "R_g2l_11": float(rotation[0, 0]),
            "R_g2l_12": float(rotation[0, 1]),
            "R_g2l_13": float(rotation[0, 2]),
            "R_g2l_21": float(rotation[1, 0]),
            "R_g2l_22": float(rotation[1, 1]),
            "R_g2l_23": float(rotation[1, 2]),
            "R_g2l_31": float(rotation[2, 0]),
            "R_g2l_32": float(rotation[2, 1]),
            "R_g2l_33": float(rotation[2, 2]),
        }
        rows.append({key: fmt(value) for key, value in row.items()})
    return rows


def parse_grosspop(path: Path) -> dict[int, dict[str, object]]:
    atoms: dict[int, dict[str, object]] = {}
    current_atom = None
    row_pattern = re.compile(
        r"^\s*(?:(\d+)\s+([A-Za-z]+)\s+)?(\S+)\s+"
        r"([-+]?\d+(?:\.\d+)?)\s+([-+]?\d+(?:\.\d+)?)\s+"
        r"([-+]?\d+(?:\.\d+)?)\s+([-+]?\d+(?:\.\d+)?)\s*$"
    )
    for line in path.read_text(encoding="ascii").splitlines():
        match = row_pattern.match(line)
        if not match:
            continue
        atom_text, element, orbital, mull_up, mull_down, loew_up, loew_down = match.groups()
        if atom_text is not None:
            current_atom = int(atom_text)
            atoms[current_atom] = {"element": element, "orbitals": {}}
        if current_atom is None or orbital == "total":
            continue
        atoms[current_atom]["orbitals"][orbital] = {
            "Mulliken": (float(mull_up), float(mull_down)),
            "Loewdin": (float(loew_up), float(loew_down)),
        }
    return atoms


def group_population(atom: dict[str, object], group: str, scheme: str) -> tuple[float, float] | None:
    orbitals = atom["orbitals"]
    labels = [label for label in orbitals if label == group or label.startswith(group + "_")]
    if not labels:
        return None
    up = sum(orbitals[label][scheme][0] for label in labels)
    down = sum(orbitals[label][scheme][1] for label in labels)
    return up, down


def population_rows(case: Case) -> list[dict[str, object]]:
    atoms = parse_grosspop(GROSSPOP_ROOT / case.grosspop_file)
    roles = [
        ("Coact", case.coact, ["3d", "4s", "4p"]),
        ("Oads", case.oads, ["2s", "2p"]),
        ("Obridge", case.obridge, ["2s", "2p"]),
        ("neighbor", case.neighbor, ["3d", "4s", "4p"] if case.neighbor_element == "Co" else ["3s", "3p", "3d"]),
    ]
    rows: list[dict[str, object]] = []
    for role, atom_index, groups in roles:
        atom = atoms[atom_index]
        for scheme in ("Mulliken", "Loewdin"):
            for group in groups:
                population = group_population(atom, group, scheme)
                if population is None:
                    row = {
                        "system": case.system,
                        "state": case.state,
                        "role": role,
                        "atom": atom_index,
                        "element": atom["element"],
                        "orbital_group": group,
                        "scheme": scheme,
                        "spin_up_e": "",
                        "spin_down_e": "",
                        "total_e": "",
                        "spin_moment_e": "",
                        "status": "not_in_recommended_basis",
                    }
                else:
                    up, down = population
                    row = {
                        "system": case.system,
                        "state": case.state,
                        "role": role,
                        "atom": atom_index,
                        "element": atom["element"],
                        "orbital_group": group,
                        "scheme": scheme,
                        "spin_up_e": up,
                        "spin_down_e": down,
                        "total_e": up + down,
                        "spin_moment_e": up - down,
                        "status": "available_global_basis",
                    }
                rows.append({key: fmt(value) for key, value in row.items()})
    return rows


def availability_rows() -> list[dict[str, object]]:
    rows = []
    for case in CASES:
        rows.append(
            {
                "system": case.system,
                "state": case.state,
                "active_Co": case.coact,
                "matrix_available": "no",
                "status": "unavailable",
                "reason": "OUTCAR has LDA+U enabled but no printed spin-resolved 5x5 onsite occupation matrix; LDAUPRINT was not enabled.",
            }
        )
    return rows


def spatial_rows() -> list[dict[str, object]]:
    source = FRONTIER_ROOT / "frontier_state_catalog.tsv"
    with source.open("r", encoding="utf-8", newline="") as handle:
        catalog = list(csv.DictReader(handle, delimiter="\t"))
    rows = []
    for item in catalog:
        atomic = {
            "Oads_local": float(item["Oads2p_weight"]),
            "Coact_local": float(item["Coact3d_weight"]),
            "Obridge_local": float(item["Obridge2p_weight"]),
            "neighbor_local": max(0.0, float(item["neighbor_weight"])),
        }
        atomic_total = sum(atomic.values())
        atomic_norm = {key: value / atomic_total if atomic_total else 0.0 for key, value in atomic.items()}
        bond = {
            "Oads_Coact": abs(float(item["Coact-Oads_minusCOHP_integral"])),
            "Coact_Obridge": abs(float(item["Coact-Obridge_minusCOHP_integral"])),
            "Obridge_neighbor": abs(float(item["neighbor-Obridge_minusCOHP_integral"])),
        }
        bond_total = sum(bond.values())
        bond_norm = {key: value / bond_total if bond_total else 0.0 for key, value in bond.items()}
        if atomic_norm["neighbor_local"] > 0.30 or bond_norm["Obridge_neighbor"] > 0.32:
            span = "framework extended"
        elif bond_norm["Oads_Coact"] > 0.20 and bond_norm["Coact_Obridge"] > 0.20:
            span = "axial extended"
        elif max(atomic_norm.values()) > 0.80 and max(bond.values()) < 0.01:
            span = "local"
        elif sum(value > 0.16 for value in atomic_norm.values()) >= 3:
            span = "three-center"
        else:
            span = "bond-local"
        row = {
            "system": item["system"],
            "state": item["state"],
            "feature_id": item["feature_id"],
            "spin": item["spin"],
            "E_peak_EF": item["E_peak_EF"],
            "atomic_H": "unavailable",
            "atomic_Oads": atomic_norm["Oads_local"],
            "atomic_Coact": atomic_norm["Coact_local"],
            "atomic_Obridge": atomic_norm["Obridge_local"],
            "atomic_neighbor": atomic_norm["neighbor_local"],
            "bond_H_Oads": "pending_active_H_COHP",
            "bond_Oads_Coact": bond_norm["Oads_Coact"],
            "bond_Coact_Osp4": "pending_sixbond_COHP",
            "bond_Coact_Obridge": bond_norm["Coact_Obridge"],
            "bond_Obridge_neighbor": bond_norm["Obridge_neighbor"],
            "qualitative_span": span,
            "status": "preliminary_three_bond_fingerprint",
        }
        rows.append({key: fmt(value) for key, value in row.items()})
    return rows


def report_text(frame_rows: list[dict[str, object]], pop_rows: list[dict[str, object]]) -> str:
    fit_by_case = {}
    for row in frame_rows:
        fit_by_case[row["system"]] = float(row["octahedral_fit_RMS_deg"])
    mulliken_d = {
        (row["system"], row["role"]): row
        for row in pop_rows
        if row["scheme"] == "Mulliken" and row["orbital_group"] == "3d" and row["status"] == "available_global_basis"
    }
    lines = [
        "# Orbital assignment audit: preliminary status",
        "",
        "This directory is independent from the original VASP and LOBSTER calculation directories. This preliminary pass contains only analyses that do not depend on the new six-bond orbital-wise LOBSTER array 111579.",
        "",
        "## Available now",
        "",
        "- The actual six-coordinate Co environment was fitted to an ideal octahedron with an orthogonal Procrustes transformation. The global-to-local matrix and every bond residual are in `local_octahedral_frame.tsv`.",
        "- Absolute spin-resolved Mulliken and Loewdin populations from the validated existing LOBSTER runs are in `absolute_orbital_populations.tsv`.",
        "- A preliminary atomic-versus-bond spatial audit using the existing three selected bonds is in `frontier_spatial_span.tsv`. Atomic PDOS and COHP bond weights remain separate.",
        "",
        "## Local frame quality",
        "",
    ]
    for case in CASES:
        lines.append(f"- {case.system}: six-bond ideal-octahedron angular RMS = {fit_by_case[case.system]:.3f} degrees.")
    lines.extend(
        [
            "",
            "## DFT+U occupation matrix limitation",
            "",
            "The four OUTCAR files confirm DFT+U, but they do not contain complete spin-resolved 5x5 onsite occupation matrices because no occupation-matrix printout was requested. Therefore no off-diagonal matrix, local-axis rotation, natural-orbital diagonalization, or local d-orbital eigenoccupation can be recovered. `local_d_occupation_matrix.tsv` records this as unavailable. Global-axis diagonal PDOS/GROSSPOP values are not substitutes for the missing density matrix.",
            "",
            "## Phase information limitation",
            "",
            "WAVECAR is sufficient for LOBSTER reprojection, but the existing PROCAR contains squared LORBIT=11 weights without cross terms or projector phases. It cannot support an arbitrary rotation of band-resolved d projections into the fitted local frame. Local-axis band weights are therefore not claimed.",
            "",
            "## Absolute Co d populations",
            "",
        ]
    )
    for case in CASES:
        row = mulliken_d[(case.system, "Coact")]
        lines.append(
            f"- {case.system}: Coact 3d Mulliken n_up={float(row['spin_up_e']):.3f}, "
            f"n_down={float(row['spin_down_e']):.3f}, total={float(row['total_e']):.3f}, "
            f"spin difference={float(row['spin_moment_e']):.3f} e."
        )
    lines.extend(
        [
            "",
            "These noninteger LOBSTER populations support a high-spin-like, strongly covalent parent description; they do not establish exact formal t2g4 eg2 occupations in the fitted local frame.",
            "",
            "## Pending array 111579",
            "",
            "The four LOBSTER-only tasks request orbital-wise COHP for all six Coact-O bonds, neighbor-metal-O_bridge, and Oads-H204 in both OH cases. Once validated, they will determine axial versus equatorial antibonding fingerprints, d-pi classifications, active O-H sigma/sigma-star regions, state correlations, empty-state fingerprints, and the final orbital audit archive.",
            "",
            "No VASP SCF calculation was submitted for this stage.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)

    frame_rows = [row for case in CASES for row in local_frame_rows(case)]
    frame_columns = list(frame_rows[0])
    write_tsv(OUT / "local_octahedral_frame.tsv", frame_rows, frame_columns)

    pop_rows = [row for case in CASES for row in population_rows(case)]
    pop_columns = list(pop_rows[0])
    write_tsv(OUT / "absolute_orbital_populations.tsv", pop_rows, pop_columns)

    matrix_rows = availability_rows()
    write_tsv(OUT / "local_d_occupation_matrix.tsv", matrix_rows, list(matrix_rows[0]))

    (OUT / "natural_d_orbitals.md").write_text(
        "# Natural d orbitals\n\n"
        "Unavailable from the completed calculations. The OUTCAR files do not print complete "
        "spin-resolved 5x5 DFT+U onsite occupation matrices, so off-diagonal terms, local-axis "
        "rotation, natural-orbital diagonalization, and overlap with local d basis functions cannot "
        "be reconstructed. Global-axis diagonal PDOS or GROSSPOP values are not used as substitutes.\n",
        encoding="utf-8",
    )

    spatial = spatial_rows()
    write_tsv(OUT / "frontier_spatial_span.tsv", spatial, list(spatial[0]))

    availability = [
        {
            "source": "OUTCAR",
            "quantity": "spin-resolved 5x5 DFT+U occupation matrix",
            "available": "no",
            "consequence": "No local-axis occupation matrix or natural d orbitals.",
        },
        {
            "source": "PROCAR",
            "quantity": "phase/cross-term-resolved projectors",
            "available": "no",
            "consequence": "No arbitrary local-axis rotation of band-resolved d weights.",
        },
        {
            "source": "WAVECAR",
            "quantity": "wavefunction coefficients usable by LOBSTER 5.1.1",
            "available": "yes",
            "consequence": "Six-bond and active O-H orbital-wise COHP array 111579 submitted.",
        },
    ]
    write_tsv(OUT / "phase_projection_availability.tsv", availability, list(availability[0]))

    (OUT / "orbital_assignment_audit.md").write_text(
        report_text(frame_rows, pop_rows), encoding="utf-8"
    )
    print(f"OUTPUT={OUT.resolve()}")
    print(f"FRAME_ROWS={len(frame_rows)}")
    print(f"POPULATION_ROWS={len(pop_rows)}")
    print(f"FRONTIER_ROWS={len(spatial)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
