from __future__ import print_function

import os

import deploy_lobster_preconverged_20260819 as deployment


BASE_O_COUNT = 138
ANALYSIS_ROOT = os.path.dirname(deployment.DEST)
STRICT_ROOT = deployment.ROOT


def append_unique(path, line):
    text = open(path).read() if os.path.isfile(path) else ""
    if line not in text:
        with open(path, "a") as handle:
            handle.write(line)


def active_extra_indices(state, elements):
    oxygen = [index for index, element in enumerate(elements, 1) if element == "O"]
    first = BASE_O_COUNT + 3
    indices = [oxygen[first - 1]]
    if state == "OOH_o03":
        indices.append(oxygen[first])
    return indices


def main():
    audit = []
    valid_jobs = []
    bare_pairs = []
    statuses = {}

    for branch, state, active_index, adjacent_index in deployment.CASES:
        case_rel = os.path.join(branch, state)
        case = os.path.join(deployment.DEST, case_rel)
        if state == "bare":
            valid_jobs.append(case_rel)
            pair_path = os.path.join(case, "PAIR_INFO.tsv")
            for line in open(pair_path).read().splitlines()[1:]:
                bare_pairs.append((branch, state, line))
            statuses[(branch, state)] = "bare_geometry_valid_binary_missing_likely_more_NBANDS"
            continue

        source = os.path.join(deployment.SOURCE, branch, state, "POSCAR")
        cell, elements, positions = deployment.read_poscar(source)
        expected = active_extra_indices(state, elements)
        nearest_labels = []
        for oxygen_index in expected:
            designated_distance = deployment.distance(
                positions[active_index - 1], positions[oxygen_index - 1], cell
            )
            nearest_distance, nearest_index = deployment.nearest_index(
                oxygen_index, {"Co", "Al"}, elements, positions, cell
            )
            nearest_label = "%s%d" % (elements[nearest_index - 1], nearest_index)
            nearest_labels.append(nearest_label)
            audit.append(
                (
                    branch,
                    state,
                    oxygen_index,
                    active_index,
                    designated_distance,
                    nearest_index,
                    elements[nearest_index - 1],
                    nearest_distance,
                )
            )
        reason = (
            "REJECTED: constructed active adsorbate atom(s) %s are not bound to designated Co%d; "
            "nearest mapped metal(s): %s. Do not use this case for adjacent-Al COHP or Bader/PDOS interpretation.\n"
            % (",".join("O%d" % value for value in expected), active_index, ",".join(nearest_labels))
        )
        with open(os.path.join(case, "BLOCKED_REASON.txt"), "w") as handle:
            handle.write(reason)
        with open(os.path.join(case, "lobsterin"), "w") as handle:
            handle.write("# " + reason)
        statuses[(branch, state)] = "rejected_constructed_adsorbate_not_on_designated_active_site"

    audit_path = os.path.join(deployment.DEST, "site_mapping_audit.tsv")
    with open(audit_path, "w") as handle:
        handle.write(
            "branch\tstate\tconstructed_ads_O\tdesignated_active_Co\tdistance_to_designated_Co_A\t"
            "nearest_metal\tnearest_element\tdistance_to_nearest_metal_A\tdecision\n"
        )
        for row in audit:
            handle.write(
                "%s\t%s\t%d\t%d\t%.6f\t%d\t%s\t%.6f\treject_for_adjacent_Al_analysis\n"
                % row
            )

    validation_path = os.path.join(deployment.DEST, "validation_manifest.tsv")
    lines = open(validation_path).read().splitlines()
    output = [lines[0]]
    for line in lines[1:]:
        fields = line.split("\t")
        fields[-1] = statuses[(fields[0], fields[1])]
        output.append("\t".join(fields))
    with open(validation_path, "w") as handle:
        handle.write("\n".join(output) + "\n")

    with open(os.path.join(deployment.DEST, "jobs_all_audited.list"), "w") as handle:
        handle.write("\n".join(os.path.join(branch, state) for branch, state, _, _ in deployment.CASES) + "\n")
    with open(os.path.join(deployment.DEST, "jobs.list"), "w") as handle:
        handle.write("\n".join(valid_jobs) + "\n")

    with open(os.path.join(deployment.DEST, "pair_manifest.tsv"), "w") as handle:
        handle.write("branch\tstate\trole\tatom1\telement1\tatom2\telement2\tdistance_A\n")
        for branch, state, line in bare_pairs:
            handle.write("%s\t%s\t%s\n" % (branch, state, line))

    with open(os.path.join(deployment.DEST, "run_lobster_array.slurm"), "w") as handle:
        handle.write(
            """#!/bin/bash
#SBATCH --job-name=cohp_bare_preconv
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --partition=n28
#SBATCH --array=0-1%1
#SBATCH --output=array_%A_%a.stdout
#SBATCH --error=array_%A_%a.stderr

set -eu
ROOT_DIR=$(cd "$(dirname "$0")" && pwd)
CASE=$(sed -n "$((SLURM_ARRAY_TASK_ID + 1))p" "$ROOT_DIR/jobs.list")
cd "$ROOT_DIR/$CASE"
if [ -f BLOCKED_REASON.txt ]; then
  cat BLOCKED_REASON.txt >&2
  exit 2
fi
LOBSTER_BIN=${LOBSTER_BIN:-}
if [ -z "$LOBSTER_BIN" ] || [ ! -x "$LOBSTER_BIN" ]; then
  echo "BLOCKED: set LOBSTER_BIN to a licensed executable under the allowed project roots." >&2
  exit 3
fi
for file in INCAR KPOINTS POSCAR POTCAR OUTCAR WAVECAR vasprun.xml lobsterin; do
  if [ ! -s "$file" ]; then
    echo "BLOCKED: missing $file in $CASE" >&2
    exit 4
  fi
done
"$LOBSTER_BIN"
grep -q "finished" lobsterout
"""
        )

    with open(os.path.join(deployment.DEST, "README.md"), "w") as handle:
        handle.write(
            """# Preliminary LOBSTER COHP deployment

- A construction audit rejected OH, O and OOH for the intended adjacent-Al comparison.
- The constructed active adsorbates are on Co42 (Al16) and Co51 (control), not designated Co16/Co21.
- Only the two bare cases remain staged, using relative links to normally terminated VASP data.
- Bare NBANDS is below a conservative recommended-orbital count; a licensed LOBSTER dry run is required.
- No LOBSTER executable or license is present under the allowed roots, so no job was submitted.
- Final COHP must use chemically corrected models and final strict relaxed static wavefunctions.
"""
        )

    analysis_manifest = os.path.join(ANALYSIS_ROOT, "analysis_manifest.tsv")
    lines = open(analysis_manifest).read().splitlines()
    updated = [lines[0]]
    for line in lines[1:]:
        fields = line.split("\t")
        if fields[2] != "bare":
            fields[-1] += ";rejected_for_adjacent_Al_interpretation_constructed_adsorbate_site_mismatch"
        updated.append("\t".join(fields))
    with open(analysis_manifest, "w") as handle:
        handle.write("\n".join(updated) + "\n")

    note = (
        "2026-08-19\tconstruction_validation_rejection\tNA\tNA\tNA\tNA\t"
        "OH_O_OOH_constructed_adsorbates_on_Al16_Co42_control_Co51_not_designated_Co16_Co21;"
        "COHP_adsorbate_cases_blocked;running_jobs_untouched_pending_user_confirmation\n"
    )
    append_unique(os.path.join(ANALYSIS_ROOT, "scheduler_manifest.tsv"), note)
    append_unique(os.path.join(STRICT_ROOT, "scheduler_manifest.tsv"), note)
    print(audit_path)
    for row in audit:
        print("%s\t%s\tO%d\tCo%d\t%.6f\t%s%d\t%.6f" % (
            row[0], row[1], row[2], row[3], row[4], row[6], row[5], row[7]
        ))


if __name__ == "__main__":
    main()
