# Theory Claim Evidence Map

## Purpose

Map possible theoretical statements in the manuscript to the computational evidence available in the repository.

This document is a planning tool and does not replace detailed calculation metadata.

---

# Claim 1

## Al substitution selectively facilitates *OH → *O conversion

Required evidence:

- OER free-energy staircase
- intermediate energetics
- comparison between pristine and Al-containing systems

Primary source:

`02_DFT_CP2K/OER_free_energy/`

---

# Claim 2

## Al substitution suppresses Co-centered electronic reconstruction

Required evidence:

- cDFT charge response
- cDFT spin response
- comparison of pristine and Al systems

Primary source:

`03_cDFT/`

Experimental connection:

TAS observation of reduced Co response after Al substitution.

---

# Claim 3

## Al changes the pathway of charge/spin redistribution rather than simply changing charge density

Required evidence:

- reaction density
- spin density
- cDFT analysis
- careful interpretation of Bader results

Important limitation:

Avoid claiming formal oxidation states only from charge partitioning.

---

# Claim 4

## The altered pathway originates from modified bonding/orbital interactions

Required evidence:

- COHP
- ICOHP
- PDOS
- orbital analysis

Required question:

Which Co-O/O-centered interactions stabilize the *OH → *O transition?

---

# Claim 5

## Al is a promoter rather than the direct active center

Required evidence:

- Al-site control OER calculation
- comparison with neighboring Co active site

Primary source:

OER staircase control calculations.

---

# Current evidence hierarchy

## Core evidence

1. OER energetics
2. cDFT charge/spin response
3. Reaction-induced electronic redistribution

## Mechanistic support

4. COHP/orbital analysis
5. PDOS/d-band analysis
6. Bader charge

The strongest conclusions should be based on the core evidence and supported by secondary analyses.
