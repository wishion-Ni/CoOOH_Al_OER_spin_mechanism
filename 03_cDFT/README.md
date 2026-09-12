# Constrained DFT analysis

This directory stores cDFT and CP2K population analyses focused on reaction-dependent charge and spin reorganization during `*OH -> *O`.

## Current manuscript-facing package

`OH_to_O_spin_response/publication_package/`

The package is organized into four complementary standalone figure materials:

- `C01` charge redistribution: total local electron-population changes at Coact, Oads, Obridge and neighboring Co/Al;
- `C02` local-spin evolution: explicit *OH -> *O local-moment evolution;
- `C03` spin-change partition: Hirshfeld Delta N_alpha / Delta N_beta components for Coact and Oads;
- `C04` constrained-state fingerprints for *O: valid cDFT charge-localization and spin-constraint penalties.

These four materials are intentionally distinct: they answer where charge redistributes, how local moments evolve, which spin channels carry the local response, and what constrained electronic responses cost energetically.

## Mechanistic role

The central manuscript question is whether Al substitution suppresses Co-centered electronic reconstruction and redirects the selected *OH/*O response toward an O-involved accommodation pathway.

## Interpretation boundary

The selected *O calculations use a globally lower multiplicity than *OH in both materials. Therefore the local population differences characterize the selected *OH/*O solutions; they are not independent proof that oxidation spontaneously selects that lower-spin branch.

The Al16 Oads local-spin sign reversal is robust across CP2K Mulliken/Hirshfeld partitions but not across VASP/LOBSTER. Main-text language should emphasize `O-centered spin reorganization`, not a universal method-independent spin reversal.

The C04 values are cDFT localization/spin constraint penalties and must not be described as CHE free energies, kinetic barriers, or applied potentials.
