# Theory Result Inventory

## Purpose

This document indexes theoretical calculation assets for manuscript-material preparation. The project is now in a figure-delivery phase: existing validated calculations are converted into standalone, reproducible figure packages for collaborators.

# 1. OER reaction-energy staircase

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

The archived source identifies this as a historical CP2K electronic-energy comparison without vibrational correction. The manuscript-facing plot is therefore labeled `Relative electronic energy (eV)` and must not be silently relabeled as a strict 298.15 K Gibbs/CHE series.

The three-site staircase already displays both the full pathway and the elementary-step values. Separate T02/T03 derivative plots are intentionally omitted because they do not add enough independent information.

# 2. cDFT / CP2K local charge-spin response

Location: `03_cDFT/OH_to_O_spin_response/`

Manuscript package: `03_cDFT/OH_to_O_spin_response/publication_package/`

Status: **figure_ready_draft**

## C01 — local electron-population response

Definition: `Delta N = N(*O) - N(*OH)`.

Hirshfeld values:
- pristine Coact: +0.219 e;
- Al16 Coact: +0.012 e;
- pristine Oads: -0.464 e;
- Al16 Oads: -0.427 e.

Main message: Al substitution strongly suppresses the Co-centered population response while substantial O-centered oxidation response remains.

## C02 — local spin response

Definition: `Delta m = m(*O) - m(*OH)`.

Hirshfeld values:
- pristine Coact: -0.821 muB;
- Al16 Coact: -0.448 muB;
- pristine Oads: -0.070 muB;
- Al16 Oads: -0.744 muB.

Main message: Al reduces the Co-centered spin response and is accompanied by substantially stronger O-centered spin reorganization.

Partition robustness: Mulliken values are retained and plotted together with Hirshfeld values. The central Co-suppression and O-spin-redistribution trends are consistent across both CP2K population partitions.

Interpretation boundary: the selected *O calculations use a globally lower multiplicity than *OH in both materials. These local differences characterize the selected *OH/*O solutions; they are not independent proof that oxidation spontaneously chooses the lower-spin branch.

The Al16 Oads local spin sign reversal is CP2K partition-robust but not VASP/LOBSTER robust. Main-text wording should emphasize `O-centered spin reorganization` rather than a universal spin reversal.

## C03 — cDFT localization/spin constraint penalties

Status: **supporting_data_ready**

Key observations:
- N-1 Co+adsorbate localization penalties are about 1.5-2.2 eV lower than Co-only constraints across the existing states, supporting an O-rich/covalent hole rather than purely Co-localized oxidation;
- at *O, the valid Co-only M+2 penalty increases from 2.899188 eV in pristine to 4.036604 eV in Al16.

These quantities are cDFT constraint penalties, not CHE reaction free energies or kinetic barriers.

# 3. Reaction-induced density and spin density

Location: `04_VASP_analysis/charge_density_difference/` and related VASP records.

Status: **candidate/supporting_dataset**

Purpose: visualize the spatial redistribution accompanying *OH -> *O. Reaction-induced density is not a Bader map and must not be interpreted directly as formal oxidation state.

# 4. Bonding and orbital analysis

Location: `04_VASP_analysis/`

Includes COHP/LOBSTER, ICOHP, PDOS/frontier-state fingerprints, Bader charge, spin density and reaction density.

Status: **candidate/supporting depending on validation**

# 5. Experimental constraint linked to theory

Pristine CoOOH shows a Co-associated spectroscopic evolution during the relevant oxidation stage, while Al substitution suppresses the corresponding Co response.

The theory package should preserve the direct comparison:

`pristine: stronger Co-centered charge/spin reconstruction`

versus

`Al substituted: suppressed Co response + stronger O-involved accommodation`.

# 6. Figure-production priority

1. T01 — complete.
2. C01/C02 — figure-ready draft.
3. reaction-induced density / spin-density rendering.
4. validated Co-O COHP/ICOHP comparison.
5. PDOS/frontier-state and Bader analyses only where they add independent information.
