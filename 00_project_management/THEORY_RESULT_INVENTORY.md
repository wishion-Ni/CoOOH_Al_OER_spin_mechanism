# Theory Result Inventory

## Purpose

This document provides a high-level index of theoretical calculation assets in the project.

The goal is to identify which datasets can be extracted for manuscript preparation and what scientific question each dataset addresses.

This file does not replace raw data or metadata files. It provides a navigation layer between scientific claims and computational evidence.

---

# 1. OER thermodynamics

## Dataset

OER free-energy staircase

Location:

`02_DFT_CP2K/OER_free_energy/`

Status:

candidate_dataset

Scientific purpose:

Explain how Al substitution modifies OER energetics.

Key datasets:

### Pristine CoOOH

Representation:
black curve

Role:
pristine benchmark.

Required interpretation:

- s2+s3 approximately 3.2 eV
- s2 is the rate-determining step

### Al-neighboring Co site

Representation:
green curve

Role:
main Al-substituted active-site comparison.

Purpose:
show that Al modifies neighboring Co activity.

### Al site

Representation:
red curve

Role:
control calculation.

Purpose:
show that Al itself is not the active OER center.

---

# 2. cDFT charge/spin response

Location:

`03_cDFT/`

Status:

candidate_dataset

Scientific purpose:

Explain the electronic reconstruction difference observed experimentally.

Main question:

Why does pristine CoOOH show Co-related TAS evolution while Al-substituted CoOOH does not?

Key evidence:

Pristine CoOOH:

- stronger Co-centered charge redistribution
- stronger spin reorganization

Al substituted system:

- suppressed Co response
- alternative charge/spin redistribution pathway

Important limitation:

cDFT describes constrained charge/spin response and should not be interpreted alone as an absolute oxidation-state assignment.

---

# 3. Charge density and spin density analysis

Location:

`04_VASP_analysis/charge_density_difference/`

Status:

candidate/supporting_dataset

Scientific purpose:

Visualize spatial redistribution associated with reaction intermediates.

Possible manuscript use:

Support the statement that Al substitution changes the spatial pattern of electronic reconstruction.

Limitations:

Do not equate density difference directly with Bader charge or formal oxidation state.

---

# 4. Bonding and orbital analysis

Location:

`04_VASP_analysis/`

Includes:

- COHP/LOBSTER
- ICOHP
- PDOS
- d-band center
- orbital analysis

Status:

candidate/supporting depending on validation.

Scientific purpose:

Identify the electronic origin of the altered OER pathway.

Required interpretation:

The analysis should explain why *OH → *O becomes energetically favorable, rather than only describing electronic structure changes.

---

# 5. Experimental constraints linked to theory

Location:

`01_experimental_constraints/`

## TAS

Scientific role:

Constraint for theoretical interpretation.

Observation:

Pristine Co system shows Co-associated evolution, while Al substitution suppresses this response.

Theory requirement:

Explain suppression of Co-centered reconstruction.

---

# 6. Recommended extraction order for manuscript preparation

1. OER staircase
2. cDFT charge/spin response
3. reaction density and spin density
4. COHP/orbital analysis
5. Supporting charge analyses

The final mechanism should integrate these datasets rather than present isolated electronic-structure observations.
