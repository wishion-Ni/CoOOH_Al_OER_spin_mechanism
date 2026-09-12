# Codex task — synchronize validated COHP / ICOHP / PDOS source data

## Goal

Collect the already-computed VASP/LOBSTER electronic-structure data needed for publication-quality COHP/ICOHP and PDOS figures, convert them into compact software-neutral tables, validate the atom/bond mappings, and push the synchronized data into this repository.

**Do not launch any new VASP/LOBSTER/CP2K calculation in this task.** This is extraction, validation, normalization and synchronization only.

Repository: `wishion-Ni/CoOOH_Al_OER_spin_mechanism`

Before doing anything, read:

- `PROJECT_MEMORY.md`
- `00_project_management/THEORY_RESULT_INVENTORY.md`
- `04_VASP_analysis/VALIDATED_ANALYSIS_LIST.md`
- `archive_20260910/03_cDFT/mechanism_validation_bundle/07_frontier_cohp.tsv`
- `archive_20260910/03_cDFT/mechanism_validation_bundle/09_spin_rehybridization.tsv`
- `archive_20260910/03_cDFT/mechanism_validation_bundle/10_neighbor_Co_vs_Al.tsv`
- `archive_20260910/03_cDFT/mechanism_validation_bundle/06_vasp_frontier_pdos.tsv`
- `archive_20260910/03_cDFT/mechanism_validation_stage2/stage2_06_vasp_lobster_crosscheck.md`

These archived files are reference/provenance aids only. Do not blindly reuse old pair IDs without re-validating the current structure mapping.

---

## Required systems / states

The synchronized package must cover these four cases if the source files exist:

1. `pristine__OH`
2. `pristine__O`
3. `Al16__OH`
4. `Al16__O`

Known historical source-path patterns include:

- `artifacts/cohp_oh_o_inputs_20260824/undoped_OH/`
- `artifacts/cohp_oh_o_inputs_20260824/undoped_O/`
- `artifacts/cohp_oh_o_inputs_20260824/Al16_OH/`
- `artifacts/cohp_oh_o_inputs_20260824/Al16_O/`
- `artifacts/pdos_oh_o_inputs_20260824/undoped_OH/`
- `artifacts/pdos_oh_o_inputs_20260824/undoped_O/`
- `artifacts/pdos_oh_o_inputs_20260824/Al16_OH/`
- `artifacts/pdos_oh_o_inputs_20260824/Al16_O/`

The actual files may live locally, in another project directory, or on the calculation server. Search first; do not assume the historical path is still current.

If the data are on the server, prefer **extracting compact TSV/CSV tables on the server and copying those tables back**. Only download large raw files when required for correct parsing.

---

# A. Structure and bond mapping — mandatory before COHP extraction

For every system/state, locate the structure actually associated with the VASP/LOBSTER result and validate the atom roles geometrically.

Create:

`04_VASP_analysis/electronic_structure_publication_data/mapping/structure_and_bond_mapping.tsv`

Required columns:

- `system`
- `state`
- `source_structure`
- `Coact_index`
- `Oads_index`
- `Obridge_index`
- `neighbor_index`
- `neighbor_element`
- `pair_role`
- `atom1_index`
- `atom1_element`
- `atom2_index`
- `atom2_element`
- `distance_A`
- `validation_status`
- `validation_note`

Mandatory pair roles to validate where present:

- `Coact-Oads`
- `Coact-Obridge`

Optional, only if scientifically meaningful and correctly mapped:

- `neighbor-Obridge`
- `Al-O`
- another explicitly justified nearest-neighbor bond

**Critical rule:** earlier project history contained incorrect COHP pair mappings. Never trust old pair numbers alone. Recalculate distances from the POSCAR/CONTCAR used by the corresponding LOBSTER run and validate the chemical identity.

---

# B. COHP / ICOHP extraction

## B1. Source files

Prefer, when available:

- `COHPCAR.lobster`
- `ICOHPLIST.lobster`
- `lobsterout`
- matching `POSCAR`/`CONTCAR`
- `lobsterin`

Do not commit multi-hundred-MB raw files unless genuinely necessary. Compact extracted data are the primary deliverable.

## B2. COHP curve table

Create:

`04_VASP_analysis/electronic_structure_publication_data/COHP/source_data/cohp_curves.tsv`

Use **long format** with columns:

- `system`
- `state`
- `pair_role`
- `atom1_index`
- `atom2_index`
- `distance_A`
- `energy_eV_rel_EF`
- `spin`
- `pCOHP_raw`
- `minus_pCOHP`
- `source_file`

Requirements:

- energy must be referenced to `E_F = 0 eV`;
- preserve the raw LOBSTER pCOHP sign in `pCOHP_raw`;
- also provide `minus_pCOHP = -pCOHP_raw` for publication plotting, where positive values represent bonding contributions;
- if spin-resolved data exist, preserve `spin = up/down` separately rather than summing prematurely;
- do not fabricate orbital-resolved COHP if it was not actually calculated.

## B3. ICOHP summary table

Create:

`04_VASP_analysis/electronic_structure_publication_data/COHP/source_data/icohp_summary.tsv`

Columns:

- `system`
- `state`
- `pair_role`
- `atom1_index`
- `atom2_index`
- `distance_A`
- `ICOHP_spin_up_eV`
- `ICOHP_spin_down_eV`
- `ICOHP_total_eV`
- `minus_ICOHP_total_eV`
- `source_file`
- `validation_status`

If the LOBSTER format labels spin channels differently, record the native convention in provenance notes.

## B4. LOBSTER quality metrics

Create:

`04_VASP_analysis/electronic_structure_publication_data/COHP/source_data/lobster_quality.tsv`

Include when available:

- charge spilling / total spilling values
- basis/projection information
- LOBSTER version
- relevant warnings
- whether the run is acceptable for qualitative manuscript use

Do not silently omit a poor projection quality warning.

---

# C. PDOS extraction

## C1. Source files

Prefer, depending on what is available:

- `DOSCAR`
- `vasprun.xml`
- `PROCAR`
- already-exported PDOS tables that can be traced to these calculations

## C2. PDOS table

Create:

`04_VASP_analysis/electronic_structure_publication_data/PDOS/source_data/pdos_curves.tsv`

Use **long format** with columns:

- `system`
- `state`
- `energy_eV_rel_EF`
- `spin`
- `site_role`
- `atom_index`
- `element`
- `orbital`
- `dos`
- `source_file`

At minimum, export the following if present in the VASP output:

- `TDOS`
- `Coact : d`
- `Oads : p`
- `Obridge : p`
- neighboring `Co : d` or neighboring `Al : s/p` as appropriate

If orbital-resolved projections are available, also retain the native components (e.g. `px/py/pz`, `dxy/dyz/dz2/dxz/dx2-y2`) in the same long table. Do not collapse them away; plotting can sum later.

Requirements:

- reference all energies to `E_F = 0 eV`;
- keep DOS values positive in the source table for both spin channels; plotting scripts can mirror spin-down visually later;
- preserve the exact site mapping used for each state;
- do not compare raw band indices between structures;
- do not label exact `eg/t2g` character unless a validated local-frame analysis supports it.

Create a matching mapping table:

`04_VASP_analysis/electronic_structure_publication_data/PDOS/source_data/pdos_site_mapping.tsv`

with:

- `system`
- `state`
- `site_role`
- `atom_index`
- `element`
- `source_structure`
- `validation_note`

---

# D. Provenance and reproducibility

Create:

`04_VASP_analysis/electronic_structure_publication_data/PROVENANCE.md`

For every dataset, record:

- original local or server path;
- whether the source was local, remote, or archived;
- source filenames;
- extraction command/script;
- software/version if known;
- Fermi energy used for alignment;
- atom/bond mapping logic;
- known limitations;
- whether the result is `validated`, `candidate`, or `supporting`.

Also create:

`04_VASP_analysis/electronic_structure_publication_data/source_manifest.tsv`

Columns:

- `dataset`
- `system`
- `state`
- `source_path`
- `source_filename`
- `file_size_bytes`
- `sha256`
- `copied_to_repo`
- `note`

For large raw files that are not committed, still record size and SHA256 if accessible.

---

# E. Optional raw-minimal files

Only if they are reasonably small and useful for independent re-parsing, copy them under:

`04_VASP_analysis/electronic_structure_publication_data/raw_minimal/<system_state>/`

Do not push huge `WAVECAR`, `CHGCAR`, or other unnecessary files.

For `COHPCAR.lobster`, `DOSCAR`, `vasprun.xml`, etc., prefer compact exported tables unless raw retention is genuinely needed.

---

# F. Validation

After synchronization, run:

```bash
python tools/validate_cohp_pdos_sync.py
```

Fix all hard errors before pushing.

Also manually verify:

1. all four system/state combinations are present where source data exist;
2. every COHP pair is distance-validated against the associated structure;
3. `energy_eV_rel_EF` crosses or brackets 0 eV;
4. the COHP sign convention is explicitly preserved and `minus_pCOHP` is mathematically correct;
5. spin labels are consistent;
6. no values are copied from historical summary TSVs when the raw source can be extracted directly;
7. if a required source is genuinely missing, document it in `MISSING_DATA_REPORT.md` instead of guessing.

---

# G. Preview plots — sanity check only

You may generate very simple validation previews under:

`04_VASP_analysis/electronic_structure_publication_data/previews/`

These are **not** final manuscript figures. Their purpose is to catch wrong indexing/sign/energy alignment before handoff.

Recommended previews:

- `cohp_sanity_preview.png`: four panels, `-pCOHP` vs `E-EF` for validated `Coact-Oads`;
- `pdos_sanity_preview.png`: four panels, spin-resolved `Coact-d` and `Oads-p` around EF.

Do not spend time on publication styling in this task.

---

# H. Git workflow

After validation:

```bash
git status
git add 04_VASP_analysis/electronic_structure_publication_data tools/validate_cohp_pdos_sync.py
git commit -m "Sync validated COHP and PDOS source data"
git push
```

If the current repo has uncommitted unrelated work, do not overwrite or discard it; isolate this task cleanly.

---

# Final response required from Codex

Report concisely:

1. which original data sources were found and where;
2. whether data were extracted on the server or locally;
3. which of the four states are complete for COHP and PDOS;
4. which COHP bond mappings were validated, including distances;
5. LOBSTER quality/spilling status;
6. exact repository paths created;
7. validator result;
8. commit SHA;
9. any missing/ambiguous data that still require attention.

Do **not** claim a dataset is publication-ready if the source mapping or projection quality remains uncertain.
