from __future__ import annotations

import importlib.util
import posixpath
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / ".codex/skills/ftfan-ncw-ssh/scripts/ssh_ncw.py"
spec = importlib.util.spec_from_file_location("ssh_ncw", HELPER)
ssh_ncw = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(ssh_ncw)

THERMO = "sfs/CoOH/cp2k/thermo_vib_5OH_U100_current_20260704"
REMOTE_BASE = posixpath.join(THERMO, "cdft_charge_spin_undoped_20260816")
SOURCE_BASE = posixpath.join(
    THERMO, "undoped_001333/site01_surface_Co32"
)

CASES = {
    "undoped_valid_co32_OH": {
        "input": posixpath.join(
            SOURCE_BASE, "OH/retry2_resubmit/Undoped_currvib_OH.inp"
        ),
        "wfn": posixpath.join(
            SOURCE_BASE,
            "OH/retry2_resubmit/Undoped_currvib_OH-RESTART.wfn",
        ),
        "active": 32,
        "adsorbate": (211, 212),
        "composition": (48, 60, 114),
    },
    "undoped_valid_co32_O": {
        "input": posixpath.join(
            SOURCE_BASE, "O/retry2_resubmit/Undoped_currvib_O.inp"
        ),
        "wfn": posixpath.join(
            SOURCE_BASE,
            "O/retry2_resubmit/Undoped_currvib_O-RESTART.wfn",
        ),
        "active": 32,
        "adsorbate": (211,),
        "composition": (48, 59, 114),
    },
    "undoped_valid_co32_OOH": {
        "input": posixpath.join(SOURCE_BASE, "OOH/Undoped_currvib_OOH.inp"),
        "wfn": posixpath.join(
            SOURCE_BASE, "OOH/Undoped_currvib_OOH-RESTART.wfn"
        ),
        "active": 32,
        "adsorbate": (211, 212, 213),
        "composition": (48, 60, 115),
    },
}


def read_text(sftp, rel: str) -> str:
    with sftp.open(posixpath.join(ssh_ncw.REMOTE_ROOT, rel), "r") as handle:
        return handle.read().decode(errors="replace")


def write_text(sftp, rel: str, content: str) -> None:
    with sftp.open(posixpath.join(ssh_ncw.REMOTE_ROOT, rel), "w") as handle:
        handle.write(content)


def mkdir_p(sftp, rel: str) -> None:
    current = ssh_ncw.REMOTE_ROOT
    for part in rel.split("/"):
        current = posixpath.join(current, part)
        try:
            sftp.stat(current)
        except FileNotFoundError:
            sftp.mkdir(current)


def run(client, command: str) -> str:
    _, stdout, stderr = client.exec_command(
        f"cd {ssh_ncw.REMOTE_ROOT} && {command}"
    )
    code = stdout.channel.recv_exit_status()
    output = stdout.read().decode()
    error = stderr.read().decode()
    if code:
        raise RuntimeError(error or output)
    return output


def remove_top_section(text: str, name: str) -> str:
    lines = text.splitlines()
    output: list[str] = []
    depth = 0
    dropping = False
    for line in lines:
        opening = re.match(r"\s*&([A-Z_]+)\b", line, re.I)
        ending = re.match(r"\s*&END(?:\s+([A-Z_]+))?\b", line, re.I)
        if (
            not dropping
            and depth == 0
            and opening
            and opening.group(1).upper() == name
        ):
            dropping = True
            depth = 1
            continue
        if dropping:
            if ending:
                depth -= 1
                if depth == 0:
                    dropping = False
            elif opening:
                depth += 1
            continue
        output.append(line)
    return "\n".join(output) + "\n"


def coordinates(text: str) -> list[tuple[str, float, float, float]]:
    match = re.search(r"(?is)&COORD\b(.*?)&END\s+COORD", text)
    if not match:
        raise RuntimeError("missing COORD section")
    atoms = []
    for raw in match.group(1).splitlines():
        fields = raw.split()
        if len(fields) >= 4 and re.fullmatch(r"[A-Za-z]+", fields[0]):
            atoms.append(
                (fields[0], float(fields[1]), float(fields[2]), float(fields[3]))
            )
    return atoms


def make_baseline(text: str, project: str) -> str:
    text = re.sub(
        r"(?im)^\s*PROJECT_NAME\s+\S+",
        f"  PROJECT_NAME {project}",
        text,
        count=1,
    )
    text = re.sub(
        r"(?im)^\s*RUN_TYPE\s+\S+", "  RUN_TYPE ENERGY", text, count=1
    )
    text = remove_top_section(text, "VIBRATIONAL_ANALYSIS")
    text = re.sub(
        r"(?im)^\s*WFN_RESTART_FILE_NAME\s+\S+",
        "    WFN_RESTART_FILE_NAME seed-RESTART.wfn",
        text,
        count=1,
    )
    if not re.search(r"(?im)^\s*WFN_RESTART_FILE_NAME\b", text):
        text = re.sub(
            r"(?im)^(\s*&SCF\b)",
            "    WFN_RESTART_FILE_NAME seed-RESTART.wfn\n\\1",
            text,
            count=1,
        )
    print_block = """    &PRINT
      &MULLIKEN ON
      &END MULLIKEN
      &HIRSHFELD ON
        SHAPE_FUNCTION GAUSSIAN
      &END HIRSHFELD
      &PLUS_U ON
      &END PLUS_U
    &END PRINT
"""
    text = re.sub(
        r"(?im)^(\s*&END\s+DFT\b)", print_block + r"\1", text, count=1
    )
    return text


def main() -> None:
    paramiko = ssh_ncw.ensure_paramiko()
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        hostname=ssh_ncw.HOST,
        port=ssh_ncw.PORT,
        username=ssh_ncw.USER,
        password=ssh_ncw.load_password(),
        look_for_keys=False,
        allow_agent=False,
    )
    try:
        sftp = client.open_sftp()
        queue = run(client, "squeue -u ftfan -h -o '%j'")
        if "Undop_cdft_base" in queue:
            raise RuntimeError("undoped baseline array already active")
        try:
            sftp.stat(posixpath.join(ssh_ncw.REMOTE_ROOT, REMOTE_BASE))
            existing = run(client, f"find {REMOTE_BASE} -mindepth 1 -maxdepth 1 -print")
            if existing.strip():
                raise RuntimeError(f"refusing to overwrite nonempty {REMOTE_BASE}")
        except FileNotFoundError:
            pass

        mkdir_p(sftp, REMOTE_BASE)
        manifest = [
            "case\tactive_atom\tadsorbate_atoms\tsource_input\tstatus"
        ]
        for case, config in CASES.items():
            source = str(config["input"])
            wfn = str(config["wfn"])
            text = read_text(sftp, source)
            atoms = coordinates(text)
            counts = tuple(
                sum(1 for atom in atoms if atom[0] == element)
                for element in ("Co", "H", "O")
            )
            if counts != config["composition"]:
                raise RuntimeError(f"{case} composition {counts} is unexpected")
            if atoms[int(config["active"]) - 1][0] != "Co":
                raise RuntimeError(f"{case} active atom is not Co")
            expected_adsorbate = {
                "undoped_valid_co32_OH": ("H", "O"),
                "undoped_valid_co32_O": ("O",),
                "undoped_valid_co32_OOH": ("H", "O", "O"),
            }[case]
            actual_adsorbate = tuple(
                atoms[index - 1][0] for index in config["adsorbate"]
            )
            if actual_adsorbate != expected_adsorbate:
                raise RuntimeError(
                    f"{case} adsorbate elements {actual_adsorbate} are unexpected"
                )
            if sftp.stat(posixpath.join(ssh_ncw.REMOTE_ROOT, wfn)).st_size == 0:
                raise RuntimeError(f"{case} source WFN is empty")

            case_dir = posixpath.join(REMOTE_BASE, case)
            mkdir_p(sftp, case_dir)
            baseline = make_baseline(text, f"cdf_base_{case}")
            write_text(sftp, posixpath.join(case_dir, "baseline.inp"), baseline)
            run(client, f"cp {wfn} {posixpath.join(case_dir, 'seed-RESTART.wfn')}")
            adsorbate = ",".join(str(x) for x in config["adsorbate"])
            manifest.append(
                f"{case}\t{config['active']}\t{adsorbate}\t{source}\tprepared"
            )

        write_text(
            sftp,
            posixpath.join(REMOTE_BASE, "baseline_manifest.tsv"),
            "\n".join(manifest) + "\n",
        )
        slurm = """#!/bin/bash
#SBATCH -J Undop_cdft_base
#SBATCH --nodes=1
#SBATCH --ntasks=28
#SBATCH --partition=n28
#SBATCH --array=0-2%1
#SBATCH --time=24:00:00
#SBATCH --output=slurm-%A_%a.out
#SBATCH --error=slurm-%A_%a.err

set -eo pipefail
export LD_LIBRARY_PATH=/apps/soft/gmp620/lib:${LD_LIBRARY_PATH:-}
export LD_LIBRARY_PATH=/apps/soft/mpfr410/lib:$LD_LIBRARY_PATH
export LD_LIBRARY_PATH=/apps/soft/mpc120/lib:$LD_LIBRARY_PATH
export LD_LIBRARY_PATH=/apps/soft/gcc840/lib64:$LD_LIBRARY_PATH
export PATH=/apps/soft/gcc840/bin:$PATH
source /apps/soft/cp2k-2024.1/tools/toolchain/install/setup
set -u
export PATH=$PATH:/apps/soft/cp2k-2024.1/exe/local
export CP2K_DATA_DIR=/apps/soft/cp2k-2024.1/data
export OMP_NUM_THREADS=1
export OMPI_MCA_btl=self,vader,tcp
export OMPI_MCA_pml=ob1

CASES=(undoped_valid_co32_OH undoped_valid_co32_O undoped_valid_co32_OOH)
CASE=${CASES[$SLURM_ARRAY_TASK_ID]}
cd "$SLURM_SUBMIT_DIR/$CASE"
mpirun -np 28 cp2k.popt -i baseline.inp -o baseline.out
"""
        write_text(sftp, posixpath.join(REMOTE_BASE, "submit_baseline.slurm"), slurm)
        write_text(
            sftp,
            posixpath.join(REMOTE_BASE, "scheduler_manifest.tsv"),
            "date\tevent\tjob_id\tstatus\tnotes\n",
        )
        submit = run(client, f"cd {REMOTE_BASE} && sbatch submit_baseline.slurm")
        match = re.search(r"Submitted batch job (\d+)", submit)
        if not match:
            raise RuntimeError(f"cannot parse sbatch output: {submit}")
        job_id = match.group(1)
        write_text(
            sftp,
            posixpath.join(REMOTE_BASE, "scheduler_manifest.tsv"),
            "date\tevent\tjob_id\tstatus\tnotes\n"
            f"2026-08-16\tbaseline_submission\t{job_id}_0-2\tpending\t"
            "undoped_Co32_OH_O_OOH_fixed_geometry;Gaussian_Hirshfeld;"
            "Mulliken;DFT+U_occupations;n28_concurrency1;no_duplicates\n",
        )
        print(job_id)
    finally:
        client.close()


if __name__ == "__main__":
    main()
