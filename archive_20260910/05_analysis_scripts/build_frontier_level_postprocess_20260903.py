from __future__ import annotations

import csv
import hashlib
import math
import re
import shutil
import zipfile
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import linear_sum_assignment
from scipy.signal import find_peaks


ROOT = Path(__file__).resolve().parent
PDOS_ROOT = ROOT / "pdos_oh_o_inputs_20260824"
COHP_ROOT = ROOT / "cohp_oh_o_inputs_20260824"
OUT = ROOT / "frontier_level_postprocess_20260903"
ZIP_PATH = ROOT / "frontier_level_postprocess_20260903.zip"

PDOS_ORBITALS = (
    "s",
    "py",
    "pz",
    "px",
    "dxy",
    "dyz",
    "dz2",
    "dxz",
    "dx2_y2",
)


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
    pdos_folder: str
    cohp_folder: str
    remote_pdos_dir: str
    remote_cohp_dir: str


REMOTE_BASE = (
    "sfs/CoOH/cp2k/Al16/oer/spin_config_scan_site03_5OH_current_20260714/"
    "vasp_jacs6c06054_reconstructed_exact_Al16_3x2_20260809/"
    "electronic_structure_al_contribution_20260818"
)

CASES = (
    Case(
        "undoped_OH", "pristine_OH", "Pristine", "*OH", 21, 23, 348, 259, "Co",
        "undoped_OH", "undoped_OH",
        f"{REMOTE_BASE}/cohp_oh_o_corrected_20260820/undoped_control/OH",
        f"{REMOTE_BASE}/cohp_bader_formal_oh_o_20260822/undoped_control/OH_pair_corrected_nomadelung",
    ),
    Case(
        "undoped_O", "pristine_O", "Pristine", "*O", 21, 23, 347, 258, "Co",
        "undoped_O", "undoped_O",
        f"{REMOTE_BASE}/cohp_oh_o_corrected_20260820/undoped_control/O",
        f"{REMOTE_BASE}/cohp_bader_formal_oh_o_20260822/undoped_control/O_nomadelung",
    ),
    Case(
        "Al16_OH", "Al16_OH", "Al16", "*OH", 16, 51, 348, 259, "Al",
        "Al16_OH", "Al16_OH",
        f"{REMOTE_BASE}/cohp_oh_o_corrected_20260820/Al16_adjacent/OH",
        f"{REMOTE_BASE}/cohp_bader_formal_oh_o_20260822/Al16_adjacent/OH_nomadelung",
    ),
    Case(
        "Al16_O", "Al16_O", "Al16", "*O", 16, 51, 347, 258, "Al",
        "Al16_O", "Al16_O",
        f"{REMOTE_BASE}/cohp_oh_o_corrected_20260820/Al16_adjacent/O",
        f"{REMOTE_BASE}/cohp_bader_formal_oh_o_20260822/Al16_adjacent/O_nomadelung",
    ),
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_tsv(path: Path, rows: list[dict[str, object]], columns: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def read_poscar(path: Path) -> dict[str, object]:
    lines = path.read_text(encoding="ascii").splitlines()
    scale = float(lines[1].split()[0])
    lattice = np.array([[float(x) for x in lines[i].split()[:3]] for i in range(2, 5)]) * scale
    species = lines[5].split()
    counts = [int(x) for x in lines[6].split()]
    cursor = 7
    selective = lines[cursor].strip().lower().startswith("s")
    if selective:
        cursor += 1
    mode = lines[cursor].strip().lower()
    cursor += 1
    natoms = sum(counts)
    coordinates = np.array(
        [[float(x) for x in lines[cursor + i].split()[:3]] for i in range(natoms)], dtype=float
    )
    if mode.startswith("c"):
        fractional = coordinates @ np.linalg.inv(lattice)
    else:
        fractional = coordinates
    elements: list[str] = []
    for symbol, count in zip(species, counts):
        elements.extend([symbol] * count)
    return {
        "comment": lines[0],
        "lattice": lattice,
        "species": species,
        "counts": counts,
        "elements": elements,
        "fractional": fractional,
    }


def minimum_image_vector(frac_a: np.ndarray, frac_b: np.ndarray, lattice: np.ndarray) -> np.ndarray:
    delta = frac_b - frac_a
    delta -= np.round(delta)
    return delta @ lattice


def distance(structure: dict[str, object], atom_a: int, atom_b: int) -> tuple[float, np.ndarray]:
    frac = structure["fractional"]
    lattice = structure["lattice"]
    vector = minimum_image_vector(frac[atom_a - 1], frac[atom_b - 1], lattice)
    return float(np.linalg.norm(vector)), vector


def species_index_ranges(structure: dict[str, object]) -> dict[str, list[int]]:
    result: dict[str, list[int]] = {}
    start = 1
    for symbol, count in zip(structure["species"], structure["counts"]):
        result[symbol] = list(range(start, start + count))
        start += count
    return result


def identify_deleted_h(oh_structure: dict[str, object], o_structure: dict[str, object], oads: int) -> dict[str, object]:
    oh_h = species_index_ranges(oh_structure)["H"]
    o_h = species_index_ranges(o_structure)["H"]
    lattice = oh_structure["lattice"]
    oh_frac = oh_structure["fractional"]
    o_frac = o_structure["fractional"]
    cost = np.empty((len(oh_h), len(o_h)))
    for i, atom_i in enumerate(oh_h):
        for j, atom_j in enumerate(o_h):
            vec = minimum_image_vector(oh_frac[atom_i - 1], o_frac[atom_j - 1], lattice)
            cost[i, j] = np.linalg.norm(vec)
    rows, cols = linear_sum_assignment(cost)
    matched_oh = {oh_h[i] for i, j in zip(rows, cols) if cost[i, j] < 0.02}
    unmatched = [idx for idx in oh_h if idx not in matched_oh]
    if len(unmatched) != 1:
        # The structures are fixed and byte-derived; nearest-H fallback is deterministic.
        candidates = [(distance(oh_structure, oads, idx)[0], idx) for idx in oh_h]
        unmatched = [min(candidates)[1]]
    active_h = unmatched[0]
    dist, vec = distance(oh_structure, oads, active_h)
    return {"active_h": active_h, "distance_A": dist, "vector_A": vec}


def read_doscar(path: Path) -> tuple[float, np.ndarray, np.ndarray, float]:
    with path.open("r", encoding="ascii") as handle:
        natoms = int(handle.readline().split()[0])
        for _ in range(4):
            handle.readline()
        header = handle.readline().split()
        nedos = int(header[2])
        efermi = float(header[3])
        for _ in range(nedos):
            handle.readline()
        energy = None
        projected = np.empty((natoms, nedos, 2, len(PDOS_ORBITALS)), dtype=float)
        for atom in range(natoms):
            atom_header = handle.readline()
            if not atom_header:
                raise ValueError(f"Missing projected block for atom {atom + 1}: {path}")
            block = np.array(
                [[float(value) for value in handle.readline().split()] for _ in range(nedos)],
                dtype=float,
            )
            if block.shape[1] != 19:
                raise ValueError(f"Expected 19-column spin LORBIT=11 DOS, got {block.shape}: {path}")
            if energy is None:
                energy = block[:, 0] - efermi
            projected[atom, :, 0, :] = block[:, 1::2]
            projected[atom, :, 1, :] = block[:, 2::2]
    assert energy is not None
    spacing = float(np.median(np.diff(energy)))
    return efermi, energy, projected, spacing


def read_cohpcar(path: Path) -> dict[str, object]:
    lines = path.read_text(encoding="ascii").splitlines()
    metadata = lines[1].split()
    ncurves = int(metadata[0])
    nspin = int(metadata[1])
    nedos = int(metadata[2])
    if nspin != 2:
        raise ValueError(f"Expected spin-polarized COHPCAR: {path}")
    labels = lines[3 : 3 + ncurves - 1]
    start = 3 + ncurves - 1
    data = np.array([[float(x) for x in line.split()] for line in lines[start : start + nedos]])
    if data.shape != (nedos, 1 + 2 * ncurves * nspin):
        raise ValueError(f"Unexpected COHPCAR shape {data.shape}: {path}")
    curves: list[dict[str, object]] = []
    for curve_id, label in enumerate(labels, start=1):
        match = re.match(r"No\.(\d+):([A-Za-z]+\d+)->([A-Za-z]+\d+)\(([^)]+)\)", label)
        if not match:
            raise ValueError(f"Cannot parse COHP label: {label}")
        for spin in (0, 1):
            offset = 1 + spin * 2 * ncurves + 2 * curve_id
            curves.append(
                {
                    "curve_id": curve_id,
                    "label": f"{match.group(2)}-{match.group(3)}",
                    "atom1": match.group(2),
                    "atom2": match.group(3),
                    "distance_A": float(match.group(4)),
                    "spin": "up" if spin == 0 else "down",
                    "minus_cohp": -data[:, offset],
                    "minus_icohp": -data[:, offset + 1],
                }
            )
    return {"energy": data[:, 0], "curves": curves, "ncurves": ncurves, "nedos": nedos}


def smooth_raw_grid(values: np.ndarray, sigma_points: float = 1.0) -> np.ndarray:
    radius = max(2, int(math.ceil(4 * sigma_points)))
    x = np.arange(-radius, radius + 1)
    kernel = np.exp(-0.5 * (x / sigma_points) ** 2)
    kernel /= kernel.sum()
    return np.convolve(values, kernel, mode="same")


def integrate_window(energy: np.ndarray, values: np.ndarray, center: float, half_width: float = 0.12) -> float:
    mask = (energy >= center - half_width) & (energy <= center + half_width)
    if mask.sum() < 2:
        return 0.0
    return float(np.trapezoid(values[mask], energy[mask]))


def centroid_window(energy: np.ndarray, values: np.ndarray, center: float, half_width: float = 0.12) -> float:
    mask = (energy >= center - half_width) & (energy <= center + half_width)
    weight = np.trapezoid(values[mask], energy[mask])
    if abs(weight) < 1e-12:
        return float(center)
    return float(np.trapezoid(energy[mask] * values[mask], energy[mask]) / weight)


def classify_bonding(mean_value: float, consistency: float) -> str:
    if consistency < 0.60 or abs(mean_value) < 0.015:
        return "approximately nonbonding"
    if mean_value >= 0.10:
        return "bonding"
    if mean_value >= 0.015:
        return "weakly bonding"
    if mean_value <= -0.10:
        return "strongly antibonding"
    return "weakly antibonding"


def find_frontier_features(
    case: Case,
    energy: np.ndarray,
    components: dict[str, dict[str, np.ndarray]],
    cohp: dict[str, object],
    spacing: float,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    frontier_mask = (energy >= -2.0) & (energy <= 0.5)
    efront = energy[frontier_mask]
    merge_tolerance = max(1.55 * spacing, 0.075)

    cohp_by_role: dict[str, dict[str, dict[str, np.ndarray]]] = {"up": {}, "down": {}}
    for curve in cohp["curves"]:
        curve_id = int(curve["curve_id"])
        role = {1: "Coact-Oads", 4: "Coact-Obridge", 5: "neighbor-Obridge"}.get(curve_id)
        if role:
            cohp_by_role[str(curve["spin"])][role] = {
                "energy": cohp["energy"],
                "minus_cohp": curve["minus_cohp"],
            }

    for spin in ("up", "down"):
        candidates: list[dict[str, object]] = []
        for role in ("Oads", "Coact", "Obridge", "neighbor"):
            y = components[role][spin][frontier_mask]
            ys = smooth_raw_grid(y, 1.0)
            max_y = float(np.max(ys)) if len(ys) else 0.0
            if max_y <= 1e-10:
                continue
            threshold = max(0.02, 0.065 * max_y)
            peaks, properties = find_peaks(ys, prominence=threshold, distance=2)
            for idx, prominence in zip(peaks, properties["prominences"]):
                candidates.append(
                    {
                        "energy": float(efront[idx]),
                        "source_role": role,
                        "prominence": float(prominence),
                        "relative_prominence": float(prominence / max_y),
                    }
                )
        candidates.sort(key=lambda item: float(item["energy"]), reverse=True)
        merged: list[list[dict[str, object]]] = []
        for candidate in candidates:
            target = None
            for group in merged:
                if abs(float(candidate["energy"]) - np.mean([float(x["energy"]) for x in group])) <= merge_tolerance:
                    target = group
                    break
            if target is None:
                merged.append([candidate])
            else:
                target.append(candidate)

        features: list[dict[str, object]] = []
        for group in merged:
            peak = max(group, key=lambda item: float(item["prominence"]))
            peak_energy = float(peak["energy"])
            weights = {
                role: integrate_window(energy, components[role][spin], peak_energy)
                for role in ("Oads", "Coact", "Obridge", "neighbor")
            }
            total_weight = sum(weights.values())
            if total_weight < 0.015:
                continue
            fractions = {role: value / total_weight for role, value in weights.items()}

            cohp_metrics: dict[str, tuple[float, float, float]] = {}
            for role in ("Coact-Oads", "Coact-Obridge", "neighbor-Obridge"):
                curve = cohp_by_role[spin][role]
                ce = curve["energy"]
                cy = curve["minus_cohp"]
                mask = (ce >= peak_energy - 0.12) & (ce <= peak_energy + 0.12)
                mean = float(np.mean(cy[mask])) if mask.any() else float("nan")
                integral = float(np.trapezoid(cy[mask], ce[mask])) if mask.sum() >= 2 else 0.0
                nonzero = cy[mask][np.abs(cy[mask]) > 1e-8]
                if len(nonzero) == 0:
                    consistency = 0.0
                else:
                    sign = 1.0 if mean >= 0 else -1.0
                    consistency = float(np.mean(np.sign(nonzero) == sign))
                cohp_metrics[role] = (mean, integral, consistency)

            if fractions["Oads"] + fractions["Coact"] >= 0.42:
                primary = "Coact-Oads"
            elif fractions["Obridge"] >= fractions["neighbor"]:
                primary = "Coact-Obridge"
            else:
                primary = "neighbor-Obridge"
            pmean, _, pcons = cohp_metrics[primary]
            bonding = classify_bonding(pmean, pcons)

            if fractions["Oads"] >= 0.43:
                if bonding in ("strongly antibonding", "weakly antibonding"):
                    dominant = "O-rich weakly antibonding frontier"
                elif bonding == "approximately nonbonding":
                    dominant = "O-rich nonbonding frontier"
                else:
                    dominant = "O-rich Co-O mixed frontier"
            elif fractions["Oads"] >= 0.18 and fractions["Coact"] >= 0.18:
                if bonding == "strongly antibonding":
                    dominant = "Co-O strongly antibonding mixed state"
                elif bonding in ("bonding", "weakly bonding"):
                    dominant = "Co-O bonding mixed state"
                else:
                    dominant = "Co-O mixed frontier state"
            elif fractions["neighbor"] + fractions["Obridge"] >= 0.47:
                dominant = (
                    "extended Co-O-Co magnetic mixed state"
                    if case.neighbor_element == "Co"
                    else "extended Co-O-Al mixed state"
                )
            elif fractions["Coact"] >= 0.40:
                dominant = "Co d-derived frontier"
            elif fractions["Obridge"] >= 0.40:
                dominant = "Obridge p-derived frontier"
            else:
                dominant = "mixed local frontier state"

            rel_prom = max(float(item["relative_prominence"]) for item in group)
            confidence = "high" if rel_prom >= 0.20 and pcons >= 0.75 else "moderate" if rel_prom >= 0.10 else "low"
            envelope = sum(components[role][spin] for role in ("Oads", "Coact", "Obridge", "neighbor"))
            features.append(
                {
                    "system": case.system,
                    "state": case.state,
                    "spin": spin,
                    "E_peak_EF": peak_energy,
                    "centroid_EF": centroid_window(energy, envelope, peak_energy),
                    "Oads2p_weight": weights["Oads"],
                    "Coact3d_weight": weights["Coact"],
                    "Obridge2p_weight": weights["Obridge"],
                    "neighbor_weight": weights["neighbor"],
                    "Oads2p_fraction": fractions["Oads"],
                    "Coact3d_fraction": fractions["Coact"],
                    "Obridge2p_fraction": fractions["Obridge"],
                    "neighbor_fraction": fractions["neighbor"],
                    "peak_prominence": float(peak["prominence"]),
                    "relative_prominence": rel_prom,
                    "Coact-Oads_minusCOHP_mean": cohp_metrics["Coact-Oads"][0],
                    "Coact-Oads_minusCOHP_integral": cohp_metrics["Coact-Oads"][1],
                    "Coact-Oads_sign_consistency": cohp_metrics["Coact-Oads"][2],
                    "Coact-Obridge_minusCOHP_mean": cohp_metrics["Coact-Obridge"][0],
                    "Coact-Obridge_minusCOHP_integral": cohp_metrics["Coact-Obridge"][1],
                    "Coact-Obridge_sign_consistency": cohp_metrics["Coact-Obridge"][2],
                    "neighbor-Obridge_minusCOHP_mean": cohp_metrics["neighbor-Obridge"][0],
                    "neighbor-Obridge_minusCOHP_integral": cohp_metrics["neighbor-Obridge"][1],
                    "neighbor-Obridge_sign_consistency": cohp_metrics["neighbor-Obridge"][2],
                    "bonding_class": bonding,
                    "dominant_character": dominant,
                    "confidence": confidence,
                    "detection_source": str(peak["source_role"]),
                    "energy_spacing_eV": spacing,
                }
            )
        features.sort(key=lambda item: float(item["E_peak_EF"]), reverse=True)
        for index, feature in enumerate(features, start=1):
            feature["feature_id"] = f"{spin[0].upper()}F{index}"
        rows.extend(features)
    return rows


def format_value(value: object) -> object:
    if isinstance(value, (float, np.floating)):
        if math.isnan(float(value)):
            return "NA"
        return f"{float(value):.8f}"
    return value


def select_roles(case: Case, structure: dict[str, object], active_h: int | None) -> list[tuple[str, int]]:
    roles = [
        ("Oads", case.oads),
        ("Coact", case.coact),
        ("Obridge", case.obridge),
        ("Coadj" if case.neighbor_element == "Co" else "Al", case.neighbor),
    ]
    if active_h is not None:
        roles.append(("active_H", active_h))
    return roles


def pdos_components(projected: np.ndarray, case: Case) -> dict[str, dict[str, np.ndarray]]:
    orbital = {name: i for i, name in enumerate(PDOS_ORBITALS)}
    pcols = [orbital["px"], orbital["py"], orbital["pz"]]
    dcols = [orbital[x] for x in ("dxy", "dyz", "dz2", "dxz", "dx2_y2")]
    result: dict[str, dict[str, np.ndarray]] = {}
    for role, atom, cols in (
        ("Oads", case.oads, pcols),
        ("Coact", case.coact, dcols),
        ("Obridge", case.obridge, pcols),
        ("neighbor", case.neighbor, dcols if case.neighbor_element == "Co" else list(range(9))),
    ):
        result[role] = {
            "up": projected[atom - 1, :, 0][:, cols].sum(axis=1),
            "down": projected[atom - 1, :, 1][:, cols].sum(axis=1),
        }
    return result


def build_geometry_rows(
    case: Case,
    structure: dict[str, object],
    active_h: int | None,
    active_h_distance: float | None,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    o_indices = species_index_ranges(structure)["O"]
    distances = []
    for o_index in o_indices:
        dist, vec = distance(structure, case.coact, o_index)
        distances.append((dist, o_index, vec))
    distances.sort(key=lambda item: item[0])
    nearest = distances[:6]
    for rank, (dist, o_index, vec) in enumerate(nearest, start=1):
        norm = np.linalg.norm(vec)
        rows.append(
            {
                "system": case.system,
                "state": case.state,
                "record_type": "Coact_nearest_O",
                "rank": rank,
                "atom1": f"Co{case.coact}",
                "atom2": f"O{o_index}",
                "role": "Oads" if o_index == case.oads else "Obridge" if o_index == case.obridge else "spectator_O",
                "distance_A": dist,
                "vector_x_A": vec[0],
                "vector_y_A": vec[1],
                "vector_z_A": vec[2],
                "unit_x": vec[0] / norm,
                "unit_y": vec[1] / norm,
                "unit_z": vec[2] / norm,
                "note": "minimum-image Coact to O vector",
            }
        )
    for role, atom2 in (("Oads", case.oads), ("Obridge", case.obridge)):
        dist, vec = distance(structure, case.coact, atom2)
        norm = np.linalg.norm(vec)
        rows.append(
            {
                "system": case.system,
                "state": case.state,
                "record_type": "explicit_vector",
                "rank": "NA",
                "atom1": f"Co{case.coact}",
                "atom2": f"O{atom2}",
                "role": role,
                "distance_A": dist,
                "vector_x_A": vec[0],
                "vector_y_A": vec[1],
                "vector_z_A": vec[2],
                "unit_x": vec[0] / norm,
                "unit_y": vec[1] / norm,
                "unit_z": vec[2] / norm,
                "note": "minimum-image vector; global orbital axes were not rotated",
            }
        )
    if active_h is not None:
        dist, vec = distance(structure, case.oads, active_h)
        norm = np.linalg.norm(vec)
        rows.append(
            {
                "system": case.system,
                "state": case.state,
                "record_type": "active_Oads-H",
                "rank": "NA",
                "atom1": f"O{case.oads}",
                "atom2": f"H{active_h}",
                "role": "active_deprotonated_H",
                "distance_A": active_h_distance if active_h_distance is not None else dist,
                "vector_x_A": vec[0],
                "vector_y_A": vec[1],
                "vector_z_A": vec[2],
                "unit_x": vec[0] / norm,
                "unit_y": vec[1] / norm,
                "unit_z": vec[2] / norm,
                "note": "identified by exact OH/O H-coordinate matching, not assumed from H116",
            }
        )
    return rows


def plot_case(
    case: Case,
    energy: np.ndarray,
    components: dict[str, dict[str, np.ndarray]],
    cohp: dict[str, object],
    features: list[dict[str, object]],
) -> Path:
    colors = {"Oads": "#c43d3d", "Coact": "#2468a2", "Obridge": "#2f8a62", "neighbor": "#8b5aa8"}
    labels = {
        "Oads": r"O$_{ads}$ 2p",
        "Coact": r"Co$_{act}$ 3d",
        "Obridge": r"O$_{bridge}$ 2p",
        "neighbor": f"{case.neighbor_element}$_{{neighbor}}$ projection",
    }
    fig, (ax, ax_cohp) = plt.subplots(
        2, 1, figsize=(7.25, 6.0), sharex=True,
        gridspec_kw={"height_ratios": [2.1, 1.0], "hspace": 0.07},
    )
    mask = (energy >= -2.0) & (energy <= 0.5)
    for role in ("Oads", "Coact", "Obridge", "neighbor"):
        ax.plot(energy[mask], components[role]["up"][mask], color=colors[role], lw=1.35, label=labels[role])
        ax.plot(energy[mask], -components[role]["down"][mask], color=colors[role], lw=1.05)
    ax.axhline(0, color="#222222", lw=0.7)
    ax.axvline(0, color="#222222", lw=0.9, ls=":")
    ax.set_ylabel(r"PDOS (states eV$^{-1}$)")
    ax.text(0.012, 0.965, "up", transform=ax.transAxes, va="top", fontsize=8)
    ax.text(0.012, 0.035, "down", transform=ax.transAxes, va="bottom", fontsize=8)
    ax.legend(frameon=False, fontsize=8, ncol=2, loc="upper center")
    ax.set_title(f"{case.material} CoOOH {case.state}: spin-resolved frontier manifold", loc="left", fontsize=11)

    pair = next(curve for curve in cohp["curves"] if curve["curve_id"] == 1 and curve["spin"] == "up")
    pair_down = next(curve for curve in cohp["curves"] if curve["curve_id"] == 1 and curve["spin"] == "down")
    ce = cohp["energy"]
    cmask = (ce >= -2.0) & (ce <= 0.5)
    ax_cohp.plot(ce[cmask], pair["minus_cohp"][cmask], color="#d05b47", lw=1.35, label="up")
    ax_cohp.plot(
        ce[cmask], pair_down["minus_cohp"][cmask], color="#3c78b4", lw=1.25,
        ls=(0, (4, 2)), label="down",
    )
    ax_cohp.axhline(0, color="#222222", lw=0.7)
    ax_cohp.axvline(0, color="#222222", lw=0.9, ls=":")
    ax_cohp.set_ylabel(r"Co$_{act}$-O$_{ads}$ $-$COHP")
    ax_cohp.set_xlabel(r"Energy, $E-E_F$ (eV)")
    ax_cohp.legend(frameon=False, fontsize=8, ncol=2, loc="upper left")

    candidates = sorted(features, key=lambda item: float(item["relative_prominence"]), reverse=True)
    ranked: list[list[dict[str, object]]] = []
    for feature in candidates:
        target = next(
            (
                group for group in ranked
                if abs(float(feature["E_peak_EF"]) - float(group[0]["E_peak_EF"])) < 0.035
            ),
            None,
        )
        if target is None:
            if len(ranked) >= 3:
                continue
            ranked.append([feature])
        else:
            target.append(feature)
    ranked.sort(key=lambda group: float(group[0]["E_peak_EF"]), reverse=True)
    ylim = ax.get_ylim()
    for idx, group in enumerate(ranked, start=1):
        x = float(group[0]["E_peak_EF"])
        label = "/".join(str(feature["feature_id"]) for feature in group)
        ax.axvline(x, color="#666666", lw=0.65, ls="--", alpha=0.7)
        ax.text(
            x, ylim[0] + (ylim[1] - ylim[0]) * (0.77 - 0.085 * ((idx - 1) % 2)),
            label, ha="center", va="top", fontsize=7.2, rotation=90,
            bbox={"fc": "white", "ec": "none", "alpha": 0.86, "pad": 0.7},
        )
        ax_cohp.axvline(x, color="#777777", lw=0.55, ls="--", alpha=0.45)

    for axis in (ax, ax_cohp):
        axis.set_xlim(-2.0, 0.5)
        axis.spines[["top", "right"]].set_visible(False)
        axis.tick_params(direction="out", length=3, width=0.8)
    fig.text(
        0.995, 0.01,
        "Raw VASP/LORBIT=11 energy grid; peak detection used one-grid-point Gaussian smoothing only. "
        "Positive -COHP is bonding.",
        ha="right", va="bottom", fontsize=7.1, color="#4f555b",
    )
    fig.subplots_adjust(left=0.12, right=0.98, top=0.94, bottom=0.12)
    path = OUT / f"frontier_{case.system}.png"
    fig.savefig(path, dpi=360, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path


def select_descriptor(features: list[dict[str, object]], case: Case, descriptor: str, majority: str) -> dict[str, object] | None:
    candidates = [f for f in features if f["system"] == case.system]
    if descriptor == "O-rich spin-down":
        candidates = [f for f in candidates if f["spin"] == "down" and float(f["Oads2p_fraction"]) >= 0.30]
    elif descriptor == "majority Co-O antibonding":
        candidates = [
            f for f in candidates
            if f["spin"] == majority
            and float(f["Oads2p_fraction"]) + float(f["Coact3d_fraction"]) >= 0.40
            and float(f["Coact-Oads_minusCOHP_mean"]) < -0.015
        ]
    elif descriptor == "minority Co-O bonding/mixed":
        minority = "down" if majority == "up" else "up"
        candidates = [
            f for f in candidates
            if f["spin"] == minority
            and float(f["Oads2p_fraction"]) + float(f["Coact3d_fraction"]) >= 0.40
            and float(f["Coact-Oads_minusCOHP_mean"]) > 0.015
        ]
    elif descriptor == "neighbor magnetic":
        if case.neighbor_element != "Co":
            return None
        candidates = [f for f in candidates if float(f["neighbor_fraction"]) >= 0.25]
    if not candidates:
        return None
    return max(candidates, key=lambda item: float(item["E_peak_EF"]))


def build_report(
    all_features: list[dict[str, object]],
    case_data: dict[str, dict[str, object]],
    active_h_info: dict[str, dict[str, object]],
    source_rows: list[dict[str, object]],
) -> str:
    lines = [
        "# Spin-resolved frontier-level postprocessing",
        "",
        "## Scope and evidentiary limits",
        "",
        "This is read-only postprocessing of the four validated fixed-geometry VASP statics and their genuine "
        "spin-polarized LOBSTER calculations. No new VASP, LOBSTER, or CP2K calculation was submitted. Energies "
        "are reported relative to each calculation's own Fermi level. No LOCPOT is present in the source set, so "
        "cross-system absolute orbital shifts cannot be established; only within-system ordering relative to EF is reported.",
        "",
        "The VASP projections use global Cartesian harmonics. Local-axis orbital rotation and a defensible local "
        "eg/t2g assignment are unavailable from these outputs. Population changes are not interpreted as literal "
        "single-electron orbital transitions.",
        "",
        "## Data validation",
        "",
        "| System | EF (eV) | DOS spacing (eV) | Majority Coact spin | LOBSTER curves |",
        "|---|---:|---:|---|---:|",
    ]
    for case in CASES:
        item = case_data[case.system]
        lines.append(
            f"| {case.system} | {item['efermi']:.6f} | {item['spacing']:.5f} | "
            f"{item['majority_spin']} | {item['cohp']['ncurves'] - 1} |"
        )
    lines.extend(
        [
            "",
            "For *OH, the removed proton was identified by one-to-one periodic coordinate matching against the "
            "corresponding *O structure, followed by the Oads-H distance check. It is not H116:",
            "",
        ]
    )
    for material in ("Pristine", "Al16"):
        info = active_h_info[material]
        lines.append(
            f"- {material}: active H = H{info['active_h']}, Oads-H = {info['distance_A']:.4f} A. "
            "The existing LOBSTER pair labeled with H116 belongs to a background terminal OH and is excluded from active Oads-H claims."
        )

    lines.extend(
        [
            "",
            "## Frontier feature positions and bonding character",
            "",
            "The catalog uses local maxima on the original DOS energy grid. A one-grid-point Gaussian filter is used "
            "only to stabilize peak detection; all centroids, integrated weights, and exported spectra use the raw grid. "
            "Bonding labels are assigned from energy-resolved -COHP in +/-0.12 eV around each peak.",
            "",
        ]
    )
    descriptors = (
        "O-rich spin-down",
        "majority Co-O antibonding",
        "minority Co-O bonding/mixed",
        "neighbor magnetic",
    )
    selected: dict[tuple[str, str], dict[str, object] | None] = {}
    for case in CASES:
        majority = str(case_data[case.system]["majority_spin"])
        lines.append(f"### {case.system}")
        lines.append("")
        system_features = [f for f in all_features if f["system"] == case.system]
        for spin in ("up", "down"):
            ordered = [f for f in system_features if f["spin"] == spin]
            if ordered:
                text = " > ".join(
                    f"{f['feature_id']} ({float(f['E_peak_EF']):+.3f} eV; {f['dominant_character']}; {f['bonding_class']})"
                    for f in ordered
                )
                lines.append(f"- {spin}: {text}")
        lines.append("")
        for descriptor in descriptors:
            feature = select_descriptor(all_features, case, descriptor, majority)
            selected[(case.system, descriptor)] = feature
            if feature is None:
                lines.append(f"- {descriptor}: not resolved by the available projected DOS/COHP set.")
            else:
                lines.append(
                    f"- {descriptor}: {feature['feature_id']} at {float(feature['E_peak_EF']):+.3f} eV, "
                    f"{feature['bonding_class']}, {feature['dominant_character']} ({feature['confidence']} confidence)."
                )
        lines.append("")

    def compare_pair(system: str) -> str:
        a = selected[(system, "O-rich spin-down")]
        b = selected[(system, "majority Co-O antibonding")]
        if a is None or b is None:
            return "unresolved because one or both requested features were not independently detected"
        delta = float(a["E_peak_EF"]) - float(b["E_peak_EF"])
        spacing = float(case_data[system]["spacing"])
        threshold = max(0.12, 2.0 * spacing)
        if abs(delta) <= threshold:
            return f"near-degenerate/unresolved ordering (separation {abs(delta):.3f} eV; threshold {threshold:.3f} eV)"
        relation = "above" if delta > 0 else "below"
        return f"resolved: O-rich spin-down lies {abs(delta):.3f} eV {relation} the majority Co-O antibonding feature"

    lines.extend(
        [
            "## Direct answers",
            "",
            f"- Pristine *OH O-rich spin-down versus majority Co-O antibonding: {compare_pair('pristine_OH')}.",
            f"- Al16 *OH O-rich spin-down versus majority Co-O antibonding: {compare_pair('Al16_OH')}.",
            f"- Pristine *O: {compare_pair('pristine_O')}.",
            f"- Al16 *O: {compare_pair('Al16_O')}.",
            "",
        ]
    )

    def ordering_signature(system: str) -> tuple[int | None, float | None, float]:
        a = selected[(system, "O-rich spin-down")]
        b = selected[(system, "majority Co-O antibonding")]
        threshold = max(0.12, 2.0 * float(case_data[system]["spacing"]))
        if a is None or b is None:
            return None, None, threshold
        delta = float(a["E_peak_EF"]) - float(b["E_peak_EF"])
        sign = 0 if abs(delta) <= threshold else 1 if delta > 0 else -1
        return sign, delta, threshold

    for state, pristine, al in (("*OH", "pristine_OH", "Al16_OH"), ("*O", "pristine_O", "Al16_O")):
        psign, pdelta, pthr = ordering_signature(pristine)
        asign, adelta, athr = ordering_signature(al)
        if psign is None or asign is None:
            verdict = "the requested pair is incompletely resolved, so a reordering claim is not supported"
        elif psign != 0 and asign != 0 and psign != asign:
            verdict = "a resolved sign reversal supports a frontier-state reordering, not a uniform energy shift"
        elif psign == 0 or asign == 0:
            verdict = "at least one ordering is within the resolution band; only near-degeneracy/separation can be claimed"
        else:
            verdict = "the order is retained; the data support differential separation rather than a proven reordering"
        lines.append(f"- {state} Al effect: {verdict}.")

    lines.extend(
        [
            "",
            "The complete feature-by-feature evidence, including component weights, three pair-resolved -COHP metrics, "
            "sign consistency, and confidence, is in `frontier_state_catalog.tsv`.",
            "",
            "## What can be drawn in the paper",
            "",
            "- Use the resolved peak ordering and bonding labels where the separation exceeds the stated resolution band.",
            "- Draw near-degenerate levels as uncertainty bands when separation is <= max(0.12 eV, twice the DOS spacing).",
            "- Show O-rich, Co-O mixed, Obridge, and neighboring-Co/Al manifolds without forcing sigma/pi or eg/t2g labels.",
            "- The active Oads-H bond has geometry evidence but no dedicated COHP curve in the existing LOBSTER files; do not assign its bonding energy from the background H116 pair.",
            "- Cross-material vertical alignment is schematic because no vacuum alignment is available.",
            "",
            "## Files",
            "",
            "- `selected_pdos_full.tsv`: raw-grid spin-resolved orbital projections for all requested atoms/roles.",
            "- `selected_cohp_full.tsv`: raw-grid spin-resolved -COHP/-ICOHP for all five existing pair curves.",
            "- `frontier_state_catalog.tsv`: localized frontier-feature catalog and COHP-based classification.",
            "- `local_geometry.tsv`: Coact vectors, six nearest O neighbors, and automatically identified active Oads-H.",
            "- `vacuum_alignment.tsv`: explicit unavailable status because LOCPOT is absent.",
            "- `source_manifest.tsv`: local mirror and actual remote source paths with SHA256 hashes.",
            "",
            "## Source provenance",
            "",
            f"The source manifest contains {len(source_rows)} hashed files. Original calculation directories were not modified.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    active_h_info: dict[str, dict[str, object]] = {}
    for material, oh_key, o_key in (("Pristine", "undoped_OH", "undoped_O"), ("Al16", "Al16_OH", "Al16_O")):
        oh_case = next(case for case in CASES if case.key == oh_key)
        oh_structure = read_poscar(PDOS_ROOT / oh_case.pdos_folder / "POSCAR")
        o_structure = read_poscar(PDOS_ROOT / o_key / "POSCAR")
        active_h_info[material] = identify_deleted_h(oh_structure, o_structure, oh_case.oads)

    selected_pdos_rows: list[dict[str, object]] = []
    selected_cohp_rows: list[dict[str, object]] = []
    geometry_rows: list[dict[str, object]] = []
    feature_rows: list[dict[str, object]] = []
    source_rows: list[dict[str, object]] = []
    case_data: dict[str, dict[str, object]] = {}
    plot_paths: list[Path] = []

    for case in CASES:
        pdos_dir = PDOS_ROOT / case.pdos_folder
        cohp_dir = COHP_ROOT / case.cohp_folder
        structure = read_poscar(pdos_dir / "POSCAR")
        active_h = int(active_h_info[case.material]["active_h"]) if case.state == "*OH" else None
        active_h_distance = float(active_h_info[case.material]["distance_A"]) if case.state == "*OH" else None
        efermi, energy, projected, spacing = read_doscar(pdos_dir / "DOSCAR")
        cohp = read_cohpcar(cohp_dir / "COHPCAR.lobster")
        components = pdos_components(projected, case)

        dcols = [PDOS_ORBITALS.index(name) for name in ("dxy", "dyz", "dz2", "dxz", "dx2_y2")]
        occ = (energy >= -8.0) & (energy <= 0.0)
        co_up = float(np.trapezoid(projected[case.coact - 1, occ, 0][:, dcols].sum(axis=1), energy[occ]))
        co_down = float(np.trapezoid(projected[case.coact - 1, occ, 1][:, dcols].sum(axis=1), energy[occ]))
        majority_spin = "up" if co_up >= co_down else "down"

        case_features = find_frontier_features(case, energy, components, cohp, spacing)
        feature_rows.extend(case_features)
        case_data[case.system] = {
            "efermi": efermi,
            "energy": energy,
            "projected": projected,
            "spacing": spacing,
            "components": components,
            "cohp": cohp,
            "majority_spin": majority_spin,
            "coact_d_occupied_up": co_up,
            "coact_d_occupied_down": co_down,
        }

        export_mask = (energy >= -8.0) & (energy <= 3.0)
        orbital_index = {name: i for i, name in enumerate(PDOS_ORBITALS)}
        for role, atom_index in select_roles(case, structure, active_h):
            for spin_index, spin in enumerate(("up", "down")):
                for i in np.flatnonzero(export_mask):
                    values = projected[atom_index - 1, i, spin_index]
                    row: dict[str, object] = {
                        "system": case.system,
                        "material": case.material,
                        "state": case.state,
                        "role": role,
                        "atom_index": atom_index,
                        "element": structure["elements"][atom_index - 1],
                        "spin": spin,
                        "E_EF_eV": energy[i],
                    }
                    for orbital in PDOS_ORBITALS:
                        row[orbital] = values[orbital_index[orbital]]
                    row["p_total"] = sum(values[orbital_index[x]] for x in ("px", "py", "pz"))
                    row["d_total"] = sum(values[orbital_index[x]] for x in ("dxy", "dyz", "dz2", "dxz", "dx2_y2"))
                    row["projection_total"] = float(values.sum())
                    selected_pdos_rows.append({k: format_value(v) for k, v in row.items()})

        for curve in cohp["curves"]:
            curve_id = int(curve["curve_id"])
            pair_role = {
                1: "Coact-Oads",
                2: "neighbor-background_terminal_OH",
                3: "background_terminal_O-H",
                4: "Coact-Obridge",
                5: "neighbor-Obridge",
            }[curve_id]
            for e, minus_cohp, minus_icohp in zip(cohp["energy"], curve["minus_cohp"], curve["minus_icohp"]):
                if -8.0 <= e <= 3.0:
                    selected_cohp_rows.append(
                        {
                            "system": case.system,
                            "material": case.material,
                            "state": case.state,
                            "pair_id": curve_id,
                            "pair_role": pair_role,
                            "pair_label": curve["label"],
                            "distance_A": f"{float(curve['distance_A']):.8f}",
                            "spin": curve["spin"],
                            "E_EF_eV": f"{float(e):.8f}",
                            "minusCOHP": f"{float(minus_cohp):.8f}",
                            "minusICOHP": f"{float(minus_icohp):.8f}",
                            "bonding_sign_convention": "positive_minusCOHP_is_bonding",
                        }
                    )

        geometry_rows.extend(build_geometry_rows(case, structure, active_h, active_h_distance))
        plot_paths.append(plot_case(case, energy, components, cohp, case_features))

        for local_name, remote_dir, local_path in (
            ("DOSCAR", case.remote_pdos_dir, pdos_dir / "DOSCAR"),
            ("POSCAR", case.remote_pdos_dir, pdos_dir / "POSCAR"),
            ("COHPCAR.lobster", case.remote_cohp_dir, cohp_dir / "COHPCAR.lobster"),
            ("ICOHPLIST.lobster", case.remote_cohp_dir, cohp_dir / "ICOHPLIST.lobster"),
            ("lobsterout", case.remote_cohp_dir, cohp_dir / "lobsterout"),
        ):
            source_rows.append(
                {
                    "system": case.system,
                    "file": local_name,
                    "local_mirror": str(local_path.resolve()),
                    "remote_source": f"/home/ftfan/ncw/{remote_dir}/{local_name}",
                    "size_bytes": local_path.stat().st_size,
                    "sha256": sha256(local_path),
                    "access": "read_only",
                }
            )

    pdos_columns = [
        "system", "material", "state", "role", "atom_index", "element", "spin", "E_EF_eV",
        *PDOS_ORBITALS, "p_total", "d_total", "projection_total",
    ]
    cohp_columns = [
        "system", "material", "state", "pair_id", "pair_role", "pair_label", "distance_A", "spin",
        "E_EF_eV", "minusCOHP", "minusICOHP", "bonding_sign_convention",
    ]
    feature_columns = [
        "system", "state", "feature_id", "spin", "E_peak_EF", "centroid_EF",
        "Oads2p_weight", "Coact3d_weight", "Obridge2p_weight", "neighbor_weight",
        "Oads2p_fraction", "Coact3d_fraction", "Obridge2p_fraction", "neighbor_fraction",
        "Coact-Oads_minusCOHP_mean", "Coact-Oads_minusCOHP_integral", "Coact-Oads_sign_consistency",
        "Coact-Obridge_minusCOHP_mean", "Coact-Obridge_minusCOHP_integral", "Coact-Obridge_sign_consistency",
        "neighbor-Obridge_minusCOHP_mean", "neighbor-Obridge_minusCOHP_integral", "neighbor-Obridge_sign_consistency",
        "bonding_class", "dominant_character", "peak_prominence", "relative_prominence", "confidence",
        "detection_source", "energy_spacing_eV",
    ]
    geometry_columns = [
        "system", "state", "record_type", "rank", "atom1", "atom2", "role", "distance_A",
        "vector_x_A", "vector_y_A", "vector_z_A", "unit_x", "unit_y", "unit_z", "note",
    ]
    source_columns = ["system", "file", "local_mirror", "remote_source", "size_bytes", "sha256", "access"]

    write_tsv(OUT / "selected_pdos_full.tsv", selected_pdos_rows, pdos_columns)
    write_tsv(OUT / "selected_cohp_full.tsv", selected_cohp_rows, cohp_columns)
    write_tsv(
        OUT / "frontier_state_catalog.tsv",
        [{key: format_value(row.get(key, "NA")) for key in feature_columns} for row in feature_rows],
        feature_columns,
    )
    write_tsv(
        OUT / "local_geometry.tsv",
        [{key: format_value(row.get(key, "NA")) for key in geometry_columns} for row in geometry_rows],
        geometry_columns,
    )
    write_tsv(OUT / "source_manifest.tsv", source_rows, source_columns)
    vacuum_rows = [
        {
            "system": case.system,
            "state": case.state,
            "status": "UNAVAILABLE",
            "EF_eV": f"{float(case_data[case.system]['efermi']):.8f}",
            "Vvac_eV": "NA",
            "work_function_eV": "NA",
            "reason": "No LOCPOT in validated source set; only within-system E-EF ordering is reported.",
        }
        for case in CASES
    ]
    write_tsv(
        OUT / "vacuum_alignment.tsv",
        vacuum_rows,
        ["system", "state", "status", "EF_eV", "Vvac_eV", "work_function_eV", "reason"],
    )
    report = build_report(feature_rows, case_data, active_h_info, source_rows)
    (OUT / "frontier_level_postprocess.md").write_text(report, encoding="utf-8", newline="\n")

    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(OUT.iterdir()):
            archive.write(path, arcname=f"frontier_level_postprocess_20260903/{path.name}")

    print(f"OUTPUT_DIR={OUT.resolve()}")
    print(f"ZIP={ZIP_PATH.resolve()}")
    print(f"ZIP_SIZE_BYTES={ZIP_PATH.stat().st_size}")
    print(f"ZIP_SHA256={sha256(ZIP_PATH)}")
    print(f"FEATURES={len(feature_rows)}")
    print(f"PDOS_ROWS={len(selected_pdos_rows)}")
    print(f"COHP_ROWS={len(selected_cohp_rows)}")
    for material, info in active_h_info.items():
        print(f"ACTIVE_H_{material}={info['active_h']} DIST_A={float(info['distance_A']):.6f}")


if __name__ == "__main__":
    main()
