# CoOOH/Al OER rapid data delivery package

This compact package reuses existing validated outputs only. No VASP, LOBSTER,
CP2K, Bader, or cDFT calculation was started by this export.

## Data groups

- `difference_density_origin/`: eight Origin-ready `x_A,y_A,value` CSV maps.
- `difference_density_source/`: matching publication TSV slices for audit.
- `bare_model/`: original/bare-model PDOS and d/p center-width-weight data.
- `formal_oh_o_cohp/`: valid spin-resolved COHP/ICOHP for pristine and Al16
  in *OH and *O states, with bond mapping and LOBSTER quality.
- `formal_oh_o_pdos/`: existing formal-state PDOS shards and site mapping.

## Interpretation boundaries

The bare/original-model LOBSTER runs did not produce valid pCOHP: pCOHP was
disabled because the available NBANDS were below the reported safe minima.
Their COOP files remain audit data only and are not called COHP or ICOHP.
The formal *OH/*O COHP group is the fastest valid COHP result and is the
appropriate source for the reaction-mechanism comparison.

Bare PDOS/d-center energies are relative to each model's own Fermi level. They
are not vacuum-aligned cross-system energy levels. Difference-density values
are local density fields, not Bader charges.

Run `python tools/validate_fast_delivery_package.py` from the project root.
