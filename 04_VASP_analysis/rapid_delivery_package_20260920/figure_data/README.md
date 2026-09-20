# Direct plotting data

These are the actual data files for plotting, not only documentation. Origin
can import the CSV files directly; the matching TSV files are retained for
tabular workflows.

## Directories

- `01_bare_model_pdos/`: spin-resolved selected-site PDOS for bare Al16 and
  undoped models. Columns include relative energy, spin, s/p/d channels,
  `p_total`, and `d_total`.
- `02_bare_model_d_center/`: Co d and O p center, width, integrated weight,
  and Fermi-level records for the occupied and extended windows.
- `03_formal_cohp/`: valid spin-resolved *OH/*O COHP curves, ICOHP summary,
  LOBSTER quality, and validated bond mapping. These are adsorbate-state data,
  not bare-model COHP.
- `04_formal_pdos/`: valid spin-resolved *OH/*O PDOS curves and site mapping.
- `05_difference_density/`: eight same-geometry `*O-*OH` maps with exactly
  `x_A,y_A,value` columns: total charge, magnetization, spin-up, and spin-down
  for undoped and Al16.

`figure_data_manifest.tsv` lists every plotting file and row count.

## Missing item

Bare/original-model pCOHP is not present because the historical LOBSTER runs
only produced COOP at insufficient NBANDS. The fixed-geometry recovery is still
running as jobs 111844 and 111845. No COOP file is relabeled as COHP.

