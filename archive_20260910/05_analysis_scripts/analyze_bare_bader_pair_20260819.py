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

CP2K_INPUT = (
    "sfs/CoOH/cp2k/Al16/oer/spin_config_scan_site03_5OH_current_20260714/"
    "cdft_charge_spin_20260812/al16_valid_co48_OH/baseline.inp"
)
VASP_ROOT = (
    "sfs/CoOH/cp2k/Al16/oer/spin_config_scan_site03_5OH_current_20260714/"
    "vasp_jacs6c06054_reconstructed_exact_Al16_3x2_20260809"
)
ANALYSIS = posixpath.join(VASP_ROOT, "electronic_structure_al_contribution_20260818")
FIXED = posixpath.join(ANALYSIS, "fixed_geometry_bader_pdos")
CASES = {
    "Al16": posixpath.join(FIXED, "Al16_adjacent/bare"),
    "control": posixpath.join(FIXED, "undoped_control/bare"),
}
RESULT = posixpath.join(ANALYSIS, "bare_bader_active_site_pair.tsv")
ACTIVE_CP2K = 48
ADJACENT_CP2K = 32
ZVAL = {"Co": 9.0, "Al": 3.0, "O": 6.0, "H": 1.0}


def remote(rel: str) -> str:
    return posixpath.join(ssh_ncw.REMOTE_ROOT, rel)


def read_text(sftp, rel: str) -> str:
    with sftp.open(remote(rel), "r") as handle:
        return handle.read().decode(errors="replace")


def write_text(sftp, rel: str, value: str) -> None:
    with sftp.open(remote(rel), "w") as handle:
        handle.write(value)


def invert(matrix: list[list[float]]) -> list[list[float]]:
    a, b, c = matrix[0]
    d, e, f = matrix[1]
    g, h, i = matrix[2]
    det = a * (e * i - f * h) - b * (d * i - f * g) + c * (d * h - e * g)
    if abs(det) < 1e-12:
        raise RuntimeError("singular lattice")
    return [
        [(e * i - f * h) / det, (c * h - b * i) / det, (b * f - c * e) / det],
        [(f * g - d * i) / det, (a * i - c * g) / det, (c * d - a * f) / det],
        [(d * h - e * g) / det, (b * g - a * h) / det, (a * e - b * d) / det],
    ]


def matvec(matrix: list[list[float]], vector: list[float]) -> list[float]:
    return [sum(matrix[row][col] * vector[col] for col in range(3)) for row in range(3)]


def frac_to_cart(lattice: list[list[float]], frac: list[float]) -> list[float]:
    return [sum(frac[row] * lattice[row][col] for row in range(3)) for col in range(3)]


def cart_to_frac(lattice: list[list[float]], cart: list[float]) -> list[float]:
    # Lattice vectors are rows, so solve lattice^T * frac = cart.
    transposed = [[lattice[col][row] for col in range(3)] for row in range(3)]
    return matvec(invert(transposed), cart)


def pbc_distance(lattice: list[list[float]], left: list[float], right: list[float]) -> float:
    delta = [a - b for a, b in zip(cart_to_frac(lattice, left), cart_to_frac(lattice, right))]
    delta = [value - round(value) for value in delta]
    cart = frac_to_cart(lattice, delta)
    return math.sqrt(sum(value * value for value in cart))


def parse_cp2k(text: str) -> tuple[list[list[float]], list[tuple[str, list[float]]]]:
    cell_match = re.search(r"(?ims)&CELL\s+(.*?)&END\s+CELL", text)
    coord_match = re.search(r"(?ims)&COORD\s+(.*?)&END\s+COORD", text)
    if not cell_match or not coord_match:
        raise RuntimeError("CP2K CELL/COORD section missing")
    cell = []
    for key in ("A", "B", "C"):
        match = re.search(rf"(?im)^\s*{key}\s+([-+0-9.Ee]+)\s+([-+0-9.Ee]+)\s+([-+0-9.Ee]+)", cell_match.group(1))
        if not match:
            raise RuntimeError(f"CP2K cell vector {key} missing")
        cell.append([float(value) for value in match.groups()])
    atoms = []
    for line in coord_match.group(1).splitlines():
        fields = line.split()
        if len(fields) >= 4 and fields[0][0].isalpha():
            atoms.append((re.match(r"[A-Za-z]+", fields[0]).group(0), [float(value) for value in fields[1:4]]))
    return cell, atoms


def parse_poscar(text: str) -> tuple[list[list[float]], list[str], list[list[float]]]:
    lines = text.splitlines()
    scale = float(lines[1].split()[0])
    lattice = [[scale * float(value) for value in lines[index].split()[:3]] for index in range(2, 5)]
    cursor = 5
    species = lines[cursor].split()
    cursor += 1
    counts = [int(value) for value in lines[cursor].split()]
    cursor += 1
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


def nearest_index(
    lattice: list[list[float]],
    elements: list[str],
    positions: list[list[float]],
    target: list[float],
    allowed: set[str],
) -> tuple[int, float]:
    candidates = [
        (pbc_distance(lattice, position, target), index)
        for index, (element, position) in enumerate(zip(elements, positions), start=1)
        if element in allowed
    ]
    distance, index = min(candidates)
    return index, distance


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
        cp2k_cell, cp2k_atoms = parse_cp2k(read_text(sftp, CP2K_INPUT))
        active_symbol, active_position = cp2k_atoms[ACTIVE_CP2K - 1]
        adjacent_symbol, adjacent_position = cp2k_atoms[ADJACENT_CP2K - 1]
        if active_symbol != "Co" or adjacent_symbol != "Al":
            raise RuntimeError(f"unexpected CP2K identities: {active_symbol}, {adjacent_symbol}")

        rows = []
        mapping = {}
        for label, case in CASES.items():
            lattice, elements, positions = parse_poscar(read_text(sftp, posixpath.join(case, "POSCAR")))
            if max(pbc_distance(lattice, [0.0, 0.0, 0.0], vector) for vector in cp2k_cell) < 1.0:
                raise RuntimeError("invalid lattice comparison")
            active_index, active_distance = nearest_index(lattice, elements, positions, active_position, {"Co"})
            adjacent_allowed = {"Al"} if label == "Al16" else {"Co"}
            adjacent_index, adjacent_distance = nearest_index(
                lattice, elements, positions, adjacent_position, adjacent_allowed
            )
            if active_distance > 2e-3 or adjacent_distance > 2e-3:
                raise RuntimeError(
                    f"unsafe CP2K-to-VASP mapping for {label}: active {active_distance}, adjacent {adjacent_distance}"
                )
            acf = parse_acf(read_text(sftp, posixpath.join(case, "ACF.dat")))
            moments = parse_magnetization(read_text(sftp, posixpath.join(case, "OUTCAR")))
            mapping[label] = (active_index, adjacent_index)
            for role, index, distance in (
                ("active_Co48", active_index, active_distance),
                ("adjacent_Al32_site", adjacent_index, adjacent_distance),
            ):
                element = elements[index - 1]
                electrons, volume = acf[index]
                rows.append(
                    (
                        label,
                        role,
                        index,
                        element,
                        distance,
                        electrons,
                        ZVAL[element] - electrons,
                        volume,
                        moments[index],
                    )
                )

        text = (
            "model\trole\tvasp_index\telement\tmapping_distance_A\tbader_electrons\t"
            "bader_net_charge_e\tbader_volume_A3\tlocal_moment_muB\n"
        )
        for row in rows:
            text += (
                f"{row[0]}\t{row[1]}\t{row[2]}\t{row[3]}\t{row[4]:.8f}\t{row[5]:.6f}\t"
                f"{row[6]:.6f}\t{row[7]:.6f}\t{row[8]:.6f}\n"
            )
        write_text(sftp, RESULT, text)
        print(text, end="")
        print(f"mapping Al16={mapping['Al16']} control={mapping['control']}")
    finally:
        client.close()


if __name__ == "__main__":
    main()
