# Missing-data report

No required COHP, ICOHP, LOBSTER quality, structure-mapping or PDOS source was
missing for the four requested states:

- `pristine__OH`
- `pristine__O`
- `Al16__OH`
- `Al16__O`

The full raw COHPCAR, DOSCAR and VASP restart/trajectory files remain on the
authorized server because they are large and are not required for routine
inspection. Their server paths, sizes and SHA256 values are recorded in
`source_manifest.tsv`. Compact server-side extraction was used instead.

The source runs contain non-fatal quality warnings, including Gaussian-smearing
fallback and, for pristine OH, one band-overlap orthonormalization warning.
These are retained in the quality table and provenance rather than omitted.

