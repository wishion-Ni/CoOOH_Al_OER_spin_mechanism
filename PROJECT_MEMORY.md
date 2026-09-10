# CoOOH/Al OER Spin Mechanism Project Memory

## 1. Project objective

Use first-principles calculations to explain why Al substitution changes the key OER intermediate conversion in CoOOH, while connecting the calculation directly to the experimentally observed suppression of a Co-sensitive electronic response after Al substitution.

The explanation must account for the differential step response rather than simply state that Al changes electronic structure.

## 2. Locked mechanistic constraints

- The first OER step becomes slightly less favorable after Al substitution (about +0.2 eV in the selected T01 electronic-energy comparison).
- The *OH -> *O step becomes more favorable in the selected neighboring-Co comparison.
- Pristine CoOOH shows stronger Co-centered charge/spin reconstruction during the relevant oxidation stage.
- Al substitution suppresses that Co-centered response and enables a different Co-O/O-involved spin/electronic accommodation pathway.
- The mechanism must explain why this alternative pathway is favored after Al substitution and why pristine CoOOH does not simply access the same response.

## 3. Current manuscript-material phase

The project is now converting existing validated results into standalone manuscript-ready theory figure components for collaborators. Each figure component should include source CSV data, a reproducible script, vector and high-resolution raster outputs, a scientific note, limitations, and a suggested caption. Final multi-panel composition and panel lettering are left to manuscript collaborators.

## 4. Completed figure component

### T01 — three-system OER staircase

Path:

`02_DFT_CP2K/OER_free_energy/T01_combined_OER_staircase/publication_package/`

Selected step energies (eV):

- pristine Co32: 1.199993, 1.793143, 1.534211, 0.392652;
- Al16 neighboring Co7: 1.403097, 1.524802, 0.871955, 1.120146;
- Al16 Al47 control: 2.382189, -1.011081, 2.217542, 1.331350.

T01 already contains the complete pathway and step annotations. Separate T02/T03 derivative plots are intentionally omitted because they add little independent information.

Important labeling boundary: the archived source identifies T01 as the historical CP2K electronic-energy comparison without vibrational correction, so the manuscript-facing panel is labeled `Relative electronic energy (eV)` rather than strict Gibbs free energy.

## 5. Next figure-production priorities

1. cDFT active-Co charge response;
2. cDFT active-Co and adsorbate-O spin response;
3. validated Co-O COHP/ICOHP;
4. reaction-induced density/spin-density renderings;
5. PDOS/frontier-state and Bader supporting panels only where they add independent evidence.

## 6. Preferred storyline

Al substitution should be presented as modifying the local electronic/spin accommodation landscape of the neighboring Co-O unit. The high-value mechanism is not a generic descriptor shift but a reaction-dependent redistribution pathway that reduces the Co-centered reconstruction requirement and is consistent with the experimentally suppressed Co-sensitive response.
