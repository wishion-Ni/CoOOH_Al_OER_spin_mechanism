# figure_ready_snapshot

## Purpose

This file provides a compact entry point for downstream manuscript figure selection from the validated theory-data interfaces and publication-ready figure packages.

It is not a final manuscript figure and does not replace scientific interpretation in the manuscript text.

## Current validated status

Compact plotting/data interfaces are available under:

```text
04_VASP_analysis/publication_figure_data/
04_VASP_analysis/electronic_structure_publication_figures/
04_VASP_analysis/diff_density_publication_data/
```

States:

- `pristine__OH`
- `pristine__O`
- `Al16__OH`
- `Al16__O`

### V01 COHP/ICOHP

- COHP curves: 9624 rows
- ICOHP summary: 12 rows
- distance-validated bond mapping
- publication figures available
- validator: PASS

### V02 reaction-induced density

- four density classes
- 19200 slice rows per class
- local sphere integration: 24 rows
- 0.8 Å sphere definition
- paired and single-panel publication figures available
- validator: PASS

### V03 spin density

- magnetization, spin-up and spin-down grids available
- paired and single-panel publication figures available
- state mapping validated

### V04 PDOS/frontier-state fingerprints

- 14660 PDOS rows
- 20 site mappings
- overview, frontier zoom, and orbital-resolved publication figures available
- validator: PASS

### V06 d-band-center presentation options

Publication-facing quantitative interfaces and reproducible plotting are available under:

```text
04_VASP_analysis/electronic_structure_publication_figures/source_data/V06_*
04_VASP_analysis/electronic_structure_publication_figures/plotting/plot_dband_center_options.py
04_VASP_analysis/electronic_structure_publication_figures/notes/V06_dband_center_interpretation_note.md
```

Three collaborator-selectable forms are generated:

1. V06a — absolute occupied active-Co 3d centroid evolution.
2. V06b — compact spin-resolved centroid-shift summary.
3. V06c — conventional semi-elliptic d-band-model schematic using exact centroid positions but symbolic DOS width.

Important boundary: the VASP states are aligned to their own Fermi levels; no vacuum-aligned interpretation of the pristine-versus-Al absolute offset is permitted.

## Recommended figure-selection logic

### Core manuscript evidence

1. T01 OER staircase comparison.
2. cDFT charge/spin response.
3. Reaction-induced magnetization/charge redistribution.
4. Selected COHP/ICOHP bonding evidence.
5. One concise PDOS/frontier-state panel where needed.

### Supporting/SI evidence

- spin-up/spin-down density maps;
- full-bond COHP/ICOHP variants;
- orbital-resolved PDOS;
- Bader charge partition;
- V06 d-band-center options.

V06 should be used as a compact spectral-response descriptor rather than as the primary proof of suppressed Co-centered reconstruction.

## Required index files

Use these files as the source of truth:

- `metadata.tsv`
- `state_index.tsv`
- `data_interfaces.tsv`
- `structure_files.tsv`
- `integrity.tsv`
- `MISSING_DATA_REPORT.md`
- `manuscript/theory_figure_package/FIGURE_DELIVERY_MANIFEST.csv`

## Figure philosophy

The current objective is production of standalone manuscript-ready subfigures:

- no infographic-style mechanism posters;
- no final figure arrangement assumptions;
- no conclusion banners inside panels;
- each panel should communicate one scientific result;
- keep scientific source data and plotting scripts beside each figure family.

Export standard:

- PDF
- SVG
- PNG
- TIFF
- EPS where useful
- 600 dpi for raster publication outputs where applicable

The principal theory figure families are now available for collaborator selection; further work should focus on curation and manuscript integration rather than generating redundant derivative plots.
