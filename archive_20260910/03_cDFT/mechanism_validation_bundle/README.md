# Mechanism validation bundle

This bundle implements `chatgpt-request.md` using only existing validated CP2K, VASP, Bader and LOBSTER results. No new electronic-structure calculation was launched.

## Method hierarchy

- CP2K cDFT, Mulliken/Hirshfeld populations and local spin are primary for the charge/spin mechanism.
- VASP PDOS and LOBSTER COHP/populations provide supporting orbital and bond analysis.
- Values from the methods are not averaged. Disagreements are reported explicitly.

## Main supported result

Al substitution suppresses Co-centered charge/spin accommodation in CP2K, removes a neighboring magnetic Co-3d relaxation channel, and reduces the spin1 contribution to Coact-Oads bond strengthening. Oxidation remains O-rich/ligand-hole-like.

## Main limitation

The exact spin label of the removed frontier electron is not method robust: CP2K Al Oads loss is alpha dominated and reverses the local Oads spin sign, while VASP/LOBSTER indicates spin-down O-2p loss without a sign reversal. The safe orbital label is therefore **O-rich spin-polarized Co-O frontier state**.

For the VASP spin-2 Oads peak proxy, the corresponding Coact-Oads COHP is approximately nonbonding in pristine *OH and weakly antibonding in Al16 *OH. This is a selected spin-channel, pair-total COHP classification, not an exact molecular-orbital assignment.

## Start here

1. `mechanism_validation_for_chatgpt.json`
2. `12_mechanism_evidence_matrix.tsv`
3. `13_safe_orbital_diagram.md`
4. `11_O_spin_reversal_audit.md`

## Data provenance

All extracted rows contain source paths. CP2K/VASP structures are related but not strictly identical; fixed-geometry VASP pristine/Al pairs are internally matched. `05_cp2k_frontier_states.png` intentionally documents missing CP2K orbital output instead of fabricating a frontier diagram.
