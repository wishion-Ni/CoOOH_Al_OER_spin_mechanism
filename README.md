# CoOOH_Al_OER_spin_mechanism

Repository for the theoretical/computational component of the CoOOH/Al OER mechanism project. The current objective is to convert validated existing calculations into **standalone manuscript-ready theory figure components** that can be handed to collaborators for final paper assembly.

## Repository map

- `00_project_management/` — mechanism decisions, result inventory, open questions and project status.
- `01_experimental_constraints/` — experimental observations that constrain theoretical interpretation.
- `02_DFT_CP2K/` — structures, OER energetics and CP2K-derived thermodynamic/electronic-energy records.
- `03_cDFT/` — constrained-DFT charge/spin response analysis.
- `04_VASP_analysis/` — reaction density, spin density, Bader, COHP/LOBSTER, PDOS and related electronic-structure analyses.
- `manuscript/` — claim/evidence mapping and manuscript-facing figure-delivery index.
- `archive_20260910/` — reproducibility snapshot and historical records; archive content is not automatically promoted to manuscript evidence.

## Manuscript figure workflow

Each theory figure component should be delivered independently with:

1. publication-quality vector output (`PDF`, `SVG`, and when useful `EPS`);
2. high-resolution raster output (`PNG` and `TIFF`);
3. software-neutral source tables (`CSV`, with spreadsheet source retained where available);
4. reproducible plotting/processing script;
5. figure note, scientific scope, limitations, and suggested caption.

The collaborator assembling the complete manuscript decides the final panel lettering and multi-panel composition. A theory component should therefore remain useful as a standalone subfigure.

## Current figure-ready result

`T01` — three-system OER staircase comparison:

`02_DFT_CP2K/OER_free_energy/T01_combined_OER_staircase/publication_package/`

The selected systems are pristine Co32, Al16 neighboring Co7, and the Al16 Al47 control site. `T01` contains the full thermodynamic/electronic-energy comparison; separate derivative T02/T03 plots are intentionally omitted because they add little independent information.
