# Difference-density publication package

This package contains comparable fixed-*OH-geometry *O minus *OH charge and spin maps for pristine and Al16 CoOOH. The four map folders contain plot-ready TSV slices with x_A, y_A, value, system, transition, map_type, units and plane_label.

The manuscript figure is in `figures/` in PNG/TIFF/PDF/SVG formats. The slice and plotting conventions are recorded in `mapping/slice_definition.tsv`; source sizes and SHA256 values are in `source_manifest.tsv`.

Run `python tools/plot_diff_density_publication.py` to regenerate the figure from the TSV slices.

