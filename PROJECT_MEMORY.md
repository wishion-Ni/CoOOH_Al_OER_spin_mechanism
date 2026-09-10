# CoOOH/Al OER Spin Mechanism Project Memory

## 1. Project objective

The goal of this project is to use first-principles calculations to explain why Al substitution in cobalt oxyhydroxide (CoOOH) facilitates the key OER intermediate conversion (*OH -> *O).

The explanation must connect DFT results with experimental observations:

- Al substitution lowers the energetic barrier/free-energy cost of the *OH -> *O step.
- TAS measurements indicate that pristine CoOOH shows Co-related spectral evolution during this reaction stage, suggesting Co oxidation-state/species evolution or electronic reconstruction.
- After Al substitution, the corresponding Co spectral change is strongly suppressed or absent.
- The first OER step becomes slightly less favorable after Al substitution (~0.2 eV increase), which must also be explained.

A successful mechanism must explain the differential influence of Al substitution on different elementary steps rather than simply stating that Al modifies electronic structure.

## 2. Required computational constraints

Important benchmark results that must be preserved:

- For pristine CoOOH, the OER free-energy diagram should reproduce the expected profile where s2+s3 is approximately 3.2 eV.
- The rate-determining step of pristine CoOOH is s2.
- Al substitution should specifically stabilize the *OH -> *O process.

## 3. Project history

The workflow has been developed through several stages:

### Stage 1: Structural optimization and OER energetics

- CP2K was used for geometry optimization and computational condition validation.
- OER intermediates and free-energy profiles were obtained.
- The resulting energetics are consistent with experimental trends.

### Stage 2: Constrained DFT calculations

- cDFT calculations were performed to investigate charge/spin reorganization during reaction steps.
- The main hypothesis is that pristine CoOOH requires substantial Co-centered electronic/spin reconstruction during *OH -> *O, whereas Al substitution enables an alternative pathway with reduced Co reorganization.

### Stage 3: VASP electronic structure analysis

Using related optimized structures:

- COHP analysis
- Bader charge analysis
- charge-density difference analysis

have been performed or are being processed.

## 4. Central mechanistic hypothesis

The mechanism should establish a causal chain:

Al substitution

-> modified local electronic environment

-> altered charge/spin redistribution pathway during oxygen oxidation

-> reduced Co-centered reconstruction requirement

-> more favorable *OH -> *O conversion

The final interpretation should connect:

- thermodynamics (free-energy changes)
- electronic structure (orbital interactions, bonding, charge transfer)
- spin/oxidation-state evolution (cDFT)
- spectroscopy (TAS Co response)

## 5. Current tasks

The immediate goal is to organize all existing calculations, discussions, and figures into a reproducible research repository suitable for developing a high-impact publication.

Required repository contents:

- calculation inputs and outputs
- analysis scripts
- processed datasets
- figure generation workflow
- mechanism discussion notes
- literature references
- manuscript-oriented figure drafts

## 6. Future figure/storyline direction

The final paper should avoid a simple "Al changes electronic structure" explanation.

The preferred storyline is:

"Al substitution enables an alternative spin-adaptive oxygen oxidation pathway, suppressing Co-centered electronic reconstruction and accelerating the key OER step."

All computational analyses should support this mechanistic narrative.
