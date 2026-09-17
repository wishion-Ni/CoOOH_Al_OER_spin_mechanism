# figure_curve_snapshot

Compact single-entry index for manuscript figure generation from the validated electronic-structure package. This file does **not** replace the original COHP/PDOS tables; it records the exact validated sources and the key summary values needed to resolve figure inputs reliably.

## Scope

Systems/states:

- `pristine__OH`
- `pristine__O`
- `Al16__OH`
- `Al16__O`

Primary data roots:

```text
04_VASP_analysis/electronic_structure_publication_data/COHP/source_data/
04_VASP_analysis/electronic_structure_publication_data/PDOS/source_data/
```

All values below are copied from the validated repository interfaces; no values are inferred or fabricated.

---

## V01 — COHP / ICOHP

### Real COHP curve files

| system | state | source file |
|---|---|---|
| pristine | *OH | `COHP/source_data/cohp_curves_pristine_OH.tsv` |
| pristine | *O | `COHP/source_data/cohp_curves_pristine_O.tsv` |
| Al16 | *OH | `COHP/source_data/cohp_curves_Al16_OH.tsv` |
| Al16 | *O | `COHP/source_data/cohp_curves_Al16_O.tsv` |

### Validated ICOHP summary

The canonical table remains:

```text
COHP/source_data/icohp_summary.tsv
```

Key values (`-ICOHP_total`, eV; larger positive value = stronger integrated bonding magnitude under the present sign convention):

| system | state | pair role | distance (Å) | ICOHP total (eV) | -ICOHP total (eV) |
|---|---|---|---:|---:|---:|
| pristine | *OH | Coact–Obridge | 2.069958 | -1.35877 | 1.35877 |
| pristine | *OH | neighbor–Obridge | 2.112332 | -1.16631 | 1.16631 |
| pristine | *OH | Coact–Oads | 1.875883 | -1.92767 | 1.92767 |
| pristine | *O | Coact–Obridge | 2.069958 | -1.42904 | 1.42904 |
| pristine | *O | neighbor–Obridge | 2.112332 | -1.17069 | 1.17069 |
| pristine | *O | Coact–Oads | 1.743233 | -3.39257 | 3.39257 |
| Al16 | *OH | Coact–Obridge | 2.069958 | -1.21466 | 1.21466 |
| Al16 | *OH | neighbor–Obridge | 2.112332 | -3.58888 | 3.58888 |
| Al16 | *OH | Coact–Oads | 1.875883 | -1.93011 | 1.93011 |
| Al16 | *O | Coact–Obridge | 2.069958 | -1.17984 | 1.17984 |
| Al16 | *O | neighbor–Obridge | 2.112332 | -3.59615 | 3.59615 |
| Al16 | *O | Coact–Oads | 1.743233 | -3.04245 | 3.04245 |

### Preferred V01 panel candidates

1. `Coact–Oads`: compare *OH → *O in pristine vs Al16.
2. `Coact–Obridge`: secondary active-site lattice bond response.
3. `neighbor–Obridge`: explicitly show the strong Al–Obridge bonding channel in Al16, but label the Al neighbor correctly rather than calling it Co.
4. ICOHP summary as a compact dot/bar panel.

Important interpretation guardrail: the numerical ICOHP values alone should not be described as proving the full catalytic mechanism. They are the bonding-origin companion to the independently established thermodynamic and charge/spin response results.

---

## V04 — PDOS

### Real PDOS curve files

| system | state | source file |
|---|---|---|
| pristine | *OH | `PDOS/source_data/pdos_curves_pristine_OH.tsv` |
| pristine | *O | `PDOS/source_data/pdos_curves_pristine_O.tsv` |
| Al16 | *OH | `PDOS/source_data/pdos_curves_Al16_OH.tsv` |
| Al16 | *O | `PDOS/source_data/pdos_curves_Al16_O.tsv` |

Canonical site mapping:

```text
PDOS/source_data/pdos_site_mapping.tsv
```

### Site mapping needed for plotting

| system | state | Coact | Oads | Obridge | neighbor |
|---|---|---:|---:|---:|---|
| pristine | *OH | Co 21 | O 348 | O 259 | Co 23 |
| pristine | *O | Co 21 | O 347 | O 258 | Co 23 |
| Al16 | *OH | Co 16 | O 348 | O 259 | Al 51 |
| Al16 | *O | Co 16 | O 347 | O 258 | Al 51 |

`Hterminal` is atom 115 in all four mapped states and should normally be omitted from the main electronic-structure panel unless a proton-specific comparison is required.

### Preferred V04 panel candidates

1. Active-site Co `d` + Oads `p` projected DOS for *OH and *O.
2. Obridge `p` as the lattice-oxygen companion.
3. Al-neighbor contribution only for Al16, clearly separated from the Co-neighbor channel used in pristine.
4. Use `E_F = 0 eV` if that is already the convention in the validated TSV files; confirm from each file header before plotting.
5. A narrow near-Fermi-window panel may be useful, but only after examining the real curves.

---

## Mapping consistency

Validated dynamic site roles from `PDOS/source_data/pdos_site_mapping.tsv`:

- pristine *OH: `Coact=21`, `Oads=348`, `Obridge=259`, `neighbor=Co23`
- pristine *O: `Coact=21`, `Oads=347`, `Obridge=258`, `neighbor=Co23`
- Al16 *OH: `Coact=16`, `Oads=348`, `Obridge=259`, `neighbor=Al51`
- Al16 *O: `Coact=16`, `Oads=347`, `Obridge=258`, `neighbor=Al51`

The change in Oads/Obridge atom indices between *OH and *O is intentional and comes from the validated state-specific mapping. Plotting scripts must use role labels rather than assuming fixed atom indices.

---

## Minimal downstream plotting workflow

1. Read this snapshot to resolve state files and site roles.
2. Read `COHP/source_data/icohp_summary.tsv` for exact ICOHP values.
3. Read only the required `cohp_curves_*.tsv` files for selected key bonds.
4. Read only the required `pdos_curves_*.tsv` files and use `pdos_site_mapping.tsv` to select active-site channels.
5. Generate standalone manuscript panels; do not assemble the final manuscript figure at this stage.

## Validation provenance

The parent package reports validated COHP/PDOS interfaces with no hard errors. The original source manifests and provenance files remain authoritative:

```text
electronic_structure_publication_data/source_manifest.tsv
electronic_structure_publication_data/PROVENANCE.md
electronic_structure_publication_data/VALIDATION_RESULT.md
```
