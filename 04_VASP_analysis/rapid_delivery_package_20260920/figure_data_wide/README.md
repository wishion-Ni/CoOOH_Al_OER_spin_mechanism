# Origin-ready wide data tables

These files are tabular plotting interfaces. They are intentionally written in wide format: one energy or coordinate row and one physical series per column. CSV files can be dragged into Origin directly; TSV files are provided for software that prefers tab-separated input.

## 1. Full-system PDOS

`01_system_pdos/*_system_wide_pdos.csv` and `.tsv` contain the complete DOSCAR projection for each model/state. The first column is `energy_eV_rel_EF`. Remaining columns use the pattern:

`<element>_<orbital>_<up|down>`

and include `TDOS_up/down`, `<element>_p_total_up/down`, `<element>_d_total_up/down`, and `<element>_total_up/down` where the source DOSCAR provides the corresponding orbitals. These are full-system element sums, not selected-site curves.

`*_metadata.tsv` records the DOSCAR/POSCAR source, model Fermi level, energy convention, and parser details.

## 2. Selected-site PDOS

`02_selected_pdos/bare_selected_sites_wide.csv` is the bare/original-model selected-atom table. Columns follow:

`<element><atom_index>_<orbital>_<up|down>`

This preserves the active Co, Al, O and H selections used in the previous figures. `03_formal_pdos_wide/*_wide.csv` provides the corresponding selected-site and TDOS curves for the four validated formal *OH/*O states.

## 3. COHP

`04_formal_cohp_wide/*_wide.csv` contains one column per validated bond and spin channel. Files ending in `_raw_wide` contain raw pCOHP; files ending in `_minus_wide` contain `-pCOHP`, the usual bonding-positive display convention. COHP is bond-resolved; there is no physically meaningful single “whole-system COHP” column. The four formal states are included. Bare/original-model COHP remains pending because the earlier bare LOBSTER runs did not meet the NBANDS requirement; their COOP output is not relabeled as COHP.

## 4. d/p-center data

`05_d_center_wide/bare_d_p_center_width_weight_wide.csv` is a two-row Origin-ready table for the Al16 and undoped bare models. Columns encode model, selected atom, orbital, energy window, center, width, integrated weight, and Fermi level. Both occupied `-8..0 eV` and extended `-8..+4 eV` windows are retained, with absolute and Fermi-relative centers.

`05_d_center_wide/bare_system_d_p_center_width_weight_wide.csv` and `.tsv` are the corresponding full-system element-projected table. They include all available bare-model `Al-p`, `Co-d`, and `O-p` projections, with the same center, width, integrated-weight, and Fermi-level fields.

## 5. Difference-density data

`06_difference_density_wide/difference_density_all_fields_wide.csv` has one row per grid point and the columns:

`x_A`, `y_A`, `charge_total_Al16`, `charge_total_undoped`, `magnetization_Al16`, `magnetization_undoped`, `spin_down_Al16`, `spin_down_undoped`, `spin_up_Al16`, `spin_up_undoped`.

The four Al16 and four undoped fields are the latest validated reaction-density data products. Values are plotted fields, not Bader charges. Use the same color scale and coordinate convention for paired comparisons.

## Origin use

For a line plot, import a CSV/TSV and select the first column as X. For a 2D density plot, import `x_A`, `y_A` and one field column as XYZ or reshape by the recorded grid dimensions in the corresponding figure-data manifest. No filtering step is required inside Origin.
