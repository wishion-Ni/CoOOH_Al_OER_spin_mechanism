# Complete theory/computation delivery package

This directory is the single collaborator-facing collection of the computational results prepared for the CoOOH/Al OER mechanism manuscript.

## Download the complete package

For collaborators who do not need to clone the Git repository, the entire directory is automatically packaged as a single ZIP archive and published as a fixed GitHub Release asset whenever this package is updated.

**[Download the latest complete ZIP package](https://github.com/wishion-Ni/CoOOH_Al_OER_spin_mechanism/releases/download/theory-package-latest/theory_calculation_complete_package.zip)**

SHA256 checksum: [theory_calculation_complete_package.zip.sha256](https://github.com/wishion-Ni/CoOOH_Al_OER_spin_mechanism/releases/download/theory-package-latest/theory_calculation_complete_package.zip.sha256)

The ZIP preserves the complete `theory_calculation_complete_package/` directory structure shown below.

It is designed so that a collaborator can obtain:

- all current manuscript/SI candidate figures;
- the numerical source tables/grids needed to redraw those figures;
- plotting scripts and scientific notes/captions;
- compact provenance and validation records;
- the four validated key structures in CIF format plus their CP2K baseline inputs;
- the project-level final audit and claim-evidence map;
- the computational Methods file (`METHODS.md`).

## Directory layout

- `01_thermodynamics/` — OER electronic-energy staircase and associated source data, plots, and provenance.
- `02_cDFT/` — charge, local-spin, spin-channel, and constrained-state analyses.
- `03_VASP_electronic_structure/` — COHP/ICOHP, PDOS/frontier, Bader, d-state-centroid, neighboring-site, and LOBSTER population results, including synchronized source data and final figure packages.
- `04_reaction_density/` — charge, magnetization, spin-up, and spin-down reaction-density data, figures, local-sphere annotations, and provenance.
- `05_structures/` — pristine/Al *OH/*O CIF structures and the corresponding CP2K baseline inputs.
- `98_project_context/` — final theory audit, result inventory, unresolved-question boundaries, claim-evidence map, and figure-delivery manifest.
- `METHODS.md` — manuscript-ready computational Methods.
- `PACKAGE_INDEX.md` — automatically generated human-readable package summary.
- `PACKAGE_MANIFEST.csv` — automatically generated file-by-file source mapping, byte size, and SHA256 checksum.

## Scientific scope

The evidence chain represented here is:

`OER electronic energetics -> local charge/spin response -> constrained-state localization -> spatial charge/spin redistribution -> Co-O bonding -> frontier electronic structure -> Bader cross-check -> d-state centroid response -> neighboring-site electronic boundary -> independent LOBSTER population cross-check`.

The central interpretation is that Al substitution changes the post-oxidation electronic/spin accommodation pathway during *OH -> *O, suppressing Co-centered reconstruction while retaining a strong oxygen-involved response.

## Important boundaries

- The OER staircase contains relative **electronic energies**, rather than a complete matched finite-temperature CHE/Gibbs series.
- cDFT constraint penalties are not reaction free energies, kinetic barriers, or electrode potentials.
- The selected CP2K *O states have lower total multiplicity than the corresponding *OH states; local spin/population changes therefore do not independently establish a spontaneous spin-state crossing.
- The Al adsorbate-O spin-sign reversal is not method-independent; the broader interpretation is O-centered spin reorganization.
- Reaction-density maps are fixed-*OH-geometry differences, rather than Bader maps or differences between independently relaxed states.
- Orbital-resolved PDOS/LOBSTER labels are global-axis projections; exact local eg/t2g or sigma/pi assignments are not claimed.
- No common vacuum alignment is available for the VASP electronic-structure comparison.
- The validated structure provenance does not establish a Miller-index surface facet, so the structure is described as a periodic CoOOH slab/supercell.

## Raw-data policy

This directory contains the complete **plot-ready/reproducible** dataset currently synchronized to the GitHub project. Very large server-side raw files, such as full wavefunction files and selected CHGCAR/DOSCAR/vasprun/COHPCAR files, are not duplicated when they were intentionally excluded from synchronization. Their source locations and provenance are retained in the corresponding records.

## Rebuilding the directory

Run from the repository root:

```bash
python scripts/assemble_theory_calculation_complete_package.py
```

The assembly script copies the canonical result modules and regenerates `PACKAGE_INDEX.md` and `PACKAGE_MANIFEST.csv` without changing scientific values.
