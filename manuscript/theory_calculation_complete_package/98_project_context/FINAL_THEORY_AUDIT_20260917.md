# Final Theory/Computation Audit — 2026-09-17

## Scope

This audit reviews the current `main` branch and the preserved `archive_20260910/` snapshot with one question: **does any already-computed dataset remain both scientifically useful and insufficiently processed/visualized for collaborator delivery?**

The answer after the final completion pass is: **no high-value completed dataset remains unprocessed in a way that materially weakens the present mechanism package.** Remaining items fall into two groups: (i) data that are intentionally retained as supporting/diagnostic records because a new figure would be redundant or too interpretation-sensitive, and (ii) questions that require genuinely new calculations or unavailable raw outputs.

The central manuscript-facing interpretation remains:

> Al substitution enables an alternative spin-adaptive oxygen-oxidation response, suppressing Co-centered electronic reconstruction during the key *OH -> *O step while preserving strong O-centered redox/spin reorganization.

This statement must remain within the method-specific limits documented below.

---

## A. Completed manuscript-ready / collaborator-ready result packages

| ID | Module | Status | Primary role | Recommended use |
|---|---|---|---|---|
| T01 | OER staircase | figure_ready | Three-site electronic-energy pathway; Al-adjacent Co selectively lowers *OH -> *O relative to pristine | main-text candidate |
| C01 | cDFT charge redistribution | figure_ready_draft | Al suppresses active-Co population response while O oxidation remains | main-text candidate |
| C02 | cDFT local-spin evolution | figure_ready_draft | Al suppresses Co-centered spin response and strengthens O-centered reorganization | main-text candidate |
| C03 | cDFT spin-channel partition | figure_ready_draft | Resolves alpha/beta construction of local Co/O response | main-text or SI |
| C04 | cDFT *O constrained-state fingerprints | figure_ready_draft | Co+adsorbate localization is favored over Co-only localization; valid Co-only M+2 penalty rises after Al substitution | main-text or SI |
| C05 | full-state cDFT constraint evolution | figure_ready | Extends Co-only vs Co+adsorbate N±1 penalties across *OH/*O/*OOH | SI / supporting |
| V01 | COHP / ICOHP | figure_ready | Validated Co-O bond rehybridization comparison | main-text or SI |
| V02 | reaction-induced charge density | figure_ready | Spatial charge redistribution for fixed-*OH-geometry *OH -> *O | main-text or SI |
| V03 | magnetization / spin-resolved density | figure_ready | Spatial spin reorganization; magnetization panel is the highest-value density map | main-text or SI |
| V04 | PDOS / frontier-state fingerprints | figure_ready | Frontier-state character and mixing/reordering without raw-band-index claims | supporting |
| V05 | Bader response | figure_ready | Net charge-partition cross-check; Oads dominates net electron loss, Coact net change is small | SI |
| V06 | d-band-center presentation set | figure_ready | Compact active-Co spectral-centroid response descriptor | supporting / SI |
| V07 | neighbor electronic boundary | figure_ready | ~197-fold loss of neighbor-site frontier PDOS weight when Co is replaced by Al | main-text supporting / SI |
| V08 | LOBSTER orbital-population cross-check | figure_ready | Independent VASP/LOBSTER support for spin-selective Co/O population redistribution | supporting / SI |

### A1. Thermodynamic scope

T01 is a **historical CP2K electronic-energy comparison without a full vibrational correction**. It is correctly presented as `Relative electronic energy (eV)`, not as a strict 298.15 K Gibbs/CHE series. Its key manuscript comparison is the selective reduction of the *OH -> *O step for the Al-adjacent Co site while the first step becomes slightly less favorable.

### A2. cDFT scope

C01-C05 characterize local population, local spin, spin-channel composition and constrained-state localization costs. The selected *O states use a globally lower multiplicity than *OH in both materials; therefore local ΔN/Δm values describe redistribution within the selected solutions and do **not** independently prove a spontaneous spin-state crossing.

The Al Oads local-spin sign reversal is robust within the CP2K population partitions but is not reproduced as a method-independent sign reversal by VASP/LOBSTER. Main-text language should therefore use `O-centered spin reorganization` or `O-rich spin-polarized Co-O response`, not a universal spin-flip claim.

cDFT constraint penalties are not CHE reaction free energies, kinetic barriers or electrode potentials.

### A3. VASP/LOBSTER scope

All manuscript-facing COHP pairs use the distance-validated current-POSCAR mappings. V02/V03 are reaction-induced density differences for matched fixed geometry and are not Bader maps. V04/V08 use frontier/orbital fingerprints without claiming exact local ligand-field irreducible representations. V06 energy centroids are referenced to each calculation's EF because no common vacuum alignment is available.

---

## B. Existing completed data intentionally not promoted into additional headline figures

These are **not missing analyses**. They remain archived because additional figures would be redundant, weakly incremental, or more interpretation-sensitive than the formal modules above.

### B1. Local-sphere integration of reaction/spin density

Useful as a numerical sanity check on V02/V03 but largely redundant with the spatial maps, cDFT local populations and V05 Bader analysis. Keep as supporting validation rather than a separate manuscript figure.

### B2. Orbital-assignment / ligand-field diagnostic bundle

The archive contains six-bond orbitalWise COHP, axial/equatorial fingerprints, frontier-state correlation, spatial-span analysis, empty-state fingerprints and local-octahedral-frame records. These were valuable for mechanism validation but should not be expanded into a new headline orbital diagram because the available OUTCAR/PROCAR data do not provide the phase/cross terms or complete spin-resolved 5x5 DFT+U onsite matrices required for exact arbitrary local-axis d-density matrices.

The defensible conclusion is differential frontier-state mixing/reordering. A literal orbital crossing or exact local `dz2`, `dx2-y2`, `eg/t2g` identity should not be claimed beyond the confidence levels already documented.

### B3. Active O-H COHP

The O-H bonding/antibonding features are available and can be cited as a diagnostic if required, but they do not add enough independent information to the present Al-sensitive *OH -> *O mechanism to justify a new figure.

### B4. Proton-relay profiles

The fixed-path / PCET proton-relay profiles are retained as diagnostic historical results. They are not rigorous NEB activation barriers and should not be promoted as kinetic evidence.

### B5. Strict 298.15 K VASP CHE record for one undoped site

A valid strict calculation exists for `strict_undoped_site03`, with OH -> O as the PDS and a reported limiting potential of 2.030710620 V. It does **not** provide a matched pristine-versus-Al series and therefore cannot replace T01 as the cross-system thermodynamic comparison.

### B6. Startup / preliminary reaction-density proxies and historical preliminary plots

These have been superseded by the current matched fixed-geometry V02/V03 package and should remain archive-only.

### B7. Additional framework COHP summaries

The framework and neighbor-bond Δ(-ICOHP) records are already represented in V01 and retained as V07 source context. Additional derivative plots would be redundant.

---

## C. Prepared calculations that do not contain completed result outputs

### C1. Terminal-OH deprotonation / coverage series

The archived coverage manifest defines ten intended structures: 2-6 deprotonated terminal OH groups for both `undoped_control` and `Al16_adjacent`. The archived coverage directories contain prepared inputs (`INCAR`, `POSCAR`) but no completed `OUTCAR` results in the preserved tree.

Therefore this is **not an unprocessed completed dataset**. Recovering the proposed coverage-dependent individual potentials, half-coverage potential or Frumkin-width analysis would require calculation outputs that are not present in the repository (or a new run if they do not exist elsewhere).

---

## D. Genuine scientific gaps that require new calculations or unavailable raw output

These should be treated as optional future extensions, not as missed post-processing tasks:

1. **Counterfactual energetic causality** — direct pairwise energy comparison showing why the same O-rich/spin-adaptive post-oxidation branch is selectively stabilized in Al-substituted CoOOH but not pristine CoOOH.
2. **Matched strict 298.15 K CHE / vibrational thermodynamics** — a fully matched pristine-versus-Al free-energy series with consistent ZPE/entropy treatment.
3. **Reaction barrier** — NEB or another defensible activation-barrier calculation for the key *OH -> *O transformation.
4. **Direct CP2K frontier-MO / removed-electron spin assignment** — unavailable in the archived outputs.
5. **Exact local d-density matrices** — complete spin-resolved 5x5 DFT+U onsite matrices / phase-resolved projection information are unavailable.
6. **Absolute energy alignment** — LOCPOT/vacuum-level alignment or equivalent work-function reference is unavailable for the current VASP electronic-structure comparison.
7. **Quantitative spectroscopy simulation** — TDDFT/XAS/TAS-like calculated spectra directly mapped onto the experimental Co-sensitive transient response.
8. **Exchange-coupling parameterization** — a quantitative J or magnetic-interaction energy decomposition supporting a specific exchange/frustration model.
9. **Alternative trivalent-substitution controls** — useful for generality but not required for the current Al-specific mechanism.

No item in this section can be recovered honestly by simply making another plot from the current repository tables.

---

## E. Superseded / legacy branches that should not re-enter the manuscript workflow

- old Al thermodynamic post-processing that conflicts with the validated T01 three-site comparison;
- preliminary cDFT tables superseded by the complete validated dataset;
- preliminary Bader plot scripts superseded by V05;
- old reaction-density/startup-density proxies superseded by V02/V03;
- any historical COHP pair mapping not validated against the current POSCAR/ICOHPLIST distances;
- raw band-index-based frontier-state identities that ignore state mixing/reordering.

Archive preservation is appropriate for provenance, but these files must not be promoted back into manuscript claims without explicit revalidation.

---

## F. Repository-management findings and completed synchronization

Two top-level project documents were stale at the start of this audit:

- the root `README.md` still described T01 as the only current figure-ready result;
- `00_project_management/THEORY_RESULT_INVENTORY.md` reflected the early T01/C01-C03 stage and did not index the current C01-C05 / V01-V08 delivery set.

**Post-audit action completed:** both files were synchronized to the current figure inventory on 2026-09-17. The root README now points collaborators to the formal manifest and this final audit, while `THEORY_RESULT_INVENTORY.md` now indexes T01, C01-C05 and V01-V08 and distinguishes completed, deliberately unpromoted and genuinely incomplete branches.

`00_project_management/unresolved_questions.md` remains scientifically useful. Its open mechanistic questions are still genuine; the file should be read as a boundary document rather than a list of unfinished plotting tasks.

The manifest retains `figure_ready_draft` for C01-C04. This is a delivery-status label, not evidence of missing source calculations: the publication package already contains source data, reproducible plotting assets and raster/vector outputs. Any future change from `figure_ready_draft` to `figure_ready` should reflect collaborator approval of the exact presentation rather than additional computation.

---

## G. Final assessment

### Completed-data completeness

**PASS.** After formalizing V05, V07, V08 and C05, no additional already-computed, high-information dataset was found that clearly warrants a new publication figure and is not already represented by T01, C01-C05 or V01-V08.

### Publication-material completeness

The repository now contains a sufficiently broad computational evidence package for collaborator assembly:

`thermodynamics -> local charge/spin response -> constrained-state localization -> spatial density/spin redistribution -> Co-O bonding -> frontier electronic structure -> net-charge cross-check -> neighboring-site electronic boundary -> independent LOBSTER population cross-check`.

### Remaining uncertainty

The principal remaining limitation is **causal energetic closure**, not missing visualization: current data strongly support an Al-induced change in the post-oxidation electronic/spin accommodation pathway, but they do not directly compute the counterfactual energetic preference of the same O-rich state in both pristine and Al-substituted systems.

Given the project constraint that no new calculations will be launched, the correct action is to preserve this as an explicit interpretation boundary rather than fill it with additional derivative figures.
