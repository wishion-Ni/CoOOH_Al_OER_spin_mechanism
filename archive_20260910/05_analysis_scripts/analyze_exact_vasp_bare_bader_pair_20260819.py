from __future__ import annotations

import importlib.util
import math
import posixpath
import re
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
CASES = {
    "Al16": posixpath.join(ANALYSIS, "fixed_geometry_bader_pdos/Al16_adjacent/bare"),
    "control": posixpath.join(ANALYSIS, "fixed_geometry_bader_pdos/undoped_control/bare"),
}
RESULT = posixpath.join(ANALYSIS, "bare_bader_active_site_pair.tsv")
REPORT = posixpath.join(ANALYSIS, "bare_bader_active_site_pair.md")
ACTIVE_COPY = (1, 0)
ACTIVE_LOCAL = 1
NX_LOCAL = 10
ZVAL = {"Co": 9.0, "Al": 3.0}


def remote(rel: str) -> str:
    return posixpath.join(ssh_ncw.REMOTE_ROOT, rel)


def read_text(sftp, rel: str) -> str:
    with sftp.open(remote(rel), "r") as handle:
        return handle.read().decode(errors="replace")


def write_text(sftp, rel: str, value: str) -> None:
    with sftp.open(remote(rel), "w") as handle:
        handle.write(value)


def frac_to_cart(lattice: list[list[float]], frac: list[float]) -> list[float]:
    return [sum(frac[row] * lattice[row][col] for row in range(3)) for col in range(3)]


def parse_poscar(text: str) -> tuple[list[list[float]], list[str], list[list[float]]]:
    lines = text.splitlines()
    scale = float(lines[1].split()[0])
    lattice = [[scale * float(value) for value in lines[index].split()[:3]] for index in range(2, 5)]
    species = lines[5].split()
    counts = [int(value) for value in lines[6].split()]
    cursor = 7
    if lines[cursor].strip().lower().startswith("s"):
        cursor += 1
    direct = lines[cursor].strip().lower().startswith("d")
    cursor += 1
    elements = [symbol for symbol, count in zip(species, counts) for _ in range(count)]
    positions = []
    for index in range(sum(counts)):
        values = [float(value) for value in lines[cursor + index].split()[:3]]
        positions.append(frac_to_cart(lattice, values) if direct else [scale * value for value in values])
    return lattice, elements, positions


def pbc_distance(lattice: list[list[float]], left: list[float], right: list[float]) -> float:
    # These exact 3x2 cells are orthogonal in-plane; enumerate neighboring images for a robust MIC.
    best = float("inf")
    for ia in (-1, 0, 1):
        for ib in (-1, 0, 1):
            for ic in (-1, 0, 1):
                shifted = [
                    right[col]
                    + ia * lattice[0][col]
                    + ib * lattice[1][col]
                    + ic * lattice[2][col]
                    for col in range(3)
                ]
                best = min(best, math.sqrt(sum((a - b) ** 2 for a, b in zip(left, shifted))))
    return best


def parse_acf(text: str) -> dict[int, tuple[float, float]]:
    result = {}
    for line in text.splitlines():
        fields = line.split()
        if len(fields) == 7 and fields[0].isdigit():
            result[int(fields[0])] = (float(fields[4]), float(fields[6]))
    return result


def parse_magnetization(text: str) -> dict[int, float]:
    starts = [match.start() for match in re.finditer(r"(?m)^\s*magnetization \(x\)", text)]
    if not starts:
        raise RuntimeError("OUTCAR magnetization table missing")
    block = text[starts[-1] :]
    result = {}
    in_rows = False
    for line in block.splitlines():
        fields = line.split()
        if fields[:3] == ["#", "of", "ion"]:
            in_rows = True
            continue
        if in_rows and fields and fields[0].isdigit() and len(fields) >= 5:
            result[int(fields[0])] = float(fields[-1])
        elif in_rows and fields and fields[0] == "tot":
            break
    if not result:
        raise RuntimeError("cannot parse final magnetization table")
    return result


def original_index(copy_x: int, copy_y: int, local_one_based: int) -> int:
    return ((copy_x * 2 + copy_y) * NX_LOCAL) + local_one_based


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
        dopant_rows = []
        for line in read_text(sftp, posixpath.join(VASP_ROOT, "dopant_manifest.tsv")).splitlines()[1:]:
            fields = line.split("\t")
            dopant_rows.append(
                {
                    "selection": int(fields[0]),
                    "original": original_index(int(fields[1]), int(fields[2]), int(fields[3])),
                    "distance": float(fields[4]),
                }
            )
        dopant_rows.sort(key=lambda row: row["selection"])
        active_original = original_index(ACTIVE_COPY[0], ACTIVE_COPY[1], ACTIVE_LOCAL)
        nearest_original = dopant_rows[0]["original"]
        if active_original in {row["original"] for row in dopant_rows}:
            raise RuntimeError("construction manifest incorrectly substitutes the active Co")
        active_al_index = active_original - sum(row["original"] < active_original for row in dopant_rows)
        nearest_al_index = 50 + dopant_rows[0]["selection"]
        indices = {
            "Al16": (active_al_index, nearest_al_index),
            "control": (active_original, nearest_original),
        }

        rows = []
        geometries = {}
        for label, case in CASES.items():
            lattice, elements, positions = parse_poscar(read_text(sftp, posixpath.join(case, "POSCAR")))
            active_index, adjacent_index = indices[label]
            expected_adjacent = "Al" if label == "Al16" else "Co"
            if elements[active_index - 1] != "Co" or elements[adjacent_index - 1] != expected_adjacent:
                raise RuntimeError(f"wrong mapped elements for {label}")
            distance = pbc_distance(lattice, positions[active_index - 1], positions[adjacent_index - 1])
            if abs(distance - dopant_rows[0]["distance"]) > 2e-5:
                raise RuntimeError(f"mapped neighbor distance mismatch for {label}: {distance}")
            acf = parse_acf(read_text(sftp, posixpath.join(case, "ACF.dat")))
            moments = parse_magnetization(read_text(sftp, posixpath.join(case, "OUTCAR")))
            geometries[label] = (lattice, positions[active_index - 1], positions[adjacent_index - 1])
            for role, index in (("active_Co", active_index), ("adjacent_substitution_site", adjacent_index)):
                element = elements[index - 1]
                electrons, volume = acf[index]
                rows.append(
                    (
                        label,
                        role,
                        index,
                        element,
                        distance if role == "adjacent_substitution_site" else 0.0,
                        electrons,
                        ZVAL[element] - electrons,
                        volume,
                        moments[index],
                    )
                )

        table = (
            "model\trole\tvasp_index\telement\tdistance_to_active_Co_A\tbader_electrons\t"
            "bader_net_charge_e\tbader_volume_A3\tlocal_moment_muB\n"
        )
        for row in rows:
            table += (
                f"{row[0]}\t{row[1]}\t{row[2]}\t{row[3]}\t{row[4]:.6f}\t{row[5]:.6f}\t"
                f"{row[6]:.6f}\t{row[7]:.6f}\t{row[8]:.6f}\n"
            )
        write_text(sftp, RESULT, table)

        by_key = {(row[0], row[1]): row for row in rows}
        al_active = by_key[("Al16", "active_Co")]
        control_active = by_key[("control", "active_Co")]
        report = f"""# Fixed-geometry bare Bader comparison

- Mapping follows the exact VASP 3x2 construction manifest, not CP2K atom numbering.
- Active site: copy (1,0), local Co1; VASP Co{active_al_index} in Al16 and Co{active_original} in control.
- Nearest substitution site: Al{nearest_al_index} in Al16 and corresponding Co{nearest_original} in control, {dopant_rows[0]['distance']:.6f} A from the active Co.
- Active-Co Bader electron change, Al16-control: {al_active[5] - control_active[5]:+.6f} e.
- Active-Co net-charge change, Al16-control: {al_active[6] - control_active[6]:+.6f} e.
- Active-Co local-moment change, Al16-control: {al_active[8] - control_active[8]:+.6f} muB.

These fixed-geometry values isolate the electronic substitution effect. They do not replace final relaxed-state Bader analysis and do not define a formal oxidation state.
"""
        write_text(sftp, REPORT, report)
        print(table, end="")
        print(report)
    finally:
        client.close()


if __name__ == "__main__":
    main()
