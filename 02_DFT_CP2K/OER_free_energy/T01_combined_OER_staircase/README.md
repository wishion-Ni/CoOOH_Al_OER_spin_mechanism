# T01 Combined OER Staircase

This directory contains provenance, candidate comparison, source data, historical plotting material, and the manuscript-facing publication package for the selected three-site OER staircase.

## Selected systems

| Label | Meaning | Source branch |
|---|---|---|
| `CoOOH_pristine` | pristine CoOOH, active Co32 | `undoped_001333/oer/sites/site01_surface_Co32` |
| `Al16_Co7_adjAl` | Al-substituted CoOOH, neighboring Co7 | `Al16/oer/sites/site03_bulk_Co7_adjAl` |
| `Al16_Al47_control` | Al47 control site | `Al16/oer/sites/site02_surface_Al47` |

## Corrected selected values

| System | * -> *OH | *OH -> *O | *O -> *OOH | *OOH -> O2 |
|---|---:|---:|---:|---:|
| pristine Co32 | 1.199993 | 1.793143 | 1.534211 | 0.392652 |
| Al16 neighboring Co7 | 1.403097 | 1.524802 | 0.871955 | 1.120146 |
| Al16 Al47 control | 2.382189 | -1.011081 | 2.217542 | 1.331350 |

Historical alternative site branches remain in `candidate_comparison.md` for provenance and must not be silently mixed into the selected table.

## Manuscript-facing output

Use `publication_package/`. It contains software-neutral source tables, a publication-size plotting script, publication output targets, figure notes and a suggested caption.

T01 is intentionally the only thermodynamic/electronic-energy panel currently packaged: additional stepwise bar charts or *OH -> *O zoom panels were rejected as redundant because the staircase already displays the same information directly.

## Important interpretation boundary

The source metadata identifies this dataset as the historical CP2K **electronic-energy** comparison without vibrational correction. The publication panel is therefore labeled `Relative electronic energy (eV)`. Do not silently relabel it as a strict 298.15 K Gibbs/CHE profile.
