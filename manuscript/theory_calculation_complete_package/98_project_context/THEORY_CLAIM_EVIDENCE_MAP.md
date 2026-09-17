# Theory Claim Evidence Map

## Claim 1 — Al substitution selectively modifies the OER pathway at the neighboring Co site

Primary figure-ready evidence: `02_DFT_CP2K/OER_free_energy/T01_combined_OER_staircase/publication_package/`

T01 compares pristine Co32, Al16 neighboring Co7, and Al16 Al47 control. The pristine-to-Al-Co comparison changes * -> *OH from 1.199993 to 1.403097 eV (+0.203104 eV) while *OH -> *O changes from 1.793143 to 1.524802 eV (-0.268341 eV).

Scope boundary: T01 is the archived historical CP2K electronic-energy comparison without vibrational correction and is labeled `Relative electronic energy (eV)` rather than a strict 298.15 K Gibbs/CHE series.

## Claim 2 — Al substitution suppresses Co-centered electronic reconstruction

Required evidence: cDFT charge response, cDFT spin response, pristine vs Al comparison.

Primary source: `03_cDFT/`

Experimental connection: Co-sensitive spectroscopy shows stronger evolution in pristine CoOOH that is suppressed after Al substitution.

## Claim 3 — Al changes the charge/spin accommodation pathway rather than merely changing net charge

Required evidence: cDFT charge/spin response, reaction-induced density, spin density, and Bader only as supporting partition information.

## Claim 4 — The altered pathway originates from modified Co-O / O-centered bonding and frontier-state interactions

Required evidence: distance-validated COHP/ICOHP, PDOS/frontier-state fingerprints, and orbital/spatial analysis.

## Claim 5 — Al acts as a promoter/control perturbation rather than the direct active center

Primary evidence: the Al47 control pathway included directly in T01 alongside the neighboring-Co pathway.

Interpretation boundary: avoid a universal claim about all possible Al-centered mechanisms beyond the sampled model.

## Current evidence hierarchy

Core: T01 OER pathway comparison; cDFT charge/spin response; reaction-induced electronic/spin redistribution.

Support: validated COHP/ICOHP and orbital fingerprints; PDOS/frontier-state analysis; Bader charge as supporting context.
