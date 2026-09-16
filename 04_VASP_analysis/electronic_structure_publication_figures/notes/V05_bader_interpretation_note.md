# V05 - Bader charge response during fixed-geometry *OH -> *O

## Quantity
`delta_N = N_Bader(*O) - N_Bader(*OH)` using the validated matched VASP atom mapping.

Positive values indicate increased Bader-assigned electron count; negative values indicate electron loss.

## Key values
- Pristine CoOOH: Co_act +0.025873 e; O_ads -0.260692 e; O_bridge -0.023564 e; neighbor Co -0.001450 e.
- Al-substituted CoOOH: Co_act +0.030430 e; O_ads -0.224205 e; O_bridge +0.000284 e; neighbor Al -0.000660 e.

## Interpretation
The adsorbate O carries the dominant net Bader electron loss in both systems, while the active-Co Bader electron count changes only slightly. This is supporting charge-partition evidence and should be read together with the cDFT local charge/spin response.

## Limitation
Bader charges are partition-dependent descriptors and do not by themselves define formal oxidation states. Small active-Co Bader changes do not exclude substantial orbital/spin reorganization.

## Recommended use
Supporting Information / cross-method context.
