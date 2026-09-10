# Partial Co spin-state relaxation test

## Assessment: PLAUSIBLE, not established

The local Hirshfeld response is qualitatively consistent with partial spin relaxation in a covalent Co-O unit:

- pristine Coact: Delta N_alpha = -0.301 e, Delta N_beta = +0.520 e, Delta m = -0.821 muB;
- Al16 Coact: Delta N_alpha = -0.218 e, Delta N_beta = +0.230 e, Delta m = -0.448 muB.

The stronger pristine alpha-to-beta reorganization is chemically compatible with depopulation of higher-energy majority antibonding character and increased minority occupation. It is also consistent with the earlier cDFT result that the Co-only M+2 penalty is 2.899188 eV in pristine and 4.036604 eV in Al16.

However, the four calculations do not hold global multiplicity fixed. In both materials, *OH -> *O removes one electron while the input multiplicity decreases by 7, giving the imposed global change Delta N_alpha=-4 and Delta N_beta=+3. The local Co response is therefore conditional on comparing two different fixed-spin branches. It cannot by itself prove a spontaneous high-spin-like to lower-spin-like transition.

A bond-aligned local frame is defined numerically in the TSV, but no existing CP2K projection resolves eg/t2g or sigma/pi occupation. Therefore:

- partial covalent spin-state relaxation: **PLAUSIBLE**;
- exact majority eg/sigma-antibonding loss: **NOT ESTABLISHED**;
- exact minority t2g/pi gain: **NOT ESTABLISHED**;
- integer HS -> LS transition: **not claimed**.
