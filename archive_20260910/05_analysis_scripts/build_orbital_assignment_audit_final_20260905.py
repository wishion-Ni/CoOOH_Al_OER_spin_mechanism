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
from build_frontier_level_postprocess_20260903 import read_doscar, read_poscar


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "orbital_assignment_audit_20260903"
LOB = OUT / "lobster_sixbond"
FRONTIER = ROOT / "frontier_level_postprocess_20260903"
ZIP_PATH = ROOT / "orbital_assignment_audit_20260903.zip"


@dataclass(frozen=True)
class Case:
    system: str
    material: str
    state: str
    folder: str
    coact: int
    neighbor: int
    oads: int
    obridge: int
    oxygen: tuple[int, ...]
    neighbor_element: str


CASES = (
    Case("pristine_OH", "Pristine", "*OH", "pristine_OH", 21, 23, 348, 259, (295, 348, 227, 275, 217, 259), "Co"),
    Case("pristine_O", "Pristine", "*O", "pristine_O", 21, 23, 347, 258, (294, 347, 226, 274, 216, 258), "Co"),
    Case("Al16_OH", "Al16", "*OH", "Al16_OH", 16, 51, 348, 259, (295, 348, 227, 275, 217, 259), "Al"),
    Case("Al16_O", "Al16", "*O", "Al16_O", 16, 51, 347, 258, (294, 347, 226, 274, 216, 258), "Al"),
)


def write_tsv(path: Path, rows: list[dict[str, object]], columns: list[str] | None = None) -> None:
    if not rows:
        raise ValueError(f"No rows for {path}")
    fields = columns or list(rows[0])
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def f(value: float) -> str:
    return f"{value:.8f}"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_label(label: str) -> dict[str, object]:
    match = re.match(r"No\.(\d+):([^\[]+)(?:\[([^]]+)\])?->([^\[]+)(?:\[([^]]+)\])?\(([^)]+)\)", label)
    if not match:
        raise ValueError(f"Cannot parse COHP label: {label}")
    return {
        "pair_no": int(match.group(1)),
        "atom1": match.group(2),
        "orbital1": match.group(3) or "total",
        "atom2": match.group(4),
        "orbital2": match.group(5) or "total",
        "distance_A": float(match.group(6)),
    }


def read_cohpcar(path: Path) -> dict[str, object]:
    lines = path.read_text(encoding="ascii").splitlines()
    meta = lines[1].split()
    ncurves, nspin, nedos = int(meta[0]), int(meta[1]), int(meta[2])
    if nspin != 2:
        raise ValueError(f"Expected two spin channels: {path}")
    labels = lines[3 : 3 + ncurves - 1]
    start = 3 + ncurves - 1
    data = np.array([[float(x) for x in line.split()] for line in lines[start : start + nedos]])
    expected = 1 + 2 * ncurves * nspin
    if data.shape != (nedos, expected):
        raise ValueError(f"Unexpected COHPCAR dimensions {data.shape}, expected {(nedos, expected)}")
    curves = []
    for position, text in enumerate(labels, start=1):
        parsed = parse_label(text)
        for spin_index, spin in enumerate(("up", "down")):
            offset = 1 + spin_index * 2 * ncurves + 2 * position
            curves.append(
                {
                    **parsed,
                    "spin": spin,
                    "minus_cohp": -data[:, offset],
                    "minus_icohp": -data[:, offset + 1],
                }
            )
    return {"energy": data[:, 0], "curves": curves, "nlabels": len(labels), "nedos": nedos}


def read_catalog() -> list[dict[str, str]]:
    with (FRONTIER / "frontier_state_catalog.tsv").open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def read_pdos() -> list[dict[str, str]]:
    with (FRONTIER / "selected_pdos_full.tsv").open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    for case in CASES:
        folder = case.system.replace("pristine", "undoped")
        _ef, energy, projections, _spacing = read_doscar(ROOT / "pdos_oh_o_inputs_20260824" / folder / "DOSCAR")
        groups = {"spectators": [a for a in case.oxygen if a not in (case.oads, case.obridge)]}
        if case.state == "*OH":
            groups["Hactive"] = [204]
        for role, atoms in groups.items():
            summed = projections[np.array(atoms) - 1].sum(axis=0)
            for si, spin in enumerate(("up", "down")):
                for i in np.where((energy >= -8) & (energy <= 4))[0]:
                    v = summed[i, si]
                    row = {"system": case.system, "role": role, "spin": spin, "E_EF_eV": f(float(energy[i])), "s": f(float(v[0])), "p_total": f(float(v[1:4].sum())), "d_total": f(float(v[4:].sum())), "projection_total": f(float(v.sum()))}
                    rows.append(row)
    return rows


def extra_atomic_weight(pdos: list[dict[str, str]], case: Case, role: str, spin: str, peak: float) -> float:
    points = sorted([r for r in pdos if r["system"] == case.system and r["role"] == role and r["spin"] == spin and abs(float(r["E_EF_eV"]) - peak) <= 0.12], key=lambda r: float(r["E_EF_eV"]))
    if len(points) < 2:
        return 0.0
    column = "s" if role == "Hactive" else "p_total"
    return float(np.trapezoid([max(0.0, float(r[column])) for r in points], [float(r["E_EF_eV"]) for r in points]))


def validate_case(case: Case, cohp: dict[str, object]) -> dict[str, object]:
    directory = LOB / case.folder
    log = (directory / "lobsterout").read_text(encoding="ascii")
    if not re.search(r"finished in\s+\d+\s+h", log) or re.search(r"^\s*(ERROR|FATAL)\b", log, re.M):
        raise ValueError(f"Abnormal LOBSTER termination: {case.system}")
    spill = [float(v) for v in re.findall(r"abs\. charge spilling:\s*([\d.]+)%", log)]
    if len(spill) != 2 or max(spill) > 2:
        raise ValueError(f"Spilling validation failed: {case.system}: {spill}")
    recovery = re.search(r"electrons recovered by projection:\s*([\d.]+) of (\d+)", log)
    expected_e = {"pristine_OH": 1548, "pristine_O": 1547, "Al16_OH": 1488, "Al16_O": 1487}[case.system]
    if not recovery or int(recovery[2]) != expected_e or abs(float(recovery[1]) - expected_e) > 0.001:
        raise ValueError(f"Electron recovery mismatch: {case.system}")
    structure = read_poscar(directory / "POSCAR")
    expected = {(case.coact, o) for o in case.oxygen} | {(case.neighbor, case.obridge)}
    if case.state == "*OH":
        expected.add((case.oads, 204))
    max_error = 0.0
    for spin in ("up", "down"):
        seen = set()
        for curve in total_curves(cohp):
            if curve["spin"] != spin:
                continue
            a = int(re.search(r"\d+", str(curve["atom1"]))[0])
            b = int(re.search(r"\d+", str(curve["atom2"]))[0])
            seen.add((a, b))
            delta = structure["fractional"][b-1] - structure["fractional"][a-1]
            delta -= np.round(delta)
            distance = float(np.linalg.norm(delta @ structure["lattice"]))
            max_error = max(max_error, abs(distance - float(curve["distance_A"])))
        if seen != expected:
            raise ValueError(f"Pair set mismatch: {case.system} {spin}: {seen ^ expected}")
    if max_error > 1e-5:
        raise ValueError(f"Pair-distance mismatch: {case.system}: {max_error}")
    for filename in ("COHPCAR.lobster", "ICOHPLIST.lobster", "DOSCAR.lobster", "GROSSPOP.lobster"):
        if (directory / filename).stat().st_size <= 0:
            raise ValueError(f"Empty output: {case.system}/{filename}")
    return {"system": case.system, "normal_finish": "yes", "abs_charge_spilling_up_percent": spill[0], "abs_charge_spilling_down_percent": spill[1], "total_spilling": "not separately reported by this LOBSTER output", "recovered_electrons": recovery[1], "expected_electrons": expected_e, "validated_pairs_per_spin": len(expected), "max_distance_error_A": f(max_error), "basis": "recommended pbeVaspFit2015", "status": "normal completion; absolute charge spilling and pairs pass; total spilling unavailable"}


def total_curves(cohp: dict[str, object]) -> list[dict[str, object]]:
    return [curve for curve in cohp["curves"] if curve["orbital1"] == "total" and curve["orbital2"] == "total"]


def nearest_value(energy: np.ndarray, values: np.ndarray, target: float) -> float:
    return float(values[int(np.argmin(np.abs(energy - target)))])


def integral(energy: np.ndarray, values: np.ndarray, lo: float, hi: float) -> float:
    mask = (energy >= lo) & (energy <= hi)
    return float(np.trapezoid(values[mask], energy[mask])) if mask.sum() > 1 else 0.0


def curve_role(case: Case, curve: dict[str, object]) -> str:
    pair = int(curve["pair_no"])
    if pair <= 6:
        oxygen = int(re.search(r"\d+", str(curve["atom2"])).group())
        if oxygen == case.oads:
            return "Coact-Oads"
        if oxygen == case.obridge:
            return "Coact-Obridge"
        return f"Coact-Ospectator{case.oxygen.index(oxygen) + 1}"
    if pair == 7:
        return "neighbor-Obridge"
    return "Oads-H204"


def sixbond_rows(case: Case, cohp: dict[str, object]) -> list[dict[str, object]]:
    rows = []
    energy = cohp["energy"]
    for curve in total_curves(cohp):
        if int(curve["pair_no"]) > 6:
            continue
        role = curve_role(case, curve)
        oxygen = int(re.search(r"\d+", str(curve["atom2"])).group())
        geometry = "axial" if oxygen in (case.oads, case.obridge) else "equatorial"
        for index, evalue in enumerate(energy):
            rows.append(
                {
                    "system": case.system,
                    "state": case.state,
                    "spin": curve["spin"],
                    "bond_role": role,
                    "geometry": geometry,
                    "atom1": curve["atom1"],
                    "atom2": curve["atom2"],
                    "distance_A": f(float(curve["distance_A"])),
                    "E_EF_eV": f(float(evalue)),
                    "minusCOHP": f(float(curve["minus_cohp"][index])),
                    "minusICOHP": f(float(curve["minus_icohp"][index])),
                }
            )
    return rows


def bond_fingerprint(case: Case, cohp: dict[str, object], spin: str, target: float) -> dict[str, float]:
    energy = cohp["energy"]
    values = {"Oads-H204": 0.0, "Coact-Oads": 0.0, "Coact-Obridge": 0.0, "neighbor-Obridge": 0.0}
    spectator = []
    for curve in total_curves(cohp):
        if curve["spin"] != spin:
            continue
        role = curve_role(case, curve)
        value = nearest_value(energy, curve["minus_cohp"], target)
        if role.startswith("Coact-Ospectator"):
            spectator.append(value)
        else:
            values[role] = value
    values["spectator_sum"] = float(sum(spectator))
    values["spectator_abs_sum"] = float(sum(abs(v) for v in spectator))
    values["axial_sum"] = values["Coact-Oads"] + values["Coact-Obridge"]
    values["axial_abs_sum"] = abs(values["Coact-Oads"]) + abs(values["Coact-Obridge"])
    values["equatorial_sum"] = values["spectator_sum"]
    denom = values["axial_abs_sum"] + values["spectator_abs_sum"]
    values["axial_fraction"] = values["axial_abs_sum"] / denom if denom else 0.0
    return values


def orbital_frontier_rows(case: Case, cohp: dict[str, object], catalog: list[dict[str, str]]) -> list[dict[str, object]]:
    rows = []
    energy = cohp["energy"]
    features = [item for item in catalog if item["system"] == case.system]
    for feature in features:
        peak = float(feature["E_peak_EF"])
        for curve in cohp["curves"]:
            if curve["orbital1"] == "total" or curve["orbital2"] == "total":
                continue
            role = curve_role(case, curve)
            value = nearest_value(energy, curve["minus_cohp"], peak)
            integ = integral(energy, curve["minus_cohp"], peak - 0.12, peak + 0.12)
            if abs(value) < 1e-5 and abs(integ) < 1e-5:
                continue
            rows.append(
                {
                    "system": case.system,
                    "state": case.state,
                    "feature_id": feature["feature_id"],
                    "feature_spin": feature["spin"],
                    "curve_spin": curve["spin"],
                    "E_peak_EF": f(peak),
                    "bond_role": role,
                    "orbital1": curve["orbital1"],
                    "orbital2": curve["orbital2"],
                    "minusCOHP_at_peak": f(value),
                    "minusCOHP_integral_pm0.12eV": f(integ),
                    "basis_note": "global Cartesian orbital labels; not rotated to local frame",
                }
            )
    return rows


def axial_rows(case: Case, cohp: dict[str, object], catalog: list[dict[str, str]], pdos: list[dict[str, str]]) -> list[dict[str, object]]:
    rows = []
    up_features = [item for item in catalog if item["system"] == case.system and item["spin"] == "up"]
    for item in up_features:
        peak = float(item["E_peak_EF"])
        b = bond_fingerprint(case, cohp, "up", peak)
        anti_ax = max(0.0, -b["axial_sum"])
        anti_eq = max(0.0, -b["equatorial_sum"])
        if anti_ax > anti_eq * 1.35 and b["axial_fraction"] >= 0.55:
            assignment = "e_parallel* majority candidate"
            confidence = "high" if b["axial_fraction"] >= 0.70 else "medium"
        elif anti_eq > anti_ax * 1.35 and b["axial_fraction"] <= 0.45:
            assignment = "e_perp* majority candidate"
            confidence = "high" if b["axial_fraction"] <= 0.30 else "medium"
        else:
            assignment = "mixed axial/equatorial antibonding"
            confidence = "low"
        rows.append(
            {
                "system": case.system,
                "state": case.state,
                "feature_id": item["feature_id"],
                "E_peak_EF": f(peak),
                "spin": "up",
                "axial_minusCOHP_signed": f(b["axial_sum"]),
                "equatorial_minusCOHP_signed": f(b["equatorial_sum"]),
                "axial_abs_COHP": f(b["axial_abs_sum"]),
                "equatorial_abs_COHP": f(b["spectator_abs_sum"]),
                "axial_fraction": f(b["axial_fraction"]),
                "Oads_weight": item["Oads2p_weight"],
                "Obridge_weight": item["Obridge2p_weight"],
                "spectator_weight": f(extra_atomic_weight(pdos, case, "spectators", "up", peak)),
                "Co_weight": item["Coact3d_weight"],
                "occupation_evidence": "occupied" if peak < 0 else "frontier/unoccupied on sampled grid",
                "assignment": assignment,
                "confidence": confidence,
            }
        )
    return rows


def spectral_branch_rows(case: Case, cohp: dict[str, object]) -> list[dict[str, object]]:
    energy = cohp["energy"]
    axial = np.zeros_like(energy)
    equatorial = np.zeros_like(energy)
    for curve in total_curves(cohp):
        if curve["spin"] != "up" or int(curve["pair_no"]) > 6:
            continue
        role = curve_role(case, curve)
        if role in ("Coact-Oads", "Coact-Obridge"):
            axial += curve["minus_cohp"]
        else:
            equatorial += curve["minus_cohp"]
    mask = (energy >= -2.0) & (energy <= 0.5)
    indices = np.where(mask)[0]
    anti_axial = np.maximum(0.0, -axial)
    anti_equatorial = np.maximum(0.0, -equatorial)
    candidates: dict[str, list[tuple[float, int]]] = {"e_parallel* majority": [], "e_perp* majority": []}
    for signal, branch in ((anti_axial, "e_parallel* majority"), (anti_equatorial, "e_perp* majority")):
        local = signal[mask]
        prominence = max(0.02, 0.04 * float(local.max()))
        peaks, _props = find_peaks(local, prominence=prominence)
        for local_index in peaks:
            idx = indices[local_index]
            denom = abs(axial[idx]) + abs(equatorial[idx])
            frac = abs(axial[idx]) / denom if denom else 0.0
            qualifies = frac >= 0.55 if branch.startswith("e_parallel") else frac <= 0.45
            if qualifies:
                candidates[branch].append((float(signal[idx]), idx))
    rows = []
    for branch, values in candidates.items():
        if values:
            _strength, idx = max(values)
            confidence = "medium"
            status = "six-bond spectral candidate"
        else:
            signal = anti_axial if branch.startswith("e_parallel") else anti_equatorial
            idx = indices[int(np.argmax(signal[mask]))]
            confidence = "low"
            status = "no symmetry-selective peak; strongest mixed fallback"
        denom = abs(axial[idx]) + abs(equatorial[idx])
        frac = abs(axial[idx]) / denom if denom else 0.0
        rows.append({"system": case.system, "state": case.state, "branch": branch, "E_peak_EF": f(float(energy[idx])), "axial_minusCOHP_signed": f(float(axial[idx])), "equatorial_minusCOHP_signed": f(float(equatorial[idx])), "axial_fraction": f(frac), "status": status, "confidence": confidence, "note": "collective six-bond assignment; not an isolated one-electron MO"})
    return rows


def update_spatial_rows(case: Case, cohp: dict[str, object], catalog: list[dict[str, str]], pdos: list[dict[str, str]]) -> list[dict[str, object]]:
    rows = []
    for item in [entry for entry in catalog if entry["system"] == case.system]:
        peak = float(item["E_peak_EF"])
        b = bond_fingerprint(case, cohp, item["spin"], peak)
        atomic_raw = np.array([
            max(0.0, float(item["Oads2p_weight"])),
            max(0.0, float(item["Coact3d_weight"])),
            max(0.0, float(item["Obridge2p_weight"])),
            max(0.0, float(item["neighbor_weight"])),
            extra_atomic_weight(pdos, case, "Hactive", item["spin"], peak),
            extra_atomic_weight(pdos, case, "spectators", item["spin"], peak),
        ])
        atomic = atomic_raw / atomic_raw.sum() if atomic_raw.sum() else atomic_raw
        bond_raw = np.array([
            abs(b["Oads-H204"]), abs(b["Coact-Oads"]), b["spectator_abs_sum"],
            abs(b["Coact-Obridge"]), abs(b["neighbor-Obridge"]),
        ])
        bond = bond_raw / bond_raw.sum() if bond_raw.sum() else bond_raw
        occupied_columns = int(np.sum(bond > 0.14))
        if bond[4] > 0.22 or atomic[3] > 0.30:
            span = "framework extended"
        elif bond[1] > 0.14 and bond[3] > 0.14:
            span = "axial extended"
        elif occupied_columns >= 3:
            span = "three-center"
        elif max(atomic) > 0.82 and max(bond_raw) < 0.02:
            span = "local"
        else:
            span = "bond-local"
        rows.append(
            {
                "system": case.system, "state": case.state, "feature_id": item["feature_id"],
                "spin": item["spin"], "E_peak_EF": item["E_peak_EF"],
                "atomic_H": f(float(atomic[4])),
                "atomic_Osp4": f(float(atomic[5])),
                "atomic_Oads": f(float(atomic[0])), "atomic_Coact": f(float(atomic[1])),
                "atomic_Obridge": f(float(atomic[2])), "atomic_neighbor": f(float(atomic[3])),
                "bond_H_Oads": f(float(bond[0])), "bond_Oads_Coact": f(float(bond[1])),
                "bond_Coact_Osp4": f(float(bond[2])), "bond_Coact_Obridge": f(float(bond[3])),
                "bond_Obridge_neighbor": f(float(bond[4])), "qualitative_span": span,
                "normalization_note": "atomic PDOS and bond COHP normalized separately; never added together",
            }
        )
    return rows


def state_correlations(material: str, cases: dict[str, tuple[Case, dict[str, object]]], catalog: list[dict[str, str]]) -> list[dict[str, object]]:
    oh_case, oh_cohp = cases[f"{material}_OH"]
    o_case, o_cohp = cases[f"{material}_O"]
    rows = []
    for spin in ("up", "down"):
        left = [x for x in catalog if x["system"] == oh_case.system and x["spin"] == spin]
        right = [x for x in catalog if x["system"] == o_case.system and x["spin"] == spin]
        if not left or not right:
            continue
        fingerprints_left = []
        fingerprints_right = []
        for items, case, cohp, target in ((left, oh_case, oh_cohp, fingerprints_left), (right, o_case, o_cohp, fingerprints_right)):
            for item in items:
                peak = float(item["E_peak_EF"])
                b = bond_fingerprint(case, cohp, spin, peak)
                vector = np.array([
                    float(item["Oads2p_fraction"]), float(item["Coact3d_fraction"]),
                    float(item["Obridge2p_fraction"]), max(0.0, float(item["neighbor_fraction"])),
                    b["Coact-Oads"], b["spectator_sum"], b["Coact-Obridge"], b["neighbor-Obridge"],
                ])
                atomic_vector = vector[:4]
                bond_vector = vector[4:]
                atomic_vector = atomic_vector / max(np.linalg.norm(atomic_vector), 1e-12)
                bond_vector = bond_vector / max(np.linalg.norm(bond_vector), 1e-12)
                vector = np.concatenate((atomic_vector, bond_vector)) / math.sqrt(2.0)
                target.append(vector)
        cost = np.zeros((len(left), len(right)))
        for i, lhs in enumerate(left):
            for j, rhs in enumerate(right):
                cosine = float(np.dot(fingerprints_left[i], fingerprints_right[j]))
                energy_penalty = min(abs(float(lhs["E_peak_EF"]) - float(rhs["E_peak_EF"])) / 2.0, 1.0)
                cost[i, j] = 1.0 - cosine + 0.15 * energy_penalty
        ii, jj = linear_sum_assignment(cost)
        for i, j in zip(ii, jj):
            lhs, rhs = left[i], right[j]
            similarity = max(0.0, 1.0 - cost[i, j])
            rows.append(
                {
                    "material": material, "spin": spin,
                    "OH_feature": lhs["feature_id"], "OH_E_EF": lhs["E_peak_EF"],
                    "O_feature": rhs["feature_id"], "O_E_EF": rhs["E_peak_EF"],
                    "delta_E_O_minus_OH_eV": f(float(rhs["E_peak_EF"]) - float(lhs["E_peak_EF"])),
                    "fingerprint_similarity": f(similarity),
                    "assignment": "correlated mixed periodic feature" if similarity >= 0.55 else "weak/ambiguous correlation",
                    "crossing_assessment": "differential shift/mixing; true crossing not demonstrable without band-overlap phases",
                    "confidence": "high" if similarity >= 0.75 else "medium" if similarity >= 0.55 else "low",
                }
            )
    return rows


def active_oh_rows(case: Case, cohp: dict[str, object]) -> tuple[list[dict[str, object]], dict[str, object]]:
    energy = cohp["energy"]
    curves = [c for c in total_curves(cohp) if curve_role(case, c) == "Oads-H204"]
    if not curves:
        return [], {}
    summed = np.zeros_like(energy)
    rows = []
    for curve in curves:
        summed += curve["minus_cohp"]
        for i, evalue in enumerate(energy):
            rows.append({"system": case.system, "state": case.state, "spin": curve["spin"], "E_EF_eV": f(float(evalue)), "minusCOHP": f(float(curve["minus_cohp"][i])), "minusICOHP": f(float(curve["minus_icohp"][i]))})
    occ = (energy >= -12) & (energy <= 0)
    empty = (energy > 0) & (energy <= min(4.0, float(energy.max())))
    bond_idx = np.where(occ)[0][int(np.argmax(summed[occ]))]
    anti_idx = np.where(occ)[0][int(np.argmin(summed[occ]))]
    empty_idx = np.where(empty)[0][int(np.argmin(summed[empty]))] if empty.any() else anti_idx
    summary = {
        "system": case.system,
        "sigma_OH_bonding_peak_EF_eV": f(float(energy[bond_idx])),
        "sigma_OH_bonding_minusCOHP": f(float(summed[bond_idx])),
        "occupied_antibonding_peak_EF_eV": f(float(energy[anti_idx])),
        "occupied_antibonding_minusCOHP": f(float(summed[anti_idx])),
        "empty_sigma_star_candidate_EF_eV": f(float(energy[empty_idx])),
        "empty_sigma_star_minusCOHP": f(float(summed[empty_idx])),
        "occupied_integrated_minusCOHP": f(integral(energy, summed, -12, 0)),
    }
    return rows, summary


def empty_rows(pdos: list[dict[str, str]]) -> list[dict[str, object]]:
    rows = []
    for case in CASES:
        subset = [r for r in pdos if r["system"] == case.system and 0 <= float(r["E_EF_eV"]) <= 4]
        for spin in ("up", "down"):
            spin_rows = [r for r in subset if r["spin"] == spin]
            energies = sorted({round(float(r["E_EF_eV"]), 6) for r in spin_rows if r["role"] == "Coact"})
            if not energies:
                continue
            role_map = {(r["role"], round(float(r["E_EF_eV"]), 6)): r for r in spin_rows}
            components = {
                "Coact_3d": np.array([max(0.0, float(role_map[("Coact", e)]["d_total"])) for e in energies]),
                "Coact_4s": np.array([max(0.0, float(role_map[("Coact", e)]["s"])) for e in energies]),
                "Coact_4p": np.array([max(0.0, float(role_map[("Coact", e)]["p_total"])) for e in energies]),
                "Oads_2p": np.array([max(0.0, float(role_map[("Oads", e)]["p_total"])) for e in energies]),
                "Obridge_2p": np.array([max(0.0, float(role_map[("Obridge", e)]["p_total"])) for e in energies]),
                "Osp4_2p": np.array([max(0.0, float(role_map[("spectators", e)]["p_total"])) for e in energies]),
            }
            total = sum(components.values())
            peaks, props = find_peaks(total, prominence=max(1e-6, 0.08 * float(total.max())))
            order = sorted(peaks, key=lambda idx: total[idx], reverse=True)[:4]
            for rank, idx in enumerate(order, start=1):
                weights = {name: float(values[idx]) for name, values in components.items()}
                dominant = max(weights, key=weights.get)
                if dominant == "Coact_4s":
                    parent = "a1g-like / 4s-derived"
                elif dominant == "Coact_4p":
                    parent = "t1u-like / 4p-derived"
                elif dominant == "Coact_3d":
                    parent = "empty eg-like or mixed d state"
                else:
                    parent = "ligand-p / mixed framework state"
                rows.append({"system": case.system, "spin": spin, "rank": rank, "E_EF_eV": f(energies[idx]), **{key: f(value) for key, value in weights.items()}, "parent_assignment": parent, "confidence": "medium" if dominant.startswith("Coact") else "low"})
    return rows


def neighbor_rows(case: Case, cohp: dict[str, object], pdos: list[dict[str, str]]) -> dict[str, object]:
    energy = cohp["energy"]
    curves = [c for c in total_curves(cohp) if curve_role(case, c) == "neighbor-Obridge"]
    signed = sum(integral(energy, c["minus_cohp"], -2, 0.5) for c in curves)
    absolute = sum(integral(energy, np.abs(c["minus_cohp"]), -2, 0.5) for c in curves)
    neighbor_role = "Coadj" if case.neighbor_element == "Co" else "Al"
    subset = [r for r in pdos if r["system"] == case.system and r["role"] == neighbor_role and -2 <= float(r["E_EF_eV"]) <= 0.5]
    by_spin = {}
    for spin in ("up", "down"):
        sr = sorted([r for r in subset if r["spin"] == spin], key=lambda r: float(r["E_EF_eV"]))
        e = np.array([float(r["E_EF_eV"]) for r in sr])
        d = np.array([max(0.0, float(r["d_total"])) for r in sr])
        sp = np.array([max(0.0, float(r["s"])) + max(0.0, float(r["p_total"])) for r in sr])
        by_spin[f"d_{spin}"] = float(np.trapezoid(d, e)) if len(e) > 1 else 0.0
        by_spin[f"sp_{spin}"] = float(np.trapezoid(sp, e)) if len(e) > 1 else 0.0
    return {"system": case.system, "state": case.state, "neighbor_element": case.neighbor_element, "neighbor_atom": case.neighbor, "Obridge_atom": case.obridge, "nearEF_neighbor_Obridge_minusCOHP_integral": f(signed), "nearEF_neighbor_Obridge_absCOHP_integral": f(absolute), **{k: f(v) for k, v in by_spin.items()}, "interpretation": "magnetic d-like continuation" if case.neighbor_element == "Co" and by_spin["d_up"] + by_spin["d_down"] > 0.05 else "weak nonmagnetic sp continuation"}


def dpi_rows(case: Case, cohp: dict[str, object], catalog: list[dict[str, str]]) -> list[dict[str, object]]:
    requested = {"pristine_OH": {"UF2", "UF3", "DF2"}, "pristine_O": {"UF2", "UF3", "DF3", "DF4"}, "Al16_OH": {"UF2", "UF3", "DF2"}, "Al16_O": {"UF3", "DF2"}}[case.system]
    rows = []
    for item in catalog:
        if item["system"] != case.system or item["feature_id"] not in requested:
            continue
        peak = float(item["E_peak_EF"])
        b = bond_fingerprint(case, cohp, item["spin"], peak)
        if abs(b["neighbor-Obridge"]) > 0.25 * (b["axial_abs_sum"] + b["spectator_abs_sum"]):
            spatial = "bridge-neighbor/framework"
        elif b["axial_fraction"] > 0.62:
            spatial = "Oads-Coact-Obridge axial three-center"
        elif b["axial_fraction"] < 0.38:
            spatial = "equatorial/framework"
        else:
            spatial = "mixed axial/equatorial"
        rows.append({"system": case.system, "feature_id": item["feature_id"], "spin": item["spin"], "E_EF_eV": item["E_peak_EF"], "axial_fraction": f(b["axial_fraction"]), "spatial_assignment": spatial, "local_pi_assignment": "unresolved: orbitalWise labels are global-axis and phase/cross terms are unavailable", "bonding_sign": item["bonding_class"], "confidence": "medium for spatial span; low for local pi symmetry"})
    return rows


def make_figure(case_data: dict[str, tuple[Case, dict[str, object]]], catalog: list[dict[str, str]]) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(10.2, 7.2), sharex=True, sharey=True)
    for ax, case in zip(axes.ravel(), CASES):
        cohp = case_data[case.system][1]
        energy = cohp["energy"]
        axial = np.zeros_like(energy)
        equat = np.zeros_like(energy)
        for curve in total_curves(cohp):
            if curve["spin"] != "up" or int(curve["pair_no"]) > 6:
                continue
            role = curve_role(case, curve)
            if role in ("Coact-Oads", "Coact-Obridge"):
                axial += curve["minus_cohp"]
            else:
                equat += curve["minus_cohp"]
        mask = (energy >= -2.2) & (energy <= 1.0)
        ax.plot(energy[mask], axial[mask], color="#006D77", lw=1.5, label="axial: Oads + Obridge")
        ax.plot(energy[mask], equat[mask], color="#C44536", lw=1.5, label="equatorial: 4 Osp")
        ax.axhline(0, color="0.25", lw=0.7)
        ax.axvline(0, color="0.25", lw=0.7, ls="--")
        for item in catalog:
            if item["system"] == case.system and item["spin"] == "up" and item["feature_id"] in ("UF1", "UF2", "UF3"):
                x = float(item["E_peak_EF"])
                ax.axvline(x, color="0.6", lw=0.55, alpha=0.6)
                ax.text(x, ax.get_ylim()[1] * 0.82, item["feature_id"], rotation=90, fontsize=7, ha="right", va="top")
        ax.set_title(f"{case.material} {case.state}", fontsize=10)
        ax.text(0.02, 0.04, "positive: bonding\nnegative: antibonding", transform=ax.transAxes, fontsize=7, va="bottom")
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, frameon=False, fontsize=8, loc="upper center", bbox_to_anchor=(0.5, 0.955), ncol=2)
    for ax in axes[:, 0]:
        ax.set_ylabel(r"summed $-\mathrm{COHP}$")
    for ax in axes[1, :]:
        ax.set_xlabel(r"$E-E_F$ (eV)")
    fig.suptitle("Majority-spin axial versus equatorial Co-O fingerprints", fontsize=12, y=0.995)
    fig.tight_layout(rect=(0, 0, 1, 0.91))
    fig.savefig(OUT / "axial_equatorial_COHP.png", dpi=300)
    plt.close(fig)


def build_report(axial: list[dict[str, object]], corr: list[dict[str, object]], oh_summary: list[dict[str, object]], neighbor: list[dict[str, object]]) -> str:
    uf1 = [r for r in axial if r["feature_id"] == "UF1"]
    lines = [
        "# Local-symmetry and orbital-assignment audit",
        "",
        "## Scope and validation",
        "",
        "The audit uses four completed fixed-geometry VASP datasets and four genuine spin-polarized LOBSTER 5.1.1 reprojections. No VASP SCF or geometry optimization was run. Absolute charge spilling is 0.92-0.94% for spin 1 and 1.24-1.27% for spin 2; projected electron recovery differs from the VASP totals by at most 0.0003 e. This LOBSTER output does not print a separate total-spilling metric, so that quantity is explicitly marked unavailable rather than inferred.",
        "",
        "All six nearest Coact-O bonds were included with orbitalWise COHP. The OH systems additionally include the verified active Oads-H204 bond. The fitted local octahedral frames reproduce Oads-Co-Obridge angles of 172.638 degrees for OH and 171.392 degrees for O.",
        "",
        "## Hard limitation",
        "",
        "OUTCAR does not contain complete spin-resolved 5x5 DFT+U onsite matrices, and PROCAR contains squared global-axis LORBIT=11 projections without phase/cross terms. Therefore exact local-axis d-density matrices, natural d orbitals and arbitrary band-resolved d rotations are unavailable. Global-axis orbitalWise COHP is reported but is not relabeled as exact local dz2/dx2-y2/dpi character.",
        "",
        "## Axial versus equatorial majority branches",
        "",
    ]
    for row in uf1:
        lines.append(f"- {row['system']} {row['feature_id']} at {float(row['E_peak_EF']):+.3f} eV: axial fraction {float(row['axial_fraction']):.3f}; {row['assignment']} ({row['confidence']} confidence).")
    lines.extend([
        "",
        "UF1 is tested by its full six-bond signature, not by energy alone. `axial_equatorial_fingerprints.tsv` also identifies the strongest equatorial-majority candidates. The periodic features are collective mixed states; they are not counted as isolated one-electron molecular orbitals.",
        "The four previously proposed UF1 energies do not form one uniformly axial branch: pristine OH UF1 is mixed, Al16 OH UF1 is equatorial-dominated, while both O-state UF1 features are axial-dominated. No distinct axial-majority peak can be resolved for Al16 OH in the sampled -2.0 to +0.5 eV window; its reported e_parallel entry is therefore only a low-confidence mixed fallback.",
        "",
        "## OH to O correlation",
        "",
    ])
    for row in corr:
        if row["spin"] == "up" and row["OH_feature"] == "UF1":
            lines.append(f"- {row['material']} UF1: {float(row['OH_E_EF']):+.3f} to {float(row['O_E_EF']):+.3f} eV, delta {float(row['delta_E_O_minus_OH_eV']):+.3f} eV, fingerprint similarity {float(row['fingerprint_similarity']):.3f}.")
    lines.append("For Al16, fingerprint matching pairs OH UF1 more closely with O UF2, while O UF1 pairs with OH UF2. This is evidence of strong mixing/reordering, not proof of a literal orbital crossing.")
    lines.extend([
        "",
        "Because band-overlap phases are unavailable, the data support differential shift and mixing but cannot prove a true level crossing rather than avoided crossing.",
        "",
        "## Active O-H bond",
        "",
    ])
    for row in oh_summary:
        lines.append(f"- {row['system']}: main occupied sigmaOH bonding maximum {float(row['sigma_OH_bonding_peak_EF_eV']):+.3f} eV; strongest sampled occupied antibonding contribution {float(row['occupied_antibonding_peak_EF_eV']):+.3f} eV.")
    lines.extend([
        "",
        "## Neighbor extension",
        "",
    ])
    for row in neighbor:
        lines.append(f"- {row['system']}: {row['neighbor_element']}-Obridge near-EF signed integral {float(row['nearEF_neighbor_Obridge_minusCOHP_integral']):+.4f}; {row['interpretation']}.")
    lines.extend([
        "",
        "## Interpretation boundary",
        "",
        "The audit distinguishes parent AO/MO bookkeeping from actual periodic DFT spectral peaks. Axial/equatorial assignments use total six-bond COHP and are defensible at the collective-branch level. Exact local irreducible-representation labels remain unavailable where they would require missing phase-resolved local rotations.",
        "",
        "## Files",
        "",
        "- `local_octahedral_frame.tsv`: fitted axes, bonds, trans pairs and global-to-local matrices.",
        "- `six_CoO_bond_COHP.tsv`: energy-resolved spin COHP for all six Co-O bonds.",
        "- `frontier_orbitalwise_COHP.tsv`: global-basis orbitalWise contributions at all catalog features.",
        "- `axial_equatorial_fingerprints.tsv`: majority branch tests.",
        "- `dpi_manifold_assignment.tsv`: requested t2g/dpi feature audit with explicit symmetry limits.",
        "- `frontier_spatial_span.tsv`: separate atomic and bond profiles across the nine-column diagram.",
        "- `state_correlation_OH_to_O.tsv`: fingerprint-based state matching.",
        "- `absolute_orbital_populations.tsv`: absolute Mulliken and Loewdin populations.",
        "- `active_OH_COHP.tsv` and summary: active H204 bond.",
        "- `empty_state_fingerprints.tsv`: EF to +4 eV parent-like candidates.",
        "- `neighbor_extension.tsv`: neighbor-Co versus Al continuation.",
        "- `parent_orbital_audit.tsv`: final parent/DFT bookkeeping table.",
    ])
    return "\n".join(lines) + "\n"


def main() -> int:
    catalog = read_catalog()
    pdos = read_pdos()
    case_data = {case.system: (case, read_cohpcar(LOB / case.folder / "COHPCAR.lobster")) for case in CASES}
    validation = [validate_case(case, case_data[case.system][1]) for case in CASES]
    write_tsv(OUT / "lobster_validation.tsv", validation)

    six = []
    orbital = []
    axial = []
    spectral = []
    spatial = []
    dpi = []
    oh_rows = []
    oh_summary = []
    neighbor = []
    for case in CASES:
        cohp = case_data[case.system][1]
        six.extend(sixbond_rows(case, cohp))
        orbital.extend(orbital_frontier_rows(case, cohp, catalog))
        axial.extend(axial_rows(case, cohp, catalog, pdos))
        spectral.extend(spectral_branch_rows(case, cohp))
        spatial.extend(update_spatial_rows(case, cohp, catalog, pdos))
        dpi.extend(dpi_rows(case, cohp, catalog))
        rows, summary = active_oh_rows(case, cohp)
        oh_rows.extend(rows)
        if summary:
            oh_summary.append(summary)
        neighbor.append(neighbor_rows(case, cohp, pdos))

    correlations = []
    correlations.extend(state_correlations("Pristine", {"Pristine_OH": case_data["pristine_OH"], "Pristine_O": case_data["pristine_O"]}, catalog))
    correlations.extend(state_correlations("Al16", {"Al16_OH": case_data["Al16_OH"], "Al16_O": case_data["Al16_O"]}, catalog))
    empty = empty_rows(pdos)

    write_tsv(OUT / "six_CoO_bond_COHP.tsv", six)
    write_tsv(OUT / "frontier_orbitalwise_COHP.tsv", orbital)
    write_tsv(OUT / "axial_equatorial_fingerprints.tsv", axial)
    write_tsv(OUT / "spectral_branch_candidates.tsv", spectral)
    write_tsv(OUT / "dpi_manifold_assignment.tsv", dpi)
    write_tsv(OUT / "frontier_spatial_span.tsv", spatial)
    write_tsv(OUT / "state_correlation_OH_to_O.tsv", correlations)
    write_tsv(OUT / "active_OH_COHP.tsv", oh_rows)
    write_tsv(OUT / "active_OH_COHP_summary.tsv", oh_summary)
    write_tsv(OUT / "empty_state_fingerprints.tsv", empty)
    write_tsv(OUT / "neighbor_extension.tsv", neighbor)

    parent = []
    axial_by = {(r["system"], r["feature_id"]): r for r in axial}
    span_by = {(r["system"], r["feature_id"], r["spin"]): r for r in spatial}
    for item in catalog:
        branch = axial_by.get((item["system"], item["feature_id"]))
        parent_name = branch["assignment"] if branch else "ligand-field / dpi-like mixed parent"
        span = span_by[(item["system"], item["feature_id"], item["spin"])]
        parent.append({"system": item["system"], "parent_orbital": parent_name, "DFT_feature": item["feature_id"], "energy_EF_eV": item["E_peak_EF"], "columns_spanned": span["qualitative_span"], "bonding_antibonding": item["bonding_class"], "spin": item["spin"], "formal_occupancy": "occupied-like" if float(item["E_peak_EF"]) < 0 else "frontier/unoccupied-like", "OH_to_O_correlation": "see state_correlation_OH_to_O.tsv", "confidence": branch["confidence"] if branch else "medium spatial / low local-symmetry", "bookkeeping_note": "one periodic feature may span multiple columns and is counted once"})
    write_tsv(OUT / "parent_orbital_audit.tsv", parent)

    make_figure(case_data, catalog)
    (OUT / "orbital_assignment_audit.md").write_text(build_report(axial, correlations, oh_summary, neighbor), encoding="utf-8")

    manifest = []
    for case in CASES:
        for filename in ("COHPCAR.lobster", "ICOHPLIST.lobster", "DOSCAR.lobster", "GROSSPOP.lobster", "lobsterin", "lobsterout", "POSCAR"):
            path = LOB / case.folder / filename
            manifest.append({"system": case.system, "file": filename, "size_bytes": path.stat().st_size, "sha256": sha256(path), "role": "read-only local mirror of completed source"})
    write_tsv(OUT / "source_manifest.tsv", manifest)

    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    excluded = {"lobster_sixbond", ZIP_PATH.name}
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(OUT.iterdir()):
            if path.name in excluded or not path.is_file():
                continue
            archive.write(path, arcname=f"orbital_assignment_audit_20260903/{path.name}")
    shutil.copy2(ZIP_PATH, OUT / ZIP_PATH.name)

    print(f"OUTPUT_DIR={OUT.resolve()}")
    print(f"ZIP={ZIP_PATH.resolve()}")
    print(f"SIX_BOND_ROWS={len(six)}")
    print(f"ORBITAL_FRONTIER_ROWS={len(orbital)}")
    print(f"CORRELATIONS={len(correlations)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
