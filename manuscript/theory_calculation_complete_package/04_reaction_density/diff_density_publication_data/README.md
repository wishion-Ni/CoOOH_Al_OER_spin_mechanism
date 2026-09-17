# Difference-density publication package

This package contains comparable fixed-*OH-geometry *O minus *OH charge and spin maps for pristine and Al16 CoOOH. The four map folders contain plot-ready TSV slices with `x_A`, `y_A`, `value`, `system`, `transition`, `map_type`, `units` and `plane_label`.

The final figure assets are independent subfigures, not a composite manuscript figure:

- `figures/subfigures/paired/`: one standalone two-panel figure for each map type, with pristine and Al16 shown at identical orientation and limits;
- `figures/subfigures/single_panel/`: one standalone figure for each system and map type;
- every figure is available as PNG, TIFF, PDF and SVG.

Figures intentionally contain no article title, caption, panel numbering or explanatory footer. They retain only axes, units, color scale, chemically relevant atom labels and key framework bonds so the collaborator can assemble the final manuscript figure.

The slice and plotting conventions are recorded in `mapping/slice_definition.tsv`; source sizes and SHA256 values are in `source_manifest.tsv`.

Regenerate the independent figures with:

```text
python tools/plot_diff_density_subfigures.py --output-dir 04_VASP_analysis/diff_density_publication_data/figures/subfigures
```

