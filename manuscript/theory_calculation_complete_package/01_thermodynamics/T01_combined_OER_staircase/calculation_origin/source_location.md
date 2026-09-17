# Calculation Origin

## Local archive records

Primary historical three-site source:

`staging/coooh_al_oer_archive_20260910_v2/05_analysis_scripts/plot_cp2k_historical_three_sites.py`

Generated historical source table:

`staging/coooh_al_oer_archive_20260910_v2/06_figures/supporting/cp2k_historical_undoped_co7_al47_staircase.tsv`

Supporting records:

- `cooh_oer_thermo_data_20260523.json`
- `cooh_oer_thermo_steps_20260523.tsv`
- `cooh_oer_thermo_summary_20260523.md`
- `metadata.md`

## Source calculation locations recorded in the JSON inventory

- Pristine: `/home/ftfan/ncw/sfs/CoOH/cp2k/undoped_001333/oer/sites/site01_surface_Co32/02_O`, with the selected OH restart from `/home/ftfan/ncw/sfs/CoOH/cp2k/undoped_001333/oer/restarts/site01_surface_Co32/01_OH_r3`.
- Al16 active Co adjacent to Al: `/home/ftfan/ncw/sfs/CoOH/cp2k/Al16/oer/restarts/site03_bulk_Co7_adjAl/02_O_r2`, with the selected OH and OOH records from the corresponding `site03_bulk_Co7_adjAl` branch.
- Al16 control Al47: `/home/ftfan/ncw/sfs/CoOH/cp2k/Al16/oer/sites/site02_surface_Al47/02_O`, with the selected OH restart from `restarts/site02_surface_Al47/01_OH_r2` and the OOH record from `site02_surface_Al47/03_OOH`.

The repository archive is the provenance layer for these paths. This T01 package intentionally stores processed table data and metadata only; it does not copy raw calculation outputs.

## Selection rationale

The active comparison needs one pristine reference, one Co site next to Al, and one Al-site control. The final historical comparison is the three-site set in `plot_cp2k_historical_three_sites.py`: undoped Co32, Al16 Co7_adjAl, and Al16 Al47. The later processed thermochemical table contains a different correction and branch history and is not mixed into this T01 figure.

