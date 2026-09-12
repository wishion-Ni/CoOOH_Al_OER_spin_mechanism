# cDFT *OH -> *O manuscript figure package

This package promotes the most useful existing CP2K population analysis into standalone manuscript-ready theory subfigures.

- `C01_local_electron_population_response`: active-Co and adsorbate-O electron-population response.
- `C02_local_spin_response`: active-Co and adsorbate-O local-spin response.
- `C03_cdft_constraint_penalties.csv`: supporting cDFT localization/spin penalty table; not yet promoted to a standalone main-text figure.

Outputs are sized as individual manuscript subfigures and include vector/raster formats plus software-neutral source data.

## Scientific scope

C01/C02 compare the selected *OH and *O CP2K solutions. They are intended to test whether Al substitution redistributes the local electronic response away from the active Co and toward an O-involved pathway.

## Important interpretation boundary

The selected *O calculations use a globally lower multiplicity than *OH in both materials. Therefore these plots characterize local redistribution within the selected *OH/*O states and must not be presented as independent proof that oxidation spontaneously selects the lower-spin branch.

The CP2K Oads local-spin sign reversal in Al16 is robust across Mulliken/Hirshfeld partitions but is not reproduced by VASP/LOBSTER. Main-text wording should emphasize `O-centered spin reorganization`; the sign reversal is a method-dependent detail.

cDFT constraint penalties are localization/spin penalties, not CHE free energies, kinetic barriers, or applied potentials.
