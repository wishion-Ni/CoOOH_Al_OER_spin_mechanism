# CP2K ligand-field interpretation

## Result

The active Co is best described as a **strongly covalent, spin-polarized Co-O center**. A high-spin-like d6 picture is a useful qualitative starting point, but not a literal integer oxidation-state assignment.

- CP2K local Co moments are 3.20-3.25 muB in *OH and 2.39-2.88 muB in *O, depending on material and partition. These values are compatible with substantial exchange polarization and broadly HS-like behavior, but are smaller than the spin-only 4 muB limit of an ideal localized S=2 center.
- Mulliken Co populations near 16.1-16.3 valence electrons and strongly partition-dependent Hirshfeld charges show that Co-O covalency invalidates a strict ionic d6 count.
- Oxidation changes both Co and O populations and spin; it is therefore safer to draw exchange-split Co-O hybrid manifolds than isolated atomic Co d levels.
- The Al-substituted *O state retains a larger Co moment than pristine *O, consistent with reduced Co-centered spin accommodation in the CP2K model.

## Safe manuscript wording

"The active site is a strongly covalent, high-spin-like Co-O unit with pronounced exchange splitting; formal d6 notation is used only as a ligand-field guide."

Source: `01_cp2k_absolute_populations.tsv` from the four validated CP2K baseline outputs.
