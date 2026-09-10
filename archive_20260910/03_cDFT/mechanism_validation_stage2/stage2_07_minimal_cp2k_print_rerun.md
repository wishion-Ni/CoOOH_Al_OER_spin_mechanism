# Minimal CP2K print rerun request (not launched)

## Unresolved question

The directly oxidized CP2K frontier spin and its Oads/Coact/Obridge/neighbor orbital weights are unknown. Existing OT WFN files contain a converged occupied subspace but no printed canonical eigenvalues, virtual states, PDOS or spin-density cube.

## Smallest defensible calculation

Priority 1: two fixed-geometry *OH single points, pristine and Al16, restarted from the final `cdf_base_...-RESTART.wfn` files. Priority 2: add the two *O states only if matched spin-density cubes are required.

Required changes relative to the validated baseline input:

```text
&GLOBAL
  RUN_TYPE ENERGY
&END GLOBAL
&DFT
  WFN_RESTART_FILE_NAME <final cdf_base ... RESTART.wfn>
  UKS T
  MULTIPLICITY <retain the validated state value>
  CHARGE 0
  &SCF
    SCF_GUESS RESTART
    EPS_SCF 1.0E-7
    MAX_SCF 20
    ADDED_MOS 80
    &DIAGONALIZATION ON
      ALGORITHM STANDARD
    &END DIAGONALIZATION
  &END SCF
  &PRINT
    &MO
      EIGENVALUES T
      OCCUPATION_NUMBERS T
    &END MO
    &PDOS
      NLUMO 50
      COMPONENTS T
    &END PDOS
    &E_DENSITY_CUBE
    &END E_DENSITY_CUBE
    &SPIN_DENSITY_CUBE
    &END SPIN_DENSITY_CUBE
  &END PRINT
&END DFT
```

The CP2K build/version input syntax must be checked before submission. Switching from OT to diagonalization and adding virtual MOs is a new static SCF, not zero-cost post-processing.

## Resources and expected cost

- one node only;
- 28 MPI ranks, 1 thread each, matching the validated baselines;
- no geometry optimization, no cDFT scan;
- estimated 1-4 h per state because diagonalization of 3978 orbital functions is substantially more expensive than the prior occupied-only OT baselines (143-1130 s);
- two priority *OH jobs: approximately 2-8 node-hours total, or 1-4 h wall time if run concurrently;
- expected outputs: alpha/beta eigenvalues, PDOS component files, and charge/spin-density cubes.

No job has been submitted. Explicit approval is required.
