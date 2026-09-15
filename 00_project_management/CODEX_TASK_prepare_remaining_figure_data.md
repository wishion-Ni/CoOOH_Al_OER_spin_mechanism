# Codex task: prepare remaining publication figure data

## Objective

The project is now entering the manuscript figure component preparation stage. Do not create infographic-style combined figures. Prepare independent publication-quality figure components that can be assembled later by collaborators.

The required output principle:

- each panel should be independently usable;
- raw/processed data must be traceable;
- plotting scripts and metadata must be included;
- suggested figure combinations can be provided only as previews.

## First inspect existing data

Before generating anything:

1. inspect existing `publication_package` directories;
2. inspect existing COHP/PDOS/cDFT/diff-density exports;
3. avoid duplicating already validated results.

## Priority 1: V02 diff density completion

Check:

`04_VASP_analysis/diff_density_publication_data/`

Ensure:

- pristine and Al-substituted comparisons are available;
- *OH -> *O state mapping is explicit;
- structure files or atom coordinate references are available;
- local sphere integration tables are exported in machine-readable format.

Preferred table:

`system,state,site_label,species,value,unit,notes`

## Priority 2: V03 spin density package

Prepare a publication package for spin-density visualization.

Required:

- pristine-*OH;
- pristine-*O;
- Al-*OH;
- Al-*O.

Export:

- volumetric data if available;
- structure coordinates;
- isovalue/color convention;
- local spin integration table if possible.

Preferred table:

`system,state,site_label,species,delta_m,unit,notes`

## Priority 3: V01 COHP/ICOHP package

Prepare:

- COHP curves;
- ICOHP summary;
- active Co-O bond assignment.

Required metadata:

`system,state,bond_label,atom1,atom2,bond_length_A,icohp_eV`

COHP energy axis should be aligned to EF=0.

## Priority 4: V04 PDOS package

Prepare only if not already available.

Required projections:

- active Co d states;
- adsorbate O p states;
- neighboring O p states;
- relevant Al contribution if meaningful.

Export CSV with EF aligned to zero.

## Output rules

For every completed component include:

- data tables;
- source file list;
- plotting script;
- README describing physical meaning and limitations.

Do not:

- create large explanatory posters;
- add conclusions directly onto figures;
- replace data export with screenshots.

The next stage will use these files to generate manuscript-style subfigures.
