# cDFT *OH -> *O publication package — four-part structure

This package organizes the existing CP2K/cDFT evidence into four standalone manuscript subfigure materials with distinct physical content.

## Figure set

- **C01 — Charge redistribution**: total local electron-population change, ΔN = N(*O) − N(*OH), for Coact, Oads, Obridge and neighboring Co/Al. Hirshfeld and Mulliken are both shown to expose partition sensitivity.
- **C02 — Local-spin evolution**: local spin moments for *OH and *O, with the strongest mechanistic changes emphasized at Coact and Oads.
- **C03 — Spin-change partition**: Hirshfeld ΔNα and ΔNβ for Coact and Oads, resolving local spin changes into spin-channel population redistribution.
- **C04 — Constrained-state fingerprints for *O**: valid *O cDFT localization/spin constraint penalties for Co-only N±1, Co+adsorbate N±1, and Co-only M+2 branches.

## Interpretation hierarchy

Together the four panels support the sequence:

`where charge redistributes -> how local moments evolve -> which spin channels carry the change -> energetic fingerprints of alternative constrained responses`

The safest mechanistic conclusion is that Al substitution suppresses Co-centered electronic/spin reconstruction and redirects the selected *OH -> *O response toward a more oxygen-involved pathway.

## Critical limitations

1. The selected *O calculations use a lower imposed total multiplicity than *OH in both materials. C02/C03 therefore characterize redistribution within the selected electronic solutions; they do not independently prove that oxidation spontaneously selects the lower-spin branch.
2. The Al16 Oads local-spin sign reversal is robust within CP2K across Hirshfeld/Mulliken partitions but is not reproduced by VASP/LOBSTER. Main-text wording should emphasize **O-centered spin reorganization**, not a method-independent spin reversal.
3. C04 values are **cDFT constraint penalties**. They are not CHE reaction free energies, kinetic barriers, or applied potentials.
4. The rejected Al16 M−2 branch is excluded from C04 because of a discontinuous spin branch.

## Source provenance

Primary archived sources:

- `archive_20260910/03_cDFT/mechanism_validation_bundle/01_cp2k_absolute_populations.tsv`
- `archive_20260910/03_cDFT/mechanism_validation_bundle/03_cp2k_spin_resolved_changes.tsv`
- `archive_20260910/03_cDFT/mechanism_validation_bundle/04_cp2k_cdft_constraints.tsv`
- `archive_20260910/03_cDFT/mechanism_validation_stage2/mechanism_stage2_for_chatgpt.md`
- `archive_20260910/03_cDFT/mechanism_validation_stage2/stage2_04_Co_spin_state_relaxation.tsv`

## Deliverables

- `source_data/`: software-neutral CSV tables.
- `plotting/plot_cdft_four_part.py`: reproducible plotting script.
- `figures/`: publication-sized independent subfigure exports.
- `notes/`: interpretation boundaries and suggested captions.

The script regenerates PNG, TIFF, PDF, SVG and EPS outputs. To avoid unnecessary repository growth, TIFF files need not be versioned if the script and source data are retained.
