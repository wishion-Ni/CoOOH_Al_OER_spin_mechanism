# CoOOH_Al_OER_spin_mechanism

Repository for the theoretical/computational component of the CoOOH/Al OER mechanism project. The current objective is to preserve validated calculations as **standalone manuscript-ready theory figure components** that can be handed to collaborators for final paper assembly.

## Repository map

- `00_project_management/` — mechanism decisions, result inventory, open questions, final audit and project status.
- `01_experimental_constraints/` — experimental observations that constrain theoretical interpretation.
- `02_DFT_CP2K/` — structures, OER energetics and CP2K-derived thermodynamic/electronic-energy records.
- `03_cDFT/` — constrained-DFT charge/spin response and localization analysis.
- `04_VASP_analysis/` — reaction/spin density, Bader, COHP/LOBSTER, PDOS, d-band-center and related electronic-structure analyses.
- `manuscript/` — claim/evidence mapping and manuscript-facing figure-delivery index.
- `archive_20260910/` — reproducibility snapshot and historical records; archive content is not automatically promoted to manuscript evidence.

## Manuscript figure workflow

Each theory figure component should be delivered independently with:

1. publication-quality vector output (`PDF`, `SVG`, and when useful `EPS`);
2. high-resolution raster output (`PNG` and `TIFF`);
3. software-neutral source tables (`CSV`/`TSV`, with spreadsheet source retained where useful);
4. reproducible plotting/processing script;
5. figure note, scientific scope, limitations, and suggested caption.

The collaborator assembling the complete manuscript decides final panel lettering and multi-panel composition. Each theory component should therefore remain useful as a standalone subfigure.

## Current figure-ready theory set

The formal delivery set is indexed in `manuscript/theory_figure_package/FIGURE_DELIVERY_MANIFEST.csv` and currently includes:

- **T01** — three-system OER electronic-energy staircase;
- **C01-C05** — cDFT charge/spin response, spin-channel partition, constrained-state fingerprints and full-state localization evolution;
- **V01** — validated COHP/ICOHP bonding analysis;
- **V02-V03** — reaction-induced charge, magnetization and spin-resolved density maps;
- **V04** — PDOS/frontier-state fingerprints;
- **V05** — Bader net-charge response;
- **V06** — d-band-center presentation options;
- **V07** — neighboring Co-to-Al frontier electronic-boundary analysis;
- **V08** — LOBSTER orbital-population cross-check.

T01 is a historical CP2K **electronic-energy** comparison without a full vibrational correction and must remain labeled `Relative electronic energy (eV)` rather than being silently promoted to a strict 298.15 K Gibbs/CHE series.

The locked mechanistic interpretation is that Al substitution suppresses Co-centered reconstruction during the key *OH -> *O oxidation while enabling stronger O-centered / Co-O-manifold spin-electronic reorganization. Method-specific limitations and unresolved causal questions remain explicit.

## Final audit

The final completed-data audit is:

`00_project_management/FINAL_THEORY_AUDIT_20260917.md`

Its conclusion is that no additional **already-computed high-information dataset** in the repository clearly warrants a new publication figure after the V05/V07/V08/C05 completion pass. Remaining scientific gaps require genuinely new calculations or unavailable raw outputs rather than additional plotting.
