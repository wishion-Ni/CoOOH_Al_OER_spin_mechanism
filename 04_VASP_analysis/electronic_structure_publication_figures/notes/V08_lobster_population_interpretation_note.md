# V08 - LOBSTER orbital-population cross-check

## Purpose
Provide an independent VASP/LOBSTER population-analysis cross-check of the CP2K cDFT charge/spin-reorganization picture for the fixed-geometry *OH -> *O comparison.

## V08a: orbital-summed spin-channel response
Mulliken and Loewdin results are shown together to expose population-scheme sensitivity.

Mulliken sums:
- pristine Co 3d: up -0.01 e; down +0.09 e
- Al16 Co 3d: up 0.00 e; down +0.04 e
- pristine Oads 2p: up +0.16 e; down -0.66 e
- Al16 Oads 2p: up +0.22 e; down -0.68 e

The largest spin-selective population redistribution is therefore associated with the adsorbate-O 2p manifold, whereas the summed active-Co 3d response is smaller.

## V08b: orbital-resolved fingerprint
The orbital-resolved panel uses LOBSTER Mulliken populations and global-axis orbital projections. It is retained as a supporting fingerprint only.

## Interpretation boundary
These global-axis orbital labels must not be promoted to exact local ligand-field irreducible representations because the phase/cross terms required for arbitrary local-axis rotations are unavailable. The robust cross-method conclusion is spin-selective Co/O population redistribution, not a method-independent Oads spin-sign reversal.

## Recommended use
V08a: SI or compact cross-method support. V08b: SI / audit-level orbital fingerprint.
