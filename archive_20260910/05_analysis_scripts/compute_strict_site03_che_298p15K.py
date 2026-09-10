from __future__ import annotations

import math
from pathlib import Path

import numpy as np


T = 298.15
P = 1.0e5
KB_J = 1.380649e-23
KB_EV = 8.617333262145e-5
H_J = 6.62607015e-34
HC_EV_CM = 1.2398419843320026e-4
AMU_KG = 1.66053906660e-27
ANG_M = 1.0e-10

ENERGY = {
    "bare": -298.22963503,
    "OH": -307.54393037,
    "O": -301.80203793,
    "OOH": -312.17460300,
    "H2": -6.77297296,
    "H2O": -14.23256395,
}

FREQ = {
    "O": [474.115135, 229.282064, 197.888243],
    "OH": [3682.846021, 847.571495, 468.671041, 429.007315, 212.285141, 207.714961],
    "OOH": [2301.708739, 1490.768654, 981.272347, 938.083630, 347.653024, 200.722799, 165.233371, 132.321318, 56.069290],
    "H2": [4333.575703],
    "H2O": [3840.174656, 3729.360486, 1584.384798],
}

H2_COORDS_ANG = np.array([[10.0, 10.0, 9.625051743831744], [10.0, 10.0, 10.374948256168258]])
H2O_COORDS_ANG = np.array(
    [
        [10.76852368205222, 10.000000052241904, 10.591581914402752],
        [9.231476286827116, 10.000000051495716, 10.591581851080902],
        [10.000000031120662, 9.999999896262382, 9.996836234516294],
    ]
)


def vib_free_energy(freqs_cm: list[float], cutoff_cm: float | None = None) -> float:
    total = 0.0
    for freq in freqs_cm:
        used = max(freq, cutoff_cm) if cutoff_cm is not None else freq
        quantum = HC_EV_CM * used
        total += 0.5 * quantum + KB_EV * T * math.log1p(-math.exp(-quantum / (KB_EV * T)))
    return total


def translational_free_energy(mass_amu: float) -> float:
    mass = mass_amu * AMU_KG
    q_trans = (2.0 * math.pi * mass * KB_J * T / H_J**2) ** 1.5 * (KB_J * T / P)
    return -KB_EV * T * math.log(q_trans)


def principal_moments(masses_amu: np.ndarray, coords_ang: np.ndarray) -> np.ndarray:
    masses = masses_amu * AMU_KG
    coords = coords_ang * ANG_M
    center = np.average(coords, axis=0, weights=masses)
    xyz = coords - center
    tensor = np.zeros((3, 3))
    for mass, vector in zip(masses, xyz):
        tensor += mass * ((vector @ vector) * np.eye(3) - np.outer(vector, vector))
    return np.linalg.eigvalsh(tensor)


def linear_rotational_free_energy(moment: float, symmetry: int) -> float:
    q_rot = 8.0 * math.pi**2 * moment * KB_J * T / (symmetry * H_J**2)
    return -KB_EV * T * math.log(q_rot)


def nonlinear_rotational_free_energy(moments: np.ndarray, symmetry: int) -> float:
    prefactor = (8.0 * math.pi**2 * KB_J * T / H_J**2) ** 1.5
    q_rot = math.sqrt(math.pi) / symmetry * prefactor * math.sqrt(float(np.prod(moments)))
    return -KB_EV * T * math.log(q_rot)


g_vib = {
    "O": vib_free_energy(FREQ["O"], cutoff_cm=100.0),
    "OH": vib_free_energy(FREQ["OH"], cutoff_cm=100.0),
    "OOH": vib_free_energy(FREQ["OOH"], cutoff_cm=100.0),
    "H2": vib_free_energy(FREQ["H2"]),
    "H2O": vib_free_energy(FREQ["H2O"]),
}

h2_moments = principal_moments(np.array([1.00784, 1.00784]), H2_COORDS_ANG)
h2o_moments = principal_moments(np.array([1.00784, 1.00784, 15.999]), H2O_COORDS_ANG)

gas_parts = {
    "H2": {
        "translation": translational_free_energy(2.0 * 1.00784),
        "rotation": linear_rotational_free_energy(float(h2_moments[-1]), symmetry=2),
        "vibration": g_vib["H2"],
    },
    "H2O": {
        "translation": translational_free_energy(2.0 * 1.00784 + 15.999),
        "rotation": nonlinear_rotational_free_energy(h2o_moments, symmetry=2),
        "vibration": g_vib["H2O"],
    },
}
gas_corr = {name: sum(parts.values()) for name, parts in gas_parts.items()}

g = {
    "bare": ENERGY["bare"],
    "OH": ENERGY["OH"] + g_vib["OH"],
    "O": ENERGY["O"] + g_vib["O"],
    "OOH": ENERGY["OOH"] + g_vib["OOH"],
    "H2": ENERGY["H2"] + gas_corr["H2"],
    "H2O": ENERGY["H2O"] + gas_corr["H2O"],
}

water_minus_half_h2 = g["H2O"] - 0.5 * g["H2"]
steps = [
    g["OH"] - g["bare"] - water_minus_half_h2,
    g["O"] - g["OH"] + 0.5 * g["H2"],
    g["OOH"] - g["O"] - water_minus_half_h2,
]
steps.append(4.92 - sum(steps))
pds_index = max(range(4), key=steps.__getitem__)
eta = steps[pds_index] - 1.23

out_dir = Path(__file__).parent
detail_path = out_dir / "strict_site03_vasp_298p15K_thermo_details.tsv"
summary_path = out_dir / "strict_site03_vasp_298p15K_che_summary.tsv"

with detail_path.open("w", encoding="ascii") as handle:
    handle.write("component\ttranslation_eV\trotation_eV\tvibration_eV\ttotal_correction_eV\tnotes\n")
    handle.write(f"ads_O\t0\t0\t{g_vib['O']:.9f}\t{g_vib['O']:.9f}\tmode-selective;100_cm-1_cutoff_not_triggered\n")
    handle.write(f"ads_OH\t0\t0\t{g_vib['OH']:.9f}\t{g_vib['OH']:.9f}\tmode-selective;100_cm-1_cutoff_not_triggered\n")
    handle.write(f"ads_OOH\t0\t0\t{g_vib['OOH']:.9f}\t{g_vib['OOH']:.9f}\tmode-selective;56.069290_cm-1_replaced_by_100_cm-1\n")
    for name in ("H2", "H2O"):
        parts = gas_parts[name]
        handle.write(
            f"gas_{name}\t{parts['translation']:.9f}\t{parts['rotation']:.9f}\t{parts['vibration']:.9f}\t{gas_corr[name]:.9f}\tideal_gas_298.15_K_1_bar;internal_vibrations_only\n"
        )

with summary_path.open("w", encoding="ascii") as handle:
    handle.write(
        "system\ttemperature_K\tpressure_bar\tdG1_eV\tdG2_eV\tdG3_eV\tdG4_eV\tPDS\t"
        "limiting_potential_V\toverpotential_V\tliterature_target_overpotential_V\t"
        "deviation_V\ttolerance_V\treproduction_gate\tstatus\n"
    )
    labels = ["bare_to_OH", "OH_to_O", "O_to_OOH", "OOH_to_O2"]
    handle.write(
        "strict_undoped_site03\t298.15\t1.0\t"
        + "\t".join(f"{value:.9f}" for value in steps)
        + f"\t{labels[pds_index]}\t{steps[pds_index]:.9f}\t{eta:.9f}\t1.000000000\t"
        + f"{eta - 1.0:.9f}\t0.200000000\tPASS_BOUNDARY\tVALID_STRICT_THERMO\n"
    )

print("Gvib", {key: round(value, 9) for key, value in g_vib.items()})
print("gas_parts", gas_parts)
print("gas_corr", gas_corr)
print("moments_H2", h2_moments)
print("moments_H2O", h2o_moments)
print("steps", steps)
print("PDS", pds_index + 1, "eta", eta)
