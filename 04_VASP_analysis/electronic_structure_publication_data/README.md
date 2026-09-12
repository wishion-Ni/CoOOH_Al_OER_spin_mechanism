# Electronic-structure publication data staging area

This directory is the canonical synchronization target for compact, validated source data used to prepare publication-quality COHP/ICOHP and PDOS figures.

The detailed extraction task is defined in:

`00_project_management/codex_prompts/SYNC_COHP_PDOS_DATA.md`

Expected structure after synchronization:

```text
04_VASP_analysis/electronic_structure_publication_data/
├── README.md
├── PROVENANCE.md
├── source_manifest.tsv
├── MISSING_DATA_REPORT.md              # only if needed
├── mapping/
│   └── structure_and_bond_mapping.tsv
├── COHP/
│   └── source_data/
│       ├── cohp_curves.tsv
│       ├── icohp_summary.tsv
│       └── lobster_quality.tsv
├── PDOS/
│   └── source_data/
│       ├── pdos_curves.tsv
│       └── pdos_site_mapping.tsv
├── raw_minimal/                        # optional; only small useful source files
└── previews/                           # optional sanity-check plots, not final figures
```

## Scientific constraints

- COHP pairs must be validated against the structure actually used by the corresponding LOBSTER run.
- Earlier historical pair mappings are not automatically trusted.
- Preserve raw COHP sign and also provide `-pCOHP` / `-ICOHP` columns for publication plotting.
- PDOS energies must be aligned to `E_F = 0 eV`.
- Keep spin-resolved DOS values positive in source tables; mirror spin-down only during plotting.
- Do not infer formal oxidation states from PDOS/Bader/COHP alone.
- Do not assign exact `eg/t2g` or other orbital classes unless independently validated in the appropriate local frame.

## Validation

Run from repository root:

```bash
python tools/validate_cohp_pdos_sync.py
```

A passing validator is necessary but not sufficient for manuscript use; pair mapping, projection quality, provenance and physical interpretation must also be reviewed.
