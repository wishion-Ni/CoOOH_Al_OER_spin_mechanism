# Upload Exclusions for This Snapshot

The following selected files remain in the local archive staging directory but are omitted from the GitHub tree in this snapshot because the connector upload path is intended for inspectable text and moderate-size figures. Their paths, sizes and provenance are retained in `archive_manifest.tsv`.

- `00_project_management/archive_manifest.tsv` (1,066,404 bytes): split copies are uploaded as `archive_manifest_part1.tsv` and `archive_manifest_part2.tsv`.
- `04_VASP_analysis/orbital_assignment/frontier_orbitalwise_COHP.tsv` (1,061,141 bytes): large processed table; source manifest retained.
- `04_VASP_analysis/orbital_assignment/six_CoO_bond_COHP.tsv` (1,890,746 bytes): large processed table; source manifest retained.
- `04_VASP_analysis/orbital_assignment/frontier_level_postprocess/selected_cohp_full.tsv` (1,146,572 bytes): large processed table; source manifest retained.
- Four `COHPCAR.lobster` files in `04_VASP_analysis/orbital_assignment/lobster_sixbond/*` (2.7-2.9 MB each): large raw COHP curves; validated ICOHPLIST, lobsterout and processed summaries are uploaded.
- `06_figures/candidate/mechanism_oh_to_o_spin_ligand_field_image2_20260831.png` and `startup_density_proxy_undoped_vs_Al16_20260831.png` (about 1.1 MB each): figure variants; smaller/primary versions are uploaded.

No scientific result is deleted or relabeled by this omission. Full local data remain available in the project workspace.
