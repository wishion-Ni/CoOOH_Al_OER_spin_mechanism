# Optional VASP/LOBSTER cross-check (not launched)

Existing WAVECAR and vasprun.xml files remain accessible through symlinks in the validated LOBSTER directories. Existing pair-total spin-resolved COHP already gives:

- pristine *OH spin-2 Oads peak proxy: approximately nonbonding, local mean -COHP = -0.001402 in +/-0.12 eV;
- Al16 *OH spin-2 Oads peak proxy: weakly antibonding, local mean -COHP = -0.030390;
- *OH -> *O bond strengthening Delta(-ICOHP) spin1/spin2: +0.56027/+0.90463 eV pristine and +0.20887/+0.90347 eV Al16.

Validated *OH WAVECAR links:

- pristine: `/home/ftfan/ncw/sfs/CoOH/cp2k/Al16/oer/spin_config_scan_site03_5OH_current_20260714/vasp_jacs6c06054_reconstructed_exact_Al16_3x2_20260809/electronic_structure_al_contribution_20260818/cohp_bader_formal_oh_o_20260822/undoped_control/OH_pair_corrected_nomadelung/WAVECAR` -> `../../../cohp_oh_o_corrected_20260820/undoped_control/OH/WAVECAR`;
- Al16: `/home/ftfan/ncw/sfs/CoOH/cp2k/Al16/oer/spin_config_scan_site03_5OH_current_20260714/vasp_jacs6c06054_reconstructed_exact_Al16_3x2_20260809/electronic_structure_al_contribution_20260818/cohp_bader_formal_oh_o_20260822/Al16_adjacent/OH_nomadelung/WAVECAR` -> `../../../cohp_oh_o_corrected_20260820/Al16_adjacent/OH/WAVECAR`.

An orbital-resolved LOBSTER rerun can be performed without VASP by reusing the existing WAVECAR/vasprun.xml and adding orbitalwise Coact-Oads interactions for Co21-O348 (pristine) and Co16-O348 (Al16). The input should retain:

```text
skipMadelungEnergy
COHPstartEnergy -2.0
COHPendEnergy 0.5
basisSet pbeVaspFit2015
useRecommendedBasisFunctions
gaussianSmearingWidth 0.05
# Add the LOBSTER-5.1.1 orbitalwise form of:
# cohpbetween atom 21 atom 348       (pristine)
# cohpbetween atom 16 atom 348       (Al16)
```

The exact orbitalwise keyword syntax must be validated against the installed LOBSTER 5.1.1 documentation before submission. Global VASP p/d labels still require a bond-axis rotation before sigma/pi assignment.

Observed prior LOBSTER wall time was about 7.5-12 h per case on one n28 node with 8 CPUs because Gaussian k-space integration was used. This is supporting Tier 1.5 work only and was not launched.
