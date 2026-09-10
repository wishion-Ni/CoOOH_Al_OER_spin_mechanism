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

VASP_ROOT = (
    "sfs/CoOH/cp2k/Al16/oer/spin_config_scan_site03_5OH_current_20260714/"
    "vasp_jacs6c06054_reconstructed_exact_Al16_3x2_20260809"
)
PRECONV = posixpath.join(VASP_ROOT, "electronic_preconverge_20260810")
ANALYSIS = posixpath.join(VASP_ROOT, "electronic_structure_al_contribution_20260818")
FIXED = posixpath.join(ANALYSIS, "fixed_geometry_bader_pdos")
JOB_NAME = "AlContribBader"
CASES = (
    ("Al16_adjacent", "bare"),
    ("undoped_control", "bare"),
    ("Al16_adjacent", "OH"),
    ("undoped_control", "OH"),
    ("Al16_adjacent", "O"),
    ("undoped_control", "O"),
    ("Al16_adjacent", "OOH_o03"),
    ("undoped_control", "OOH_o03"),
)


def remote_path(rel: str) -> str:
    return posixpath.join(ssh_ncw.REMOTE_ROOT, rel)


def run(client, command: str) -> str:
    _, stdout, stderr = client.exec_command(f"cd {ssh_ncw.REMOTE_ROOT} && {command}")
    code = stdout.channel.recv_exit_status()
    output = stdout.read().decode(errors="replace")
    error = stderr.read().decode(errors="replace")
    if code:
        raise RuntimeError(error or output)
    return output


def read_text(sftp, rel: str) -> str:
    with sftp.open(remote_path(rel), "r") as handle:
        return handle.read().decode(errors="replace")


def write_text(sftp, rel: str, value: str) -> None:
    with sftp.open(remote_path(rel), "w") as handle:
        handle.write(value)


def mkdirs(sftp, rel: str) -> None:
    current = ssh_ncw.REMOTE_ROOT
    for part in rel.split("/"):
        current = posixpath.join(current, part)
        try:
            sftp.stat(current)
        except FileNotFoundError:
            sftp.mkdir(current)


def exists(sftp, rel: str) -> bool:
    try:
        sftp.stat(remote_path(rel))
        return True
    except FileNotFoundError:
        return False


def set_tag(text: str, tag: str, value: str) -> str:
    pattern = rf"(?im)^\s*{re.escape(tag)}\s*=.*$"
    replacement = f"{tag} = {value}"
    if re.search(pattern, text):
        return re.sub(pattern, replacement, text, count=1)
    return text.rstrip() + f"\n{replacement}\n"


def remove_tag(text: str, tag: str) -> str:
    return re.sub(rf"(?im)^\s*{re.escape(tag)}\s*=.*\n?", "", text)


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
        queue = run(client, "squeue -u ftfan -h -o '%i|%j|%T|%P'")
        if JOB_NAME in queue:
            raise RuntimeError("fixed-geometry Bader/PDOS array is already active")
        if exists(sftp, posixpath.join(ANALYSIS, "submitted_job_id.txt")):
            raise RuntimeError("analysis root already contains a submitted job id")

        mkdirs(sftp, FIXED)
        jobs: list[str] = []
        manifest = [
            "task\tbranch\tstate\tsource\tgeometry\tdensity\tmode\tstatus"
        ]
        for task, (branch, state) in enumerate(CASES):
            source = posixpath.join(PRECONV, branch, state)
            dest = posixpath.join(FIXED, branch, state)
            mkdirs(sftp, dest)

            outcar = read_text(sftp, posixpath.join(source, "OUTCAR"))
            if "General timing and accounting informations" not in outcar:
                raise RuntimeError(f"source is not normally terminated: {source}")
            for name, minimum in (("CHGCAR", 100_000_000), ("WAVECAR", 500_000_000)):
                size = sftp.stat(remote_path(posixpath.join(source, name))).st_size
                if size < minimum:
                    raise RuntimeError(f"invalid {name} in {source}: {size}")

            for name in ("POSCAR", "POTCAR", "KPOINTS"):
                run(client, f"cp {posixpath.join(source, name)} {posixpath.join(dest, name)}")

            incar = read_text(sftp, posixpath.join(source, "INCAR"))
            for tag, value in (
                ("SYSTEM", f"fixed-geometry Al contribution {branch} {state}"),
                ("ISTART", "1"),
                ("ICHARG", "11"),
                ("IBRION", "-1"),
                ("NSW", "0"),
                ("EDIFF", "1E-6"),
                ("LREAL", ".FALSE."),
                ("LAECHG", ".TRUE."),
                ("LCHARG", ".FALSE."),
                ("LWAVE", ".FALSE."),
                ("LORBIT", "11"),
                ("NEDOS", "3000"),
                ("EMIN", "-12"),
                ("EMAX", "6"),
                ("ISYM", "0"),
                ("NCORE", "4"),
            ):
                incar = set_tag(incar, tag, value)
            for tag in ("EDIFFG", "ISIF"):
                incar = remove_tag(incar, tag)
            write_text(sftp, posixpath.join(dest, "INCAR"), incar)

            for name in ("CHGCAR", "WAVECAR"):
                target = remote_path(posixpath.join(source, name))
                link = remote_path(posixpath.join(dest, name))
                if exists(sftp, posixpath.join(dest, name)):
                    raise RuntimeError(f"destination already contains {name}: {dest}")
                sftp.symlink(target, link)

            jobs.append(remote_path(dest))
            manifest.append(
                f"{task}\t{branch}\t{state}\t{source}\tpreconverged_fixed\t"
                "validated_preconvergence_CHGCAR\tICHARG11_PAW_reconstruction_PDOS\tprepared"
            )

        write_text(sftp, posixpath.join(FIXED, "jobs.list"), "\n".join(jobs) + "\n")
        write_text(sftp, posixpath.join(ANALYSIS, "analysis_manifest.tsv"), "\n".join(manifest) + "\n")
        write_text(
            sftp,
            posixpath.join(ANALYSIS, "README.md"),
            """# Al contribution electronic-structure analysis

This first tier isolates the electronic substitution effect at the shared fixed geometry.
It uses the validated preconverged CHGCAR/WAVECAR seeds and the production PBE+U,
dispersion, cutoff, k-mesh and spin settings. ICHARG=11 is used only to reconstruct
PAW core densities and projected DOS without changing the validated density.

Outputs required for validation: normal VASP termination, AECCAR0, AECCAR2,
DOSCAR, PROCAR/vasprun.xml and local magnetic moments. Bader analysis uses
CHGCAR with AECCAR0+AECCAR2 as the reference density. These fixed-geometry
results are diagnostic and will be repeated on final relaxed strict statics.

COHP requires a licensed LOBSTER executable, which is not currently available
in the login environment. No DOS or overlap proxy will be labelled as COHP.
""",
        )

        slurm = f"""#!/bin/bash
#SBATCH --job-name={JOB_NAME}
#SBATCH --nodes=1
#SBATCH --ntasks=40
#SBATCH --partition=n40
#SBATCH --array=0-7%1
#SBATCH --time=24:00:00
#SBATCH --output=array_%A_%a.stdout
#SBATCH --error=array_%A_%a.stderr

set -eo pipefail
WORKDIR=\"$(sed -n \"$((SLURM_ARRAY_TASK_ID + 1))p\" jobs.list)\"
cd \"$WORKDIR\"
if [ -f OUTCAR ] && grep -q \"General timing and accounting informations\" OUTCAR; then
  echo \"Already complete: $WORKDIR\"
  exit 0
fi
VASP_HOME=/apps/vasp/6.3.0_vtst_optcell_vaspsol/O3
if [ -f \"$HOME/intel/oneapi/setvars.sh\" ]; then
  source \"$HOME/intel/oneapi/setvars.sh\" --force
fi
export LD_LIBRARY_PATH=\"$HOME/intel/oneapi/mkl/latest/lib/intel64:$HOME/intel/oneapi/compiler/latest/linux/compiler/lib/intel64_lin:${{LD_LIBRARY_PATH:-}}\"
ulimit -s unlimited
\"$HOME/intel/oneapi/mpi/2021.11/bin/mpirun\" -n \"$SLURM_NTASKS\" \"$VASP_HOME/vasp_std\" > vasp.out 2>&1
"""
        write_text(sftp, posixpath.join(FIXED, "vasp_array.slurm"), slurm)

        submitted = run(client, f"cd {FIXED} && sbatch vasp_array.slurm")
        match = re.search(r"Submitted batch job (\d+)", submitted)
        if not match:
            raise RuntimeError(f"cannot parse sbatch output: {submitted}")
        job_id = match.group(1)
        write_text(sftp, posixpath.join(ANALYSIS, "submitted_job_id.txt"), job_id + "\n")
        scheduler = (
            "date\tevent\tjob_id\tpartition\tranks\tarray_limit\tnotes\n"
            f"2026-08-18\tfixed_geometry_bader_pdos_submission\t{job_id}_0-7\t"
            "n40\t40\t1\tvalidated_preconvergence_density;ICHARG11;LAECHG;"
            "LORBIT11;no_duplicate;diagnostic_fixed_geometry\n"
        )
        write_text(sftp, posixpath.join(ANALYSIS, "scheduler_manifest.tsv"), scheduler)
        print(job_id)
    finally:
        client.close()


if __name__ == "__main__":
    main()
