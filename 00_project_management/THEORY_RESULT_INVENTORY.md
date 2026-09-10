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

# 2. cDFT charge/spin response

Location: `03_cDFT/`

Status: **candidate_dataset; next figure-production priority**

Purpose: explain why pristine CoOOH shows stronger Co-centered charge/spin reconstruction during *OH -> *O whereas Al substitution suppresses that Co response and redirects the response toward an alternative Co-O/O-involved accommodation pathway.

# 3. Reaction-induced density and spin density

Location: `04_VASP_analysis/charge_density_difference/` and related VASP records.

Status: **candidate/supporting_dataset**

Purpose: visualize the spatial redistribution accompanying *OH -> *O. Reaction-induced density is not a Bader map and must not be interpreted directly as formal oxidation state.

# 4. Bonding and orbital analysis

Location: `04_VASP_analysis/`

Includes COHP/LOBSTER, ICOHP, PDOS/frontier-state fingerprints, Bader charge, spin density and reaction density.

Status: **candidate/supporting depending on validation**

# 5. Figure-production priority

1. T01 — complete.
2. cDFT active-Co charge response.
3. cDFT active-Co / adsorbate-O spin response.
4. validated Co-O COHP/ICOHP comparison.
5. reaction-induced density / spin-density rendering.
6. PDOS/frontier-state and Bader analyses where they add independent evidence.
