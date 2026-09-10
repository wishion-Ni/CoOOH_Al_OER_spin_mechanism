# Safe orbital diagram specification

## Mandatory drawing rule

Draw **exchange-split, covalent Co-O hybrid manifolds**, not a strict ionic Co d6 crystal-field diagram. Do not invent exact eg/t2g or sigma/pi labels. Use the generic label **O-rich spin-polarized Co-O frontier state**.

## Four panels

### Pristine *OH

1. Lower occupied Co-O bonding manifold, both spins occupied. Evidence: VASP PDOS + finite bonding COHP; occupancy arrows are schematic, not integer orbital counts.
2. O-rich occupied frontier manifold near EF with Co 3d admixture. Evidence: VASP Oads 2p and Coact 3d PDOS overlap; CP2K favors Co+adsorbate over Co-only holes.
   - VASP/LOBSTER spin-2 peak proxy: approximately nonbonding with respect to Coact-Oads; local mean -COHP = -0.001402 in +/-0.12 eV.
3. Neighbor-Co 3d/O-2p/Co-3d relaxation channel adjacent to the active manifold. Evidence: Coadj spin-polarized PDOS and bridge COHP.

### Pristine *O

1. Show one electron removed from the O-rich frontier manifold, but label the removed spin **method dependent**: CP2K and VASP/LOBSTER do not agree.
2. Show stronger Coact-Oads bonding after oxidation: Delta(-ICOHP) = +1.46490 eV (spin1 +0.56027; spin2 +0.90463 eV).
3. Show CP2K redistribution: Hirshfeld Delta N(Coact)=+0.219 e, Delta N(Oads)=-0.464 e; Delta m(Coact)=-0.821 muB.

### Al16 *OH

1. Same covalent exchange-split Co-O manifold.
   - VASP/LOBSTER spin-2 peak proxy: weakly antibonding with respect to Coact-Oads; local mean -COHP = -0.030390 in +/-0.12 eV.
2. Replace the neighboring magnetic Co level bundle with a high/weakly magnetic Al state label: Al has no equivalent low-energy magnetic Co-3d manifold and local moment about 0.003 muB.
3. Keep Al-O framework as a thin structural support, not a redox orbital.

### Al16 *O

1. Remove one electron from the O-rich frontier manifold with the same method-dependent spin annotation.
2. Show weaker total Co-O bond strengthening than pristine: Delta(-ICOHP)=+1.11234 eV (spin1 +0.20887; spin2 +0.90347 eV), 0.35256 eV less than pristine and almost entirely a spin1 bonding difference.
3. Show suppressed Co response from CP2K: Hirshfeld Delta N(Coact)=+0.012 e versus +0.219 e pristine; Co-only M+2 penalty is 4.036604 versus 2.899188 eV.
4. Show O-centered response: Hirshfeld Delta N(Oads)=-0.427 e and CP2K local spin +0.336 to -0.408 muB. Add a dagger: "local sign reversal is CP2K partition-robust but not VASP-robust."

## Electron-arrow justification

- Use arrows only to indicate exchange polarization and oxidation of an O-rich covalent manifold.
- Do not label the removed electron universally as minority spin. CP2K Al Oads loses alpha population while VASP/LOBSTER loses spin-down O 2p population.
- Do not draw a literal integer d6 occupation or exact orbital degeneracies.

## Safe one-sentence mechanism

Al substitution removes a neighboring magnetic Co-3d relaxation channel, raises the cost of Co-centered spin accommodation, and leaves *OH-to-*O oxidation more ligand/O-centered while reducing the spin1 contribution to Co-O bond strengthening.
