# Accepted same-source annotations

Eight independent panels are in `single_panel/`, each in 600-dpi PNG/TIFF and PDF/SVG. The contact sheet is only an assembly example. Individual panels have no title, caption, or panel number.

All labels are local sphere integrals of the same downsampled VASP difference fields used for the image. Radius is 0.8 Angstrom for every site and system. These are not Bader charges, full atomic moments, or CP2K/cDFT populations. Do not compare their magnitudes as if the partition methods were identical. Positive electron-number difference means electron gain; all differences are O-at-OH-geometry minus OH.

`sphere_integrals.tsv` supplies unrounded numbers, atom indices, radii 0.6/0.7/0.8 Angstrom, and sampled sphere volumes. Radius sensitivity is provided for inspection, not as an uncertainty estimate. The grid is downsampled; full-grid convergence has not been established for these local integrals. Displayed zero means rounding to three decimals, not exact zero.

`source_hashes.tsv` identifies the local source density files. The parent source manifest records their provenance. Existing parent map TSV files provide the image data.

Re-render from repository tables (no large density files required):

```sh
python tools/plot_diff_density_same_source_preview.py --integrals 04_VASP_analysis/diff_density_publication_data/local_sphere_annotations/sphere_integrals.tsv --output-dir 04_VASP_analysis/diff_density_publication_data/local_sphere_annotations
```

No new electronic-structure calculations were performed. Original unannotated publication panels remain available in the parent figures directory.
