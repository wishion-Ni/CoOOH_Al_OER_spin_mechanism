# Final Archive Report

## 1. Repository tree

The snapshot is under `archive_20260910/` and follows the protocol sections `00_project_management` through `07_literature`, plus `manuscript`. The root index is `ARCHIVE_20260910_INDEX.md`.

## 2. Uploaded datasets

- CP2K OER staircase records and selected validated CP2K baseline inputs/outputs.
- cDFT population, spin, constraint and mechanism-validation tables, notes and figures.
- Four fixed-geometry VASP OH/O structure and Bader records.
- Accepted spin-resolved LOBSTER summaries, ICOHPLIST/lobsterout records, pair definitions and orbital-assignment audits.
- Processed PDOS, d-band-center, frontier-state, reaction-density, spin-density and deprotonation records.
- Candidate/supporting figures and compressed browser previews for large figures.
- Dated analysis, validation, plotting and deployment scripts.
- Conversation summary, decision history, conflicts, experimental constraints, figure catalog and manuscript evidence map.

## 3. Files remaining locally or on the server

The complete local inventory is `00_project_management/archive_manifest.tsv`; the split inventory files are also retained locally. Large VASP wavefunctions, full DOSCAR/CHGCAR grids, raw downsampled density arrays and several large processed tables remain outside the GitHub tree. Remote paths and transfer rationale are in `server_files_manifest.md` and `upload_exclusions_20260910.md`.

## 4. Manual literature retrieval

The literature PDFs and ZIP files referenced by the user are outside the workspace under `E:\xwechat_files\...` and `E:\Subject\...`. They were not copied because their redistribution status and stable bibliographic metadata were not verified. Add them only after rights and citation details are confirmed.

## 5. Candidate manuscript figures

The current candidate set covers cDFT charge/spin response, validated COHP, Bader comparison, reaction-induced density/spin density, PDOS/d-band centers, ligand-field/spin-selective mechanism, and OER/CHE staircases. Numerical source tables and limitations must accompany every figure.

## 6. Missing calculations or audits

- Final validated S13-style terminal-OH deprotonation series, individual potentials, half-coverage potential and Frumkin width, if not already present in a later source tree.
- Any publication-level reconciliation between cDFT population changes and VASP/Bader net charges.
- Full DFT+U occupation matrices or phase-resolved cross terms if an exact orbital label is required.
- Any final relaxed-statistics charge/COHP repeat intended to replace the fixed-geometry comparison.

No calculation was launched for this archive, and no historical or conflicting result was deleted.
