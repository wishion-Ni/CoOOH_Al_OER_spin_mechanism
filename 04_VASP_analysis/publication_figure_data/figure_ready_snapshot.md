# figure_ready_snapshot

## Purpose

This file provides a compact entry point for downstream manuscript figure generation from the validated `publication_figure_data` interfaces.

It is not a final manuscript figure and does not replace scientific interpretation in the manuscript text.

## Current validated status

- Compact plotting interfaces are available under:

```text
04_VASP_analysis/publication_figure_data/
```

- States:
  - `pristine__OH`
  - `pristine__O`
  - `Al16__OH`
  - `Al16__O`

- V01 COHP/ICOHP:
  - COHP curves: 9624 rows
  - ICOHP summary: 12 rows
  - validator: PASS

- V02 diff density:
  - Four density classes
  - 19200 slice rows per class
  - local sphere integration: 24 rows
  - 0.8 Å sphere definition
  - validator: PASS

- V03 spin density:
  - magnetization, spin-up and spin-down grids available
  - state mapping validated

- V04 PDOS:
  - 14660 rows
  - 20 site mappings
  - validator: PASS

## Recommended figure production order

### V02: Diff density and local integration

Primary scientific purpose:

Show where oxidation-induced charge redistribution occurs during `*OH -> *O` and how Al substitution changes the response pathway.

Recommended panels:

1. Local sphere integration quantitative comparison.
2. Representative matched diff-density slices for pristine and Al-substituted systems.

Important:

- Keep the 0.8 Å integration definition explicit in caption/method.
- Avoid adding mechanism conclusions directly inside figures.

### V03: Spin density

Primary scientific purpose:

Show redistribution of spin response associated with the oxidation step.

Recommended panels:

1. Spin-density spatial comparison.
2. Local spin summary if available.

### V01: COHP/ICOHP

Primary scientific purpose:

Establish bonding-level origin of the modified oxidation pathway.

Recommended panels:

1. Selected active-site Co-O COHP curves.
2. ICOHP summary of key bonds.

Avoid plotting unnecessary bond families.

### V04: PDOS

Primary scientific purpose:

Provide orbital-character support for the electronic-structure interpretation.

Recommended panels:

1. Active Co d and oxygen p projected DOS.
2. Optional near-Fermi-level zoom.

## Required index files

Use these files as the source of truth:

- `metadata.tsv`
- `state_index.tsv`
- `data_interfaces.tsv`
- `structure_files.tsv`
- `integrity.tsv`
- `MISSING_DATA_REPORT.md`

## Figure philosophy

The current objective is production of standalone manuscript-ready subfigures:

- no infographic-style mechanism posters;
- no final figure arrangement assumptions;
- no conclusion banners inside panels;
- each panel should communicate one scientific result.

Export standard:

- PDF
- SVG
- PNG
- TIFF
- 600 dpi where applicable

Next step:

Read `data_interfaces.tsv` and generate V02, V03, V01 and V04 standalone figure components.
