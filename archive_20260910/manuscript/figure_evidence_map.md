# Figure Evidence Map

## Purpose

This document maps scientific claims to computational and experimental evidence. It is intended to guide manuscript-level figure design and prevent accumulation of disconnected electronic-structure analyses.

The current goal is not to maximize the number of figures, but to construct a causal chain:

experiment → scientific question → computational evidence → mechanistic conclusion

---

# Central manuscript claim

Al substitution does not simply enhance OER activity through generic electronic structure modification. Instead, it changes the accessible charge/spin reorganization pathway during oxygen oxidation, reducing unfavorable Co-centered reconstruction and facilitating the *OH → *O transformation.

---

# Figure 1: Experimental motivation and OER thermodynamics

## Scientific claim

Al substitution selectively improves the key *OH → *O oxidation step while slightly affecting the initial oxidation step.

## Evidence

### OER free-energy staircase

Datasets:

- pristine CoOOH (black curve)
- Al-neighboring Co active site (green curve)
- Al site control (red curve)

## Interpretation

- Black: establishes pristine benchmark.
- Green: demonstrates that neighboring Co is the relevant modified active site.
- Red: excludes Al itself as the catalytic center.

## Required checks

- pristine s2+s3 ≈ 3.2 eV.
- pristine rate-determining step remains s2.
- Al-neighbor Co gives improved *OH → *O energetics.

---

# Figure 2: Charge/spin reconstruction during *OH → *O

## Scientific claim

The key difference between pristine and Al-substituted systems is not only adsorption energy, but reaction-induced electronic reorganization.

## Evidence

### cDFT analysis

Datasets:

- constrained charge response
- local spin evolution
- Co/O population changes

## Interpretation

Pristine CoOOH:

- strong Co-centered charge/spin response.
- significant electronic reconstruction during oxygen oxidation.

Al-substituted CoOOH:

- suppressed Co-centered response.
- alternative redistribution pathway involving oxygen-related states.

## Experimental connection

Matches TAS observation:

- pristine system shows Co-related spectral evolution.
- Al-substituted system suppresses this response.

---

# Figure 3: Spatial origin of electronic redistribution

## Scientific claim

Al substitution changes where charge and spin redistribution occur during reaction.

## Evidence

Datasets:

- charge density difference
- spin density difference
- reaction-induced density maps

## Interpretation

Use these results to visualize:

- Co-centered reconstruction in pristine system.
- redistributed oxygen/neighboring-site response after Al substitution.

## Limitation

Do not interpret density maps alone as formal oxidation states.

Combine with cDFT/Bader/orbital analysis.

---

# Figure 4: Orbital and bonding origin

## Scientific claim

The altered reaction pathway originates from modified orbital interaction and bonding evolution.

## Evidence

Datasets:

- COHP/LOBSTER
- PDOS
- frontier-state analysis
- d-band/orbital analysis

## Interpretation

Questions to answer:

- How does Al modify Co-O bonding?
- Which orbital interactions stabilize the *O state?
- Why is Co reconstruction energetically unfavorable in pristine CoOOH?

## Caution

Avoid generic statements such as "Al improves covalency" unless directly supported.

---

# Figure 5: Unified mechanism scheme

## Scientific claim

Al substitution enables a spin-adaptive oxygen oxidation pathway.

## Required integration

Combine:

- TAS experimental constraint.
- OER thermodynamics.
- cDFT charge/spin response.
- orbital/bonding analysis.

## Final mechanism wording

Preferred:

"Al substitution redirects the oxygen oxidation pathway by suppressing Co-centered electronic reconstruction and enabling a more favorable charge/spin reorganization route for *OH → *O conversion."

Avoid:

"Al simply changes electronic structure and improves activity."

---

# Data status rules

Each figure component must specify:

- candidate_dataset
- supporting_dataset
- historical_dataset

No dataset should be promoted to final manuscript evidence without checking:

- computational consistency;
- structural consistency;
- method dependence;
- relation to the central mechanism.

---

# Remaining tasks

1. Confirm exact source files for each figure.
2. Verify selected datasets against calculation conditions.
3. Generate manuscript-quality plots only after evidence mapping is complete.
4. Identify any missing calculations required for causal proof.
