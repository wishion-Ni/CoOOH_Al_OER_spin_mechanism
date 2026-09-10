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

REMOTE = (
    "sfs/CoOH/cp2k/thermo_vib_5OH_U100_current_20260704/"
    "proton_relay_al16_vs_undoped_20260817"
)
HARTREE_TO_EV = 27.211386245988


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
        manifest = read_text(sftp, posixpath.join(REMOTE, "scan_manifest.tsv"))
        lines = manifest.splitlines()
        rows = []
        for line_index, line in enumerate(lines[1:], start=1):
            fields = line.split("\t")
            if len(fields) != 10:
                raise RuntimeError(f"bad manifest row: {line}")
            task, case, image = int(fields[0]), fields[1], int(fields[2])
            output = read_text(
                sftp,
                posixpath.join(REMOTE, case, f"image_{image:02d}", "scan.out"),
            )
            if "PROGRAM ENDED AT" not in output:
                raise RuntimeError(f"task {task} has not ended cleanly")
            forbidden = (
                "ABORT in",
                "SCF run NOT converged",
                "Cholesky decompose failed",
                "BAD TERMINATION",
            )
            if any(marker in output for marker in forbidden):
                raise RuntimeError(f"task {task} contains a fatal signature")
            energies = re.findall(
                r"ENERGY\| Total FORCE_EVAL \( QS \) energy \[a\.u\.\]:\s*"
                r"([-+0-9.Ee]+)",
                output,
            )
            if not energies:
                raise RuntimeError(f"task {task} has no final energy")
            energy = float(energies[-1])
            fields[9] = f"valid_111126_{task}_E{energy:.12f}Ha"
            lines[line_index] = "\t".join(fields)
            rows.append(
                {
                    "task": task,
                    "case": case,
                    "image": image,
                    "segment": fields[3],
                    "h_acceptor": float(fields[8]),
                    "energy": energy,
                }
            )

        references = {
            case: next(row["energy"] for row in rows if row["case"] == case and row["image"] == 0)
            for case in ("al16", "undoped")
        }
        tsv_lines = [
            "task\tcase\timage\tsegment\tH_acceptor_A\tenergy_Ha\trelative_eV"
        ]
        for row in rows:
            row["relative"] = (row["energy"] - references[row["case"]]) * HARTREE_TO_EV
            tsv_lines.append(
                f"{row['task']}\t{row['case']}\t{row['image']}\t{row['segment']}\t"
                f"{row['h_acceptor']:.6f}\t{row['energy']:.12f}\t{row['relative']:.6f}"
            )
        profile = "\n".join(tsv_lines) + "\n"
        write_text(sftp, posixpath.join(REMOTE, "fixed_path_energy_profile.tsv"), profile)
        write_text(sftp, posixpath.join(REMOTE, "scan_manifest.tsv"), "\n".join(lines) + "\n")

        summaries = {}
        for case in ("al16", "undoped"):
            case_rows = [row for row in rows if row["case"] == case]
            maximum = max(case_rows, key=lambda row: row["relative"])
            product = next(row for row in case_rows if row["image"] == 6)
            summaries[case] = (maximum, product)
        scheduler = read_text(sftp, posixpath.join(REMOTE, "scheduler_manifest.tsv"))
        row = (
            "2026-08-17\tfixed_path_completion\t111126\tcompleted\t"
            f"Al16_max{summaries['al16'][0]['relative']:.6f}eV_image"
            f"{summaries['al16'][0]['image']};Al16_product"
            f"{summaries['al16'][1]['relative']:.6f}eV;undoped_max"
            f"{summaries['undoped'][0]['relative']:.6f}eV_image"
            f"{summaries['undoped'][0]['image']};undoped_product"
            f"{summaries['undoped'][1]['relative']:.6f}eV;fixed_heavy_atom_screen_not_NEB\n"
        )
        if row not in scheduler:
            scheduler += ("" if scheduler.endswith("\n") else "\n") + row
        write_text(sftp, posixpath.join(REMOTE, "scheduler_manifest.tsv"), scheduler)

        local_tsv = ROOT / "artifacts/proton_relay_fixed_path_20260817.tsv"
        local_tsv.write_text(profile, encoding="ascii")
    finally:
        client.close()

    import matplotlib.pyplot as plt

    labels = {
        "al16": "Al16: Co-OH -> Al-OH",
        "undoped": "Undoped: Co-OH -> Co-OH",
    }
    colors = {"al16": "#c43c39", "undoped": "#246b8e"}
    fig, ax = plt.subplots(figsize=(7.2, 4.6), dpi=180)
    for case in ("al16", "undoped"):
        case_rows = sorted(
            (row for row in rows if row["case"] == case), key=lambda row: row["image"]
        )
        ax.plot(
            [row["image"] for row in case_rows],
            [row["relative"] for row in case_rows],
            marker="o",
            linewidth=2.1,
            markersize=5,
            color=colors[case],
            label=labels[case],
        )
    ax.set_xlabel("Fixed proton-path image")
    ax.set_ylabel("Relative electronic energy (eV)")
    ax.set_xticks(range(7), ["Initial", "Rotate", "0.2", "0.4", "0.6", "0.8", "Product"])
    ax.grid(axis="y", color="#d8d8d8", linewidth=0.7)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False)
    ax.set_title("Neutral proton-relay fixed-geometry screening")
    fig.tight_layout()
    png = ROOT / "artifacts/proton_relay_fixed_path_20260817.png"
    svg = ROOT / "artifacts/proton_relay_fixed_path_20260817.svg"
    fig.savefig(png, bbox_inches="tight")
    fig.savefig(svg, bbox_inches="tight")
    plt.close(fig)
    print(profile)


if __name__ == "__main__":
    main()
