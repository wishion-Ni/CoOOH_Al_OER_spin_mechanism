from __future__ import annotations

import importlib.util
import posixpath
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SSH_HELPER = ROOT / ".codex/skills/ftfan-ncw-ssh/scripts/ssh_ncw.py"
spec = importlib.util.spec_from_file_location("ssh_ncw", SSH_HELPER)
ssh_ncw = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(ssh_ncw)

REMOTE_BASE = (
    "sfs/CoOH/cp2k/Al16/oer/spin_config_scan_site03_5OH_current_20260714/"
    "cdft_charge_spin_20260812"
)

# Co40 in the model label maps to CP2K atom 48 in the accepted structures.
CASES = {
    "al16_valid_co48_OH": (
        "sfs/CoOH/cp2k/Al16/oer/spin_config_scan_site03_5OH_current_20260714/"
        "neighbor_Co_screen_20260721/co40_state_rescue_20260725/OH/o02_free/"
        "A16_Co40_OH_o02_free.inp",
        "A16_Co40_OH_o02_free-RESTART.wfn",
        48,
    ),
    "al16_valid_co48_O": (
        "sfs/CoOH/cp2k/Al16/oer/spin_config_scan_site03_5OH_current_20260714/"
        "neighbor_Co_screen_20260721/co40_state_rescue_20260725/"
        "O_direction_rescue_20260726/o01_free/A16_Co40_O_alt01_free.inp",
        "A16_Co40_O_alt01_free-RESTART.wfn",
        48,
    ),
    "al16_valid_co48_OOH": (
        "sfs/CoOH/cp2k/Al16/oer/spin_config_scan_site03_5OH_current_20260714/"
        "neighbor_Co_screen_20260721/ooh_orientation_gate_20260724/Co40/o01_free/"
        "A16_Co40_OOH_o01_free.inp",
        "A16_Co40_OOH_o01_free-RESTART.wfn",
        48,
    ),
}


def read_text(sftp, rel_path: str) -> str:
    with sftp.open(posixpath.join(ssh_ncw.REMOTE_ROOT, rel_path), "r") as handle:
        return handle.read().decode()


def write_text(sftp, rel_path: str, text: str) -> None:
    with sftp.open(posixpath.join(ssh_ncw.REMOTE_ROOT, rel_path), "w") as handle:
        handle.write(text)


def mkdir_p(sftp, rel_path: str) -> None:
    current = ssh_ncw.REMOTE_ROOT
    for part in rel_path.split("/"):
        current = posixpath.join(current, part)
        try:
            sftp.stat(current)
        except FileNotFoundError:
            sftp.mkdir(current)


def top_level_remove(text: str, section_name: str) -> str:
    lines = text.splitlines()
    out: list[str] = []
    depth = 0
    dropping = False
    for line in lines:
        open_match = re.match(r"\s*&([A-Z_]+)\b", line, re.I)
        end_match = re.match(r"\s*&END(?:\s+([A-Z_]+))?\b", line, re.I)
        if not dropping and depth == 0 and open_match and open_match.group(1).upper() == section_name:
            dropping = True
            depth = 1
            continue
        if dropping:
            if end_match:
                depth -= 1
                if depth == 0:
                    dropping = False
            elif open_match:
                depth += 1
            continue
        out.append(line)
    return "\n".join(out) + "\n"


def make_baseline(text: str, project: str, wfn_name: str) -> str:
    text = re.sub(r"(?im)^\s*PROJECT_NAME\s+\S+", f"  PROJECT_NAME {project}", text, count=1)
    text = re.sub(r"(?im)^\s*RUN_TYPE\s+\S+", "  RUN_TYPE ENERGY", text, count=1)
    text = top_level_remove(text, "VIBRATIONAL_ANALYSIS")
    text = re.sub(
        r"(?im)^\s*WFN_RESTART_FILE_NAME\s+\S+",
        f"    WFN_RESTART_FILE_NAME {wfn_name}",
        text,
        count=1,
    )
    if not re.search(r"(?im)^\s*WFN_RESTART_FILE_NAME\b", text):
        text = re.sub(
            r"(?im)^(\s*&SCF\b)",
            rf"    WFN_RESTART_FILE_NAME {wfn_name}\n\1",
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
    text = re.sub(r"(?im)^(\s*&END\s+DFT\b)", print_block + r"\1", text, count=1)
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
        mkdir_p(sftp, REMOTE_BASE)
        manifest = ["case\tactive_atom\tsource_input\tstatus"]
        for case, (source, wfn_source_name, active_atom) in CASES.items():
            case_dir = posixpath.join(REMOTE_BASE, case)
            mkdir_p(sftp, case_dir)
            source_text = read_text(sftp, source)
            source_dir = posixpath.dirname(source)
            project = f"cdf_base_{case}"
            wfn_dest = "seed-RESTART.wfn"
            baseline = make_baseline(source_text, project, wfn_dest)
            write_text(sftp, posixpath.join(case_dir, "baseline.inp"), baseline)
            copy_command = (
                f"cp {posixpath.join(source_dir, wfn_source_name)} "
                f"{posixpath.join(case_dir, wfn_dest)}"
            )
            stdin, stdout, stderr = client.exec_command(
                f"cd {ssh_ncw.REMOTE_ROOT} && {copy_command}"
            )
            code = stdout.channel.recv_exit_status()
            if code:
                raise RuntimeError(stderr.read().decode())
            manifest.append(f"{case}\t{active_atom}\t{source}\tprepared")

        write_text(sftp, posixpath.join(REMOTE_BASE, "baseline_manifest.tsv"), "\n".join(manifest) + "\n")
        slurm = """#!/bin/bash
#SBATCH -J CoOH_cdft_base
#SBATCH --nodes=1
#SBATCH --ntasks=28
#SBATCH --partition=n28
#SBATCH --array=0-2%1
#SBATCH --time=24:00:00
#SBATCH --output=slurm-%A_%a.out
#SBATCH --error=slurm-%A_%a.err

set -euo pipefail
source /apps/soft/cp2k-2024.1/tools/toolchain/install/setup
export PATH=$PATH:/apps/soft/cp2k-2024.1/exe/local
export CP2K_DATA_DIR=/apps/soft/cp2k-2024.1/data
export OMP_NUM_THREADS=1
export OMPI_MCA_btl=self,vader,tcp
export OMPI_MCA_pml=ob1

CASES=(al16_valid_co48_OH al16_valid_co48_O al16_valid_co48_OOH)
CASE=${CASES[$SLURM_ARRAY_TASK_ID]}
cd "$SLURM_SUBMIT_DIR/$CASE"
mpirun -np 28 cp2k.popt -i baseline.inp -o baseline.out
"""
        write_text(sftp, posixpath.join(REMOTE_BASE, "submit_baseline.slurm"), slurm)
        print(REMOTE_BASE)
    finally:
        client.close()


if __name__ == "__main__":
    main()
