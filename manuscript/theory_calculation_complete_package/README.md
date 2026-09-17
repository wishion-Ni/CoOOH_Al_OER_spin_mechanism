# Complete theory/computation delivery package

This directory is the single collaborator-facing collection of the computational results prepared for the CoOOH/Al OER mechanism manuscript.

It is designed so that a collaborator can enter one directory and obtain:

- all current manuscript/SI candidate figures;
- the numerical source tables/grids needed to redraw those figures;
- plotting scripts and scientific notes/captions;
- compact provenance and validation records;
- the four validated key structures in CIF format plus their CP2K baseline inputs;
- the project-level final audit and claim-evidence map;
- a manuscript-oriented computational Methods draft (`METHODS.md`).

## Directory layout

- `01_thermodynamics/` — T01 OER electronic-energy staircase and all associated source data/plots/provenance.
- `02_cDFT/` — C01-C05 charge, local-spin, spin-channel and constrained-state analyses.
- `03_VASP_electronic_structure/` — V01 and V04-V08 COHP/ICOHP, PDOS/frontier, Bader, d-band-center, neighbor-site and LOBSTER population results. Both synchronized source data and final figure packages are copied.
- `04_reaction_density/` — V02/V03 charge, magnetization, spin-up and spin-down reaction-density data, figures, local-sphere annotations and provenance.
- `05_structures/` — validated pristine/Al *OH/*O CIF structures and the four CP2K baseline inputs from which they were exported.
- `98_project_context/` — final theory audit, result inventory, unresolved-question boundaries, claim-evidence map and figure-delivery manifest.
- `PACKAGE_INDEX.md` — automatically generated human-readable summary.
- `PACKAGE_MANIFEST.csv` — automatically generated file-by-file source mapping, byte size and SHA256 checksum.

## Scientific scope

The formal evidence chain represented here is:

`OER electronic energetics -> local charge/spin response -> constrained-state localization -> spatial charge/spin redistribution -> Co-O bonding -> frontier electronic structure -> Bader cross-check -> d-state centroid response -> neighboring-site electronic boundary -> independent LOBSTER population cross-check`.

The central manuscript-facing interpretation is that Al substitution changes the post-oxidation electronic/spin accommodation pathway during *OH -> *O, suppressing Co-centered reconstruction while retaining a strong oxygen-involved response.

## Important boundaries

- T01 contains relative **electronic energies**, not a complete matched 298.15 K CHE/Gibbs series.
- cDFT constraint penalties are not reaction free energies, kinetic barriers or electrode potentials.
- The selected CP2K *O states have lower total multiplicity than the corresponding *OH states; local spin/population changes therefore do not independently establish a spontaneous spin-state crossing.
- The Al adsorbate-O spin-sign reversal is not method-independent; use the broader wording `O-centered spin reorganization`.
- Reaction-density maps are fixed-*OH-geometry differences, not Bader maps or differences between independently relaxed states.
- Orbital-resolved PDOS/LOBSTER labels are global-axis projections; exact local eg/t2g or sigma/pi assignments are not claimed.
- No common vacuum alignment is available for the VASP electronic-structure comparison.
- The current validated provenance does not establish a Miller-index surface facet, so the structure should be called a periodic CoOOH slab/supercell unless the original slab-construction record is recovered.

## Raw-data policy

This directory contains the complete **plot-ready/reproducible** data currently present in the GitHub project. Very large raw server-side files (for example full wavefunction files, CHGCAR/DOSCAR/vasprun/COHPCAR files that were intentionally not synchronized) are not duplicated here. Their authoritative paths and hashes are retained in the copied provenance/source-manifest files.

## Rebuilding the directory

Run from repository root:

```bash
python scripts/assemble_theory_calculation_complete_package.py
```

The assembly script copies the canonical result modules and regenerates `PACKAGE_INDEX.md` and `PACKAGE_MANIFEST.csv` without changing any scientific values.
