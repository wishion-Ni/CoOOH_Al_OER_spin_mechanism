# Metadata: VASP/LOBSTER/Bader Analysis

- **Status:** candidate for fixed-geometry OH/O comparisons; supporting for orbital interpretation.
- **Source:** validated four formal VASP statics, matched Bader post-processing, and genuine no-Madelung LOBSTER runs.
- **Method:** VASP PBE+U fixed-geometry statics, Bader charge partitioning, spin-resolved LOBSTER 5.1.1 COHP and DOS/PDOS post-processing.
- **Quality gates:** normal termination, explicit EDIFF, fixed geometry, required output files, current-POSCAR pair distances, charge conservation, and charge spilling target at or below 2%.
- **Key observation:** Al16 reduces the change in active Co moment and O electron loss relative to pristine and weakens the *OH -> *O increase in active Co-Oads bond strength by approximately 0.35 eV, with the difference mostly spin-selective.
- **Limitations:** Bader is a net partitioned charge, COHP is basis/pair dependent, related structures are not identical across CP2K/VASP, and the reaction-density images are not Bader maps.
