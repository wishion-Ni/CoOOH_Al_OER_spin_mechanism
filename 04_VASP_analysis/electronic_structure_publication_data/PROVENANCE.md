# COHP / ICOHP / PDOS synchronization provenance

## Scope

This package contains compact tables extracted from the already completed
formal VASP/LOBSTER OH and O statics. No VASP, LOBSTER or CP2K calculation was
started for this synchronization.

## Source locations

The authoritative server root is:

`/home/ftfan/ncw/sfs/CoOH/cp2k/Al16/oer/spin_config_scan_site03_5OH_current_20260714/vasp_jacs6c06054_reconstructed_exact_Al16_3x2_20260809/electronic_structure_al_contribution_20260818`

COHP/ICOHP/LOBSTER sources are under:

`cohp_bader_formal_oh_o_20260822/{undoped_control/OH_pair_corrected_nomadelung,undoped_control/O_nomadelung,Al16_adjacent/OH_nomadelung,Al16_adjacent/O_nomadelung}`

The matching VASP PDOS sources are under:

`cohp_oh_o_corrected_20260820/{undoped_control/OH,undoped_control/O,Al16_adjacent/OH,Al16_adjacent/O}/DOSCAR`

The complete source filenames, byte sizes and SHA256 values are recorded in
`source_manifest.tsv`. Long per-row source fields use a manifest key; the
corresponding absolute path and SHA256 are in `source_manifest.tsv`. Large raw
COHPCAR, DOSCAR and vasprun files remain on the authorized server and were not
copied into this repository.

## Extraction

The extraction was performed on the server by
`tools/remote_extract_cohp_pdos_sync.py`, which sent a standard-library
parser to the server and wrote compact tables under
`/home/ftfan/ncw/sync_server_extract_20260913_run4`. The compact tables were
then copied to this package through the authorized SSH connection.

COHPCAR was parsed using the native `Average` plus interaction-column layout;
the `Average` column was excluded from the pair table. Native pCOHP signs are
preserved in `pCOHP_raw`, and `minus_pCOHP` is exactly `-pCOHP_raw`.

PDOS was parsed from the matching VASP `DOSCAR`. Native site/orbital
components were retained for TDOS, active Co d, adsorbate O p, bridge O p and
the neighboring metal site; non-diagnostic site/orbital components were
excluded from the compact table. Energies were shifted by the native VASP Fermi
energy and restricted to -8 to +4 eV for a compact publication-data table.
The native Fermi energies were -3.34736655, -3.39977505, -3.30884118 and
-3.30217436 eV for pristine OH, pristine O, Al16 OH and Al16 O, respectively.

## Structure and bond mapping

Roles were determined from the active-site definition and the current
`POSCAR.lobster.vasp`, then checked against the current ICOHPLIST and direct
minimum-image distances. The active Co is Co21 for pristine and Co16 for Al16.
The adsorbate O is the shorter active-Co/O interaction listed in the current
ICOHPLIST; the bridge O is the O shared by active Co and the nearest second
metal interaction. The nearest terminal H to that bridge O is recorded in the
site mapping but is not used as a COHP publication pair.

The required mapping table is
`mapping/structure_and_bond_mapping.tsv`. Distances in that table are
recomputed from the associated structure, not copied from historical pair
labels. The corresponding ICOHPLIST distance is retained in the validation
note.

## Software and quality

The source runs report LOBSTER 5.1.1 with recommended basis functions. All four
runs finished normally, recovered the expected electron count within the
reported projection precision, and have spin absolute charge spilling below
2 percent. Warnings about reading k-points from `vasprun.xml` and fallback to
Gaussian smearing are retained in `COHP/source_data/lobster_quality.tsv`.
The pristine OH source also reports one band-overlap orthonormalization
warning; it is retained and should be considered when using that state for
quantitative orbital claims.

## Status and limitations

All four requested states have compact COHP/ICOHP and PDOS tables. The data
are validated for synchronization and mapping. They are not silently promoted
to a universal publication-ready orbital interpretation: the COHP values are
pairwise, spin-resolved projections with method-dependent spilling and the
PDOS comparison is a site fingerprint, not a band-index identity. No
orbital-resolved COHP was fabricated.

