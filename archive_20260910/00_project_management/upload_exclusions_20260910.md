# Upload Exclusions for This Snapshot

The following selected files remain in the local archive staging directory but are omitted from the GitHub tree in this snapshot because the connector upload path is intended for inspectable text and moderate-size figures. Their paths, sizes and provenance are retained in `archive_manifest.tsv`. Compressed GitHub-preview copies of the large figures are included where useful.

- `00_project_management/archive_manifest.tsv` (1,066,404 bytes): split copies are retained locally; the uploadable inventory is represented by the two split files when within the connector size limit.
- `00_project_management/archive_manifest_part1.tsv` (544,055 bytes) and `archive_manifest_part2.tsv` (522,394 bytes): above the conservative per-file transfer threshold; retain the complete local manifest.
- `04_VASP_analysis/cooh_al16_stage_summary_20260819.png` (533,500 bytes): a compressed GitHub-preview copy is included.
- `04_VASP_analysis/orbital_assignment/frontier_orbitalwise_COHP.tsv` (1,061,141 bytes): large processed table; source manifest retained.
- `04_VASP_analysis/orbital_assignment/six_CoO_bond_COHP.tsv` (1,890,746 bytes): large processed table; source manifest retained.
- `04_VASP_analysis/orbital_assignment/frontier_level_postprocess/selected_cohp_full.tsv` (1,146,572 bytes): large processed table; source manifest retained.
- `04_VASP_analysis/orbital_assignment/frontier_level_postprocess/selected_pdos_full.tsv` (667,110 bytes): large processed table; source manifest retained.
- `04_VASP_analysis/orbital_assignment_20260903.zip` (527,945 bytes): preserved locally; its unpacked selected contents are uploaded.
- Four `COHPCAR.lobster` files in `04_VASP_analysis/orbital_assignment/lobster_sixbond/*` (2.7-2.9 MB each): large raw COHP curves; validated ICOHPLIST, lobsterout and processed summaries are uploaded.
- `06_figures/candidate/bader_charge_structure_map_20260823.png` (911,843 bytes), `reaction_density_undoped_vs_Al16_final_20260901.png` (1,046,437 bytes), `mechanism_oh_to_o_spin_ligand_field_image2_20260831.png` (1,121,215 bytes), and `startup_density_proxy_undoped_vs_Al16_20260831.png` (1,147,396 bytes): compressed GitHub-preview copies are included.

No scientific result is deleted or relabeled by this omission. Full local data remain available in the project workspace.
