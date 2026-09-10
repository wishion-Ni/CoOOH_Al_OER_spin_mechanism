from __future__ import annotations

import csv
import importlib.util
import io
import posixpath
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


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
REMOTE_FILES = {
    "stage_summary_bare_bader_20260819.tsv": posixpath.join(ANALYSIS, "bare_bader_active_site_pair.tsv"),
    "stage_summary_bare_pdos_20260819.tsv": posixpath.join(ANALYSIS, "bare_pdos_active_co_pair.tsv"),
    "stage_summary_analysis_manifest_20260819.tsv": posixpath.join(ANALYSIS, "analysis_manifest.tsv"),
}

OUT_STEM = ARTIFACTS / "cooh_al16_stage_summary_20260819"


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="ascii") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def fetch_remote_sources() -> None:
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
        for local_name, remote_rel in REMOTE_FILES.items():
            with sftp.open(posixpath.join(ssh_ncw.REMOTE_ROOT, remote_rel), "r") as handle:
                content = handle.read().decode("ascii")
            (ARTIFACTS / local_name).write_text(content, encoding="ascii")
    finally:
        client.close()


def style_axis(ax: plt.Axes) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", color="#D1D5DB", linewidth=0.7, alpha=0.65)
    ax.set_axisbelow(True)


def plot_che(ax: plt.Axes) -> None:
    rows = read_tsv(ARTIFACTS / "strict_site03_vasp_298p15K_staircase.tsv")
    labels = [row["state"] for row in rows]
    x = np.arange(len(rows))
    u0 = np.array([float(row["dG_U0_eV"]) for row in rows])
    u123 = np.array([float(row["dG_U1.23_eV"]) for row in rows])
    ax.plot(x, u0, marker="o", linewidth=2.3, color="#374151", label="U = 0 V")
    ax.plot(x, u123, marker="s", linewidth=2.1, color="#0F766E", label="U = 1.23 V")
    ax.fill_between([1, 2], [u0[1], u0[1]], [u0[2], u0[2]], color="#D97706", alpha=0.12)
    ax.annotate(
        "PDS: OH* -> O*\n2.031 eV",
        xy=(1.5, (u0[1] + u0[2]) / 2),
        xytext=(2.25, 2.55),
        arrowprops={"arrowstyle": "->", "color": "#B45309", "lw": 1.4},
        color="#92400E",
        fontsize=9,
        ha="center",
    )
    ax.text(
        0.02,
        0.96,
        "Undoped strict CHE complete\neta = 0.801 V",
        transform=ax.transAxes,
        va="top",
        fontsize=10,
        color="#111827",
        bbox={"facecolor": "white", "edgecolor": "#9CA3AF", "pad": 5},
    )
    ax.text(
        0.98,
        0.04,
        "Exact Al16/control CHE: pending",
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=9,
        color="#B45309",
    )
    ax.set_xticks(x, labels)
    ax.set_ylabel("Free energy (eV)")
    ax.set_title("A  Conventional four-step AEM/CHE", loc="left", fontweight="bold")
    ax.legend(frameon=False, loc="upper center", ncol=2, fontsize=9)
    style_axis(ax)


def plot_cdft(ax: plt.Axes) -> None:
    rows = read_tsv(ARTIFACTS / "cdft_undoped_vs_al16_complete_20260818.tsv")
    selected = {
        row["state"]: row
        for row in rows
        if row["constraint_scope"] == "Co+adsorbate" and row["direction"] == "N-1"
    }
    states = ["OH", "O", "OOH"]
    x = np.arange(len(states))
    undoped = np.array([float(selected[state]["undoped_eV"]) for state in states])
    al16 = np.array([float(selected[state]["Al16_eV"]) for state in states])
    delta = al16 - undoped
    width = 0.34
    ax.bar(x - width / 2, undoped, width, color="#4B5563", label="Undoped")
    ax.bar(x + width / 2, al16, width, color="#0F766E", label="Al16")
    for index, value in enumerate(delta):
        color = "#B91C1C" if value > 0 else "#047857"
        ax.text(
            index,
            max(undoped[index], al16[index]) + 0.11,
            f"Delta={value:+.3f} eV",
            ha="center",
            fontsize=9,
            color=color,
            fontweight="bold",
        )
    ax.set_xticks(x, ["OH", "O", "OOH"])
    ax.set_ylim(0, 4.55)
    ax.set_ylabel("Fragment N-1 penalty (eV)")
    ax.set_title("B  cDFT oxidation localization", loc="left", fontweight="bold")
    ax.legend(frameon=False, ncol=2, loc="upper left")
    ax.text(
        0.98,
        0.98,
        "Fragment cost < Co-only cost: delocalized Co-O response\nAl effect: OH/O harder, OOH easier",
        transform=ax.transAxes,
        fontsize=8.8,
        ha="right",
        va="top",
        color="#374151",
        bbox={"facecolor": "white", "edgecolor": "#D1D5DB", "pad": 4},
    )
    style_axis(ax)


def plot_relay(ax: plt.Axes) -> None:
    neutral_rows = read_tsv(ARTIFACTS / "proton_relay_fixed_path_20260817.tsv")
    pcet_rows = read_tsv(ARTIFACTS / "proton_relay_pcet_nm1_profile_20260818.tsv")
    colors = {"al16": "#B91C1C", "undoped": "#4B5563"}
    labels = {"al16": "Al16: Co-OH -> Al-OH", "undoped": "Control: Co-OH -> Co-OH"}
    for case in ("al16", "undoped"):
        case_rows = [row for row in neutral_rows if row["case"] == case]
        x = [int(row["image"]) for row in case_rows]
        y = [float(row["relative_eV"]) for row in case_rows]
        ax.plot(x, y, marker="o", linewidth=2.3, color=colors[case], label=labels[case])
        conditioned = [row for row in pcet_rows if row["case"] == case]
        cx = [int(row["image"]) for row in conditioned]
        cy = [float(row["Nm1_conditioned_relative_eV"]) for row in conditioned]
        ax.plot(cx, cy, marker="D", linestyle="--", linewidth=1.7, color=colors[case], alpha=0.72)
    ax.text(5.95, 3.43, "+3.36", color="#B91C1C", ha="right", fontsize=9)
    ax.text(5.95, 0.78, "+0.71", color="#374151", ha="right", fontsize=9)
    ax.set_xlabel("Fixed proton-coordinate image")
    ax.set_ylabel("Relative energy (eV)")
    ax.set_xticks(range(7))
    ax.set_ylim(-0.08, 3.75)
    ax.set_title("C  Adjacent-OH proton relay screen", loc="left", fontweight="bold")
    ax.legend(frameon=False, fontsize=8.5, loc="upper left")
    ax.text(
        0.98,
        0.05,
        "Solid: neutral   Dashed: N-1 conditioned\nCurrent geometry does not support Al-OH relay",
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=9,
        color="#374151",
    )
    style_axis(ax)


def plot_electronic_and_progress(ax: plt.Axes) -> None:
    bader = read_tsv(ARTIFACTS / "stage_summary_bare_bader_20260819.tsv")
    pdos = read_tsv(ARTIFACTS / "stage_summary_bare_pdos_20260819.tsv")
    manifest = read_tsv(ARTIFACTS / "stage_summary_analysis_manifest_20260819.tsv")
    active = {row["model"]: row for row in bader if row["role"] == "active_Co"}
    pdos_by_model = {row["model"]: row for row in pdos}
    dq = float(active["Al16"]["bader_net_charge_e"]) - float(active["control"]["bader_net_charge_e"])
    dmu = float(active["Al16"]["local_moment_muB"]) - float(active["control"]["local_moment_muB"])
    ded = float(pdos_by_model["Al16"]["d_center_occ_m8_0_eV"]) - float(
        pdos_by_model["control"]["d_center_occ_m8_0_eV"]
    )
    fixed_done = sum("valid_vasp_" in row["status"] for row in manifest)
    bader_done = sum("bader_" in row["status"] and "_valid_" in row["status"] for row in manifest)
    matched_pairs = sum(
        all(
            "bader_" in manifest[2 * pair + offset]["status"]
            and "_valid_" in manifest[2 * pair + offset]["status"]
            for offset in (0, 1)
        )
        for pair in range(4)
    )

    ax.set_title("D  Electronic diagnostics and workflow", loc="left", fontweight="bold")
    ax.axis("off")
    callouts = [
        (0.04, "Active Co net charge", f"{dq:+.3f} e", "slightly less positive"),
        (0.36, "Active Co moment", f"{dmu:+.3f} muB", "higher local spin"),
        (0.68, "Occupied Co-d center", f"{ded:+.3f} eV", "upshift vs own EF"),
    ]
    for x, title, value, note in callouts:
        ax.text(x, 0.91, title, transform=ax.transAxes, fontsize=9, color="#4B5563")
        ax.text(x, 0.82, value, transform=ax.transAxes, fontsize=17, fontweight="bold", color="#0F766E")
        ax.text(x, 0.76, note, transform=ax.transAxes, fontsize=8.5, color="#6B7280")

    progress = [
        ("cDFT matched scans", 1.00, "14/14 valid"),
        ("Proton-relay screen", 1.00, "14 neutral + 6 N-1"),
        ("Fixed-geometry VASP", fixed_done / 8.0, f"{fixed_done}/8 complete"),
        ("Bader analyses", bader_done / 8.0, f"{bader_done}/8 valid"),
        ("Matched electronic pairs", matched_pairs / 4.0, f"{matched_pairs}/4 pairs"),
        ("Strict Al16/control relax", 0.00, "8 running; 0 valid final"),
        ("Exact matched CHE", 0.00, "pending relax/statics/vib"),
    ]
    start_y = 0.64
    for index, (label, fraction, note) in enumerate(progress):
        y = start_y - index * 0.083
        ax.add_patch(plt.Rectangle((0.04, y), 0.54, 0.031, transform=ax.transAxes, color="#E5E7EB", lw=0))
        if fraction > 0:
            ax.add_patch(
                plt.Rectangle((0.04, y), 0.54 * fraction, 0.031, transform=ax.transAxes, color="#0F766E", lw=0)
            )
        ax.text(0.04, y + 0.04, label, transform=ax.transAxes, fontsize=8.7, color="#111827")
        ax.text(0.61, y + 0.014, note, transform=ax.transAxes, va="center", fontsize=8.4, color="#4B5563")
    ax.text(
        0.04,
        0.025,
        "Bare result: weak electronic tuning, not strong Co electron withdrawal.\n"
        "COHP pending licensed LOBSTER; structural effects await final relaxed statics.",
        transform=ax.transAxes,
        fontsize=9,
        color="#92400E",
    )


def write_summary() -> None:
    text = """# CoOH Al16 stage summary (2026-08-19)

## Completed and validated

- Strict undoped site03 CHE: dG = (1.755822390, 2.030710620, 0.669871268, 0.463595722) eV; PDS OH* -> O*; eta = 0.800710620 V.
- Matched cDFT scan set: 14/14 undoped scans valid and Al16 comparison complete. OER-relevant Co+adsorbate N-1 Al16-undoped shifts are OH +0.282946 eV, O +0.077453 eV, OOH -0.367431 eV.
- Proton-relay screen: neutral and N-1-conditioned fixed-coordinate profiles complete. The current Al-bound OH geometry does not assist adjacent Co-OH deprotonation.
- Bare fixed-geometry Bader/PDOS pair: active Co gains 0.026856 Bader electron, moment rises 0.146 muB, and occupied d center shifts +0.081891 eV in Al16.

## Running or pending

- Exact matched Al16/control strict relaxations: eight unique jobs running; no final validated geometry yet.
- Fixed-geometry Bader/PDOS VASP: tasks 0-2 complete; task3 control-OH running; O and OOH queued.
- Al16-OH Bader is valid but remains single-sided until control-OH completes.
- Exact matched statics, vibrations and Al16/control 298.15 K CHE remain pending.
- COHP is not available without a licensed LOBSTER executable.

## Preliminary interpretation

Al does not produce a simple, uniformly electron-withdrawing active-Co response. The bare site is slightly more electron rich and higher spin, while cDFT shows state-selective delocalized Co-adsorbate charge accommodation, with the clearest favorable oxidation effect at OOH. The current Al-OH arrangement is not a favorable proton relay. A catalytic-performance claim must wait for the exact matched OH/O/OOH electronic trends and final CHE.

## Scope cautions

- The cDFT comparison uses the historical accepted undoped Co32 model and chemically valid Al16 Co40 model; local sites are not identical.
- Proton-relay profiles are fixed-heavy-atom screens, not NEB barriers.
- Current Bader/PDOS data use preconverged fixed geometries and isolate electronic substitution effects; relaxed structural effects are pending.
"""
    OUT_STEM.with_suffix(".md").write_text(text, encoding="ascii")


def main() -> None:
    fetch_remote_sources()
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "axes.labelcolor": "#111827",
            "axes.titlecolor": "#111827",
            "xtick.color": "#374151",
            "ytick.color": "#374151",
            "figure.facecolor": "white",
            "axes.facecolor": "white",
        }
    )
    fig, axes = plt.subplots(2, 2, figsize=(14.5, 10.3), constrained_layout=False)
    fig.subplots_adjust(left=0.07, right=0.98, top=0.90, bottom=0.08, wspace=0.20, hspace=0.29)
    fig.suptitle("CoOH OER with Al16: interim mechanistic summary", fontsize=19, fontweight="bold", y=0.975)
    fig.text(
        0.5,
        0.942,
        "Validated diagnostics through 2026-08-19 | Final matched Al16/control CHE remains pending",
        ha="center",
        fontsize=10.5,
        color="#4B5563",
    )
    plot_che(axes[0, 0])
    plot_cdft(axes[0, 1])
    plot_relay(axes[1, 0])
    plot_electronic_and_progress(axes[1, 1])
    fig.text(
        0.07,
        0.025,
        "N-1 means one electron removed from the constrained fragment. Bader charges are partition-dependent diagnostics, not formal oxidation states.",
        fontsize=8.5,
        color="#6B7280",
    )
    fig.savefig(OUT_STEM.with_suffix(".png"), dpi=220)
    fig.savefig(OUT_STEM.with_suffix(".svg"))
    fig.savefig(OUT_STEM.with_suffix(".pdf"))
    plt.close(fig)
    write_summary()
    print(OUT_STEM.with_suffix(".png"))


if __name__ == "__main__":
    main()
