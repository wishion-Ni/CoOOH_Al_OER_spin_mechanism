# Oads spin-reversal audit

## Classification

**CP2K PARTITION-ROBUST BUT NOT VASP-ROBUST**

## CP2K primary result

- In Al16, Oads changes from +0.339262 to -0.462897 muB (Mulliken) and from +0.336 to -0.408 muB (Hirshfeld).
- Both CP2K partitions therefore support a local Oads spin-polarization reversal.
- Hirshfeld Oads changes from N_alpha/N_beta = 3.318/2.981 in *OH to 2.732/3.140 in *O. The dominant electron loss is alpha relative to the positive Co spin axis; beta gains population.
- Pristine Oads does not reverse sign and loses both alpha and beta population more evenly.

## VASP/LOBSTER supporting result

- VASP local Oads moments remain positive: pristine +0.159 to +0.813 muB; Al16 +0.328 to +1.028 muB.
- LOBSTER Oads 2p populations indicate spin-down loss with spin-up gain, not the CP2K alpha-dominant loss.
- This is not a simple global spin-axis sign inversion because active Co has the same positive orientation in both descriptions.

## Why the methods can differ

The CP2K and VASP structures are related but not identical, use different cells/local sites, basis/projection definitions, and population partitions. Local spin assigned to an oxygen basin or atom-centered basis is not an observable invariant. The sign reversal is robust inside CP2K across Mulliken and Hirshfeld, but not across methods.

## Manuscript use

Use CP2K to support an Al-induced O-centered spin reorganization and disclose the CP2K local sign reversal as method dependent. Do not draw a universal removed minority-spin electron or claim a method-independent O spin reversal.
