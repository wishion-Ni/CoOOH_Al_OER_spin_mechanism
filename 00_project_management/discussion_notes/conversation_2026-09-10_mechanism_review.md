# Discussion notes — 2026-09-10

## Scope

This note archives the major conclusions from the mechanism-review discussion. It is not a new mechanistic analysis.

## Main issue identified

Early mechanism sketches were repeatedly rejected because they showed numerical outputs (magnetic moments, charge values, generic electron clouds) without explaining why those changes occur or why Al substitution changes the *OH -> *O pathway.

The discussion converged on the requirement that the mechanism figure must explain causal structure rather than simply summarize calculated results.

## Key mechanistic insights retained

### 1. Oxidation remains O-centered in both systems

The oxygen-centered oxidation event is broadly similar before and after Al substitution. The important distinction is not the existence of oxidation itself but the subsequent electronic/spin accommodation.

### 2. Pristine CoOOH undergoes distributed framework-coupled reconstruction

The relevant response is distributed over Oact, Coact, and Obridge:

- Oact carries the main net oxidation;
- Coact shows strong charge backfilling and large spin depolarization;
- Obridge shows little net charge change but substantial spin redistribution.

This indicates collective electronic accommodation rather than a simple Co oxidation state change.

### 3. Al changes the downstream magnetic/electronic boundary

The local structural bond to Al remains intact. The important change is the absence of the same near-EF magnetic d-like continuation associated with a neighboring Co site.

The visual/mechanistic distinction must therefore be drawn as a change in magnetic/electronic continuation, not as a broken bond or blocked electron-transfer path.

### 4. Al shifts accommodation toward Oact

In the Al-substituted system:

- Co charge backfilling is strongly reduced in cDFT/Hirshfeld;
- Obridge spin response is strongly reduced;
- Oact carries the dominant local spin reorganization and exhibits a sign reversal in local spin polarization.

Coact is not completely inactive: it still shows a non-negligible spin response.

### 5. Global spin reorganization is not eliminated

Both systems undergo the same overall CP2K multiplicity/electron-spin-count change. The difference is spatial/orbital redistribution of that spin response.

## Figure-design conclusions

The following visualization principles were locked:

- Do not use generative AI to decide atomic connectivity or orbital topology.
- Oact must remain the terminal adsorbate oxygen.
- Do not draw Oact connected to Obridge or Al.
- Do not use a single ↑ -> ↓ arrow to represent Oact spin reversal.
- Charge and spin must use different visual encodings.
- Coact should be treated as an electronic junction coupling the O-centered oxidation sector to the lower Co-O-neighbor accommodation sector.
- Al should retain a normal structural bond while lacking a magnetic d-like continuation.
- A central intermediate structure panel should be avoided unless it corresponds to an actual calculated state.

## Electronic-structure data representation discussion

Simple bar charts were judged useful for internal analysis but not ideal for the final manuscript.

Preferred manuscript data views:

1. spin-resolved orbital-projected PDOS or spectral-feature maps;
2. reaction-difference PDOS when raw energy-resolved data are available;
3. spin-resolved COHP(E);
4. cumulative ICOHP(E);
5. cDFT charge/spin population analysis as a complementary, integrated-space view.

The existing postprocessing is already sufficient for mechanistic reasoning, but raw energy-grid PDOS/COHP files should be preserved for publication-quality spectral plots.