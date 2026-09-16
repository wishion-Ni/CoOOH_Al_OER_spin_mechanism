# Theory Result Inventory

## Purpose

This document indexes the current validated theory/computation assets for manuscript-material preparation. It reflects the repository after the final V05/V07/V08/C05 completion pass and should be read together with:

- `manuscript/theory_figure_package/FIGURE_DELIVERY_MANIFEST.csv`
- `00_project_management/FINAL_THEORY_AUDIT_20260917.md`
- `00_project_management/unresolved_questions.md`

The project is in a **figure-delivery / collaborator handoff** phase. Existing validated calculations are converted into standalone reproducible components; no additional calculation is implied by an archived input directory.

---

# 1. OER reaction-energy staircase — T01

Location: `02_DFT_CP2K/OER_free_energy/T01_combined_OER_staircase/`

Manuscript package: `02_DFT_CP2K/OER_free_energy/T01_combined_OER_staircase/publication_package/`

Status: **figure_ready**

| System | * -> *OH | *OH -> *O | *O -> *OOH | *OOH -> O2 |
|---|---:|---:|---:|---:|
| pristine Co32 | 1.199993 | 1.793143 | 1.534211 | 0.392652 |
| Al16 neighboring Co7 | 1.403097 | 1.524802 | 0.871955 | 1.120146 |
| Al16 Al47 control | 2.382189 | -1.011081 | 2.217542 | 1.331350 |

Key pristine -> Al-neighboring-Co comparison:
- first step: +0.203104 eV;
- *OH -> *O: -0.268341 eV.

Scope: historical CP2K electronic-energy comparison without a full vibrational correction. The y-axis is `Relative electronic energy (eV)`. Do not relabel as a strict 298.15 K Gibbs/CHE series. T02/T03 derivative plots remain intentionally omitted as redundant.

---

# 2. cDFT / CP2K charge-spin and constrained-state package — C01-C05

Location: `03_cDFT/OH_to_O_spin_response/`

Manuscript package: `03_cDFT/OH_to_O_spin_response/publication_package/`

## C01 — charge redistribution

Status: **figure_ready_draft**

Definition: `Delta N = N(*O) - N(*OH)`.

Hirshfeld examples:
- pristine Coact: +0.219 e;
- Al16 Coact: +0.012 e;
- pristine Oads: -0.464 e;
- Al16 Oads: -0.427 e.

Message: Al substitution strongly suppresses the Co-centered population response while substantial O-centered oxidation remains.

## C02 — local-spin evolution

Status: **figure_ready_draft**

Hirshfeld examples:
- pristine Coact: Δm = -0.821 muB;
- Al16 Coact: Δm = -0.448 muB;
- pristine Oads: Δm = -0.070 muB;
- Al16 Oads: Δm = -0.744 muB.

Message: Al reduces Co-centered spin reconstruction and is accompanied by stronger O-centered spin reorganization.

Boundary: selected *O calculations use a globally lower multiplicity than *OH in both systems. Local changes characterize the selected states; they are not independent proof of a spontaneous spin-state crossing. The Al Oads sign reversal is not method-independent, so main-text language should emphasize O-centered spin reorganization rather than universal spin reversal.

## C03 — spin-change partition

Status: **figure_ready_draft**

Purpose: decompose local Co/O changes into alpha- and beta-population contributions. Do not identify either channel as the emitted electron because the global spin state differs and the directly removed CP2K frontier orbital is unavailable.

## C04 — *O constrained-state fingerprints

Status: **figure_ready_draft**

Purpose: compare Co-only versus Co+adsorbate charge constraints and the valid Co-only-spin M+2 branch at *O.

Key result: Co+adsorbate localization is less costly than Co-only localization, and the valid Co-only M+2 penalty rises from 2.899188 eV in pristine to 4.036604 eV in Al16.

## C05 — full-state cDFT constraint evolution

Status: **figure_ready**

Purpose: extend N-1/N+1 Co-only versus Co+adsorbate localization penalties across *OH, *O and *OOH.

Message: lower Co+adsorbate penalties across the state sequence support an electronically distributed Co-O response rather than purely Co-localized accommodation.

All C03-C05 constraint values are **cDFT constraint penalties**, not CHE free energies, kinetic barriers or electrode potentials.

---

# 3. Validated bonding analysis — V01

Location: `04_VASP_analysis/electronic_structure_publication_data/`

Figure package: `04_VASP_analysis/electronic_structure_publication_figures/`

Status: **figure_ready**

Contents: energy-resolved COHP and ICOHP summaries for validated Coact-Oads, Coact-Obridge and neighbor-Obridge pairs.

Key Coact-Oads change:
- pristine: -ICOHP 1.92767 -> 3.39257 eV, Δ = +1.46490 eV;
- Al16: -ICOHP 1.93011 -> 3.04245 eV, Δ = +1.11234 eV.

Interpretation: the two systems exhibit different occupied Co-O rehybridization/bonding responses. Do not reduce this to the claim that Al simply strengthens the Co-O bond.

---

# 4. Reaction-induced charge and spin density — V02/V03

Location: `04_VASP_analysis/diff_density_publication_data/`

Status: **figure_ready**

Formal maps:
- V02 charge-density difference;
- V03 magnetization difference;
- spin-up / spin-down derived density differences retained as complementary/SI panels.

Definition: fixed-*OH-geometry *O minus *OH. These are local reaction-induced density fields, not Bader maps and not formal oxidation-state maps.

Recommended priority: magnetization paired panel > charge paired panel > spin-up/down SI.

---

# 5. PDOS / frontier-state fingerprints — V04

Location: `04_VASP_analysis/electronic_structure_publication_data/PDOS/`

Figure package: `04_VASP_analysis/electronic_structure_publication_figures/`

Status: **figure_ready**

Purpose: compare active-Co, adsorbate-O, bridge-O and selected neighboring states across pristine/Al16 *OH/*O.

Boundary: frontier states mix/reorder. Raw band indices must not be identified as the same physical state across structures without fingerprint tracking. Exact local ligand-field irreducible representations remain unavailable where phase/cross terms would be required.

---

# 6. Bader charge response — V05

Status: **figure_ready**

Fixed-geometry ΔN_Bader = *O - *OH:

| System | Coact | Oads | Obridge | Neighbor |
|---|---:|---:|---:|---:|
| pristine | +0.025873 | -0.260692 | -0.023564 | -0.001450 |
| Al16 | +0.030430 | -0.224205 | +0.000284 | -0.000660 |

Message: adsorbate O carries the dominant net Bader electron loss, while active-Co net Bader change is small. This is supporting charge-partition context and must not be used alone to define oxidation state.

Recommended use: SI.

---

# 7. d-band-center / spectral-centroid descriptors — V06

Status: **figure_ready**

Presentation options:
- V06a absolute occupied active-Co 3d centroid;
- V06b *OH -> *O centroid-shift summary;
- V06c schematic d-band/DOS-style representation.

Occupied active-Co shift:
- pristine: +0.106577 eV;
- Al16: +0.175229 eV.

Framework-average shifts remain small. No common vacuum alignment is available, so cross-system absolute centroid values are not a strict absolute-energy alignment. V06c uses schematic DOS shapes; only centroid positions are data-derived.

---

# 8. Neighbor electronic boundary — V07

Status: **figure_ready**

Neighbor-site PDOS integrated from -2.0 to +0.5 eV relative to EF:
- pristine neighboring Co: 2.449529 states;
- Al16 neighboring Al: 0.012442 states.

This is an approximately 197-fold reduction.

Message: Al removes a neighboring Co-like frontier/magnetic manifold and behaves as a frontier-inactive local electronic boundary. This is supporting evidence for an altered local accommodation landscape, not a standalone proof of the full causal pathway.

---

# 9. LOBSTER orbital-population cross-check — V08

Status: **figure_ready**

Orbital-summed *OH -> *O spin-channel changes (Mulliken examples):
- pristine Co 3d: up -0.01 e; down +0.09 e;
- Al16 Co 3d: up 0.00 e; down +0.04 e;
- pristine Oads 2p: up +0.16 e; down -0.66 e;
- Al16 Oads 2p: up +0.22 e; down -0.68 e.

Purpose: independent VASP/LOBSTER cross-check of spin-selective Co/O population redistribution.

Boundary: orbital-resolved labels are global-axis projections, not exact local ligand-field orbitals. V08 does not establish a method-independent Oads spin-sign reversal.

---

# 10. Existing data intentionally kept as diagnostic/supporting records

No additional headline figure is currently recommended for:
- local-sphere density integrations;
- axial/equatorial / local-symmetry orbital-assignment audit;
- frontier-state correlation/span diagnostics;
- active O-H COHP;
- proton-relay fixed-path / PCET profiles;
- single-site strict-298.15 K undoped CHE record;
- preliminary/startup reaction-density proxies;
- additional derivative framework COHP plots.

These are archived for validation and provenance. See `FINAL_THEORY_AUDIT_20260917.md` for the reason each is not promoted.

---

# 11. Prepared but incomplete calculation series

The terminal-OH deprotonation coverage manifest contains intended 2-6 deprotonation structures for pristine and Al16 branches, but the preserved coverage directories contain calculation inputs rather than completed OUTCAR result sets. This is therefore not an unprocessed completed dataset.

A strict 298.15 K VASP CHE result exists only for `strict_undoped_site03`; it is not a matched pristine/Al thermodynamic series.

---

# 12. Final completeness assessment

After formalization of V05, V07, V08 and C05, **no remaining already-computed high-information dataset in the repository clearly warrants a new publication figure**.

Remaining scientific gaps concern causal energetic closure, strict matched thermodynamics, barriers, exact frontier/local-orbital information, absolute-energy alignment or explicit spectroscopy simulation. These require new calculations or unavailable raw outputs and should not be disguised as post-processing tasks.
