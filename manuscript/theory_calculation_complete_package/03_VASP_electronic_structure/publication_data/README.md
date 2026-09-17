# Synchronized electronic-structure data

This directory is the compact synchronization package for the four formal
states `pristine__OH`, `pristine__O`, `Al16__OH` and `Al16__O`.

- `mapping/structure_and_bond_mapping.tsv`: geometry-checked atom and bond roles.
- `COHP/source_data/cohp_curves_<state>.tsv`: long-format spin-resolved pCOHP curves, one shard per state.
- `COHP/source_data/icohp_summary.tsv`: spin-resolved and total ICOHP values.
- `COHP/source_data/lobster_quality.tsv`: spilling, basis and warning records.
- `PDOS/source_data/pdos_curves_<state>.tsv`: compact native VASP site/orbital PDOS, one shard per state.
- `PDOS/source_data/pdos_site_mapping.tsv`: PDOS site roles.
- `source_manifest.tsv`: source provenance, sizes and hashes.
- `previews/`: sanity-check plots, not manuscript figures.

Run from the repository root:

`python tools/validate_cohp_pdos_sync.py`

