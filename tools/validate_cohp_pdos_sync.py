from __future__ import annotations

import csv
import math
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1] / "04_VASP_analysis/electronic_structure_publication_data"
EXPECTED = {("pristine", "*OH"), ("pristine", "*O"), ("Al16", "*OH"), ("Al16", "*O")}


def rows(path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def read_poscar(path):
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    scale = float(lines[1].split()[0])
    cell = [[scale * float(x) for x in lines[i].split()[:3]] for i in range(2, 5)]
    elements = lines[5].split()
    counts = [int(x) for x in lines[6].split()]
    idx = 7
    if lines[idx].strip().lower().startswith("s"):
        idx += 1
    direct = lines[idx].strip().lower().startswith("d")
    idx += 1
    species = [e for e, n in zip(elements, counts) for _ in range(n)]
    coords = []
    for line in lines[idx : idx + len(species)]:
        v = [float(x) for x in line.split()[:3]]
        if direct:
            coords.append([sum(v[j] * cell[j][k] for j in range(3)) for k in range(3)])
        else:
            coords.append([scale * x for x in v])
    return cell, species, coords


def distance(cell, a, b):
    best = float("inf")
    for i in range(-1, 2):
        for j in range(-1, 2):
            for k in range(-1, 2):
                d = [b[q] - a[q] + i * cell[0][q] + j * cell[1][q] + k * cell[2][q] for q in range(3)]
                best = min(best, math.sqrt(sum(x * x for x in d)))
    return best


def main():
    errors = []
    required = {
        "mapping/structure_and_bond_mapping.tsv": ["system", "state", "source_structure", "Coact_index", "Oads_index", "Obridge_index", "neighbor_index", "neighbor_element", "pair_role", "atom1_index", "atom1_element", "atom2_index", "atom2_element", "distance_A", "validation_status", "validation_note"],
        "COHP/source_data/cohp_curves.tsv": ["system", "state", "pair_role", "atom1_index", "atom2_index", "distance_A", "energy_eV_rel_EF", "spin", "pCOHP_raw", "minus_pCOHP", "source_file"],
        "COHP/source_data/icohp_summary.tsv": ["system", "state", "pair_role", "atom1_index", "atom2_index", "distance_A", "ICOHP_spin_up_eV", "ICOHP_spin_down_eV", "ICOHP_total_eV", "minus_ICOHP_total_eV", "source_file", "validation_status"],
        "COHP/source_data/lobster_quality.tsv": ["system", "state", "lobster_version", "abs_charge_spilling_up_percent", "abs_charge_spilling_down_percent", "electrons_recovered", "total_electrons", "normal_finish", "basis_report", "warnings", "quality_note"],
        "PDOS/source_data/pdos_curves.tsv": ["system", "state", "energy_eV_rel_EF", "spin", "site_role", "atom_index", "element", "orbital", "dos", "source_file"],
        "PDOS/source_data/pdos_site_mapping.tsv": ["system", "state", "site_role", "atom_index", "element", "source_structure", "validation_note"],
        "source_manifest.tsv": ["dataset", "system", "state", "source_path", "source_filename", "file_size_bytes", "sha256", "copied_to_repo", "note"],
    }
    data = {}
    shard_specs = {
        "COHP/source_data/cohp_curves.tsv": "cohp_curves_*.tsv",
        "PDOS/source_data/pdos_curves.tsv": "pdos_curves_*.tsv",
    }
    for rel, cols in required.items():
        p = ROOT / rel
        if not p.exists():
            if rel in shard_specs:
                continue
            errors.append("missing file: " + rel)
            continue
        rs = rows(p)
        data[rel] = rs
        missing = [c for c in cols if c not in (rs[0].keys() if rs else [])]
        if missing:
            errors.append("missing columns in %s: %s" % (rel, ",".join(missing)))

    for rel, pattern in shard_specs.items():
        p = ROOT / rel
        paths = [p] if p.exists() else sorted(p.parent.glob(pattern))
        if not paths:
            errors.append("missing file or shards: " + rel)
            data[rel] = []
            continue
        merged = []
        for shard in paths:
            rs = rows(shard)
            cols = required[rel]
            missing = [c for c in cols if c not in (rs[0].keys() if rs else [])]
            if missing:
                errors.append("missing columns in %s: %s" % (shard.name, ",".join(missing)))
            merged.extend(rs)
        data[rel] = merged

    mapping = data.get("mapping/structure_and_bond_mapping.tsv", [])
    combos = {(r.get("system"), r.get("state")) for r in mapping}
    if combos != EXPECTED:
        errors.append("mapping state coverage is %s" % sorted(combos))
    for r in mapping:
        try:
            p = ROOT / r["source_structure"]
            cell, species, coords = read_poscar(p)
            a, b = int(r["atom1_index"]), int(r["atom2_index"])
            if species[a - 1] != r["atom1_element"] or species[b - 1] != r["atom2_element"]:
                errors.append("element mismatch in mapping %s %s" % (r["system"], r["state"]))
            d = distance(cell, coords[a - 1], coords[b - 1])
            if abs(d - float(r["distance_A"])) > 0.005:
                errors.append("distance mismatch %s %s %s" % (r["system"], r["state"], r["pair_role"]))
        except Exception as e:
            errors.append("mapping parse failure %s %s: %s" % (r.get("system"), r.get("state"), e))

    cohp = data.get("COHP/source_data/cohp_curves.tsv", [])
    cohp_combos = {(r.get("system"), r.get("state")) for r in cohp}
    if cohp_combos != EXPECTED:
        errors.append("COHP state coverage is %s" % sorted(cohp_combos))
    for r in cohp:
        if r.get("spin") not in ("up", "down"):
            errors.append("invalid COHP spin label: " + str(r.get("spin")))
        if abs(float(r["minus_pCOHP"]) + float(r["pCOHP_raw"])) > 1e-7:
            errors.append("COHP sign mismatch at %s %s" % (r["system"], r["state"]))
    for combo in EXPECTED:
        es = [float(r["energy_eV_rel_EF"]) for r in cohp if (r["system"], r["state"]) == combo]
        if not es or min(es) >= 0 or max(es) <= 0:
            errors.append("COHP energy does not bracket EF for %s" % (combo,))

    ic = data.get("COHP/source_data/icohp_summary.tsv", [])
    if len(ic) != 12:
        errors.append("expected 12 ICOHP rows, found %d" % len(ic))
    for r in ic:
        if r.get("validation_status") != "validated":
            errors.append("unvalidated ICOHP row")
        if abs(float(r["ICOHP_total_eV"]) - float(r["ICOHP_spin_up_eV"]) - float(r["ICOHP_spin_down_eV"])) > 1e-5:
            errors.append("ICOHP spin sum mismatch at %s %s" % (r["system"], r["state"]))

    quality = data.get("COHP/source_data/lobster_quality.tsv", [])
    if {(r.get("system"), r.get("state")) for r in quality} != EXPECTED:
        errors.append("LOBSTER quality state coverage incomplete")
    for r in quality:
        if r.get("normal_finish") != "yes":
            errors.append("LOBSTER did not finish normally for %s %s" % (r["system"], r["state"]))
        if float(r["abs_charge_spilling_up_percent"]) > 2 or float(r["abs_charge_spilling_down_percent"]) > 2:
            errors.append("spilling >2%% for %s %s" % (r["system"], r["state"]))
        if "fatal" in (r.get("warnings", "") + r.get("quality_note", "")).lower():
            errors.append("fatal warning in LOBSTER quality for %s %s" % (r["system"], r["state"]))

    pdos = data.get("PDOS/source_data/pdos_curves.tsv", [])
    pdos_combos = {(r.get("system"), r.get("state")) for r in pdos}
    if pdos_combos != EXPECTED:
        errors.append("PDOS state coverage is %s" % sorted(pdos_combos))
    for combo in EXPECTED:
        es = [float(r["energy_eV_rel_EF"]) for r in pdos if (r["system"], r["state"]) == combo]
        if not es or min(es) >= 0 or max(es) <= 0:
            errors.append("PDOS energy does not bracket EF for %s" % (combo,))
        roles = {r["site_role"] for r in pdos if (r["system"], r["state"]) == combo}
        if not {"TDOS", "Coact", "Oads", "Obridge", "neighbor"}.issubset(roles):
            errors.append("PDOS required site roles missing for %s" % (combo,))

    manifest = data.get("source_manifest.tsv", [])
    for r in manifest:
        if not re.fullmatch(r"[0-9a-fA-F]{64}", r.get("sha256", "")):
            errors.append("invalid SHA256 in source manifest")
        if not r.get("source_path", "").startswith("/home/ftfan/ncw/"):
            errors.append("source path outside allowed server root")
    if errors:
        print("FAIL")
        for e in errors:
            print("ERROR: " + e)
        return 1
    print("PASS: COHP/ICOHP/PDOS synchronization validated; 0 hard errors")
    print("states=4; mapping_rows=%d; icohp_rows=%d; cohp_rows=%d; pdos_rows=%d" % (len(mapping), len(ic), len(cohp), len(pdos)))
    return 0


if __name__ == "__main__":
    sys.exit(main())

