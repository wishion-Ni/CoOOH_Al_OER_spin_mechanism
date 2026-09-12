#!/usr/bin/env python3
"""Validate the compact COHP/ICOHP/PDOS synchronization package.

This script performs structural/schema sanity checks only. It does not certify
scientific correctness of the underlying DFT/LOBSTER calculations.
"""

from __future__ import annotations

import csv
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "04_VASP_analysis" / "electronic_structure_publication_data"

REQUIRED_CASES = {
    ("pristine", "OH"),
    ("pristine", "O"),
    ("Al16", "OH"),
    ("Al16", "O"),
}


def read_tsv(path: Path):
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def finite_float(value: str) -> bool:
    try:
        return math.isfinite(float(value))
    except Exception:
        return False


def norm_case(row):
    system = row.get("system", "").strip()
    state = row.get("state", "").strip().replace("*", "")
    if system.lower().startswith("pristine"):
        system = "pristine"
    elif system.lower().startswith("al16") or system.lower().startswith("al-") or system.lower().startswith("al_sub"):
        system = "Al16"
    if state.upper() == "OH":
        state = "OH"
    elif state.upper() == "O":
        state = "O"
    return system, state


def require_columns(rows, columns, label, errors):
    if not rows:
        errors.append(f"{label}: empty table")
        return
    missing = [c for c in columns if c not in rows[0]]
    if missing:
        errors.append(f"{label}: missing columns {missing}")


def check_case_coverage(rows, label, errors, warnings):
    cases = {norm_case(r) for r in rows}
    missing = sorted(REQUIRED_CASES - cases)
    if missing:
        warnings.append(f"{label}: missing system/state cases {missing}")


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    files = {
        "mapping": BASE / "mapping" / "structure_and_bond_mapping.tsv",
        "cohp": BASE / "COHP" / "source_data" / "cohp_curves.tsv",
        "icohp": BASE / "COHP" / "source_data" / "icohp_summary.tsv",
        "pdos": BASE / "PDOS" / "source_data" / "pdos_curves.tsv",
        "pdos_map": BASE / "PDOS" / "source_data" / "pdos_site_mapping.tsv",
        "manifest": BASE / "source_manifest.tsv",
        "provenance": BASE / "PROVENANCE.md",
    }

    for key, path in files.items():
        if not path.exists():
            errors.append(f"missing required file: {path.relative_to(ROOT)}")

    if errors:
        print("ERROR: required package files are missing")
        for e in errors:
            print(" -", e)
        return 1

    mapping = read_tsv(files["mapping"])
    cohp = read_tsv(files["cohp"])
    icohp = read_tsv(files["icohp"])
    pdos = read_tsv(files["pdos"])
    pdos_map = read_tsv(files["pdos_map"])
    manifest = read_tsv(files["manifest"])

    require_columns(mapping, [
        "system", "state", "source_structure", "Coact_index", "Oads_index",
        "Obridge_index", "neighbor_index", "neighbor_element", "pair_role",
        "atom1_index", "atom1_element", "atom2_index", "atom2_element",
        "distance_A", "validation_status", "validation_note"
    ], "mapping", errors)

    require_columns(cohp, [
        "system", "state", "pair_role", "atom1_index", "atom2_index",
        "distance_A", "energy_eV_rel_EF", "spin", "pCOHP_raw",
        "minus_pCOHP", "source_file"
    ], "cohp", errors)

    require_columns(icohp, [
        "system", "state", "pair_role", "atom1_index", "atom2_index",
        "distance_A", "ICOHP_spin_up_eV", "ICOHP_spin_down_eV",
        "ICOHP_total_eV", "minus_ICOHP_total_eV", "source_file",
        "validation_status"
    ], "icohp", errors)

    require_columns(pdos, [
        "system", "state", "energy_eV_rel_EF", "spin", "site_role",
        "atom_index", "element", "orbital", "dos", "source_file"
    ], "pdos", errors)

    require_columns(pdos_map, [
        "system", "state", "site_role", "atom_index", "element",
        "source_structure", "validation_note"
    ], "pdos_map", errors)

    require_columns(manifest, [
        "dataset", "system", "state", "source_path", "source_filename",
        "file_size_bytes", "sha256", "copied_to_repo", "note"
    ], "manifest", errors)

    check_case_coverage(cohp, "COHP", errors, warnings)
    check_case_coverage(pdos, "PDOS", errors, warnings)

    # COHP sign consistency and EF bracketing
    by_case = {}
    for i, r in enumerate(cohp, start=2):
        for col in ["distance_A", "energy_eV_rel_EF", "pCOHP_raw", "minus_pCOHP"]:
            if not finite_float(r.get(col, "")):
                errors.append(f"cohp line {i}: non-finite {col}={r.get(col)!r}")
                continue
        if finite_float(r.get("pCOHP_raw", "")) and finite_float(r.get("minus_pCOHP", "")):
            raw = float(r["pCOHP_raw"])
            neg = float(r["minus_pCOHP"])
            if abs(raw + neg) > 1e-7 * max(1.0, abs(raw), abs(neg)):
                errors.append(f"cohp line {i}: minus_pCOHP != -pCOHP_raw")
        case = norm_case(r)
        by_case.setdefault(case, []).append(float(r["energy_eV_rel_EF"]))

    for case, energies in by_case.items():
        if min(energies) > 0 or max(energies) < 0:
            warnings.append(f"COHP {case}: energy grid does not bracket EF=0")

    # ICOHP sign consistency
    for i, r in enumerate(icohp, start=2):
        for col in ["distance_A", "ICOHP_total_eV", "minus_ICOHP_total_eV"]:
            if not finite_float(r.get(col, "")):
                errors.append(f"icohp line {i}: non-finite {col}={r.get(col)!r}")
        if finite_float(r.get("ICOHP_total_eV", "")) and finite_float(r.get("minus_ICOHP_total_eV", "")):
            raw = float(r["ICOHP_total_eV"])
            neg = float(r["minus_ICOHP_total_eV"])
            if abs(raw + neg) > 1e-7 * max(1.0, abs(raw), abs(neg)):
                errors.append(f"icohp line {i}: minus_ICOHP_total_eV != -ICOHP_total_eV")

    # Mandatory validated Coact-Oads mapping per available case
    validated = {
        (*norm_case(r), r.get("pair_role", "").strip())
        for r in mapping
        if r.get("validation_status", "").strip().lower() in {"validated", "pass", "ok", "accepted"}
    }
    for case in REQUIRED_CASES:
        if (*case, "Coact-Oads") not in validated:
            warnings.append(f"mapping {case}: no validated Coact-Oads entry")

    # PDOS numerics, non-negative DOS convention, EF bracketing
    pdos_by_case = {}
    for i, r in enumerate(pdos, start=2):
        if not finite_float(r.get("energy_eV_rel_EF", "")):
            errors.append(f"pdos line {i}: invalid energy")
            continue
        if not finite_float(r.get("dos", "")):
            errors.append(f"pdos line {i}: invalid dos")
            continue
        dos = float(r["dos"])
        if dos < -1e-12:
            warnings.append(f"pdos line {i}: negative DOS found; source table should normally keep both spins positive")
        case = norm_case(r)
        pdos_by_case.setdefault(case, []).append(float(r["energy_eV_rel_EF"]))

    for case, energies in pdos_by_case.items():
        if min(energies) > 0 or max(energies) < 0:
            warnings.append(f"PDOS {case}: energy grid does not bracket EF=0")

    # Basic scientific roles expected in PDOS mapping
    pdos_roles = {(norm_case(r), r.get("site_role", "").strip()) for r in pdos_map}
    for case in REQUIRED_CASES:
        for role in ("Coact", "Oads"):
            if (case, role) not in pdos_roles:
                warnings.append(f"PDOS mapping {case}: missing {role}")

    if warnings:
        print("WARNINGS:")
        for w in warnings:
            print(" -", w)

    if errors:
        print("\nFAILED:")
        for e in errors:
            print(" -", e)
        return 1

    print("\nPASS: COHP/ICOHP/PDOS synchronization package passed schema/sign/coverage sanity checks.")
    print("Note: this does not replace scientific validation of pair mapping or projection quality.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
