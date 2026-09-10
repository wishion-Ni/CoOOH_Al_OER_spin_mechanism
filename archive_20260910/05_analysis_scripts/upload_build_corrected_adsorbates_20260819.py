from __future__ import annotations

import importlib.util
import posixpath
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / ".codex/skills/ftfan-ncw-ssh/scripts/ssh_ncw.py"
REMOTE_DIR = (
    "sfs/CoOH/cp2k/Al16/oer/spin_config_scan_site03_5OH_current_20260714/"
    "vasp_jacs6c06054_reconstructed_exact_Al16_3x2_20260809/"
    "electronic_structure_al_contribution_20260818/tools"
)
SCRIPTS = (
    "build_corrected_adsorbates_20260819.py",
    "diagnose_source_adsorbates_20260819.py",
    "diagnose_active_index_mapping_20260819.py",
    "validate_corrected_adsorbates_20260819.py",
    "repair_corrected_preconverge_slurm_20260819.py",
    "record_corrected_submission_20260819.py",
)


def main() -> None:
    spec = importlib.util.spec_from_file_location("ssh_ncw", HELPER)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load SSH helper")
    ssh_ncw = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ssh_ncw)
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
        for script in SCRIPTS:
            local = ROOT / "artifacts" / script
            remote = posixpath.join(ssh_ncw.REMOTE_ROOT, REMOTE_DIR, script)
            sftp.put(str(local), remote)
    finally:
        client.close()

    script = sys.argv[1] if len(sys.argv) > 1 else SCRIPTS[0]
    if script not in SCRIPTS:
        raise RuntimeError("unsupported script: " + script)
    subprocess.run(
        [sys.executable, str(HELPER), "--", "python " + posixpath.join(REMOTE_DIR, script)],
        cwd=ROOT,
        check=True,
    )


if __name__ == "__main__":
    main()
