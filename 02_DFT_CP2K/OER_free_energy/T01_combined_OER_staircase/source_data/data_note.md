# T01 Data Note

## Definition

`dG_eV` is the cumulative Gibbs free-energy level, in eV, relative to the clean `*` state at U = 0 V. The reaction coordinate is the conventional four-step AEM/CHE sequence:

`* -> *OH -> *O -> *OOH -> O2`

The endpoint is closed to `4.920000 eV` using the archived OER closure convention. The four step increments are obtained from successive differences of the cumulative levels.

## Selected values

| system | step 1 | step 2 | step 3 | step 4 | rate-determining step in source table |
|---|---:|---:|---:|---:|---|
| CoOOH_pristine | 1.199993 | 1.793143 | 1.534211 | 0.392652 | s2 |
| Al16_Co7_adjAl | 2.978921 | 0.968096 | 1.226737 | -0.253754 | s1 |
| Al16_Al47_control | 2.172485 | 0.371060 | 0.822645 | 1.553810 | s1 |

The values are rounded to 6 decimal places in the source CSV. The unrounded cumulative values are retained in the archived JSON/TSV source records.

## Validation

- All rows contain exactly five states with steps 0 through 4.
- Every series starts at 0.000000 eV.
- Every series ends at 4.920000 eV.
- The increments reconstruct each cumulative series within the displayed 1e-6 eV rounding.
- The selected three rows come from one processed CP2K OER table, avoiding cross-branch mixing in the main figure.

## Interpretation boundary

This package archives a comparison dataset and figure materials. It does not rerun CP2K, re-optimize structures, or establish a new thermodynamic correction. The selected Al16 Co7 row is the active Co site adjacent to Al used for the mechanism-focused comparison; Al47 is retained as the Al-related site control. Other historical site rows are documented in `candidate_comparison.md` and excluded from the main figure.
