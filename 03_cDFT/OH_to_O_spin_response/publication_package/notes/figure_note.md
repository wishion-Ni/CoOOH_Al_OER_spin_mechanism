# C01/C02 cDFT local-response figure package

## C01 — local electron-population response

Definition: `Delta N = N(*O) - N(*OH)`.

Hirshfeld values:
- pristine Coact: +0.219 e
- Al16 Coact: +0.012 e
- pristine Oads: -0.464 e
- Al16 Oads: -0.427 e

The Co-centered population response is strongly suppressed after Al substitution, whereas substantial O-centered oxidation response remains.

## C02 — local spin response

Definition: `Delta m = m(*O) - m(*OH)`.

Hirshfeld values:
- pristine Coact: -0.821 muB
- Al16 Coact: -0.448 muB
- pristine Oads: -0.070 muB
- Al16 Oads: -0.744 muB

This supports reduced Co-centered spin accommodation after Al substitution and stronger O-centered spin reorganization.

## Partition robustness

Filled circles show Hirshfeld values; open diamonds show Mulliken values. The central Co-suppression and O-spin-redistribution trends are consistent across the two CP2K population partitions.

## Interpretation boundary

The selected *O calculations use a globally lower multiplicity than *OH in both materials. C01/C02 therefore describe local redistribution within the selected *OH/*O solutions and must not be presented as independent proof that oxidation spontaneously selects the lower-spin branch.

The Al16 Oads local spin sign reversal is robust across CP2K Mulliken/Hirshfeld partitions but not across VASP/LOBSTER. Main-text wording should emphasize `O-centered spin reorganization`; the local sign reversal is a method-dependent detail.

## Provenance

Extracted from:
- `archive_20260910/03_cDFT/mechanism_validation_bundle/01_cp2k_absolute_populations.tsv`
- `archive_20260910/03_cDFT/mechanism_validation_bundle/03_cp2k_spin_resolved_changes.tsv`
- `archive_20260910/03_cDFT/mechanism_validation_stage2/mechanism_stage2_for_chatgpt.md`
