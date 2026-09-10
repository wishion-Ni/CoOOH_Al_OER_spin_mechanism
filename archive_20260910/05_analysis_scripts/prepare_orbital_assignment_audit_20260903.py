from __future__ import annotations

import importlib.util
import posixpath
import re
from pathlib import Path


WORKSPACE = Path(__file__).resolve().parents[1]
SSH_HELPER = WORKSPACE / ".codex" / "skills" / "ftfan-ncw-ssh" / "scripts" / "ssh_ncw.py"
REMOTE_HOME = "/home/ftfan/ncw"
REL_BASE = (
    "sfs/CoOH/cp2k/Al16/oer/spin_config_scan_site03_5OH_current_20260714/"
    "vasp_jacs6c06054_reconstructed_exact_Al16_3x2_20260809/"
    "electronic_structure_al_contribution_20260818"
)
REMOTE_BASE = posixpath.join(REMOTE_HOME, REL_BASE)
OUTPUT_ROOT = posixpath.join(REMOTE_BASE, "orbital_assignment_audit_20260903")
LOBSTER = posixpath.join(REMOTE_BASE, "tools/lobster-5.1.1/lobster-5.1.1")


CASES = [
    {
        "name": "pristine_OH",
        "source": "cohp_oh_o_corrected_20260820/undoped_control/OH",
        "co": 21,
        "oxygen": [295, 348, 227, 275, 217, 259],
        "neighbor": 23,
        "bridge": 259,
        "oh": (348, 204),
    },
    {
        "name": "pristine_O",
        "source": "cohp_oh_o_corrected_20260820/undoped_control/O",
        "co": 21,
        "oxygen": [294, 347, 226, 274, 216, 258],
        "neighbor": 23,
        "bridge": 258,
        "oh": None,
    },
    {
        "name": "Al16_OH",
        "source": "cohp_oh_o_corrected_20260820/Al16_adjacent/OH",
        "co": 16,
        "oxygen": [295, 348, 227, 275, 217, 259],
        "neighbor": 51,
        "bridge": 259,
        "oh": (348, 204),
    },
    {
        "name": "Al16_O",
        "source": "cohp_oh_o_corrected_20260820/Al16_adjacent/O",
        "co": 16,
        "oxygen": [294, 347, 226, 274, 216, 258],
        "neighbor": 51,
        "bridge": 258,
        "oh": None,
    },
]


def load_helper():
    spec = importlib.util.spec_from_file_location("ssh_ncw", SSH_HELPER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {SSH_HELPER}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def require_allowed(path: str) -> None:
    normalized = posixpath.normpath(path)
    if normalized != REMOTE_HOME and not normalized.startswith(REMOTE_HOME + "/"):
        raise ValueError(f"Remote path outside allowed root: {path}")


def mkdir_p(sftp, path: str) -> None:
    require_allowed(path)
    current = REMOTE_HOME
    relative = posixpath.relpath(path, REMOTE_HOME)
    if relative == ".":
        return
    for part in relative.split("/"):
        current = posixpath.join(current, part)
        try:
            sftp.stat(current)
        except FileNotFoundError:
            sftp.mkdir(current)


def write_text(sftp, path: str, content: str) -> None:
    require_allowed(path)
    with sftp.file(path, "w") as handle:
        handle.write(content)


def ensure_symlink(sftp, source: str, target: str) -> None:
    require_allowed(source)
    require_allowed(target)
    source_size = sftp.stat(source).st_size
    if source_size <= 0:
        raise RuntimeError(f"Empty source file: {source}")
    try:
        existing = sftp.readlink(target)
    except (FileNotFoundError, OSError):
        try:
            sftp.stat(target)
        except FileNotFoundError:
            sftp.symlink(source, target)
            return
        raise RuntimeError(f"Existing non-symlink blocks target: {target}")
    if existing != source:
        raise RuntimeError(f"Symlink mismatch: {target} -> {existing}, expected {source}")


def lobsterin(case: dict) -> str:
    lines = [
        "skipMadelungEnergy",
        "COHPstartEnergy -15.0",
        "COHPendEnergy 5.0",
        "basisSet pbeVaspFit2015",
        "useRecommendedBasisFunctions",
        "gaussianSmearingWidth 0.05",
    ]
    for oxygen in case["oxygen"]:
        lines.append(f"cohpBetween atom {case['co']} atom {oxygen} orbitalWise")
    lines.append(
        f"cohpBetween atom {case['neighbor']} atom {case['bridge']} orbitalWise"
    )
    if case["oh"] is not None:
        oxygen, hydrogen = case["oh"]
        lines.append(f"cohpBetween atom {oxygen} atom {hydrogen} orbitalWise")
    return "\n".join(lines) + "\n"


def slurm_script() -> str:
    names = " ".join(f'"{case["name"]}"' for case in CASES)
    return f"""#!/bin/bash
#SBATCH --job-name=OrbAssignLob
#SBATCH --partition=n28
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --time=14:00:00
#SBATCH --array=0-3%2
#SBATCH --output=slurm_%A_%a.out
#SBATCH --error=slurm_%A_%a.err

set -eo pipefail
ROOT={OUTPUT_ROOT}/lobster_sixbond
LOBSTER={LOBSTER}
CASES=({names})
CASE=${{CASES[$SLURM_ARRAY_TASK_ID]}}
cd "$ROOT/$CASE"

if grep -q "finished successfully" lobsterout 2>/dev/null; then
    echo "Validated-looking lobsterout already exists; refusing duplicate run."
    exit 0
fi

for input in INCAR KPOINTS POSCAR CONTCAR POTCAR OUTCAR WAVECAR vasprun.xml lobsterin; do
    test -s "$input"
done

export OMP_NUM_THREADS=${{SLURM_CPUS_PER_TASK}}
ulimit -s unlimited
"$LOBSTER"
"""


def run_remote(client, command: str) -> tuple[int, str, str]:
    remote = f"cd {REMOTE_HOME} && {command}"
    _stdin, stdout, stderr = client.exec_command(remote, timeout=None)
    out = stdout.read().decode(errors="replace")
    err = stderr.read().decode(errors="replace")
    return stdout.channel.recv_exit_status(), out, err


def main() -> int:
    helper = load_helper()
    paramiko = helper.ensure_paramiko()
    password = helper.load_password()

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        hostname=helper.HOST,
        port=helper.PORT,
        username=helper.USER,
        password=password,
        timeout=15,
        banner_timeout=15,
        auth_timeout=60,
        look_for_keys=False,
        allow_agent=False,
    )
    try:
        code, out, err = run_remote(
            client,
            "squeue -h -u ftfan -n OrbAssignLob -o '%A_%a %T'",
        )
        if code != 0:
            raise RuntimeError(err or out)
        if out.strip():
            raise RuntimeError(f"Existing OrbAssignLob job detected:\n{out}")

        sftp = client.open_sftp()
        try:
            lobster_root = posixpath.join(OUTPUT_ROOT, "lobster_sixbond")
            mkdir_p(sftp, lobster_root)
            manifest = [
                "case\tsource\tactive_Co\tsix_O\tneighbor\tbridge_O\tactive_OH",
            ]
            required = [
                "INCAR",
                "KPOINTS",
                "POSCAR",
                "CONTCAR",
                "POTCAR",
                "OUTCAR",
                "WAVECAR",
                "vasprun.xml",
            ]
            for case in CASES:
                case_dir = posixpath.join(lobster_root, case["name"])
                source_dir = posixpath.join(REMOTE_BASE, case["source"])
                mkdir_p(sftp, case_dir)
                for filename in required:
                    ensure_symlink(
                        sftp,
                        posixpath.join(source_dir, filename),
                        posixpath.join(case_dir, filename),
                    )
                write_text(sftp, posixpath.join(case_dir, "lobsterin"), lobsterin(case))
                active_oh = "" if case["oh"] is None else f"O{case['oh'][0]}-H{case['oh'][1]}"
                manifest.append(
                    "\t".join(
                        [
                            case["name"],
                            case["source"],
                            str(case["co"]),
                            ",".join(str(v) for v in case["oxygen"]),
                            str(case["neighbor"]),
                            str(case["bridge"]),
                            active_oh,
                        ]
                    )
                )

            write_text(
                sftp,
                posixpath.join(OUTPUT_ROOT, "sixbond_input_manifest.tsv"),
                "\n".join(manifest) + "\n",
            )
            script_path = posixpath.join(OUTPUT_ROOT, "run_lobster_sixbond_array.slurm")
            write_text(sftp, script_path, slurm_script())
        finally:
            sftp.close()

        rel_script = posixpath.relpath(script_path, REMOTE_HOME)
        code, out, err = run_remote(client, f"sbatch {rel_script}")
        if code != 0:
            raise RuntimeError(err or out)
        match = re.search(r"Submitted batch job\s+(\d+)", out)
        if not match:
            raise RuntimeError(f"Could not parse sbatch output: {out!r}")
        job_id = match.group(1)

        sftp = client.open_sftp()
        try:
            write_text(
                sftp,
                posixpath.join(OUTPUT_ROOT, "submission.tsv"),
                "job_id\tjob_name\tarray\tconcurrency\tpartition\tnodes_per_task\tcpus_per_task\n"
                f"{job_id}\tOrbAssignLob\t0-3\t2\tn28\t1\t8\n",
            )
        finally:
            sftp.close()

        print(f"JOB_ID={job_id}")
        print(f"OUTPUT_ROOT={OUTPUT_ROOT}")
        return 0
    finally:
        client.close()


if __name__ == "__main__":
    raise SystemExit(main())
