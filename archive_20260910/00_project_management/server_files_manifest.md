# Server and External File Manifest

This archive does not copy large remote calculation trees blindly. The following locations and categories remain provenance references or require manual retrieval from the authorized server/archive.

## Remote calculation roots referenced in the project

- `/home/ftfan/ncw` is the only authorized remote boundary.
- CoOH roots referenced by the workflow include `thermo_vib_5OH_U100_current_20260704` and `spin_config_scan_site03_5OH_current_20260714/vasp_jacs6c06054_reconstructed_exact_Al16_3x2_20260809/electronic_structure_al_contribution_20260818`.
- Large VASP outputs include WAVECAR, CHGCAR, AECCAR0/AECCAR2 and full DOSCAR files. Selected input structures, processed tables, validation logs and small COHP outputs are archived locally.

## Not uploaded by design

- Full wavefunctions and very large charge-density grids: reproducibility manifest only; too large and not needed for routine inspection.
- Full VASP DOSCAR files: processed PDOS tables are included; raw DOSCAR files remain in the local/source tree manifest.
- Temporary scheduler logs, runtime libraries, cached Python environments and intermediate recovery directories.
- Credentials and secret files, including `.codex/secrets/`.
- Unrelated MoO3, ZnO, Li3Tl and rental-server projects in the same workspace.

## Manual-download / external-literature items

The user-referenced literature PDFs and ZIP files under `E:\xwechat_files\...` and `E:\Subject\...` are outside this workspace and are not copied into the repository. Their expected role is recorded in `07_literature/README.md`; add them only if redistribution rights and a stable source are confirmed.
