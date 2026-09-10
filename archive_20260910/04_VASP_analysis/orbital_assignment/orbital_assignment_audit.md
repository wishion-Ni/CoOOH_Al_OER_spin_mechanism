# Local-symmetry and orbital-assignment audit

## Scope and validation

The audit uses four completed fixed-geometry VASP datasets and four genuine spin-polarized LOBSTER 5.1.1 reprojections. No VASP SCF or geometry optimization was run. Absolute charge spilling is 0.92-0.94% for spin 1 and 1.24-1.27% for spin 2; projected electron recovery differs from the VASP totals by at most 0.0003 e. This LOBSTER output does not print a separate total-spilling metric, so that quantity is explicitly marked unavailable rather than inferred.

All six nearest Coact-O bonds were included with orbitalWise COHP. The OH systems additionally include the verified active Oads-H204 bond. The fitted local octahedral frames reproduce Oads-Co-Obridge angles of 172.638 degrees for OH and 171.392 degrees for O.

## Hard limitation

OUTCAR does not contain complete spin-resolved 5x5 DFT+U onsite matrices, and PROCAR contains squared global-axis LORBIT=11 projections without phase/cross terms. Therefore exact local-axis d-density matrices, natural d orbitals and arbitrary band-resolved d rotations are unavailable. Global-axis orbitalWise COHP is reported but is not relabeled as exact local dz2/dx2-y2/dpi character.

## Axial versus equatorial majority branches

- pristine_OH UF1 at -0.097 eV: axial fraction 0.524; mixed axial/equatorial antibonding (low confidence).
- pristine_O UF1 at +0.032 eV: axial fraction 0.733; e_parallel* majority candidate (high confidence).
- Al16_OH UF1 at -0.550 eV: axial fraction 0.340; e_perp* majority candidate (medium confidence).
- Al16_O UF1 at -0.441 eV: axial fraction 0.737; e_parallel* majority candidate (high confidence).

UF1 is tested by its full six-bond signature, not by energy alone. `axial_equatorial_fingerprints.tsv` also identifies the strongest equatorial-majority candidates. The periodic features are collective mixed states; they are not counted as isolated one-electron molecular orbitals.
The four previously proposed UF1 energies do not form one uniformly axial branch: pristine OH UF1 is mixed, Al16 OH UF1 is equatorial-dominated, while both O-state UF1 features are axial-dominated. No distinct axial-majority peak can be resolved for Al16 OH in the sampled -2.0 to +0.5 eV window; its reported e_parallel entry is therefore only a low-confidence mixed fallback.

## OH to O correlation

- Pristine UF1: -0.097 to +0.032 eV, delta +0.128 eV, fingerprint similarity 0.885.
- Al16 UF1: -0.550 to -1.105 eV, delta -0.555 eV, fingerprint similarity 0.645.
For Al16, fingerprint matching pairs OH UF1 more closely with O UF2, while O UF1 pairs with OH UF2. This is evidence of strong mixing/reordering, not proof of a literal orbital crossing.

Because band-overlap phases are unavailable, the data support differential shift and mixing but cannot prove a true level crossing rather than avoided crossing.

## Active O-H bond

- pristine_OH: main occupied sigmaOH bonding maximum -5.363 eV; strongest sampled occupied antibonding contribution -0.050 eV.
- Al16_OH: main occupied sigmaOH bonding maximum -5.564 eV; strongest sampled occupied antibonding contribution -0.451 eV.

## Neighbor extension

- pristine_OH: Co-Obridge near-EF signed integral -0.3953; magnetic d-like continuation.
- pristine_O: Co-Obridge near-EF signed integral -0.3919; magnetic d-like continuation.
- Al16_OH: Al-Obridge near-EF signed integral +0.0057; weak nonmagnetic sp continuation.
- Al16_O: Al-Obridge near-EF signed integral +0.0035; weak nonmagnetic sp continuation.

## Interpretation boundary

The audit distinguishes parent AO/MO bookkeeping from actual periodic DFT spectral peaks. Axial/equatorial assignments use total six-bond COHP and are defensible at the collective-branch level. Exact local irreducible-representation labels remain unavailable where they would require missing phase-resolved local rotations.

## Files

- `local_octahedral_frame.tsv`: fitted axes, bonds, trans pairs and global-to-local matrices.
- `six_CoO_bond_COHP.tsv`: energy-resolved spin COHP for all six Co-O bonds.
- `frontier_orbitalwise_COHP.tsv`: global-basis orbitalWise contributions at all catalog features.
- `axial_equatorial_fingerprints.tsv`: majority branch tests.
- `dpi_manifold_assignment.tsv`: requested t2g/dpi feature audit with explicit symmetry limits.
- `frontier_spatial_span.tsv`: separate atomic and bond profiles across the nine-column diagram.
- `state_correlation_OH_to_O.tsv`: fingerprint-based state matching.
- `absolute_orbital_populations.tsv`: absolute Mulliken and Loewdin populations.
- `active_OH_COHP.tsv` and summary: active H204 bond.
- `empty_state_fingerprints.tsv`: EF to +4 eV parent-like candidates.
- `neighbor_extension.tsv`: neighbor-Co versus Al continuation.
- `parent_orbital_audit.tsv`: final parent/DFT bookkeeping table.
