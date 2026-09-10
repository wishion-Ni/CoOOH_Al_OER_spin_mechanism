# Minimal additional calculation request (not executed)

## Unresolved questions

1. Is the chemically redox-active CP2K frontier state alpha or beta, and what are its Oads/Coact/neighbor weights?
2. Is the selected near-EF Co-O feature sigma-like or pi-like in a bond-aligned local coordinate system?
3. Can total pair COHP be decomposed into specific Co d - O p interactions at the frontier feature?

## Why existing data are insufficient

The four CP2K baseline outputs contain populations but no MO eigenvalues or PDOS. VASP PDOS uses global axes, and existing LOBSTER COHP is pair-total rather than orbital-resolved. CP2K and VASP also disagree on the dominant spin channel of Oads electron loss.

## Requested Tier 1 / 1.5 work

- CP2K PDOS/MO post-processing from existing converged restart/WFN files, if those files exist: atom/orbital/spin projections for Coact, Oads, Obridge and neighbor in HOMO-2 to LUMO+0.5 eV. No new SCF.
- Orbital-resolved LOBSTER COHP rerun from existing WAVECAR/vasprun.xml using bond-aligned p-d pair definitions or equivalent local-axis analysis. No VASP rerun and no ionic relaxation.

Expected cost: post-processing only, likely minutes to hours and negligible relative to the completed statics. Expected outputs: CP2K PDOS/MO projection and orbital-resolved p-d COHP. Do not launch without explicit approval and confirmation that existing restart/WFN files are available.
