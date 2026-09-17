# V03 orbital-resolved PDOS interpretation note

## What these plots establish

- V03a resolves the active-Co 3d projection into the five VASP Cartesian d components.
- V03b resolves the adsorbate-O 2p projection into Cartesian px/py/pz components.
- V03c compares the spectral redistribution from *OH to *O after aligning each state's spectrum to its own Fermi level.
- V03d quantifies changes in integrated local PDOS spectral weight in selected frontier-energy windows.
- `V03_frontier_peak_candidates.csv` is an automated local-maximum inventory for inspection; it is **not** a multi-Gaussian fit and individual numerical peaks are not automatically distinct physical quasiparticle states.

## Required interpretation boundaries

1. The labels dxy/dyz/dz2/dxz/dx2-y2 and px/py/pz are the Cartesian projector components supplied by the VASP DOS output. The local Co-O coordination axes are not explicitly rotated here. Therefore do **not** make strict eg/t2g or sigma/pi assignments from these labels alone.
2. V03c is an EF-aligned **spectral difference**, not a charge-density-difference map and not a conserved electron-transfer density.
3. Integrated PDOS spectral weight is not equivalent to Bader/Hirshfeld charge or an exact orbital occupation number.
4. Because the *OH and *O calculations correspond to different electron counts and selected global spin states, the plots describe the electronic structure of the selected states; they do not independently prove the kinetic route by which the system reaches the *O spin branch.
5. Tiny negative projected-DOS values, when present, are retained rather than silently clipped; they should be treated as projection/numerical artifacts unless independently validated.
6. For the mechanism narrative, emphasize robust redistribution between Co-centered and O-centered frontier character. Exact orbital-symmetry claims require an explicit local-axis/orbital analysis.
