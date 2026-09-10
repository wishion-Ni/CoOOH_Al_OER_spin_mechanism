from __future__ import annotations

import re
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parent
INPUT = ROOT / "pdos_oh_o_inputs_20260824"
H2_E0_EV = -6.77297296
G_VIB_O_EV = 0.030322924
G_VIB_OH_EV = 0.332635319
G_CORR_H2_EV = -0.044765890


def final_e0(path: Path) -> float:
    pattern = re.compile(r"\bE0=\s*([-+0-9.Ee]+)")
    values = []
    for line in path.read_text(encoding="ascii").splitlines():
        match = pattern.search(line)
        if match:
            values.append(float(match.group(1)))
    if not values:
        raise ValueError(f"No final E0 in {path}")
    return values[-1]


def main() -> None:
    rows = []
    local_correction = G_VIB_O_EV - G_VIB_OH_EV + 0.5 * G_CORR_H2_EV
    for material, prefix in (("Undoped CoOOH", "undoped"), ("Al-doped CoOOH", "Al16")):
        e_oh = final_e0(INPUT / f"{prefix}_OH/OSZICAR")
        e_o = final_e0(INPUT / f"{prefix}_O/OSZICAR")
        u_electronic = e_o - e_oh + 0.5 * H2_E0_EV
        u_298 = u_electronic + local_correction
        rows.append((material, e_oh, e_o, u_electronic, local_correction, u_298))

    tsv = ROOT / "deprotonation_potential_preliminary_20260824.tsv"
    with tsv.open("w", encoding="ascii", newline="\n") as handle:
        handle.write("material\tE0_OH_eV\tE0_O_eV\tUeq_electronic_V\t"
                     "local_298K_correction_eV\tUeq_298K_CHE_V\tstatus\n")
        for row in rows:
            handle.write("\t".join([row[0], *(f"{value:.8f}" for value in row[1:]),
                                     "preliminary_fixed_geometry_first_deprotonation"]) + "\n")

    colors = {"Undoped CoOOH": "#555555", "Al-doped CoOOH": "#D04A35"}
    fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.2), constrained_layout=True)
    potentials = np.linspace(1.0, 3.2, 300)
    for material, _, _, _, _, u_298 in rows:
        dg = u_298 - potentials
        axes[0].plot(potentials, dg, lw=1.8, color=colors[material], label=material)
        axes[0].scatter([u_298], [0], s=28, color=colors[material], zorder=3)
        axes[0].annotate(f"{u_298:.2f} V", (u_298, 0), xytext=(4, 8),
                         textcoords="offset points", fontsize=8, color=colors[material])
    axes[0].axhline(0, color="#222222", lw=0.8)
    axes[0].set_xlabel("Potential vs RHE (V)")
    axes[0].set_ylabel(r"$\Delta G_{\mathrm{OH\rightarrow O}}(U)$ (eV)")
    axes[0].set_title("First-site CHE crossing", loc="left", fontsize=10)
    axes[0].legend(frameon=False, fontsize=8)

    values = [row[-1] for row in rows]
    bars = axes[1].bar([0, 1], values, color=[colors[row[0]] for row in rows], width=0.62)
    axes[1].set_xticks([0, 1], ["Undoped", "Al-doped"])
    axes[1].set_ylabel("Required deprotonation potential (V)")
    axes[1].set_title("Matched *OH → *O", loc="left", fontsize=10)
    axes[1].set_ylim(0, max(values) + 0.45)
    for bar, value in zip(bars, values):
        axes[1].text(bar.get_x() + bar.get_width() / 2, value + 0.06, f"{value:.2f}",
                     ha="center", va="bottom", fontsize=9)
    delta = values[1] - values[0]
    axes[1].text(0.5, max(values) + 0.25, f"Al shift = {delta:+.2f} V",
                 ha="center", va="center", fontsize=9)
    for ax in axes:
        ax.spines[["top", "right"]].set_visible(False)
        ax.tick_params(direction="out", width=0.8, length=3)
    fig.text(0.5, -0.02,
             "Preliminary fixed-geometry first deprotonation; coverage sequence pending",
             ha="center", fontsize=8, color="#444444")
    output = ROOT / "deprotonation_potential_preliminary_20260824.png"
    fig.savefig(output, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(tsv)
    print(output)


if __name__ == "__main__":
    main()
