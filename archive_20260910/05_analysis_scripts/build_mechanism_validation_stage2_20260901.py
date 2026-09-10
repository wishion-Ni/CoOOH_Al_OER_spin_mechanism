from __future__ import annotations

import csv
import json
import re
import shutil
from pathlib import Path

import numpy as np

from build_mechanism_validation_bundle_20260901 import distance, min_image, parse_cp2k_input


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "mechanism_validation_sources_20260901"
STAGE1 = ROOT / "mechanism_validation_bundle"
OUT = ROOT / "mechanism_validation_stage2"


def write_tsv(path: Path, rows: list[dict], fields: list[str] | None = None) -> None:
    if fields is None:
        fields = list(rows[0])
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def rel(path: Path) -> str:
    return path.relative_to(ROOT.parent).as_posix()


def parse_global_settings(inp: Path, out: Path) -> dict:
    inp_text = inp.read_text(encoding="utf-8", errors="replace")
    out_text = out.read_text(encoding="utf-8", errors="replace")

    def input_value(pattern: str):
        match = re.search(pattern, inp_text, re.MULTILINE | re.IGNORECASE)
        return match.group(1) if match else None

    uks_raw = input_value(r"^\s*UKS\s+(\S+)")
    multiplicity = input_value(r"^\s*MULTIPLICITY\s+(\d+)")
    charge = input_value(r"^\s*CHARGE\s+([-+]?\d+)")
    electron_matches = re.findall(r"Number of electrons:\s+(\d+)", out_text)
    occupied_matches = re.findall(r"Number of occupied orbitals:\s+(\d+)", out_text)
    mo_matches = re.findall(r"Number of molecular orbitals:\s+(\d+)", out_text)
    total_match = re.search(
        r"# Total charge and spin\s+([-+0-9.]+)\s+([-+0-9.]+)\s+([-+0-9.]+)\s+([-+0-9.]+)",
        out_text,
    )
    basis_match = re.search(r"Number of orbital functions:\s+(\d+)", out_text)
    mpi_match = re.search(r"Total number of message passing processes\s+(\d+)", out_text)
    timing_matches = re.findall(r"^\s*CP2K\s+1\s+1\.0\s+.*?\s([0-9.]+)\s+([0-9.]+)\s*$", out_text, re.MULTILINE)
    if len(electron_matches) < 2 or not total_match:
        raise ValueError(f"Could not parse global spin settings: {out}")
    alpha, beta = int(electron_matches[0]), int(electron_matches[1])
    return {
        "UKS_printed": uks_raw,
        "multiplicity_input": int(multiplicity) if multiplicity else None,
        "charge_input_e": int(charge) if charge else None,
        "total_electrons_printed": alpha + beta,
        "N_alpha_printed": alpha,
        "N_beta_printed": beta,
        "total_magnetization_printed_Nalpha_minus_Nbeta": float(total_match.group(4)),
        "total_spin_printed": None,
        "derived_Sz_hbar": (alpha - beta) / 2,
        "occupied_orbitals_alpha_printed": int(occupied_matches[0]) if len(occupied_matches) >= 2 else None,
        "occupied_orbitals_beta_printed": int(occupied_matches[1]) if len(occupied_matches) >= 2 else None,
        "molecular_orbitals_alpha_printed": int(mo_matches[0]) if len(mo_matches) >= 2 else None,
        "molecular_orbitals_beta_printed": int(mo_matches[1]) if len(mo_matches) >= 2 else None,
        "orbital_functions_printed": int(basis_match.group(1)) if basis_match else None,
        "MPI_ranks_printed": int(mpi_match.group(1)) if mpi_match else None,
        "CP2K_wall_seconds_printed": float(timing_matches[-1][1]) if timing_matches else None,
    }


def local_frame(inp: Path, co_idx: int, oads_idx: int):
    cell, atoms = parse_cp2k_input(inp)
    co = atoms[co_idx - 1][1]
    oads = atoms[oads_idx - 1][1]
    z = min_image(oads - co, cell)
    z /= np.linalg.norm(z)
    oxygen_neighbors = []
    for idx, (element, coord) in enumerate(atoms, start=1):
        if element != "O":
            continue
        d = distance(co, coord, cell)
        if d <= 2.35:
            oxygen_neighbors.append((d, idx, min_image(coord - co, cell)))
    oxygen_neighbors.sort()
    reference = next(v for _, idx, v in oxygen_neighbors if idx != oads_idx)
    x = reference - np.dot(reference, z) * z
    x /= np.linalg.norm(x)
    y = np.cross(z, x)
    y /= np.linalg.norm(y)
    return {
        "x": x,
        "y": y,
        "z": z,
        "neighbors": [(idx, dist) for dist, idx, _ in oxygen_neighbors],
    }


def vec(v):
    return ",".join(f"{x:.8f}" for x in v)


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    cases = [
        ("pristine", "*OH", "undoped_OH", 32, 212),
        ("pristine", "*O", "undoped_O", 32, 211),
        ("Al16", "*OH", "Al16_OH", 48, 222),
        ("Al16", "*O", "Al16_O", 48, 221),
    ]

    global_rows = []
    settings = {}
    for system, state, stem, _, _ in cases:
        inp = SOURCE / f"cp2k_{stem}_baseline.inp"
        out = SOURCE / f"cp2k_{stem}_baseline.out"
        values = parse_global_settings(inp, out)
        settings[(system, state)] = values
        global_rows.append({
            "system": system,
            "state": state,
            **{k: "" if v is None else v for k, v in values.items()},
            "multiplicity_consistency": "PASS" if values["multiplicity_input"] == values["N_alpha_printed"] - values["N_beta_printed"] + 1 else "FAIL",
            "source_input": rel(inp),
            "source_output": rel(out),
        })
    write_tsv(OUT / "stage2_01_global_spin_settings.tsv", global_rows)

    global_change_rows = []
    for system in ("pristine", "Al16"):
        oh, oo = settings[(system, "*OH")], settings[(system, "*O")]
        global_change_rows.append({
            "system": system,
            "delta_total_electrons_O_minus_OH": oo["total_electrons_printed"] - oh["total_electrons_printed"],
            "delta_N_alpha": oo["N_alpha_printed"] - oh["N_alpha_printed"],
            "delta_N_beta": oo["N_beta_printed"] - oh["N_beta_printed"],
            "delta_total_magnetization": oo["total_magnetization_printed_Nalpha_minus_Nbeta"] - oh["total_magnetization_printed_Nalpha_minus_Nbeta"],
            "delta_input_multiplicity": oo["multiplicity_input"] - oh["multiplicity_input"],
            "interpretation": "The *O calculation is on an explicitly lower fixed-multiplicity branch; local alpha-to-beta changes are conditional on this global choice.",
        })
    write_tsv(OUT / "stage2_01b_global_spin_changes.tsv", global_change_rows)

    base_remote = "/home/ftfan/ncw/"
    inventory_raw = [
        ("pristine", "*OH", "final_wfn", "sfs/CoOH/cp2k/thermo_vib_5OH_U100_current_20260704/cdft_charge_spin_undoped_20260816/undoped_valid_co32_OH/cdf_base_undoped_valid_co32_OH-RESTART.wfn", 49694540, "2026-08-16T22:35:26.419928474+08:00"),
        ("pristine", "*OH", "seed_wfn", "sfs/CoOH/cp2k/thermo_vib_5OH_U100_current_20260704/cdft_charge_spin_undoped_20260816/undoped_valid_co32_OH/seed-RESTART.wfn", 49694540, "2026-08-16T22:11:13.792640863+08:00"),
        ("pristine", "*O", "final_wfn", "sfs/CoOH/cp2k/thermo_vib_5OH_U100_current_20260704/cdft_charge_spin_undoped_20260816/undoped_valid_co32_O/cdf_base_undoped_valid_co32_O-RESTART.wfn", 49587808, "2026-08-16T22:44:32.731769372+08:00"),
        ("pristine", "*O", "seed_wfn", "sfs/CoOH/cp2k/thermo_vib_5OH_U100_current_20260704/cdft_charge_spin_undoped_20260816/undoped_valid_co32_O/seed-RESTART.wfn", 49587808, "2026-08-16T22:11:15.821633012+08:00"),
        ("Al16", "*OH", "final_wfn", "sfs/CoOH/cp2k/Al16/oer/spin_config_scan_site03_5OH_current_20260714/cdft_charge_spin_20260812/al16_valid_co48_OH/cdf_base_al16_valid_co48_OH-RESTART.wfn", 44088780, "2026-08-13T21:24:13.217312443+08:00"),
        ("Al16", "*OH", "seed_wfn", "sfs/CoOH/cp2k/Al16/oer/spin_config_scan_site03_5OH_current_20260714/cdft_charge_spin_20260812/al16_valid_co48_OH/seed-RESTART.wfn", 44088780, "2026-08-12T16:50:15.163509567+08:00"),
        ("Al16", "*O", "final_wfn", "sfs/CoOH/cp2k/Al16/oer/spin_config_scan_site03_5OH_current_20260714/cdft_charge_spin_20260812/al16_valid_co48_O/cdf_base_al16_valid_co48_O-RESTART.wfn", 43988832, "2026-08-13T21:30:52.196229438+08:00"),
        ("Al16", "*O", "seed_wfn", "sfs/CoOH/cp2k/Al16/oer/spin_config_scan_site03_5OH_current_20260714/cdft_charge_spin_20260812/al16_valid_co48_O/seed-RESTART.wfn", 43988832, "2026-08-12T16:50:17.307504381+08:00"),
    ]
    inventory_rows = [
        {
            "system": s,
            "state": st,
            "file_category": cat,
            "status": "FOUND",
            "exact_path": base_remote + path,
            "size_bytes": size,
            "modified_timestamp": timestamp,
            "postprocessing_value": "Converged binary WFN exists, but OT orbitals have no printed eigenvalue/projection inventory and only occupied MO count is present.",
        }
        for s, st, cat, path, size, timestamp in inventory_raw
    ]
    for category, pattern in (
        ("restart_text", "*.restart / *.restart.bak*"),
        ("pdos", "*.pdos"),
        ("MO_eigenvalue_output", "MOLog/eigenvalue files or printed MO spectrum"),
        ("cube", "*.cube, including density and spin-density cube"),
    ):
        inventory_rows.append({
            "system": "all four states",
            "state": "*OH/*O",
            "file_category": category,
            "status": "NOT_FOUND",
            "exact_path": "",
            "size_bytes": "",
            "modified_timestamp": "",
            "postprocessing_value": f"No {pattern} file was found under the four baseline directories or the two complete cDFT roots.",
        })
    write_tsv(OUT / "stage2_02_cp2k_wavefunction_inventory.tsv", inventory_rows)

    frontier_rows = []
    for system, state, stem, co_idx, oads_idx in cases:
        if state != "*OH":
            continue
        values = settings[(system, state)]
        final_wfn = next(base_remote + p for s, st, cat, p, _, _ in inventory_raw if s == system and st == state and cat == "final_wfn")
        frontier_rows.append({
            "system": system,
            "state": state,
            "extraction_status": "STOPPED_NO_ZERO_COST_PATH",
            "existing_WFN": final_wfn,
            "N_alpha": values["N_alpha_printed"],
            "N_beta": values["N_beta_printed"],
            "MO_count_alpha": values["molecular_orbitals_alpha_printed"],
            "MO_count_beta": values["molecular_orbitals_beta_printed"],
            "occupied_count_alpha": values["occupied_orbitals_alpha_printed"],
            "occupied_count_beta": values["occupied_orbitals_beta_printed"],
            "highest_occupied_O_rich_spin": "UNKNOWN",
            "Oads_weight": "",
            "Coact_weight": "",
            "Obridge_weight": "",
            "neighbor_weight": "",
            "reason": "OT WFN has only occupied orbital count in output; no eigenvalues, virtual orbitals, PDOS or orbital projections. A CP2K diagonalization/print rerun is required.",
            "source_output": rel(SOURCE / f"cp2k_{stem}_baseline.out"),
        })
    write_tsv(OUT / "stage2_03_cp2k_frontier_MO.tsv", frontier_rows)
    (OUT / "stage2_03_cp2k_frontier_MO.md").write_text(
        """# CP2K frontier redox orbital

## Stop condition reached

The four final CP2K WFN files exist, but the baseline calculations used orbital transformation (OT). Each output reports the number of molecular orbitals as exactly equal to the occupied-orbital count, and no MO eigenvalues, virtual states, PDOS, LDOS, cube orbitals or atom/orbital projections were printed.

The binary WFN therefore does not provide a zero-calculation route to a **canonical** HOMO/LUMO spectrum or Oads/Coact projected frontier eigenstate. OT orbitals are optimized occupied subspace vectors, not a printed canonical eigenvalue ladder. Obtaining HOMO-2 eV to LUMO+0.5 eV with atom/orbital weights requires a fixed-geometry CP2K restart using diagonalization and added virtual MOs.

Per the prompt, no such job was launched.

## Answer available now

- Directly oxidized CP2K frontier spin: **UNKNOWN**.
- O-rich character of the total oxidation response: **STRONGLY SUPPORTED** by cDFT localization penalties and Oads population loss, but not assigned to one existing CP2K MO.
- Do not infer the removed electron spin from final-state Delta N_alpha/Delta N_beta; those values include ionization, self-consistent rehybridization and a change to a lower fixed multiplicity.
""",
        encoding="utf-8",
    )

    changes = {}
    with (STAGE1 / "03_cp2k_spin_resolved_changes.tsv").open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            if row["method_partition"] == "Hirshfeld" and row["atom_role"] == "Coact":
                changes[row["system"]] = row
    frame_rows = []
    for system, state, stem, co_idx, oads_idx in cases:
        if state != "*OH":
            continue
        frame_oh = local_frame(SOURCE / f"cp2k_{stem}_baseline.inp", co_idx, oads_idx)
        o_stem = "undoped_O" if system == "pristine" else "Al16_O"
        o_oads = 211 if system == "pristine" else 221
        frame_o = local_frame(SOURCE / f"cp2k_{o_stem}_baseline.inp", co_idx, o_oads)
        row = changes[system]
        frame_rows.append({
            "system": system,
            "local_frame_definition": "z=Coact->Oads; x=nearest noncollinear Coact-O ligand projected perpendicular to z; y=z cross x",
            "OH_local_x": vec(frame_oh["x"]),
            "OH_local_y": vec(frame_oh["y"]),
            "OH_local_z": vec(frame_oh["z"]),
            "O_local_x": vec(frame_o["x"]),
            "O_local_y": vec(frame_o["y"]),
            "O_local_z": vec(frame_o["z"]),
            "OH_Co_O_coordination_index_distance_A": ";".join(f"O{i}:{d:.5f}" for i, d in frame_oh["neighbors"]),
            "O_Co_O_coordination_index_distance_A": ";".join(f"O{i}:{d:.5f}" for i, d in frame_o["neighbors"]),
            "delta_Co_N_alpha_Hirshfeld_e": row["delta_N_up"],
            "delta_Co_N_beta_Hirshfeld_e": row["delta_N_down"],
            "delta_Co_spin_Hirshfeld_muB": row["delta_spin_muB"],
            "alpha_eg_like_weight_change": "",
            "beta_eg_like_weight_change": "",
            "alpha_t2g_like_weight_change": "",
            "beta_t2g_like_weight_change": "",
            "orbital_class_result": "NOT_ESTABLISHED",
            "partial_spin_state_relaxation_result": "PLAUSIBLE",
            "reason": "Population trend matches alpha-to-beta accommodation, but exact local orbital projections are absent and total multiplicity was explicitly reduced by 7.",
            "source_files": f"{rel(SOURCE / f'cp2k_{stem}_baseline.inp')};{rel(SOURCE / f'cp2k_{o_stem}_baseline.inp')};{rel(STAGE1 / '03_cp2k_spin_resolved_changes.tsv')}",
        })
    write_tsv(OUT / "stage2_04_Co_spin_state_relaxation.tsv", frame_rows)
    (OUT / "stage2_04_Co_spin_state_relaxation.md").write_text(
        """# Partial Co spin-state relaxation test

## Assessment: PLAUSIBLE, not established

The local Hirshfeld response is qualitatively consistent with partial spin relaxation in a covalent Co-O unit:

- pristine Coact: Delta N_alpha = -0.301 e, Delta N_beta = +0.520 e, Delta m = -0.821 muB;
- Al16 Coact: Delta N_alpha = -0.218 e, Delta N_beta = +0.230 e, Delta m = -0.448 muB.

The stronger pristine alpha-to-beta reorganization is chemically compatible with depopulation of higher-energy majority antibonding character and increased minority occupation. It is also consistent with the earlier cDFT result that the Co-only M+2 penalty is 2.899188 eV in pristine and 4.036604 eV in Al16.

However, the four calculations do not hold global multiplicity fixed. In both materials, *OH -> *O removes one electron while the input multiplicity decreases by 7, giving the imposed global change Delta N_alpha=-4 and Delta N_beta=+3. The local Co response is therefore conditional on comparing two different fixed-spin branches. It cannot by itself prove a spontaneous high-spin-like to lower-spin-like transition.

A bond-aligned local frame is defined numerically in the TSV, but no existing CP2K projection resolves eg/t2g or sigma/pi occupation. Therefore:

- partial covalent spin-state relaxation: **PLAUSIBLE**;
- exact majority eg/sigma-antibonding loss: **NOT ESTABLISHED**;
- exact minority t2g/pi gain: **NOT ESTABLISHED**;
- integer HS -> LS transition: **not claimed**.
""",
        encoding="utf-8",
    )

    (OUT / "stage2_05_spin_density_interpretation.md").write_text(
        """# O spin reversal as ligand-hole polarization

No CP2K charge-density or spin-density cube was found under the four baseline directories or the complete cDFT roots. A real-space spin-density image cannot be produced from existing outputs alone.

The CP2K atom-partition result nevertheless supports a qualified local interpretation:

| system/state | Coact Hirshfeld spin (muB) | Oads Hirshfeld spin (muB) | local relation |
|---|---:|---:|---|
| pristine *OH | +3.215 | +0.607 | aligned |
| pristine *O | +2.394 | +0.537 | aligned |
| Al16 *OH | +3.224 | +0.336 | aligned |
| Al16 *O | +2.776 | -0.408 | antiparallel |

Thus CP2K Mulliken and Hirshfeld populations support **local antiparallel ligand-hole spin polarization** on Oads in Al16-*O. This phrase describes the sign of atom-partitioned local spin relative to Coact. It is not proof of an exchange constant, antiferromagnetic coupling, or a spatially isolated O-centered spin density.

Confidence: medium inside CP2K, because both population schemes reverse sign; not cross-method robust, because VASP/LOBSTER does not show the same sign reversal. Cube confirmation remains unavailable without a print rerun.
""",
        encoding="utf-8",
    )

    (OUT / "stage2_06_vasp_lobster_crosscheck.md").write_text(
        """# Optional VASP/LOBSTER cross-check (not launched)

Existing WAVECAR and vasprun.xml files remain accessible through symlinks in the validated LOBSTER directories. Existing pair-total spin-resolved COHP already gives:

- pristine *OH spin-2 Oads peak proxy: approximately nonbonding, local mean -COHP = -0.001402 in +/-0.12 eV;
- Al16 *OH spin-2 Oads peak proxy: weakly antibonding, local mean -COHP = -0.030390;
- *OH -> *O bond strengthening Delta(-ICOHP) spin1/spin2: +0.56027/+0.90463 eV pristine and +0.20887/+0.90347 eV Al16.

Validated *OH WAVECAR links:

- pristine: `/home/ftfan/ncw/sfs/CoOH/cp2k/Al16/oer/spin_config_scan_site03_5OH_current_20260714/vasp_jacs6c06054_reconstructed_exact_Al16_3x2_20260809/electronic_structure_al_contribution_20260818/cohp_bader_formal_oh_o_20260822/undoped_control/OH_pair_corrected_nomadelung/WAVECAR` -> `../../../cohp_oh_o_corrected_20260820/undoped_control/OH/WAVECAR`;
- Al16: `/home/ftfan/ncw/sfs/CoOH/cp2k/Al16/oer/spin_config_scan_site03_5OH_current_20260714/vasp_jacs6c06054_reconstructed_exact_Al16_3x2_20260809/electronic_structure_al_contribution_20260818/cohp_bader_formal_oh_o_20260822/Al16_adjacent/OH_nomadelung/WAVECAR` -> `../../../cohp_oh_o_corrected_20260820/Al16_adjacent/OH/WAVECAR`.

An orbital-resolved LOBSTER rerun can be performed without VASP by reusing the existing WAVECAR/vasprun.xml and adding orbitalwise Coact-Oads interactions for Co21-O348 (pristine) and Co16-O348 (Al16). The input should retain:

```text
skipMadelungEnergy
COHPstartEnergy -2.0
COHPendEnergy 0.5
basisSet pbeVaspFit2015
useRecommendedBasisFunctions
gaussianSmearingWidth 0.05
# Add the LOBSTER-5.1.1 orbitalwise form of:
# cohpbetween atom 21 atom 348       (pristine)
# cohpbetween atom 16 atom 348       (Al16)
```

The exact orbitalwise keyword syntax must be validated against the installed LOBSTER 5.1.1 documentation before submission. Global VASP p/d labels still require a bond-axis rotation before sigma/pi assignment.

Observed prior LOBSTER wall time was about 7.5-12 h per case on one n28 node with 8 CPUs because Gaussian k-space integration was used. This is supporting Tier 1.5 work only and was not launched.
""",
        encoding="utf-8",
    )

    (OUT / "stage2_07_minimal_cp2k_print_rerun.md").write_text(
        """# Minimal CP2K print rerun request (not launched)

## Unresolved question

The directly oxidized CP2K frontier spin and its Oads/Coact/Obridge/neighbor orbital weights are unknown. Existing OT WFN files contain a converged occupied subspace but no printed canonical eigenvalues, virtual states, PDOS or spin-density cube.

## Smallest defensible calculation

Priority 1: two fixed-geometry *OH single points, pristine and Al16, restarted from the final `cdf_base_...-RESTART.wfn` files. Priority 2: add the two *O states only if matched spin-density cubes are required.

Required changes relative to the validated baseline input:

```text
&GLOBAL
  RUN_TYPE ENERGY
&END GLOBAL
&DFT
  WFN_RESTART_FILE_NAME <final cdf_base ... RESTART.wfn>
  UKS T
  MULTIPLICITY <retain the validated state value>
  CHARGE 0
  &SCF
    SCF_GUESS RESTART
    EPS_SCF 1.0E-7
    MAX_SCF 20
    ADDED_MOS 80
    &DIAGONALIZATION ON
      ALGORITHM STANDARD
    &END DIAGONALIZATION
  &END SCF
  &PRINT
    &MO
      EIGENVALUES T
      OCCUPATION_NUMBERS T
    &END MO
    &PDOS
      NLUMO 50
      COMPONENTS T
    &END PDOS
    &E_DENSITY_CUBE
    &END E_DENSITY_CUBE
    &SPIN_DENSITY_CUBE
    &END SPIN_DENSITY_CUBE
  &END PRINT
&END DFT
```

The CP2K build/version input syntax must be checked before submission. Switching from OT to diagonalization and adding virtual MOs is a new static SCF, not zero-cost post-processing.

## Resources and expected cost

- one node only;
- 28 MPI ranks, 1 thread each, matching the validated baselines;
- no geometry optimization, no cDFT scan;
- estimated 1-4 h per state because diagonalization of 3978 orbital functions is substantially more expensive than the prior occupied-only OT baselines (143-1130 s);
- two priority *OH jobs: approximately 2-8 node-hours total, or 1-4 h wall time if run concurrently;
- expected outputs: alpha/beta eigenvalues, PDOS component files, and charge/spin-density cubes.

No job has been submitted. Explicit approval is required.
""",
        encoding="utf-8",
    )

    summary = """# CP2K-primary mechanism validation, stage 2

## Decisive global-spin finding

All four calculations are UKS and internally satisfy multiplicity = N_alpha - N_beta + 1. In both materials, *OH -> *O removes one electron but also changes the imposed multiplicity by -7:

- pristine: M=175 -> 168, N_alpha/N_beta=867/693 -> 863/696;
- Al16: M=149 -> 142, N_alpha/N_beta=798/650 -> 794/653.

Therefore the global change is Delta N_alpha=-4, Delta N_beta=+3 and Delta magnetization=-7 in both systems. Local alpha-to-beta redistribution is meaningful as a response on the selected lower-spin *O branch, but is not an independent proof that oxidation spontaneously chooses that spin branch.

## Required answers

### A. Is the directly oxidized frontier state alpha or beta in CP2K?

**UNKNOWN from existing CP2K data.** Final-state Delta populations cannot identify the directly removed electron. Existing OT WFN files have no printed canonical frontier eigenvalues, virtual states or atom/orbital projections. VASP/LOBSTER favors spin-down loss, but that does not replace the CP2K answer.

### B. Is it O-rich?

**STRONGLY SUPPORTED for the oxidation response, not yet proven for one CP2K MO.** Oads loses -0.464 e (pristine) and -0.427 e (Al16) by Hirshfeld analysis, and Co+adsorbate N-1 constraints are 1.50-2.21 eV cheaper than Co-only N-1 constraints across the existing *OH/*O/*OOH cases.

### C. Is it bonding, nonbonding or antibonding?

**UNKNOWN in CP2K.** Supporting VASP/LOBSTER classifies the selected spin-2 Oads peak proxy as approximately nonbonding in pristine *OH and weakly antibonding in Al16 *OH. This is not a CP2K orbital assignment.

### D. Does Co undergo a partial high-spin-like -> lower-spin-like orbital relaxation?

**PLAUSIBLE, not established.** Coact alpha decreases, beta increases and local spin falls, more strongly in pristine. However, the *O states were explicitly computed at multiplicity seven lower than *OH, and no local orbital-class projection exists.

### E. Which Co orbital class loses and which gains occupation?

**Not established.** Safe statement: Co alpha population decreases and beta population increases. It is not yet safe to label the loss as eg/sigma-antibonding or the gain as t2g/pi/nonbonding.

### F. Why is this relaxation stronger in pristine than Al?

Pristine Coact changes by Delta N_alpha=-0.301 e, Delta N_beta=+0.520 e and Delta m=-0.821 muB, versus -0.218, +0.230 and -0.448 in Al16. Al also raises the Co-only M+2 penalty from 2.899188 to 4.036604 eV and lacks the neighboring magnetic Co-3d frontier manifold. This supports suppressed Co-centered accommodation with Al, although the exact orbital pathway remains unresolved.

### G. Does CP2K support an antiparallel ligand-hole spin on O in Al-*O?

**Yes, at the atom-partition level.** Al16 Oads changes from +0.336 to -0.408 muB while Coact remains +2.776 muB in *O. The safe phrase is **local antiparallel ligand-hole spin polarization**. No spin-density cube exists, so spatial localization is not directly imaged; VASP/LOBSTER also does not reproduce the sign reversal.

### H. Which exact orbitals and electron arrows are now safe to draw?

Safe:

1. an O-rich/ligand-centered PCET oxidation arrow with the removed spin left unspecified;
2. a dashed, qualified Co alpha-to-beta population-relaxation arrow, stronger in pristine and weaker with Al;
3. an Al-*O O-local-spin arrow antiparallel to positive Co, marked "CP2K population result; method dependent";
4. generic exchange-split covalent Co-O manifolds.

Not safe:

- a definite alpha or beta CP2K oxidation arrow;
- exact eg, t2g, sigma* or pi* labels;
- an integer high-spin -> low-spin transition;
- antiferromagnetic coupling or exchange J;
- a method-independent O spin reversal.

## Action status

The prompt's zero-cost extraction limit was reached. No CP2K, VASP or LOBSTER job was launched. `stage2_07_minimal_cp2k_print_rerun.md` specifies the smallest next calculation requiring explicit approval.
"""
    (OUT / "mechanism_stage2_for_chatgpt.md").write_text(summary, encoding="utf-8")

    readme = """# Mechanism validation stage 2

Focused CP2K-primary validation of an O-rich PCET plus partial Co spin-relaxation interpretation. No electronic-structure job was launched.

Start with `mechanism_stage2_for_chatgpt.md`.

Key result: the partial Co spin-relaxation picture is plausible but not established because *OH and *O were computed on explicitly different total-multiplicity branches and existing OT WFN files lack canonical frontier eigenvalues/orbital projections. The CP2K Oads sign reversal supports local antiparallel ligand-hole spin polarization only at the population-partition level.
"""
    (OUT / "README.md").write_text(readme, encoding="utf-8")

    zip_path = ROOT / "mechanism_validation_stage2.zip"
    if zip_path.exists():
        zip_path.unlink()
    shutil.make_archive(str(zip_path.with_suffix("")), "zip", root_dir=OUT.parent, base_dir=OUT.name)
    print(f"Wrote {OUT}")
    print(f"Wrote {zip_path}")
    print(f"Files: {len(list(OUT.iterdir()))}")


if __name__ == "__main__":
    main()
