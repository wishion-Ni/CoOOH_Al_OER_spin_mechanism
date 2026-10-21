# DATA MANIFEST

Front-door index only. Detailed scientific meaning remains in the native project records and package READMEs.

| Data class | Canonical/project package | Verified external/source namespace | State |
|---|---|---|---|
| T01/OER staircase and CP2K/cDFT compact records | canonical Git workspace `02_DFT_CP2K/`, `03_cDFT/` | `REMOTE-COMPUTE-01:sfs/CoOH/cp2k/thermo_vib_5OH_U100_current_20260704/` and related Al16/undoped trees | packaged; raw source indexed |
| cDFT charge/spin comparison | canonical Git workspace `03_cDFT/`; legacy local mechanism bundle | `REMOTE-COMPUTE-01:sfs/CoOH/cp2k/thermo_vib_5OH_U100_current_20260704/cdft_charge_spin_undoped_20260816/` and Al16 cDFT scan | compact evidence present; do not promote disputed branches |
| Four-state COHP/ICOHP/PDOS | `04_VASP_analysis/electronic_structure_publication_data/` | formal source namespace below `REMOTE-COMPUTE-01`, including `cohp_bader_formal_oh_o_20260822/` and corrected `cohp_oh_o_corrected_20260820/` | package validator recorded PASS, 0 hard errors |
| Publication figure interfaces V01-V04 | `04_VASP_analysis/publication_figure_data/` | derived from compact package and verified source manifests | four-state index complete |
| Difference-density publication assets | `04_VASP_analysis/diff_density_publication_data/` | reaction-density namespace below `REMOTE-COMPUTE-01`, including `reaction_density_oh_to_o_same_geometry_20260823/` | local package present; remote final Al16 mapping requires review |
| Legacy local reaction-density artifact | `LOCAL-LEGACY-01:artifacts/reaction_density_final_20260901/` | copied/derived local artifact; not a raw server tree | large local derivative; provenance conflict retained |
| COHP input artifact | `LOCAL-LEGACY-01:artifacts/cohp_oh_o_inputs_20260824/` | formal four-state extraction | local-only compact input package |
| PDOS input artifact | `LOCAL-LEGACY-01:artifacts/pdos_oh_o_inputs_20260824/` | formal four-state extraction | local-only large derivative |

## Retention rule

Do not upload large raw grids, wavefunctions, charge files, DOSCAR, COHPCAR, or full scratch trees merely to synchronize the project. Record stable logical aliases, relative namespaces, source names, sizes, hashes, mapping, and validation status instead.
