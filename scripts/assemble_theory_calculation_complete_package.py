#!/usr/bin/env python3
"""Assemble all collaborator-facing theory/computation outputs into one directory.

This script does not recalculate science. It copies the canonical, already
validated result packages and creates a manifest with SHA256 checksums.
"""
from __future__ import annotations

from pathlib import Path
import csv
import hashlib
import shutil

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "manuscript" / "theory_calculation_complete_package"

COPY_DIRS = [
    (ROOT / "02_DFT_CP2K" / "OER_free_energy" / "T01_combined_OER_staircase",
     DEST / "01_thermodynamics" / "T01_combined_OER_staircase"),
    (ROOT / "03_cDFT" / "OH_to_O_spin_response",
     DEST / "02_cDFT" / "OH_to_O_spin_response"),
    (ROOT / "04_VASP_analysis" / "electronic_structure_publication_data",
     DEST / "03_VASP_electronic_structure" / "publication_data"),
    (ROOT / "04_VASP_analysis" / "electronic_structure_publication_figures",
     DEST / "03_VASP_electronic_structure" / "publication_figures"),
    (ROOT / "04_VASP_analysis" / "publication_figure_data",
     DEST / "03_VASP_electronic_structure" / "publication_figure_data"),
    (ROOT / "04_VASP_analysis" / "diff_density_publication_data",
     DEST / "04_reaction_density" / "diff_density_publication_data"),
    (ROOT / "structures" / "key_structures",
     DEST / "05_structures" / "key_structures"),
]

CP2K_INPUTS = [
    "cp2k_undoped_OH_baseline.inp",
    "cp2k_undoped_O_baseline.inp",
    "cp2k_Al16_OH_baseline.inp",
    "cp2k_Al16_O_baseline.inp",
]

CONTEXT_FILES = [
    ROOT / "00_project_management" / "FINAL_THEORY_AUDIT_20260917.md",
    ROOT / "00_project_management" / "THEORY_RESULT_INVENTORY.md",
    ROOT / "00_project_management" / "unresolved_questions.md",
    ROOT / "manuscript" / "THEORY_CLAIM_EVIDENCE_MAP.md",
    ROOT / "manuscript" / "theory_figure_package" / "FIGURE_DELIVERY_MANIFEST.csv",
]

GENERATED_SUBDIRS = [
    "01_thermodynamics", "02_cDFT", "03_VASP_electronic_structure",
    "04_reaction_density", "05_structures", "98_project_context",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def copy_dir(src: Path, dst: Path) -> None:
    if not src.exists():
        print(f"WARNING: source directory missing: {src.relative_to(ROOT)}")
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, dst, dirs_exist_ok=True)


def main() -> None:
    DEST.mkdir(parents=True, exist_ok=True)

    # Rebuild copied science modules but preserve hand-authored top-level docs.
    for name in GENERATED_SUBDIRS:
        p = DEST / name
        if p.exists():
            shutil.rmtree(p)

    for src, dst in COPY_DIRS:
        copy_dir(src, dst)

    # Preserve the validated CP2K baseline inputs next to the exported CIFs.
    inp_src = ROOT / "archive_20260910" / "02_DFT_CP2K" / "validated_sources"
    inp_dst = DEST / "05_structures" / "cp2k_baseline_inputs"
    inp_dst.mkdir(parents=True, exist_ok=True)
    for name in CP2K_INPUTS:
        src = inp_src / name
        if src.exists():
            shutil.copy2(src, inp_dst / name)
        else:
            print(f"WARNING: missing validated CP2K input: {src.relative_to(ROOT)}")

    # Project-level audit/claim maps make the package interpretable on its own.
    context_dst = DEST / "98_project_context"
    context_dst.mkdir(parents=True, exist_ok=True)
    for src in CONTEXT_FILES:
        if src.exists():
            shutil.copy2(src, context_dst / src.name)
        else:
            print(f"WARNING: context file missing: {src.relative_to(ROOT)}")

    # Map destination files back to their canonical repository source where possible.
    mappings: list[tuple[Path, Path]] = []
    for src, dst in COPY_DIRS:
        if src.exists() and dst.exists():
            for p in dst.rglob("*"):
                if p.is_file():
                    rel = p.relative_to(dst)
                    mappings.append((p, src / rel))
    for name in CP2K_INPUTS:
        p = inp_dst / name
        if p.exists():
            mappings.append((p, inp_src / name))
    for src in CONTEXT_FILES:
        p = context_dst / src.name
        if p.exists():
            mappings.append((p, src))

    manifest = DEST / "PACKAGE_MANIFEST.csv"
    rows = []
    for packaged, canonical in sorted(mappings, key=lambda x: str(x[0])):
        rows.append({
            "package_path": packaged.relative_to(DEST).as_posix(),
            "canonical_repo_source": canonical.relative_to(ROOT).as_posix(),
            "bytes": packaged.stat().st_size,
            "sha256": sha256(packaged),
        })
    with manifest.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["package_path", "canonical_repo_source", "bytes", "sha256"])
        w.writeheader()
        w.writerows(rows)

    # Compact human-readable file index.
    categories = [
        ("01_thermodynamics", "T01 OER electronic-energy staircase, figures, source tables and plotting assets"),
        ("02_cDFT", "C01-C05 local charge/spin and constrained-state results"),
        ("03_VASP_electronic_structure", "V01/V04-V08 COHP, PDOS, Bader, d-center and LOBSTER results"),
        ("04_reaction_density", "V02/V03 charge, magnetization and spin-resolved reaction-density data/figures"),
        ("05_structures", "Validated key CIF structures plus four CP2K baseline inputs"),
        ("98_project_context", "Final audit, claim-evidence map, result inventory and figure manifest"),
    ]
    idx = DEST / "PACKAGE_INDEX.md"
    lines = ["# Package index", "", f"Total copied files: **{len(rows)}**", ""]
    for d, desc in categories:
        n = sum(1 for r in rows if r["package_path"].startswith(d + "/"))
        lines += [f"## `{d}/`", "", f"{desc}. Files: **{n}**.", ""]
    lines += [
        "## Integrity", "",
        "`PACKAGE_MANIFEST.csv` records the canonical repository source, byte size and SHA256 for every copied file.", "",
        "The package intentionally uses compact/plot-ready data instead of duplicating very large server-side raw wavefunction, CHGCAR, DOSCAR, vasprun or COHPCAR files when those are not already present in the repository. Their server provenance/hashes remain in the copied provenance manifests.", "",
    ]
    idx.write_text("\n".join(lines), encoding="utf-8")

    required = [
        DEST / "METHODS.md",
        DEST / "01_thermodynamics" / "T01_combined_OER_staircase" / "publication_package" / "source_data" / "stepwise_dG.csv",
        DEST / "02_cDFT" / "OH_to_O_spin_response" / "publication_package" / "source_data",
        DEST / "03_VASP_electronic_structure" / "publication_data" / "PROVENANCE.md",
        DEST / "04_reaction_density" / "diff_density_publication_data" / "README.md",
        DEST / "05_structures" / "key_structures" / "pristine_OH.cif",
        manifest,
    ]
    missing = [p for p in required if not p.exists()]
    if missing:
        raise SystemExit("Missing required package items:\n" + "\n".join(str(p.relative_to(ROOT)) for p in missing))

    print(f"Assembled {len(rows)} files under {DEST.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
