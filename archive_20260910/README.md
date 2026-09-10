# CoOOH/Al OER Spin Mechanism Archive

This repository preserves the computational history and analysis assets for the CoOOH/Al OER project. The scientific question is why Al substitution changes the *OH -> *O oxidation pathway in cobalt oxyhydroxide.

This is an archive, not a claim that every calculation is manuscript-ready. Each dataset is classified as `candidate_dataset`, `supporting_dataset`, or `historical_dataset`. Numerical results retain their source method and limitations; CP2K/cDFT populations are not averaged with VASP/Bader populations.

## Start here

1. `00_project_management/conversation_history/conversation_summary_2026-05_to_2026-09.md`
2. `00_project_management/conflicting_results.md`
3. `03_cDFT/mechanism_validation_bundle/12_mechanism_evidence_matrix.tsv`
4. `04_VASP_analysis/orbital_assignment/orbital_assignment_audit.md`
5. `06_figures/figure_catalog.md`

## Archive layout

- `00_project_management/`: protocol, decisions, conversation summary, provenance and exclusion manifests.
- `01_experimental_constraints/`: experimental constraints and theory-to-experiment evidence map.
- `02_DFT_CP2K/`: OER energetics and selected CP2K source/output records.
- `03_cDFT/`: cDFT charge/spin evidence and mechanism validation bundles.
- `04_VASP_analysis/`: fixed-geometry Bader, LOBSTER/COHP, PDOS, d-band, reaction-density and deprotonation assets.
- `05_analysis_scripts/`: analysis, validation, plotting and deployment scripts.
- `06_figures/`: candidate and supporting figures with source-data pointers.
- `07_literature/`: literature provenance and external-file locations.
- `manuscript/`: manuscript-oriented figure and evidence map.

## Scope and exclusions

Large wavefunctions, full VASP DOSCAR/CHGCAR grids, temporary scheduler/runtime files, credentials, and unrelated MoO3/ZnO/Li3Tl work are not blindly uploaded. Their local or remote locations and reasons are recorded in `00_project_management/archive_manifest.tsv` and `00_project_management/server_files_manifest.md`.

No new electronic-structure calculation was launched for this archive. The archive preserves failed and superseded calculation records where available, but does not promote them to candidate data.
