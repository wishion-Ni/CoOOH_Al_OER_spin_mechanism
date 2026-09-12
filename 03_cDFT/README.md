# Constrained DFT analysis

This directory stores cDFT and CP2K population analyses focused on reaction-dependent charge and spin reorganization during `*OH -> *O`.

## Current manuscript-facing package

`OH_to_O_spin_response/publication_package/`

The package currently contains two high-priority standalone subfigures:

- `C01` local electron-population response (`Delta N = N(*O) - N(*OH)`);
- `C02` local spin response (`Delta m = m(*O) - m(*OH)`).

Both figures show Hirshfeld values and overlay Mulliken values to expose population-partition sensitivity.

A supporting cDFT constraint table (`C03_cdft_constraint_penalties.csv`) is also included but is not yet promoted to a standalone main-text figure.

## Mechanistic role

The central manuscript question is whether Al substitution suppresses Co-centered electronic reconstruction and redirects the selected *OH/*O response toward an O-involved accommodation pathway.

## Interpretation boundary

The selected *O calculations use a globally lower multiplicity than *OH in both materials. Therefore the local population differences characterize the selected *OH/*O solutions; they are not independent proof that oxidation spontaneously selects that lower-spin branch.

The Al16 Oads local-spin sign reversal is robust across CP2K Mulliken/Hirshfeld partitions but not across VASP/LOBSTER. Main-text language should emphasize `O-centered spin reorganization`, not a universal method-independent spin reversal.
