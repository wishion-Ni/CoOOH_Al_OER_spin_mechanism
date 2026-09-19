# COMPUTE MANIFEST

Read-only reconciliation of existing calculations and post-processing roots.

| Family | Verified external namespace | Repository/local derivative | Status |
|---|---|---|---|
| CP2K thermodynamic/OER | `REMOTE-COMPUTE-01:sfs/CoOH/cp2k/thermo_vib_5OH_U100_current_20260704/` | canonical Git workspace `02_DFT_CP2K/` | source namespace verified |
| CP2K/cDFT undoped | `REMOTE-COMPUTE-01:sfs/CoOH/cp2k/thermo_vib_5OH_U100_current_20260704/cdft_charge_spin_undoped_20260816/` | `03_cDFT/` and legacy local mechanism bundle | source namespace verified |
| CP2K/cDFT Al16 | `REMOTE-COMPUTE-01:sfs/CoOH/cp2k/Al16/oer/spin_config_scan_site03_5OH_current_20260714/cdft_charge_spin_20260812/` | `03_cDFT/` | comparison source namespace verified |
| VASP/LOBSTER/PDOS/Bader | `REMOTE-COMPUTE-01:sfs/CoOH/cp2k/Al16/oer/spin_config_scan_site03_5OH_current_20260714/.../electronic_structure_al_contribution_20260818/` | `04_VASP_analysis/` | large source tree; compact packages retained |
| Formal COHP/Bader states | namespace below `REMOTE-COMPUTE-01` ending in `cohp_bader_formal_oh_o_20260822/` | `04_VASP_analysis/electronic_structure_publication_data/` | four-state compact validation recorded |
| Reaction density | namespace below `REMOTE-COMPUTE-01` ending in `reaction_density_oh_to_o_same_geometry_20260823/` | `LOCAL-LEGACY-01:artifacts/reaction_density_final_20260901/` and diff-density package | remote final-directory mismatch retained for review |
| LOBSTER executable | tool installation below `REMOTE-COMPUTE-01` | not copied into Git | installed tool verified |
| Bader executable | tool installation below `REMOTE-COMPUTE-01` | not copied into Git | installed tool verified |

## Audit note

Large source-tree sizes and exact machine-specific resolution were checked locally during reconciliation but are intentionally not required in the public durable-state interface. Exact endpoint/user/home-path resolution remains in machine-local configuration.
