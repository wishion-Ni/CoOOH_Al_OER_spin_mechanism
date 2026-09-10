# T01 Data Note

## Definition

`dG_eV` is the cumulative historical CP2K electronic OER energy level, in eV, relative to the clean `*` state. The reaction coordinate is the conventional four-step AEM/CHE sequence:

`* -> *OH -> *O -> *OOH -> O2`

The endpoint is closed to approximately `4.920000 eV` using the archived OER closure convention. This is the historical CP2K electronic-energy comparison and has no vibrational correction; it must not be relabeled as the later strict 298.15 K CHE series.

## Selected values

| system | step 1 | step 2 | step 3 | step 4 | rate-determining step in source table |
|---|---:|---:|---:|---:|---|
| CoOOH_pristine | 1.199993 | 1.793143 | 1.534211 | 0.392652 | s2 |
| Al16_Co7_adjAl | 1.403097 | 1.524802 | 0.871955 | 1.120146 | not assigned in this historical plot |
| Al16_Al47_control | 2.382189 | -1.011081 | 2.217542 | 1.331350 | not assigned in this historical plot |

The values are rounded to 6 decimal places in the source CSV. The unrounded cumulative values are retained in the archived JSON/TSV source records.

## Validation

- All rows contain exactly five states with steps 0 through 4.
- Every series starts at 0.000000 eV.
- Every series ends at nominally 4.920000 eV (the undoped source sum is 4.919999 eV at displayed precision).
- The increments reconstruct each cumulative series within the displayed 1e-6 eV rounding.
- The selected three rows come from the archived historical three-site CP2K comparison, avoiding cross-branch mixing in the main figure.

## Interpretation boundary

This package archives a comparison dataset and figure materials. It does not rerun CP2K, re-optimize structures, or establish a new thermodynamic correction. The selected Al16 Co7 row is the active Co site adjacent to Al used for the mechanism-focused comparison; Al47 is retained as the Al-related site control. Other historical site rows are documented in `candidate_comparison.md` and excluded from the main figure.

