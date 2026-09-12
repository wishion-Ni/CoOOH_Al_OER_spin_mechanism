# VASP electronic structure analysis

Store COHP, Bader charge, charge-density difference, DOS and orbital analysis here.

Results should be labeled as candidate datasets unless fully validated.

## Publication-source synchronization

The canonical staging area for compact COHP/ICOHP and PDOS source data is:

`04_VASP_analysis/electronic_structure_publication_data/`

The Codex synchronization task is defined in:

`00_project_management/codex_prompts/SYNC_COHP_PDOS_DATA.md`

After synchronization, run:

```bash
python tools/validate_cohp_pdos_sync.py
```

Do not promote historical COHP pair IDs into manuscript evidence without structure/distance re-validation. PDOS comparisons should use state/site fingerprinting rather than raw band-index matching.
