from __future__ import print_function

import os


ROOT = (
    "sfs/CoOH/cp2k/Al16/oer/spin_config_scan_site03_5OH_current_20260714/"
    "vasp_jacs6c06054_reconstructed_exact_Al16_3x2_20260809/"
    "corrected_adsorbates_20260819"
)
OLD = 'ROOT_DIR=$(cd "$(dirname "$0")" && pwd)'
NEW = 'ROOT_DIR=${SLURM_SUBMIT_DIR:?SLURM_SUBMIT_DIR_is_not_set}'


def replace_once(path):
    text = open(path).read()
    if NEW in text:
        return
    if text.count(OLD) != 1:
        raise RuntimeError("expected one obsolete ROOT_DIR line in " + path)
    updated = text.replace(OLD, NEW)
    temporary = path + ".tmp"
    with open(temporary, "w") as handle:
        handle.write(updated)
    os.rename(temporary, path)


def append_unique(path, line):
    text = open(path).read()
    if line in text:
        return
    with open(path, "a") as handle:
        handle.write(line + "\n")


def main():
    replace_once(os.path.join(ROOT, "preconverge_array.slurm"))
    replace_once(os.path.join(ROOT, "build_corrected_adsorbates.py"))
    append_unique(
        os.path.join(ROOT, "scheduler_manifest.tsv"),
        "2026-08-19\tnonscientific_scheduler_failure\t111236_0-5\tn40\t40\t2\t"
        "zero_second_exit2;batch_copy_used_script_dir;no_VASP_started;rejected",
    )
    print(os.path.join(ROOT, "preconverge_array.slurm"))


if __name__ == "__main__":
    main()
