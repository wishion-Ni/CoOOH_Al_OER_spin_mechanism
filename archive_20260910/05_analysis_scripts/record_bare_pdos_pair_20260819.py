from __future__ import annotations

import csv
import importlib.util
import io
import posixpath
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
ANALYSIS = posixpath.join(VASP_ROOT, "electronic_structure_al_contribution_20260818")
RESULT = posixpath.join(ANALYSIS, "bare_pdos_active_co_pair.tsv")
BADER = posixpath.join(ANALYSIS, "bare_bader_active_site_pair.tsv")
REPORT = posixpath.join(ANALYSIS, "bare_bader_pdos_interpretation.md")
MANIFEST = posixpath.join(ANALYSIS, "analysis_manifest.tsv")
SCHEDULER = posixpath.join(ANALYSIS, "scheduler_manifest.tsv")
JOB_ID = "111193"


def remote(rel: str) -> str:
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
    with sftp.open(remote(rel), "r") as handle:
        return handle.read().decode(errors="replace")


def write_text(sftp, rel: str, value: str) -> None:
    with sftp.open(remote(rel), "w") as handle:
        handle.write(value)


def rows(text: str) -> dict[str, dict[str, str]]:
    return {row["model"]: row for row in csv.DictReader(io.StringIO(text), delimiter="\t")}


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
        state = run(client, f"sacct -j {JOB_ID} -n -P -o State,ExitCode").splitlines()[0]
        if state != "COMPLETED|0:0":
            raise RuntimeError(f"PDOS analysis did not complete cleanly: {state}")
        pdos = rows(read_text(sftp, RESULT))
        bader_rows = list(csv.DictReader(io.StringIO(read_text(sftp, BADER)), delimiter="\t"))
        if set(pdos) != {"Al16", "control"}:
            raise RuntimeError("PDOS result does not contain the matched pair")
        if int(pdos["Al16"]["vasp_index"]) != 16 or int(pdos["control"]["vasp_index"]) != 21:
            raise RuntimeError("PDOS active-site indices do not match the construction mapping")
        if any(int(pdos[label]["natoms"]) != 346 for label in pdos):
            raise RuntimeError("PDOS atom count mismatch")
        bader_active = {
            row["model"]: row for row in bader_rows if row["role"] == "active_Co"
        }
        if set(bader_active) != {"Al16", "control"}:
            raise RuntimeError("Bader active-site pair is incomplete")

        def delta(field: str) -> float:
            return float(pdos["Al16"][field]) - float(pdos["control"][field])

        electron_delta = (
            float(bader_active["Al16"]["bader_electrons"])
            - float(bader_active["control"]["bader_electrons"])
        )
        charge_delta = (
            float(bader_active["Al16"]["bader_net_charge_e"])
            - float(bader_active["control"]["bader_net_charge_e"])
        )
        moment_delta = (
            float(bader_active["Al16"]["local_moment_muB"])
            - float(bader_active["control"]["local_moment_muB"])
        )
        report = f"""# Bare fixed-geometry Al contribution: Bader and PDOS

## Matched observables

- Active Co Bader-electron change (Al16-control): {electron_delta:+.6f} e.
- Active Co net-charge change (Al16-control): {charge_delta:+.6f} e.
- Active Co local-moment change (Al16-control): {moment_delta:+.6f} muB.
- Occupied Co-d center (-8 to 0 eV relative to each Fermi level): {delta('d_center_occ_m8_0_eV'):+.6f} eV.
- Full Co-d center (-8 to +5 eV): {delta('d_center_m8_p5_eV'):+.6f} eV.
- Near-Fermi Co-d center (-2 to +2 eV): {delta('d_center_m2_p2_eV'):+.6f} eV.

## Interpretation

At fixed bare geometry, Al substitution produces a small redistribution rather than strong electron withdrawal from the active Co: the Co gains about 0.027 Bader electron, becomes slightly less positively charged, and its local moment rises by 0.146 muB. The occupied and full-window Co-d centers shift upward by about 0.08 eV relative to each model's Fermi level. This is consistent with weak electronic tuning of the neighboring Co, not an integer oxidation-state change.

This bare-state diagnostic cannot establish an OER improvement. State-dependent OH/O/OOH Bader and PDOS trends, final relaxed statics, and matched CHE are required. The cDFT result already indicates state-selective, delocalized Co-adsorbate charge accommodation. Absolute Fermi energies are not compared because no common vacuum alignment was applied.
"""
        write_text(sftp, REPORT, report)

        lines = read_text(sftp, MANIFEST).splitlines()
        for row_index in (1, 2):
            fields = lines[row_index].split("\t")
            expected = f"_pdos_{JOB_ID}_pending"
            if not fields[7].endswith(expected):
                raise RuntimeError(f"unexpected task{row_index - 1} status: {fields[7]}")
            fields[7] = fields[7][: -len(expected)] + f"_pdos_{JOB_ID}_valid"
            lines[row_index] = "\t".join(fields)
        write_text(sftp, MANIFEST, "\n".join(lines) + "\n")

        scheduler = read_text(sftp, SCHEDULER)
        scheduler += (
            f"2026-08-19\tfixed_geometry_bare_pdos_pair_valid\t{JOB_ID}\tn28\t1\t1\t"
            f"active_Co_dcenter_occ_delta{delta('d_center_occ_m8_0_eV'):+.6f}eV;"
            f"full_delta{delta('d_center_m8_p5_eV'):+.6f}eV;"
            f"nearEF_delta{delta('d_center_m2_p2_eV'):+.6f}eV\n"
        )
        write_text(sftp, SCHEDULER, scheduler)
        print(report)
    finally:
        client.close()


if __name__ == "__main__":
    main()
