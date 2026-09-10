# CP2K frontier redox orbital

## Stop condition reached

The four final CP2K WFN files exist, but the baseline calculations used orbital transformation (OT). Each output reports the number of molecular orbitals as exactly equal to the occupied-orbital count, and no MO eigenvalues, virtual states, PDOS, LDOS, cube orbitals or atom/orbital projections were printed.

The binary WFN therefore does not provide a zero-calculation route to a **canonical** HOMO/LUMO spectrum or Oads/Coact projected frontier eigenstate. OT orbitals are optimized occupied subspace vectors, not a printed canonical eigenvalue ladder. Obtaining HOMO-2 eV to LUMO+0.5 eV with atom/orbital weights requires a fixed-geometry CP2K restart using diagonalization and added virtual MOs.

Per the prompt, no such job was launched.

## Answer available now

- Directly oxidized CP2K frontier spin: **UNKNOWN**.
- O-rich character of the total oxidation response: **STRONGLY SUPPORTED** by cDFT localization penalties and Oads population loss, but not assigned to one existing CP2K MO.
- Do not infer the removed electron spin from final-state Delta N_alpha/Delta N_beta; those values include ionization, self-consistent rehybridization and a change to a lower fixed multiplicity.
