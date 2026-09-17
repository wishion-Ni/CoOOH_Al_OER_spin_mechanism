# COHP / PDOS publication-figure notes

## Dataset status

All curves are generated from the synchronized four-state package and validated geometry mapping.
The COHP panels use only distance-validated pairs from the current structures.

LOBSTER quality in the synchronized records has absolute charge spilling below 2% in both spin
channels for all four states. The pristine *OH run also reports a 1-of-8 k-point orthonormalization
warning; it should be disclosed in the methods/SI and checked against `bandOverlaps.lobster` if a
more quantitative claim depends on fine spectral detail.

## Figure interpretation

- `V01a`: spin-summed -pCOHP; positive values denote bonding contributions and negative values
  antibonding contributions. The main panel deliberately emphasizes Coact-Oads and Coact-Obridge.
- `V01b`: integrated -ICOHP for Coact-Oads. It quantifies the occupied bond-strengthening response
  on going from *OH to *O but is not a reaction free energy or barrier.
- `V01c/V01d`: supplementary all-bond context including neighbor-Obridge. In Al16 the neighbor bond
  is Al-Obridge, so its magnitude should not be compared as though it were the same chemical bond as
  neighboring Co-Obridge in pristine CoOOH.
- `V02a/V02b`: local PDOS only. Coact 3d and O 2p components are summed over their component
  orbitals. Spin-down is mirrored solely for visualization. Do not infer formal oxidation states from
  PDOS peak areas alone.

## Mechanistic boundary

These figures support changes in Co-O covalency and O-rich frontier-state participation. They do not
by themselves establish an exact emitted-electron spin, a unique raw-band correspondence across
structures, an integer high-spin/low-spin transition, or a formal oxidation-state assignment.
