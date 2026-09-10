# Scientific constraints

## Status labels

Use these labels consistently:

- **Established observation** — directly measured or directly calculated.
- **Supported interpretation** — strongly supported by multiple observations/calculations but not uniquely proven.
- **Working hypothesis** — plausible mechanistic explanation requiring further validation.
- **Open question** — unresolved issue that may affect interpretation.

## OER free-energy constraints

### Established observation

The relevant OER sequence is the conventional four-step AEM/CHE pathway:

1. * + H2O -> *OH + H+ + e-
2. *OH -> *O + H+ + e-
3. *O + H2O -> *OOH + H+ + e-
4. *OOH -> * + O2 + H+ + e-

The mechanistic focus is step 2, *OH -> *O.

Historical CP2K comparison:

- pristine: dG1 ≈ 1.200 eV, dG2 ≈ 1.793 eV
- Al-substituted: dG1 ≈ 1.403 eV, dG2 ≈ 1.525 eV

Therefore:

- step 1 becomes ≈ +0.20 eV less favorable after Al substitution;
- step 2 becomes ≈ -0.27 eV more favorable.

These models/sites are useful for mechanistic trends but should not be mixed with a separate strict final coverage-matched free-energy staircase.

## TAS / transient spectroscopy constraints

### Established observation

During the relevant reaction stage:

- pristine CoOOH exhibits a change in a Co-sensitive spectroscopic species/feature;
- after Al substitution, the corresponding Co response is strongly suppressed or absent.

### Interpretation target

The theory must explain why pristine Co requires a significant electronic/spin reconstruction while the Al-substituted system reduces the Co-centered reconstruction channel.

## cDFT constraints

### Established observation

Pristine *OH -> *O, cDFT/Hirshfeld:

- Oact: ΔN = -0.464 e, Δm = -0.070 μB
- Coact: ΔN = +0.219 e, Δm = -0.821 μB
- Obridge: ΔN ≈ +0.003 e, Δm = -0.242 μB
- Coadj: reaction change is very small

Al-substituted:

- Oact: ΔN = -0.427 e, Δm = -0.744 μB
- Coact: ΔN = +0.012 e, Δm = -0.448 μB
- Obridge: ΔN = +0.040 e, Δm = -0.043 μB
- Al: nearly reaction-inert

Oact spin polarization in the Al case changes sign:

- *OH: m ≈ +0.336 μB
- *O: m ≈ -0.408 μB

Mulliken analysis shows the same sign reversal qualitatively.

## Charge/spin redistribution interpretation target

The mechanism must distinguish:

- **net oxidation** from **spin redistribution**;
- **local charge accumulation/depletion** from **electron transfer trajectories**;
- **global spin change** from **where local spin accommodation occurs**.

Both pristine and Al systems show the same overall multiplicity change pattern in the CP2K bookkeeping; therefore Al should not be described as reducing the total amount of global spin change. Instead, it changes where and how the spin-polarization response is accommodated.

## COHP / bonding constraints

### Established observation

For Coact-Oact during *OH -> *O:

- pristine: Δ(-ICOHP) spin1 ≈ +0.560 eV; spin2 ≈ +0.905 eV
- Al-substituted: spin1 ≈ +0.209 eV; spin2 ≈ +0.903 eV

Thus the Al-sensitive difference is strongly spin-selective rather than a uniform weakening of Co-O rebonding.

For Coact-Obridge:

- pristine shows a small strengthening response in one spin channel;
- Al-substituted largely suppresses/reverses that response.

## Structural constraints

The local motif must remain:

- pristine: Oact-Coact-Obridge-Coadj
- Al-substituted: Oact-Coact-Obridge-Al

Oact is the terminal adsorbate oxygen, not Obridge.

The *OH -> *O transformation removes H from Oact and shortens Coact-Oact; it does not create an O-O bond or an Oact-Obridge bond.

## Prohibited over-interpretations

Do not claim as established:

- integer Co3+ -> Co4+ oxidation;
- Al as the direct redox center;
- Al as a proton relay to an Al-OH species;
- a unique dz2/dxz orbital mechanism;
- an exact emitted-electron spin from cDFT-primary analysis;
- a computed exchange-current or spin-current pathway;
- direct equivalence between ICOHP changes and reaction free-energy lowering;
- method-independent O-spin reversal.