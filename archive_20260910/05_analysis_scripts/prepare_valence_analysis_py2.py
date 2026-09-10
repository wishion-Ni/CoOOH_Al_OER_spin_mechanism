#!/usr/bin/env python
from __future__ import print_function

import os
import re


BASE = os.getcwd()
OER = os.path.join(BASE, "oer")
VA = os.path.join(BASE, "valence_analysis")

SITES = {
    "site01_surface_Co13_adjAl": {
        "active_index": 13,
        "label": "Co13",
        "element": "Co",
        "role": "surface Al-neighbor Co",
    },
    "site02_surface_Al47": {
        "active_index": 47,
        "label": "Al47",
        "element": "Al",
        "role": "surface doped Al",
    },
    "site03_bulk_Co7_adjAl": {
        "active_index": 7,
        "label": "Co7",
        "element": "Co",
        "role": "bulk Al-neighbor Co",
    },
    "site04_far_Co19": {
        "active_index": 19,
        "label": "Co19",
        "element": "Co",
        "role": "far Co reference",
    },
}

MULTS = {
    "O": [1, 3, 5],
    "OH": [2, 4, 6],
    "OOH": [2, 4, 6],
}

ADS_INDICES = {
    "O": [211],
    "OH": [211, 212],
    "OOH": [211, 212, 213],
}


def mkdir_p(path):
    if not os.path.isdir(path):
        os.makedirs(path)


def read_text(path):
    with open(path, "r") as f:
        return f.read()


def write_text(path, text):
    d = os.path.dirname(path)
    if d:
        mkdir_p(d)
    with open(path, "w") as f:
        f.write(text)


def parse_manifest():
    path = os.path.join(OER, "submission_manifest.tsv")
    rows = []
    lines = read_text(path).splitlines()
    for line in lines[1:]:
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) < 6:
            continue
        rows.append(
            {
                "site": parts[0],
                "intermediate": parts[1],
                "rel": parts[2],
                "project": parts[3],
                "atoms": int(parts[4]),
                "status": parts[5],
            }
        )
    return rows


def last_energy(out_text):
    vals = re.findall(
        r"ENERGY\| Total FORCE_EVAL \( QS \) energy \[a\.u\.\]:\s+([-0-9.]+)",
        out_text,
    )
    if vals:
        return vals[-1]
    return ""


def parse_population_block(lines, header_re, kind):
    starts = []
    for i, line in enumerate(lines):
        if re.search(header_re, line):
            starts.append(i)
    if not starts:
        return {}
    data = {}
    i = starts[-1] + 1
    while i < len(lines):
        line = lines[i].strip()
        i += 1
        if not line:
            if data:
                break
            continue
        parts = line.split()
        if not parts or not parts[0].isdigit():
            if data:
                break
            continue
        try:
            idx = int(parts[0])
            elem = parts[1]
            if kind == "mulliken":
                data[idx] = {
                    "element": elem,
                    "charge": float(parts[-2]),
                    "spin": float(parts[-1]),
                }
            else:
                data[idx] = {
                    "element": elem,
                    "charge": float(parts[-1]),
                    "spin": float(parts[-2]),
                }
        except Exception:
            pass
    return data


def parse_populations(out_text):
    lines = out_text.splitlines()
    mull = parse_population_block(
        lines, r"#\s+Atom\s+Element\s+Kind\s+Atomic population", "mulliken"
    )
    hir = parse_population_block(
        lines, r"#Atom\s+Element\s+Kind\s+Ref Charge", "hirshfeld"
    )
    return mull, hir


def parse_last_xyz(path):
    lines = [x.strip() for x in read_text(path).splitlines() if x.strip()]
    frames = []
    i = 0
    while i < len(lines):
        try:
            n = int(lines[i])
        except Exception:
            break
        title = lines[i + 1] if i + 1 < len(lines) else ""
        coords = []
        for line in lines[i + 2 : i + 2 + n]:
            p = line.split()
            coords.append((p[0], float(p[1]), float(p[2]), float(p[3])))
        frames.append((title, coords))
        i += n + 2
    if not frames:
        raise RuntimeError("no XYZ frames in %s" % path)
    return frames[-1]


def make_spin_input(template, coords, project, multiplicity):
    text = template
    text = re.sub(
        r"(\n\s*PROJECT\s+)\S+",
        lambda m: m.group(1) + project,
        text,
        count=1,
    )
    text = re.sub(
        r"(\n\s*RUN_TYPE\s+)\S+",
        lambda m: m.group(1) + "ENERGY_FORCE",
        text,
        count=1,
    )
    text = re.sub(
        r"(\n\s*MULTIPLICITY\s+)\d+",
        lambda m: m.group(1) + str(multiplicity),
        text,
        count=1,
    )
    coord_lines = ["    &COORD"]
    for elem, x, y, z in coords:
        coord_lines.append("      %-2s %16.10f %16.10f %16.10f" % (elem, x, y, z))
    coord_lines.append("    &END COORD")
    text = re.sub(
        r"    &COORD\b.*?    &END COORD",
        "\n".join(coord_lines),
        text,
        count=1,
        flags=re.S,
    )
    text = re.sub(r"\n&MOTION\b.*?\n&END MOTION\s*", "\n", text, count=1, flags=re.S)
    return text


SLURM = """#!/bin/bash
#SBATCH -J {job}
#SBATCH --nodes=1
#SBATCH --ntasks=40
#SBATCH --partition=n40
#SBATCH --error=%J.stderr
#SBATCH --output=%J.stdout

export LD_LIBRARY_PATH=/apps/soft/gmp620/lib:$LD_LIBRARY_PATH
export LD_LIBRARY_PATH=/apps/soft/mpfr410/lib:$LD_LIBRARY_PATH
export LD_LIBRARY_PATH=/apps/soft/mpc120/lib:$LD_LIBRARY_PATH
export LD_LIBRARY_PATH=/apps/soft/gcc840/lib64:$LD_LIBRARY_PATH
export PATH=/apps/soft/gcc840/bin:$PATH

CP2K_ROOT=/apps/soft/cp2k-2024.1
source ${CP2K_ROOT}/tools/toolchain/install/setup
export PATH=$PATH:${CP2K_ROOT}/exe/local
export CP2K_DATA_DIR=${CP2K_ROOT}/data

NPROCS=$SLURM_NTASKS
ulimit -s unlimited
INPUT=$1
OUTPUT=`echo ${INPUT} | awk -F'.' '{{print $1".out"}}'`
ERR=`echo ${INPUT} | awk -F'.' '{{print $1".err"}}'`
mpirun -np ${NPROCS} cp2k.popt ${INPUT} 1>${OUTPUT} 2>${ERR}
"""


SUBMIT_SCRIPT = """#!/bin/bash
set -euo pipefail

MAX_RUNNING=${1:-5}
PREFIX="Al16_spin_"

running=$(squeue -h -u "$USER" -o "%j %T" | awk -v p="$PREFIX" '$1 ~ "^"p && ($2=="RUNNING" || $2=="PENDING") {c++} END {print c+0}')
slots=$((MAX_RUNNING - running))
if [ "$slots" -le 0 ]; then
  echo "No slots available: ${running}/${MAX_RUNNING} ${PREFIX} jobs already RUNNING/PENDING."
  exit 0
fi

submitted=0
while IFS=$'\t' read -r site intermediate source spin_project mult rel status; do
  [ "$site" = "site" ] && continue
  [ "$status" = "candidate_not_submitted" ] || continue
  [ "$submitted" -lt "$slots" ] || break
  inp="${spin_project}.inp"
  echo "Submit: $rel/$inp"
  pushd "$rel" >/dev/null
  sbatch_out=$(sbatch cp2k "$inp")
  popd >/dev/null
  jobid=$(printf '%s\n' "$sbatch_out" | awk '{print $NF}')
  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "$(date '+%F %T')" "$jobid" "$site" "$intermediate" "$spin_project" "$mult" "submitted" >> submitted_spin_jobs.tsv
  tmp=$(mktemp)
  awk -F'\t' -v OFS='\t' -v r="$rel" -v jid="$jobid" 'NR==1 {print; next} $6==r && $7=="candidate_not_submitted" {$7="submitted_"jid} {print}' spin_scan_manifest.tsv > "$tmp"
  mv "$tmp" spin_scan_manifest.tsv
  echo "$sbatch_out"
  submitted=$((submitted + 1))
done < spin_scan_manifest.tsv

echo "Submitted ${submitted}; active cap ${MAX_RUNNING}."
"""


def main():
    mkdir_p(VA)
    mkdir_p(os.path.join(VA, "01_population_summary"))
    mkdir_p(os.path.join(VA, "02_spin_scan"))
    mkdir_p(os.path.join(VA, "03_cdft_design"))

    rows = parse_manifest()
    completed = [r for r in rows if r["status"].startswith("completed_")]

    summary_lines = [
        "site\tintermediate\tproject\tstatus\tatom_index\telement\tmulliken_charge\tmulliken_spin\thirshfeld_charge\thirshfeld_spin\tenergy_au"
    ]
    scan_lines = [
        "site\tintermediate\tsource_project\tspin_project\tmultiplicity\trelative_directory\tstatus"
    ]

    prepared = 0
    for r in completed:
        task_dir = os.path.join(OER, r["rel"])
        out_path = os.path.join(task_dir, r["project"] + ".out")
        inp_path = os.path.join(task_dir, r["project"] + ".inp")
        xyz_path = os.path.join(task_dir, r["project"] + "-pos-1.xyz")
        if not os.path.isfile(out_path):
            continue
        out_text = read_text(out_path)
        mull, hir = parse_populations(out_text)
        energy = last_energy(out_text)
        atom_indices = [SITES[r["site"]]["active_index"]] + ADS_INDICES.get(
            r["intermediate"], []
        )
        for idx in atom_indices:
            m = mull.get(idx, {})
            h = hir.get(idx, {})
            summary_lines.append(
                "\t".join(
                    [
                        r["site"],
                        r["intermediate"],
                        r["project"],
                        r["status"],
                        str(idx),
                        str(m.get("element", h.get("element", ""))),
                        str(m.get("charge", "")),
                        str(m.get("spin", "")),
                        str(h.get("charge", "")),
                        str(h.get("spin", "")),
                        energy,
                    ]
                )
            )
        ads = ADS_INDICES.get(r["intermediate"], [])
        if ads:
            mq = sum([mull.get(i, {}).get("charge", 0.0) for i in ads])
            ms = sum([mull.get(i, {}).get("spin", 0.0) for i in ads])
            hq = sum([hir.get(i, {}).get("charge", 0.0) for i in ads])
            hs = sum([hir.get(i, {}).get("spin", 0.0) for i in ads])
            summary_lines.append(
                "\t".join(
                    [
                        r["site"],
                        r["intermediate"],
                        r["project"],
                        r["status"],
                        "adsorbate_sum",
                        "ads",
                        "%.6f" % mq,
                        "%.6f" % ms,
                        "%.6f" % hq,
                        "%.6f" % hs,
                        energy,
                    ]
                )
            )

        if os.path.isfile(inp_path) and os.path.isfile(xyz_path):
            template = read_text(inp_path)
            title, coords = parse_last_xyz(xyz_path)
            for mult in MULTS[r["intermediate"]]:
                spin_project = "Al16_spin_%s_M%d" % (r["project"].replace("Al16_", ""), mult)
                rel = os.path.join(
                    "02_spin_scan", r["site"], r["intermediate"], "M%d" % mult
                )
                out_dir = os.path.join(VA, rel)
                mkdir_p(out_dir)
                write_text(
                    os.path.join(out_dir, spin_project + ".inp"),
                    make_spin_input(template, coords, spin_project, mult),
                )
                write_text(
                    os.path.join(out_dir, "cp2k"),
                    SLURM.replace("{job}", spin_project[:32]),
                )
                scan_lines.append(
                    "\t".join(
                        [
                            r["site"],
                            r["intermediate"],
                            r["project"],
                            spin_project,
                            str(mult),
                            rel,
                            "candidate_not_submitted",
                        ]
                    )
                )
                prepared += 1

    write_text(
        os.path.join(VA, "01_population_summary", "population_summary_completed.tsv"),
        "\n".join(summary_lines) + "\n",
    )
    write_text(
        os.path.join(VA, "spin_scan_manifest.tsv"), "\n".join(scan_lines) + "\n"
    )
    if not os.path.isfile(os.path.join(VA, "submitted_spin_jobs.tsv")):
        write_text(
            os.path.join(VA, "submitted_spin_jobs.tsv"),
            "time\tjobid\tsite\tintermediate\tspin_project\tmultiplicity\tstatus\n",
        )
    write_text(os.path.join(VA, "submit_spin_next_batch.sh"), SUBMIT_SCRIPT)
    write_text(
        os.path.join(VA, "README.md"),
        "# Al16 Valence Analysis\n\n"
        "Population summaries and spin-scan candidate inputs for completed OER states.\n"
        "Spin scan jobs are prepared but not submitted automatically.\n",
    )
    write_text(
        os.path.join(VA, "03_cdft_design", "cdft_fragment_plan.md"),
        "# cDFT Fragment Plan\n\n"
        "Use after OER and spin-scan results identify key intermediates.\n"
        "Candidate fragments: active metal, adsorbate, active metal plus adsorbate, "
        "and active metal plus nearest lattice O shell plus adsorbate.\n"
        "CP2K cDFT constrains local charge/spin; formal Co valence must be inferred "
        "from constrained-state energy, local charge, local spin, and bond lengths.\n",
    )
    print("completed_oer_states", len(completed))
    print("spin_scan_candidates", prepared)
    print("valence_analysis", VA)


if __name__ == "__main__":
    main()
