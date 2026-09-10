from __future__ import annotations

import importlib.util
import posixpath
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts"
HELPER = ROOT / ".codex/skills/ftfan-ncw-ssh/scripts/ssh_ncw.py"
spec = importlib.util.spec_from_file_location("ssh_ncw", HELPER)
ssh_ncw = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(ssh_ncw)

VASP_ROOT = (
    "sfs/CoOH/cp2k/Al16/oer/spin_config_scan_site03_5OH_current_20260714/"
    "vasp_jacs6c06054_reconstructed_exact_Al16_3x2_20260809"
)
ANALYSIS = posixpath.join(VASP_ROOT, "electronic_structure_al_contribution_20260818")
DEST = posixpath.join(ANALYSIS, "stage_summary_20260819")
SCHEDULER = posixpath.join(ANALYSIS, "scheduler_manifest.tsv")
FILES = (
    "cooh_al16_stage_summary_20260819.png",
    "cooh_al16_stage_summary_20260819.svg",
    "cooh_al16_stage_summary_20260819.pdf",
    "cooh_al16_stage_summary_20260819.md",
    "stage_summary_bare_bader_20260819.tsv",
    "stage_summary_bare_pdos_20260819.tsv",
    "stage_summary_analysis_manifest_20260819.tsv",
    "cdft_undoped_vs_al16_complete_20260818.tsv",
    "proton_relay_fixed_path_20260817.tsv",
    "proton_relay_pcet_nm1_profile_20260818.tsv",
    "strict_site03_vasp_298p15K_staircase.tsv",
)


def remote(rel: str) -> str:
    return posixpath.join(ssh_ncw.REMOTE_ROOT, rel)


def read_text(sftp, rel: str) -> str:
    with sftp.open(remote(rel), "r") as handle:
        return handle.read().decode(errors="replace")


def write_text(sftp, rel: str, value: str) -> None:
    with sftp.open(remote(rel), "w") as handle:
        handle.write(value)


def main() -> None:
    for name in FILES:
        if not (ARTIFACTS / name).is_file():
            raise RuntimeError(f"missing local stage artifact: {name}")
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
        try:
            sftp.stat(remote(DEST))
        except FileNotFoundError:
            sftp.mkdir(remote(DEST))
        existing = set(sftp.listdir(remote(DEST)))
        if existing.intersection(FILES):
            raise RuntimeError("stage-summary destination already contains versioned artifacts")
        for name in FILES:
            sftp.put(str(ARTIFACTS / name), remote(posixpath.join(DEST, name)))
        scheduler = read_text(sftp, SCHEDULER)
        scheduler += (
            "2026-08-19\tstage_summary_report\tNA\tNA\tNA\tNA\t"
            "validated_CHE_cdft_relay_bare_Bader_PDOS;preliminary_figure;"
            "exact_Al16_control_CHE_pending\n"
        )
        write_text(sftp, SCHEDULER, scheduler)
        print(remote(DEST))
    finally:
        client.close()


if __name__ == "__main__":
    main()
