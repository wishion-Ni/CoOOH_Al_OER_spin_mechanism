# Spin-resolved frontier-level postprocessing

## Scope and evidentiary limits

This is read-only postprocessing of the four validated fixed-geometry VASP statics and their genuine spin-polarized LOBSTER calculations. No new VASP, LOBSTER, or CP2K calculation was submitted. Energies are reported relative to each calculation's own Fermi level. No LOCPOT is present in the source set, so cross-system absolute orbital shifts cannot be established; only within-system ordering relative to EF is reported.

The VASP projections use global Cartesian harmonics. Local-axis orbital rotation and a defensible local eg/t2g assignment are unavailable from these outputs. Population changes are not interpreted as literal single-electron orbital transitions.

## Data validation

| System | EF (eV) | DOS spacing (eV) | Majority Coact spin | LOBSTER curves |
|---|---:|---:|---|---:|
| pristine_OH | -3.347367 | 0.10500 | up | 5 |
| pristine_O | -3.399775 | 0.10600 | up | 5 |
| Al16_OH | -3.308841 | 0.11000 | up | 5 |
| Al16_O | -3.302174 | 0.11100 | up | 5 |

For *OH, the removed proton was identified by one-to-one periodic coordinate matching against the corresponding *O structure, followed by the Oads-H distance check. It is not H116:

- Pristine: active H = H204, Oads-H = 0.9777 A. The existing LOBSTER pair labeled with H116 belongs to a background terminal OH and is excluded from active Oads-H claims.
- Al16: active H = H204, Oads-H = 0.9777 A. The existing LOBSTER pair labeled with H116 belongs to a background terminal OH and is excluded from active Oads-H claims.

## Frontier feature positions and bonding character

The catalog uses local maxima on the original DOS energy grid. A one-grid-point Gaussian filter is used only to stabilize peak detection; all centroids, integrated weights, and exported spectra use the raw grid. Bonding labels are assigned from energy-resolved -COHP in +/-0.12 eV around each peak.

### pristine_OH

- up: UF1 (-0.097 eV; O-rich weakly antibonding frontier; strongly antibonding) > UF2 (-0.730 eV; extended Co-O-Co magnetic mixed state; strongly antibonding) > UF3 (-1.362 eV; extended Co-O-Co magnetic mixed state; strongly antibonding) > UF4 (-1.890 eV; mixed local frontier state; strongly antibonding)
- down: DF1 (-0.097 eV; O-rich nonbonding frontier; approximately nonbonding) > DF2 (-0.941 eV; extended Co-O-Co magnetic mixed state; strongly antibonding)

- O-rich spin-down: DF1 at -0.097 eV, approximately nonbonding, O-rich nonbonding frontier (high confidence).
- majority Co-O antibonding: UF1 at -0.097 eV, strongly antibonding, O-rich weakly antibonding frontier (high confidence).
- minority Co-O bonding/mixed: not resolved by the available projected DOS/COHP set.
- neighbor magnetic: UF2 at -0.730 eV, strongly antibonding, extended Co-O-Co magnetic mixed state (high confidence).

### pristine_O

- up: UF1 (+0.032 eV; Co-O strongly antibonding mixed state; strongly antibonding) > UF2 (-0.710 eV; O-rich weakly antibonding frontier; strongly antibonding) > UF3 (-1.345 eV; O-rich weakly antibonding frontier; weakly antibonding)
- down: DF1 (+0.350 eV; O-rich Co-O mixed frontier; bonding) > DF2 (+0.032 eV; O-rich Co-O mixed frontier; bonding) > DF3 (-1.027 eV; extended Co-O-Co magnetic mixed state; strongly antibonding) > DF4 (-1.769 eV; Co-O bonding mixed state; bonding)

- O-rich spin-down: DF1 at +0.350 eV, bonding, O-rich Co-O mixed frontier (moderate confidence).
- majority Co-O antibonding: UF1 at +0.032 eV, strongly antibonding, Co-O strongly antibonding mixed state (high confidence).
- minority Co-O bonding/mixed: DF1 at +0.350 eV, bonding, O-rich Co-O mixed frontier (moderate confidence).
- neighbor magnetic: UF2 at -0.710 eV, strongly antibonding, O-rich weakly antibonding frontier (low confidence).

### Al16_OH

- up: UF1 (-0.550 eV; O-rich weakly antibonding frontier; strongly antibonding) > UF2 (-1.433 eV; Co-O mixed frontier state; weakly antibonding) > UF3 (-1.764 eV; extended Co-O-Al mixed state; weakly antibonding)
- down: DF1 (+0.001 eV; O-rich weakly antibonding frontier; weakly antibonding) > DF2 (-1.212 eV; O-rich Co-O mixed frontier; bonding)

- O-rich spin-down: DF1 at +0.001 eV, weakly antibonding, O-rich weakly antibonding frontier (high confidence).
- majority Co-O antibonding: UF1 at -0.550 eV, strongly antibonding, O-rich weakly antibonding frontier (high confidence).
- minority Co-O bonding/mixed: DF2 at -1.212 eV, bonding, O-rich Co-O mixed frontier (high confidence).
- neighbor magnetic: not resolved by the available projected DOS/COHP set.

### Al16_O

- up: UF1 (-0.441 eV; Co-O strongly antibonding mixed state; strongly antibonding) > UF2 (-1.105 eV; O-rich weakly antibonding frontier; strongly antibonding) > UF3 (-1.879 eV; extended Co-O-Al mixed state; approximately nonbonding)
- down: DF1 (+0.001 eV; O-rich Co-O mixed frontier; bonding) > DF2 (-1.879 eV; Co-O bonding mixed state; bonding)

- O-rich spin-down: DF1 at +0.001 eV, bonding, O-rich Co-O mixed frontier (high confidence).
- majority Co-O antibonding: UF1 at -0.441 eV, strongly antibonding, Co-O strongly antibonding mixed state (high confidence).
- minority Co-O bonding/mixed: DF1 at +0.001 eV, bonding, O-rich Co-O mixed frontier (high confidence).
- neighbor magnetic: not resolved by the available projected DOS/COHP set.

## Direct answers

- Pristine *OH O-rich spin-down versus majority Co-O antibonding: near-degenerate/unresolved ordering (separation 0.000 eV; threshold 0.210 eV).
- Al16 *OH O-rich spin-down versus majority Co-O antibonding: resolved: O-rich spin-down lies 0.551 eV above the majority Co-O antibonding feature.
- Pristine *O: resolved: O-rich spin-down lies 0.318 eV above the majority Co-O antibonding feature.
- Al16 *O: resolved: O-rich spin-down lies 0.442 eV above the majority Co-O antibonding feature.

- *OH Al effect: at least one ordering is within the resolution band; only near-degeneracy/separation can be claimed.
- *O Al effect: the order is retained; the data support differential separation rather than a proven reordering.

The complete feature-by-feature evidence, including component weights, three pair-resolved -COHP metrics, sign consistency, and confidence, is in `frontier_state_catalog.tsv`.

## What can be drawn in the paper

- Use the resolved peak ordering and bonding labels where the separation exceeds the stated resolution band.
- Draw near-degenerate levels as uncertainty bands when separation is <= max(0.12 eV, twice the DOS spacing).
- Show O-rich, Co-O mixed, Obridge, and neighboring-Co/Al manifolds without forcing sigma/pi or eg/t2g labels.
- The active Oads-H bond has geometry evidence but no dedicated COHP curve in the existing LOBSTER files; do not assign its bonding energy from the background H116 pair.
- Cross-material vertical alignment is schematic because no vacuum alignment is available.

## Files

- `selected_pdos_full.tsv`: raw-grid spin-resolved orbital projections for all requested atoms/roles.
- `selected_cohp_full.tsv`: raw-grid spin-resolved -COHP/-ICOHP for all five existing pair curves.
- `frontier_state_catalog.tsv`: localized frontier-feature catalog and COHP-based classification.
- `local_geometry.tsv`: Coact vectors, six nearest O neighbors, and automatically identified active Oads-H.
- `vacuum_alignment.tsv`: explicit unavailable status because LOCPOT is absent.
- `source_manifest.tsv`: local mirror and actual remote source paths with SHA256 hashes.

## Source provenance

The source manifest contains 20 hashed files. Original calculation directories were not modified.
