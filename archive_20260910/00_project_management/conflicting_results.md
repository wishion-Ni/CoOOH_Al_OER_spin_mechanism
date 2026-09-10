# Conflicting and Non-equivalent Results

Conflicts are preserved. They are not resolved by averaging values from different methods.

| Topic | Observed records | Archive treatment | Current preferred wording |
|---|---|---|---|
| Co charge response | cDFT indicates a visible pristine Co-centered redistribution and nearly suppressed Al-substituted Co redistribution; VASP/Bader fixed-geometry net active-Co changes are small in both systems. | Keep both datasets with method labels and different geometry/partitioning caveats. | cDFT supports a suppressed Co-centered constrained response; Bader gives only a small net charge change and cannot by itself certify orbital compensation. |
| O spin response | CP2K/cDFT Al Oads loss is alpha-dominated and can reverse the local O spin sign; VASP/LOBSTER supports spin-down O-2p loss without a robust sign reversal. | Do not force a common spin label. | O-rich spin-polarized Co-O frontier response; exact spin assignment is method dependent. |
| COHP pair mapping | Early copied indices selected distant or background-OH pairs. | Reject those ICOHP entries; retain preflight outputs for audit. | Use only current-POSCAR distance-validated pairs. |
| LOBSTER completion | Initial jobs timed out during unnecessary Madelung evaluation after valid projection/spilling output. | Preserve timed-out outputs; use no-Madelung reruns for accepted COHP. | Accepted COHP requires normal finish, pair validation and spilling threshold. |
| Orbital identity | Frontier states mix and reorder between *OH/*O and pristine/Al16. | Preserve fingerprint and spatial evidence; do not map by raw band index alone. | Use mixed-character/fingerprint language unless a state-tracking proof exists. |
| Reaction density | Full-system density difference contains net electron removal; cropped display is only a visualization choice. | Keep grid statistics and images; distinguish from Bader charge. | Report isovalue and call it reaction-induced density, not a Bader map. |

## Dataset status rules

- `candidate_dataset`: accepted for manuscript-oriented comparison after validation.
- `supporting_dataset`: useful for mechanism context, but not sufficient alone for a central claim.
- `historical_dataset`: retained for reproducibility, debugging or provenance and not used as a final figure source.

The archive protocol itself is the controlling document for promotions between these statuses.
