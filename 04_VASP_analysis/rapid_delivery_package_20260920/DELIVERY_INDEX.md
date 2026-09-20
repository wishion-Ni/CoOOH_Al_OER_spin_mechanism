# Rapid electronic-structure delivery package

This directory contains the currently validated, already-computed results for
the CoOOH/Al OER comparison. It is a data delivery package, not a new
calculation campaign.

## Included

- `formal_oh_o_cohp/`: spin-resolved COHP curves, ICOHP summaries, quality
  metrics, and geometry-checked bond mappings for pristine/Al16 in *OH and *O.
- `formal_oh_o_pdos/`: matching formal-state PDOS curves and site mapping.
- `bare_model/`: original-model PDOS and d/p center, width, and weight data.
- `difference_density_origin/`: eight Origin-ready `x_A,y_A,value` CSV maps:
  total charge, magnetization, spin-up, and spin-down for undoped and Al16.
- `difference_density_source/`: matching audit TSV slices.
- `preview_figures/`: quick-look COHP, PDOS, d-center, and orbital-resolved
  PDOS previews. The underlying TSV files remain the authoritative source.

The publication-quality eight difference-density panels in all available
formats remain under
`../diff_density_publication_data/local_sphere_annotations/single_panel/`.

## Validation

The package was independently checked before synchronization:

- rapid delivery package: PASS, 0 hard errors;
- COHP/PDOS synchronization: PASS;
- difference-density synchronization: PASS;
- Origin maps: 8 maps, 9,600 points each;
- formal COHP: 4 states, all quality records retained;
- formal PDOS: 4 states, site mapping retained.

## Explicit limitation

The bare/original-model pCOHP is not included as a completed result. The
historical bare calculation produced COOP only and had insufficient NBANDS for
the safe LOBSTER projection. A separate fixed-geometry high-NBANDS recovery is
running remotely; its output must pass VASP and LOBSTER quality checks before
it is promoted into this package.

