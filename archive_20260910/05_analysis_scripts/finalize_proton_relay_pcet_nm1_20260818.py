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

REMOTE_ROOT = (
    "sfs/CoOH/cp2k/thermo_vib_5OH_U100_current_20260704/"
    "proton_relay_al16_vs_undoped_20260817"
)
PCET = posixpath.join(REMOTE_ROOT, "pcet_CoO_fragment_Nm1")
IMAGES = (0, 4, 6)
NEUTRAL = {
    "al16": {0: 0.000000, 4: 2.610560, 6: 3.362339},
    "undoped": {0: 0.000000, 4: 0.892610, 6: 0.708609},
}


def read_text(sftp, rel: str) -> str:
    with sftp.open(posixpath.join(ssh_ncw.REMOTE_ROOT, rel), "r") as handle:
        return handle.read().decode(errors="replace")


def write_text(sftp, rel: str, value: str) -> None:
    with sftp.open(posixpath.join(ssh_ncw.REMOTE_ROOT, rel), "w") as handle:
        handle.write(value)


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
        manifest = read_text(sftp, posixpath.join(PCET, "scan_manifest.tsv"))
        rows = {}
        for line in manifest.splitlines()[1:]:
            fields = line.split("\t")
            if len(fields) < 8:
                raise RuntimeError(f"bad manifest row: {line}")
            task, case, image = int(fields[0]), fields[1], int(fields[2])
            match = re.fullmatch(
                r"valid_(\S+)_dE([-+0-9.]+)eV_CoSpin([-+0-9.]+)_OSpin([-+0-9.]+)",
                fields[7],
            )
            if not match:
                raise RuntimeError(f"task {task} is not valid: {fields[7]}")
            rows[(case, image)] = {
                "task": task,
                "job": match.group(1),
                "dE": float(match.group(2)),
                "co_spin": float(match.group(3)),
                "o_spin": float(match.group(4)),
            }

        expected = {(case, image) for case in ("al16", "undoped") for image in IMAGES}
        if set(rows) != expected:
            raise RuntimeError(f"unexpected valid point set: {sorted(rows)}")

        conditioned = {}
        for case in ("al16", "undoped"):
            reference = rows[(case, 0)]["dE"]
            conditioned[case] = {
                image: NEUTRAL[case][image] + rows[(case, image)]["dE"] - reference
                for image in IMAGES
            }

        tsv_lines = [
            "case\timage\tneutral_relative_eV\tNm1_penalty_eV\t"
            "Nm1_conditioned_relative_eV\tCo_spin\tdonor_O_spin\tjob"
        ]
        for case in ("al16", "undoped"):
            for image in IMAGES:
                row = rows[(case, image)]
                tsv_lines.append(
                    f"{case}\t{image}\t{NEUTRAL[case][image]:.6f}\t"
                    f"{row['dE']:.6f}\t{conditioned[case][image]:.6f}\t"
                    f"{row['co_spin']:.3f}\t{row['o_spin']:.3f}\t{row['job']}"
                )
        profile = "\n".join(tsv_lines) + "\n"

        report = f"""# Al16 versus undoped proton-relay cDFT screen

Fixed-heavy-atom representative images 0, 4 and 6 were compared using matched Co-O fragment N-1 Hirshfeld cDFT constraints. This is a screening coordinate, not a NEB barrier or a CHE free-energy profile.

## Results

- Neutral Al16 selected-image profile: 0.000000, 2.610560, 3.362339 eV.
- Neutral undoped selected-image profile: 0.000000, 0.892610, 0.708609 eV.
- N-1-conditioned Al16 profile: 0.000000, {conditioned['al16'][4]:.6f}, {conditioned['al16'][6]:.6f} eV.
- N-1-conditioned undoped profile: 0.000000, {conditioned['undoped'][4]:.6f}, {conditioned['undoped'][6]:.6f} eV.

N-1 oxidation lowers the Al16 image-4 and product energies by {NEUTRAL['al16'][4] - conditioned['al16'][4]:.6f} and {NEUTRAL['al16'][6] - conditioned['al16'][6]:.6f} eV relative to its initial image. For undoped, it raises them by {conditioned['undoped'][4] - NEUTRAL['undoped'][4]:.6f} and {conditioned['undoped'][6] - NEUTRAL['undoped'][6]:.6f} eV. Even after N-1 conditioning, the Al16 path remains {conditioned['al16'][4] - conditioned['undoped'][4]:.6f} eV higher at image 4 and {conditioned['al16'][6] - conditioned['undoped'][6]:.6f} eV higher at the product.

## Interpretation

For this local geometry, oxidation does not reverse the neutral conclusion: the adjacent Al-bound OH is not a favorable proton acceptor for Co-OH deprotonation. The initial Al16 OH points away from the acceptor and requires a costly rotation. This result does not exclude different solvated proton networks, locally relaxed pathways or other Al arrangements. The Al16 and historical-undoped active sites are not locally identical, so the comparison is mechanistic screening rather than a quantitative matched barrier claim.
"""

        write_text(sftp, posixpath.join(REMOTE_ROOT, "pcet_nm1_energy_profile.tsv"), profile)
        write_text(sftp, posixpath.join(REMOTE_ROOT, "pcet_nm1_interpretation.md"), report)
        scheduler = read_text(sftp, posixpath.join(PCET, "scheduler_manifest.tsv"))
        summary_row = (
            "2026-08-18\tPCET_profile_completion\t111141_series\tcompleted\t"
            f"Al16_Nm1_0_4_6=0,{conditioned['al16'][4]:.6f},{conditioned['al16'][6]:.6f}eV;"
            f"undoped_Nm1_0_4_6=0,{conditioned['undoped'][4]:.6f},{conditioned['undoped'][6]:.6f}eV;"
            "fixed_heavy_atom_screen_not_NEB\n"
        )
        if summary_row not in scheduler:
            scheduler += ("" if scheduler.endswith("\n") else "\n") + summary_row
        write_text(sftp, posixpath.join(PCET, "scheduler_manifest.tsv"), scheduler)
    finally:
        client.close()

    tsv_path = ROOT / "artifacts/proton_relay_pcet_nm1_profile_20260818.tsv"
    report_path = ROOT / "artifacts/proton_relay_pcet_nm1_report_20260818.md"
    tsv_path.write_text(profile, encoding="ascii")
    report_path.write_text(report, encoding="ascii")

    import matplotlib.pyplot as plt

    colors = {"al16": "#b23a32", "undoped": "#23688b"}
    labels = {"al16": "Al16: Co-OH to Al-OH", "undoped": "Undoped: Co-OH to Co-OH"}
    x = [0.0, 1.0, 2.0]
    xticklabels = ["Initial", "Image 4", "Product"]
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 4.4), dpi=180, sharey=True)
    panels = (
        ("Neutral electronic profile", NEUTRAL),
        ("Co-O fragment N-1 conditioned", conditioned),
    )
    for ax, (title, data) in zip(axes, panels):
        for case in ("al16", "undoped"):
            y = [data[case][image] for image in IMAGES]
            for index, value in enumerate(y):
                ax.plot(
                    [x[index] - 0.16, x[index] + 0.16],
                    [value, value],
                    color=colors[case],
                    linewidth=2.3,
                )
                ax.text(
                    x[index],
                    value + 0.09,
                    f"{value:.2f}",
                    ha="center",
                    va="bottom",
                    fontsize=8,
                    color=colors[case],
                )
                if index < len(y) - 1:
                    ax.plot(
                        [x[index] + 0.16, x[index + 1] - 0.16],
                        [value, y[index + 1]],
                        color=colors[case],
                        linewidth=1.6,
                    )
            ax.plot([], [], color=colors[case], linewidth=2.3, label=labels[case])
        ax.set_title(title, fontsize=10)
        ax.set_xticks(x, xticklabels)
        ax.grid(axis="y", color="#d8d8d8", linewidth=0.7)
        ax.spines[["top", "right"]].set_visible(False)
    axes[0].set_ylabel("Relative electronic energy (eV)")
    axes[1].legend(frameon=False, fontsize=8, loc="upper left")
    fig.suptitle("Fixed-geometry proton-relay screening", fontsize=11)
    fig.tight_layout()
    png = ROOT / "artifacts/proton_relay_pcet_nm1_profile_20260818.png"
    svg = ROOT / "artifacts/proton_relay_pcet_nm1_profile_20260818.svg"
    fig.savefig(png, bbox_inches="tight")
    fig.savefig(svg, bbox_inches="tight")
    plt.close(fig)
    print(profile)


if __name__ == "__main__":
    main()
