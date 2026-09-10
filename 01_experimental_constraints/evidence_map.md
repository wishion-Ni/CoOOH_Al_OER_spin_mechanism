# Evidence map

This document links each experimental/theoretical question to the evidence required and the currently available supporting data. It does not modify any calculation result.

| Question | Evidence needed | Existing support | Status |
|---|---|---|---|
| Why does Al selectively lower *OH -> *O rather than uniformly improve all OER steps? | Intermediate-specific thermodynamics plus state-specific electronic response | Historical CP2K trend: step 1 becomes ~0.20 eV less favorable while step 2 improves by ~0.27 eV; cDFT/COHP responses are strongly intermediate- and channel-specific | supported interpretation |
| Why does pristine Co show a strong Co-sensitive transient response? | Evidence of substantial Co-centered reconstruction during *OH -> *O | cDFT/Hirshfeld Coact ΔN = +0.219 e and Δm = -0.821 μB; Co-O spin-resolved rebonding is strong | supported interpretation |
| Why is the Co-sensitive transient response suppressed after Al substitution? | Reduced Co-centered electronic reconstruction | cDFT/Hirshfeld Coact ΔN = +0.012 e; Co spin response remains but is smaller; Obridge spin response is strongly reduced | supported interpretation |
| Is oxidation still oxygen-centered after Al substitution? | Comparable Oact net oxidation in both systems | cDFT/Hirshfeld: ΔN(Oact) = -0.464 e pristine and -0.427 e Al; Bader also identifies Oads as the principal net-loss site | established observation |
| What changes most strongly after Al substitution? | Spin-resolved local response | Oact Δm changes from -0.070 μB pristine to -0.744 μB Al; Al case shows local O spin-polarization sign reversal | established observation within cDFT/Hirshfeld; supported by Mulliken |
| Does Al itself become a redox-active site? | Al charge/spin response | Al has ~zero reaction-induced ΔN and Δm in the relevant local partitioning | established observation |
| What is special about Obridge in pristine CoOOH? | Separate charge and spin response | ΔN(Obridge) ≈ 0 but Δm(Obridge) = -0.242 μB, indicating spin redistribution without significant net charge transfer | established observation |
| What electronic feature connects neighboring Co substitution to active O response? | Evidence for a magnetic/electronic continuation through Coact-Obridge-neighbor | near-EF magnetic d-like continuation exists for neighboring Co and is essentially absent for Al; spin-resolved Coact-Obridge/Coact-Oact COHP responses change selectively | supported interpretation |
| Is the mechanism a simple Co oxidation-state change? | Co-only versus Co-O/adsorbate hole localization energetics | Co-only N-1 constraints are ~1.8-1.9 eV more costly than Co+adsorbate N-1 in pristine | established calculation; argues against simple Co-only oxidation |
| Does Al reduce the total amount of global spin change? | Total spin-resolved electron bookkeeping | Both systems show the same overall CP2K ΔNα=-4, ΔNβ=+3, ΔM=-7 pattern | established observation; rejects this interpretation |
| Does Al lower ΔG because Co-O rebonding is globally weaker? | Spin-resolved COHP and free-energy decomposition | One Co-O spin channel changes strongly while the other is nearly unchanged; no rigorous ΔG decomposition exists | working hypothesis only; avoid direct equivalence |

## Status definitions

- **established observation**: directly measured or calculated.
- **supported interpretation**: consistent with multiple data sources and used as the current mechanistic interpretation.
- **working hypothesis**: plausible but not uniquely demonstrated.
- **open question**: insufficient evidence for a firm conclusion.