# CoOH Al16 stage summary (2026-08-19)

## Completed and validated

- Strict undoped site03 CHE: dG = (1.755822390, 2.030710620, 0.669871268, 0.463595722) eV; PDS OH* -> O*; eta = 0.800710620 V.
- Matched cDFT scan set: 14/14 undoped scans valid and Al16 comparison complete. OER-relevant Co+adsorbate N-1 Al16-undoped shifts are OH +0.282946 eV, O +0.077453 eV, OOH -0.367431 eV.
- Proton-relay screen: neutral and N-1-conditioned fixed-coordinate profiles complete. The current Al-bound OH geometry does not assist adjacent Co-OH deprotonation.
- Bare fixed-geometry Bader/PDOS pair: active Co gains 0.026856 Bader electron, moment rises 0.146 muB, and occupied d center shifts +0.081891 eV in Al16.

## Running or pending

- Exact matched Al16/control strict relaxations: eight unique jobs running; no final validated geometry yet.
- Fixed-geometry Bader/PDOS VASP: tasks 0-2 complete; task3 control-OH running; O and OOH queued.
- Al16-OH Bader is valid but remains single-sided until control-OH completes.
- Exact matched statics, vibrations and Al16/control 298.15 K CHE remain pending.
- COHP is not available without a licensed LOBSTER executable.

## Preliminary interpretation

Al does not produce a simple, uniformly electron-withdrawing active-Co response. The bare site is slightly more electron rich and higher spin, while cDFT shows state-selective delocalized Co-adsorbate charge accommodation, with the clearest favorable oxidation effect at OOH. The current Al-OH arrangement is not a favorable proton relay. A catalytic-performance claim must wait for the exact matched OH/O/OOH electronic trends and final CHE.

## Scope cautions

- The cDFT comparison uses the historical accepted undoped Co32 model and chemically valid Al16 Co40 model; local sites are not identical.
- Proton-relay profiles are fixed-heavy-atom screens, not NEB barriers.
- Current Bader/PDOS data use preconverged fixed geometries and isolate electronic substitution effects; relaxed structural effects are pending.
