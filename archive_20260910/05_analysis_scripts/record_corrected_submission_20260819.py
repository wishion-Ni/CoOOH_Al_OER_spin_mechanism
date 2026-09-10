from __future__ import print_function

import os


PARENT = (
    "sfs/CoOH/cp2k/Al16/oer/spin_config_scan_site03_5OH_current_20260714/"
    "vasp_jacs6c06054_reconstructed_exact_Al16_3x2_20260809"
)
ELECTRONIC = os.path.join(PARENT, "electronic_structure_al_contribution_20260818")
CORRECTED = os.path.join(PARENT, "corrected_adsorbates_20260819")


def append_unique(path, line):
    text = open(path).read()
    if line in text:
        return
    with open(path, "a") as handle:
        handle.write(line + "\n")


def main():
    append_unique(
        os.path.join(CORRECTED, "scheduler_manifest.tsv"),
        "2026-08-19\tcorrected_preconvergence_submission\t111242_0-5\tn40\t40\t2\t"
        "six_validated_OH_O_OOH_states;SLURM_SUBMIT_DIR_recovery;no_duplicates",
    )
    append_unique(
        os.path.join(PARENT, "scheduler_manifest.tsv"),
        "2026-08-19\tuser_authorized_cancellation\t"
        "110989_2,111001_3,111004_4,111049_5,111005_6,111088_7\tmixed\tmixed\tNA\t"
        "invalid_adsorbate_site_mapping;outputs_preserved;no_duplicates",
    )
    append_unique(
        os.path.join(PARENT, "scheduler_manifest.tsv"),
        "2026-08-19\tcorrected_preconvergence_submission\t111242_0-5\tn40\t40\t2\t"
        "molecule_aware_minimum_image;Co16_Al51_vs_Co21_Co23;independent_validation_passed",
    )
    append_unique(
        os.path.join(PARENT, "scheduler_manifest.tsv"),
        "2026-08-19\tbare_construction_reaudit\t110978_0,110989_1\tmixed\tmixed\tNA\t"
        "active_vacancy_occupied_by_wrapped_background_OH;do_not_use_for_intended_site;"
        "jobs_unchanged_pending_explicit_user_confirmation",
    )
    append_unique(
        os.path.join(ELECTRONIC, "scheduler_manifest.tsv"),
        "2026-08-19\tuser_authorized_cancellation\t111172_3-7\tn28\t28\t1\t"
        "invalid_adsorbate_site_mapping;111172_2_completed_but_rejected;no_duplicates",
    )
    append_unique(
        os.path.join(ELECTRONIC, "scheduler_manifest.tsv"),
        "2026-08-19\tbare_construction_reaudit\t111172_0-1,111190,111192,111193\tmixed\tmixed\tNA\t"
        "numerically_valid_outputs_but_rejected_for_intended_active_vacancy_mechanism;"
        "background_OH_periodic_image_shift",
    )
    analysis = os.path.join(ELECTRONIC, "analysis_manifest.tsv")
    source_root = os.path.join(PARENT, "electronic_preconverge_20260810")
    append_unique(
        analysis,
        "0\tAl16_adjacent\tbare\t%s\tpreconverged_fixed\tvalidated_preconvergence_CHGCAR\t"
        "construction_reaudit\trejected_for_intended_active_vacancy_mechanism_background_OH_image_shift"
        % os.path.join(source_root, "Al16_adjacent", "bare"),
    )
    append_unique(
        analysis,
        "1\tundoped_control\tbare\t%s\tpreconverged_fixed\tvalidated_preconvergence_CHGCAR\t"
        "construction_reaudit\trejected_for_intended_active_vacancy_mechanism_background_OH_image_shift"
        % os.path.join(source_root, "undoped_control", "bare"),
    )
    print("recorded", CORRECTED)


if __name__ == "__main__":
    main()
