# Difference-density provenance

No new VASP, LOBSTER or CP2K calculation was run. The synchronized sources are the completed same-geometry reaction-density outputs under `artifacts/reaction_density_final_20260901/`: charge and magnetization binary maps plus the corresponding *O-at-*OH-geometry POSCAR files and statistics.

The source maps represent `rho(*O@*OH geometry)-rho(*OH@*OH geometry)` and `m(*O@*OH geometry)-m(*OH@*OH geometry)`. Spin-up and spin-down density differences are derived as `0.5*(Delta rho + Delta m)` and `0.5*(Delta rho - Delta m)`, using `m=rho_up-rho_down`. The full 3D fields are downsampled from 420x280x420 to 210x140x210 before the synchronized slice is sampled.

The plotted plane is a common PCA plane through active Co, adsorbate O, bridge O and the neighboring Co/Al. The displayed slice uses 120x80 points, identical orientation and identical color limits for pristine and Al16. Slice values are local densities, not Bader charges. The full-density charge integrals are approximately -1 electron for both systems; the magnetization integrals are recorded in the original statistics files.

Source hashes, exact paths and metadata are recorded in `source_manifest.tsv`.

