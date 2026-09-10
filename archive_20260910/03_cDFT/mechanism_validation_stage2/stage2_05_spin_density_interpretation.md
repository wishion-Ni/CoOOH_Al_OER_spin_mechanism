# O spin reversal as ligand-hole polarization

No CP2K charge-density or spin-density cube was found under the four baseline directories or the complete cDFT roots. A real-space spin-density image cannot be produced from existing outputs alone.

The CP2K atom-partition result nevertheless supports a qualified local interpretation:

| system/state | Coact Hirshfeld spin (muB) | Oads Hirshfeld spin (muB) | local relation |
|---|---:|---:|---|
| pristine *OH | +3.215 | +0.607 | aligned |
| pristine *O | +2.394 | +0.537 | aligned |
| Al16 *OH | +3.224 | +0.336 | aligned |
| Al16 *O | +2.776 | -0.408 | antiparallel |

Thus CP2K Mulliken and Hirshfeld populations support **local antiparallel ligand-hole spin polarization** on Oads in Al16-*O. This phrase describes the sign of atom-partitioned local spin relative to Coact. It is not proof of an exchange constant, antiferromagnetic coupling, or a spatially isolated O-centered spin density.

Confidence: medium inside CP2K, because both population schemes reverse sign; not cross-method robust, because VASP/LOBSTER does not show the same sign reversal. Cube confirmation remains unavailable without a print rerun.
