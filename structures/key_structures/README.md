# Key CoOOH structures (CIF)

These CIF files are converted directly from the validated CP2K baseline input structures archived in this repository.
They are intended for structure visualization, collaborator handoff, and reproducible manuscript graphics.

| Structure | atoms | composition | CP2K source | CIF |
|---|---:|---|---|---|
| `pristine_OH` | 222 | Co48, H60, O114 | `archive_20260910/02_DFT_CP2K/validated_sources/cp2k_undoped_OH_baseline.inp` | `structures/key_structures/pristine_OH.cif` |
| `pristine_O` | 221 | Co48, H59, O114 | `archive_20260910/02_DFT_CP2K/validated_sources/cp2k_undoped_O_baseline.inp` | `structures/key_structures/pristine_O.cif` |
| `Al16_OH` | 222 | Al8, Co40, H60, O114 | `archive_20260910/02_DFT_CP2K/validated_sources/cp2k_Al16_OH_baseline.inp` | `structures/key_structures/Al16_OH.cif` |
| `Al16_O` | 221 | Al8, Co40, H59, O114 | `archive_20260910/02_DFT_CP2K/validated_sources/cp2k_Al16_O_baseline.inp` | `structures/key_structures/Al16_O.cif` |

## Important scope note

- `pristine_OH` / `pristine_O` and `Al16_OH` / `Al16_O` are the four validated baseline structures used in the current electronic/spin-response analysis.
- The CIF conversion does not alter coordinates except wrapping fractional coordinates into [0,1).
- Space group is intentionally written as `P 1`; no symmetry is imposed during export.
- These files should not be confused with the historical three-site T01 thermodynamic branches, whose raw structures are not all copied into the current repository.
