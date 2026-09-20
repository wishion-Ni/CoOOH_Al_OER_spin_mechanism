# Rapid delivery validation

This package is a post-processing export. No VASP, LOBSTER, CP2K, Bader, or
cDFT calculation was started for this package.

| Dataset | Status | Evidence |
|---|---|---|
| Latest same-geometry difference density | PASS | 8 Origin CSV maps, 9,600 rows per map |
| Difference-density source slices | PASS | 8 matching publication TSV slices |
| Bare/original PDOS | PASS | spin/orbital selected-site TSV present |
| Bare/original d/p centers | PASS | center, RMS width, weight for both systems; independently reintegrated |
| Formal *OH/*O COHP/ICOHP | PASS | four state curve files, ICOHP summary, quality table |
| Formal *OH/*O PDOS | PASS | four state curve files and site mapping |
| Bare/original COHP | NOT_AVAILABLE_BY_SOURCE_LIMITATION | pCOHP was disabled by insufficient NBANDS; retained COOP is not COHP |

The raw bare-model source snapshot is hash-indexed in
`bare_model/raw_source_manifest.tsv`; it is not duplicated into this compact
package.

The compact package validator is `tools/validate_fast_delivery_package.py`.
The source-specific validators remain authoritative for the synchronized
formal-state COHP/PDOS and difference-density packages.
