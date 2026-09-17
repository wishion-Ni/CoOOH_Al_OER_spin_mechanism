# Four-part cDFT figure-material package

## C01 — Charge redistribution

Definition: `Delta N_total = N(*O) - N(*OH)`.

The figure shows Coact, Oads, Obridge and neighboring Co/Al. Filled circles are Hirshfeld; open diamonds are Mulliken.

Key Hirshfeld values:
- pristine Coact: +0.219 e
- Al16 Coact: +0.012 e
- pristine Oads: -0.464 e
- Al16 Oads: -0.427 e

The central robust trend is strong suppression of the Co-centered population response after Al substitution while substantial O-centered oxidation response remains.

## C02 — Local-spin evolution

Hirshfeld local spin moments are plotted explicitly for both selected states, with open symbols for *OH and filled symbols for *O.

Key values:
- pristine Coact: 3.215 -> 2.394 muB (Delta m = -0.821 muB)
- Al16 Coact: 3.224 -> 2.776 muB (Delta m = -0.448 muB)
- pristine Oads: 0.607 -> 0.537 muB (Delta m = -0.070 muB)
- Al16 Oads: 0.336 -> -0.408 muB (Delta m = -0.744 muB)

This supports reduced Co-centered spin accommodation after Al substitution and stronger O-centered spin reorganization.

## C03 — Spin-change partition

Hirshfeld spin-resolved population changes are plotted separately as Delta N_alpha and Delta N_beta for Coact and Oads.

Representative values:
- pristine Coact: Delta N_alpha = -0.301 e; Delta N_beta = +0.520 e
- Al16 Coact: -0.218 e; +0.230 e
- pristine Oads: -0.267 e; -0.197 e
- Al16 Oads: -0.586 e; +0.159 e

C03 is distinct from C02: C02 shows the resulting local-moment evolution, whereas C03 shows how the alpha/beta populations construct that response.

## C04 — Constrained-state fingerprints for *O

Valid *O cDFT penalties shown:
- Co-only N-1
- Co-only N+1
- Co+adsorbate N-1
- Co+adsorbate N+1
- Co-only spin M+2

The valid Co-only M+2 penalty rises from 2.899188 eV in pristine to 4.036604 eV in Al16, a +1.137416 eV change. Co+adsorbate hole-localization penalties are also substantially lower than Co-only hole-localization penalties, supporting an O-rich/ligand-involved oxidation response.

The rejected Al16 M-2 branch is omitted because of a discontinuous spin branch.

## Interpretation boundary

The selected *O calculations use a globally lower multiplicity than *OH in both materials. C02/C03 therefore characterize local redistribution within the selected *OH/*O solutions and must not be presented as independent proof that oxidation spontaneously selects the lower-spin branch.

The Al16 Oads local-spin sign reversal is robust across CP2K Mulliken/Hirshfeld partitions but not across VASP/LOBSTER. Main-text language should emphasize `O-centered spin reorganization`; the sign reversal is a method-dependent detail.

C04 quantities are cDFT localization/spin constraint penalties. They are not CHE free energies, kinetic barriers, or applied potentials.
