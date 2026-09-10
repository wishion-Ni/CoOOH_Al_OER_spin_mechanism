# CP2K cDFT interpretation

1. **Ligand/Co-O holes are favored over Co-only holes.** Existing N-1 penalties are about 4.89-5.27 eV for Co-only constraints but 2.87-3.39 eV for Co+adsorbate constraints. This supports an O-rich, covalent hole rather than a purely Co-localized oxidation.
2. **Al makes Co-centered spin accommodation harder in the *O state.** The valid Co-only M+2 penalty increases from 2.899188 eV (pristine) to 4.036604 eV (Al16), a +1.137416 eV difference.
3. **Al suppresses the CP2K Co-centered charge response.** Hirshfeld Delta N(Coact) is +0.219 e in pristine but +0.012 e in Al16; Mulliken gives +0.147192 and +0.050237 e, respectively. The magnitude is partition dependent, but the suppression trend is consistent.
4. **O is the dominant redox center.** Hirshfeld Delta N(Oads) is -0.464 e (pristine) and -0.427 e (Al16). In Al16 the Oads local spin changes from +0.336 to -0.408 muB in CP2K.
5. The Al16 M-2 branch was rejected because of a discontinuous spin branch and cannot be used.

These values are cDFT localization/spin penalties. They are not CHE reaction free energies, kinetic barriers, or applied potentials.
