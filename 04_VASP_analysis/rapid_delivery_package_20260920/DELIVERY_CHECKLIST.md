# Original-model and difference-density delivery checklist

This checklist separates the requested bare/original-model deliverables from
the already validated adsorbate-state COHP/PDOS package.

| Requested item | Status | Delivered evidence |
|---|---|---|
| 1. Bare Al16 and undoped PDOS | COMPLETE | `bare_model/source_data/bare_pdos_selected_sites.tsv`; `bare_model/bare_site_mapping.tsv`; `bare_model/metadata.tsv` |
| 2. Bare Al16 and undoped COHP | IN PROGRESS | Historical source has COOP only and pCOHP was disabled by insufficient NBANDS. Recovery is VASP `111844`, followed by LOBSTER `111845`; no bare ICOHP is promoted yet. |
| 3. Bare d-band inputs | COMPLETE | `bare_model/source_data/bare_d_p_center_width_weight.tsv`: Co d and O p center, width, integrated weight, and model Fermi level for occupied and extended windows. |
| 4. Eight difference-density maps | COMPLETE | `difference_density_origin/*.csv`: 8 Origin-ready maps, each with `x_A,y_A,value` and 9,600 points; rendered panels are under `difference_density_figures/single_panel/`. |

## Scope of the completed items

- Bare PDOS covers the selected active/framework sites needed for the model
  comparison, with spin-resolved orbital channels retained.
- d/p centers use each model's own Fermi level as the zero; the reported
  absolute Fermi energy is provenance data and is not vacuum alignment.
- The eight maps are the same-geometry `*O - *OH` fields for total charge,
  magnetization, spin-up, and spin-down, for undoped and Al16.
- The formal adsorbate-state COHP/PDOS files in
  `formal_oh_o_cohp/` and `formal_oh_o_pdos/` are complete, but they do not
  replace the missing bare-model pCOHP requested in item 2.

## Current exception

Do not use `COOPCAR.lobster` or `ICOOPLIST.lobster` as COHP/ICOHP. The old bare
calculations used NBANDS 1035 (undoped) and 990 (Al16), below the validated
minimums 1075 and 1055. The current high-NBANDS fixed-geometry recovery is not
a relaxation and does not modify the completed datasets.

