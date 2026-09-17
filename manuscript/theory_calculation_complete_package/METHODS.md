# Computational Methods — manuscript draft

> **Status:** manuscript-oriented draft assembled only from settings and provenance that are explicitly recoverable from the validated repository. Items that still require checking against the original server-side VASP run directories are isolated in the final verification section rather than guessed.

## Density-functional-theory models and CP2K calculations

Periodic spin-polarized density-functional-theory calculations were performed with the Quickstep module of CP2K. The exchange-correlation energy was described using the PBE generalized-gradient approximation. Goedecker-Teter-Hutter PBE pseudopotentials and molecularly optimized Gaussian basis sets were used; the validated baseline inputs specify `TZVP-MOLOPT-PBE-GTH-q17` for Co, `TZVP-MOLOPT-PBE-GTH-q6` for O and `TZVP-MOLOPT-PBE-GTH-q1` for H. The Co 3d states were treated with an effective on-site interaction of U−J = 0.1212728 Hartree (approximately 3.30 eV). The auxiliary plane-wave density cutoff and relative cutoff were 400 and 55 Ry, respectively. Electronic minimization used the orbital-transformation scheme with a conjugate-gradient minimizer, `FULL_SINGLE_INVERSE` preconditioning, an SCF convergence threshold of 1 × 10−7 and up to 500 inner SCF cycles; an outer-SCF loop with a convergence threshold of approximately 1 × 10−6 and up to 80 cycles was used for the validated baseline states.

The current validated pristine and Al-substituted models use the same orthorhombic periodic cell, a = 8.648200 Å, b = 26.079300 Å and c = 21.657400 Å. The validated *OH structures contain 222 atoms. The pristine model has composition Co48H60O114, whereas the Al-substituted model has composition Co40Al8H60O114. Removal of the adsorbate proton gives the corresponding 221-atom *O structures. The exported CIF files retain the calculated coordinates and cell and are written in P1 without imposing additional symmetry. The source provenance does **not** explicitly establish a Miller-index surface assignment; therefore the model should be described as a periodic CoOOH slab/supercell unless the original structure-generation record is separately verified.

All baseline calculations were unrestricted-spin calculations. For the selected solutions used in the *OH→*O electronic/spin-response analysis, the total multiplicity changes from 175 to 168 for pristine CoOOH and from 149 to 142 for the Al-substituted model. Consequently, local population and local-spin changes reported below characterize redistribution within these selected electronic solutions and should not, by themselves, be interpreted as proof of a spontaneous spin-state crossing.

## OER electronic-energy comparison

The OER pathway was represented by the conventional sequence * → *OH → *O → *OOH → O2. The manuscript-facing T01 dataset compares a pristine Co site, the Co site adjacent to Al substitution, and an Al-site control. Relative energies were assembled from the validated CP2K electronic energies for the selected intermediates and are reported as **relative electronic energies**. No complete matched vibrational/ZPE/entropy correction is included in this historical three-site comparison; therefore T01 is not described as a strict 298.15 K Gibbs-free-energy/CHE series and is not used to claim a rigorously corrected theoretical overpotential.

## Constrained-DFT and population analysis

Constrained-DFT calculations were performed in CP2K using the same baseline electronic-structure framework. Charge-localization constraints were applied either to the active Co center alone or to a combined active-Co/adsorbate fragment, with N−1 and N+1 perturbations evaluated for the relevant OER intermediates. Selected local-spin constraints were additionally examined for the *O state. The reported energetic quantity is the **cDFT constraint penalty** of the constrained electronic solution; it is not a CHE reaction free energy, an activation barrier or an applied electrode potential.

Local electron populations and spin moments were evaluated using both Hirshfeld and Mulliken partitions. For the *OH→*O comparison, changes were defined as the value in *O minus that in *OH. Spin-resolved population changes were further decomposed into alpha- and beta-electron contributions. The agreement and disagreement between partition schemes were retained explicitly rather than using population analysis as a formal oxidation-state assignment. In particular, the adsorbate-O spin-sign reversal found for the Al-containing state within the CP2K population analyses is treated as method-dependent; the robust interpretation is an Al-induced change in O-centered/O-rich spin reorganization rather than a universal spin-flip claim.

## Matched VASP electronic-structure calculations and fixed-geometry comparison

Four matched VASP states were used for the electronic-structure post-processing: pristine-*OH, pristine-*O, Al-substituted-*OH and Al-substituted-*O. The formal COHP/PDOS package is derived from completed static calculations whose provenance, source paths, sizes and SHA256 hashes are recorded in the synchronized data manifests. The compact repository intentionally retains plot-ready numerical tables and minimal LOBSTER/structure files while the very large DOSCAR, vasprun.xml, COHPCAR and related raw files remain at the recorded server-side locations.

For the reaction-induced real-space analysis, the *O electronic density was evaluated at the matched *OH geometry and compared directly with the *OH state at that same geometry. The plotted charge-density difference is therefore

Δρ = ρ(*O at *OH geometry) − ρ(*OH at *OH geometry),

and the magnetization-density difference is defined analogously. With m = ρ↑ − ρ↓, spin-resolved density differences were reconstructed as

Δρ↑ = 1/2(Δρ + Δm),

Δρ↓ = 1/2(Δρ − Δm).

The full three-dimensional fields were downsampled from 420 × 280 × 420 to 210 × 140 × 210 before slice sampling. A common PCA-defined plane passing through the active Co, adsorbate O, bridge O and neighboring Co/Al site was used for both materials, and the final slices contain 120 × 80 points. Identical orientation and color limits were used for direct pristine/Al comparison. These maps represent local reaction-induced densities, not Bader charges, and they should not be interpreted as the density difference between two independently fully relaxed structures. Optional local numerical annotations were obtained by integrating the fields within 0.8 Å spheres around selected sites.

## Projected density of states and d-state centroids

Site- and orbital-projected densities of states were extracted from the matching VASP DOSCAR files for the active Co, adsorbate O, bridge O and neighboring metal site. Energies were shifted by the native Fermi energy of each calculation and compacted to −8 to +4 eV for the publication data package. Because a common vacuum-level/LOCPOT alignment is not available, absolute Fermi-referenced energies from different calculations are not interpreted as rigorously aligned vacuum-level orbital energies.

The active-Co d-state centroid was evaluated from the projected Co 3d DOS. The occupied-state descriptor uses the −8 to 0 eV interval relative to the corresponding Fermi level, with

εd = ∫E ρd(E)dE / ∫ρd(E)dE.

Spin-resolved centroids and framework-averaged Co descriptors were evaluated analogously. These values are used as spectral-response descriptors rather than as a stand-alone adsorption-strength model.

## COHP/ICOHP and LOBSTER analysis

Chemical-bonding analysis was performed with LOBSTER 5.1.1 using the `pbeVaspFit2015` basis set and recommended basis functions. The preserved LOBSTER inputs use a COHP energy range from −15 to +5 eV, a Gaussian smearing width of 0.05 eV and `skipMadelungEnergy`. Native pCOHP signs were retained during extraction; figures that use −pCOHP or −ICOHP state that sign convention explicitly. All manuscript-facing Co–O interaction pairs were assigned from the current structures and validated by direct minimum-image distances against the corresponding ICOHPLIST entries rather than by historical atom labels. The four formal LOBSTER runs completed normally, and the recorded absolute spin charge spilling is below 2%. Warnings retained in the provenance files, including Gaussian-smearing fallback and the pristine-*OH band-overlap orthonormalization warning, were not suppressed.

LOBSTER Mulliken and Löwdin orbital populations were also used as an independent cross-check of spin-selective redistribution. Orbital-resolved labels refer to the native global Cartesian projections. Because the archived projections do not contain all phase/cross terms required for arbitrary local-axis rotations, these components are not promoted to exact local ligand-field eg/t2g or sigma/pi assignments.

## Bader analysis

Bader-assigned electron populations were extracted from the matched fixed-geometry VASP calculations using the validated atom mapping. For the *OH→*O comparison, ΔNBader = NBader(*O) − NBader(*OH) was evaluated for the active Co, adsorbate O, bridge O and neighboring Co/Al site. Bader values are used only as a net charge-partition cross-check and not as formal oxidation states.

## Data reduction, visualization and reproducibility

All manuscript-facing numerical figures are regenerated from software-neutral CSV/TSV tables stored together with the plotting scripts. COHP/ICOHP, PDOS, Bader, d-band-center, neighbor-site and LOBSTER-population panels are derived from the synchronized VASP/LOBSTER tables; cDFT panels are derived from the validated CP2K population/constraint tables; reaction-density panels retain the sampled numerical grids and mapping metadata. Raster and vector exports are provided wherever available. The complete collaborator package includes a SHA256 manifest that maps every copied file back to its canonical location in the project repository.

## Parameters to verify before journal submission

The compact repository does not mirror the complete historical VASP `INCAR`, `KPOINTS`, `POTCAR` provenance for every static calculation. The original server-side paths and hashes are retained in the copied provenance/source-manifest files, but the following conventional VASP details should be checked directly against those source directories before this Methods section is frozen: VASP version/build; plane-wave energy cutoff; k-point mesh; smearing/occupation settings; electronic convergence criterion; PAW dataset labels; and the exact VASP-side DFT+U tags used for the matched statics. These values are deliberately **not guessed** here.

Likewise, a crystallographic Miller index is not assigned to the CoOOH surface in this document because the validated structure provenance currently establishes the periodic cell and atomic coordinates but not an unambiguous facet label. If the original slab-construction record is recovered, that facet can be added at final manuscript assembly.
