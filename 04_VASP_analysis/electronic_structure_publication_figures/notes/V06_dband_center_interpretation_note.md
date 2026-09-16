# V06 d-band-center presentation options

## Purpose

This package provides three interchangeable presentation styles for the existing Co 3d centroid analysis so manuscript collaborators can select the format that best fits the final layout.

- **V06a — absolute occupied active-Co centroid:** quantitative *OH → *O evolution of the occupied active-Co 3d centroid.
- **V06b — centroid-shift summary:** quantitative Δεd comparison for active-Co total 3d, spin-up, spin-down, and framework-averaged Co 3d response.
- **V06c — semi-elliptic d-band schematic:** conventional d-band-model-style visualization using the exact occupied centroid positions but a symbolic common semi-elliptic DOS width.

## Source and provenance

The quantitative values are copied from the archived validated analysis:

- `archive_20260910/04_VASP_analysis/d_band_center_oh_o_20260824.tsv`
- `archive_20260910/04_VASP_analysis/d_band_center_framework_oh_o_20260824.tsv`

The publication-facing copies are:

- `source_data/V06_activeCo_dcenter_values.csv`
- `source_data/V06_framework_dcenter_values.csv`
- `source_data/V06_shift_summary.csv` (derived reproducibly by the plotting script)

## Quantitative occupied-window results (-8 to 0 eV)

Active-Co total 3d centroid:

- pristine: -5.10710210 eV (*OH) → -5.00052496 eV (*O), Δεd = +0.10657714 eV
- Al-substituted: -4.87437773 eV (*OH) → -4.69914879 eV (*O), Δεd = +0.17522894 eV

Spin-resolved active-Co shifts:

- pristine: spin-up +0.16843250 eV; spin-down -0.09692405 eV
- Al-substituted: spin-up +0.23227799 eV; spin-down +0.03363030 eV

Framework-averaged occupied Co 3d centroid:

- pristine: Δεd = -0.00163526 eV
- Al-substituted: Δεd = -0.01185645 eV

## Interpretation boundary

The four VASP states are aligned to **their own Fermi levels**. The validated source set has no usable LOCPOT/vacuum reference for these calculations. Therefore:

1. within-system *OH → *O centroid shifts are the safest quantitative comparison;
2. the absolute pristine-versus-Al offset must **not** be interpreted as a vacuum-aligned orbital-energy shift;
3. d-band-center changes do not independently establish oxidation state or charge transfer;
4. V06b is best used as evidence for a localized, spin-channel-specific spectral response at the active Co, while cDFT remains the primary evidence for suppression of Co-centered charge/spin reconstruction;
5. V06c is explicitly schematic: the centroid positions are data, but the common semi-elliptic width/shape is illustrative and is not fitted to the calculated PDOS.

## Recommended use

- **V06a:** safest quantitative standalone option; main text or SI.
- **V06b:** compact summary when space is limited; especially useful next to cDFT.
- **V06c:** d-band-model-style visual option for schematic presentation; use only with an explicit schematic label/caption.

All three options use the project palette (pristine `#374151`, Al-substituted `#2A9D8F`), four-sided frames, publication-sized typography, and export to PNG/TIF/PDF/SVG/EPS.
