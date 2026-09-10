# CP2K-primary mechanism validation, stage 2

## Decisive global-spin finding

All four calculations are UKS and internally satisfy multiplicity = N_alpha - N_beta + 1. In both materials, *OH -> *O removes one electron but also changes the imposed multiplicity by -7:

- pristine: M=175 -> 168, N_alpha/N_beta=867/693 -> 863/696;
- Al16: M=149 -> 142, N_alpha/N_beta=798/650 -> 794/653.

Therefore the global change is Delta N_alpha=-4, Delta N_beta=+3 and Delta magnetization=-7 in both systems. Local alpha-to-beta redistribution is meaningful as a response on the selected lower-spin *O branch, but is not an independent proof that oxidation spontaneously chooses that spin branch.

## Required answers

### A. Is the directly oxidized frontier state alpha or beta in CP2K?

**UNKNOWN from existing CP2K data.** Final-state Delta populations cannot identify the directly removed electron. Existing OT WFN files have no printed canonical frontier eigenvalues, virtual states or atom/orbital projections. VASP/LOBSTER favors spin-down loss, but that does not replace the CP2K answer.

### B. Is it O-rich?

**STRONGLY SUPPORTED for the oxidation response, not yet proven for one CP2K MO.** Oads loses -0.464 e (pristine) and -0.427 e (Al16) by Hirshfeld analysis, and Co+adsorbate N-1 constraints are 1.50-2.21 eV cheaper than Co-only N-1 constraints across the existing *OH/*O/*OOH cases.

### C. Is it bonding, nonbonding or antibonding?

**UNKNOWN in CP2K.** Supporting VASP/LOBSTER classifies the selected spin-2 Oads peak proxy as approximately nonbonding in pristine *OH and weakly antibonding in Al16 *OH. This is not a CP2K orbital assignment.

### D. Does Co undergo a partial high-spin-like -> lower-spin-like orbital relaxation?

**PLAUSIBLE, not established.** Coact alpha decreases, beta increases and local spin falls, more strongly in pristine. However, the *O states were explicitly computed at multiplicity seven lower than *OH, and no local orbital-class projection exists.

### E. Which Co orbital class loses and which gains occupation?

**Not established.** Safe statement: Co alpha population decreases and beta population increases. It is not yet safe to label the loss as eg/sigma-antibonding or the gain as t2g/pi/nonbonding.

### F. Why is this relaxation stronger in pristine than Al?

Pristine Coact changes by Delta N_alpha=-0.301 e, Delta N_beta=+0.520 e and Delta m=-0.821 muB, versus -0.218, +0.230 and -0.448 in Al16. Al also raises the Co-only M+2 penalty from 2.899188 to 4.036604 eV and lacks the neighboring magnetic Co-3d frontier manifold. This supports suppressed Co-centered accommodation with Al, although the exact orbital pathway remains unresolved.

### G. Does CP2K support an antiparallel ligand-hole spin on O in Al-*O?

**Yes, at the atom-partition level.** Al16 Oads changes from +0.336 to -0.408 muB while Coact remains +2.776 muB in *O. The safe phrase is **local antiparallel ligand-hole spin polarization**. No spin-density cube exists, so spatial localization is not directly imaged; VASP/LOBSTER also does not reproduce the sign reversal.

### H. Which exact orbitals and electron arrows are now safe to draw?

Safe:

1. an O-rich/ligand-centered PCET oxidation arrow with the removed spin left unspecified;
2. a dashed, qualified Co alpha-to-beta population-relaxation arrow, stronger in pristine and weaker with Al;
3. an Al-*O O-local-spin arrow antiparallel to positive Co, marked "CP2K population result; method dependent";
4. generic exchange-split covalent Co-O manifolds.

Not safe:

- a definite alpha or beta CP2K oxidation arrow;
- exact eg, t2g, sigma* or pi* labels;
- an integer high-spin -> low-spin transition;
- antiferromagnetic coupling or exchange J;
- a method-independent O spin reversal.

## Action status

The prompt's zero-cost extraction limit was reached. No CP2K, VASP or LOBSTER job was launched. `stage2_07_minimal_cp2k_print_rerun.md` specifies the smallest next calculation requiring explicit approval.
