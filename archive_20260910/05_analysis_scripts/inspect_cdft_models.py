from __future__ import annotations

import importlib.util
import math
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SSH_HELPER = ROOT / ".codex/skills/ftfan-ncw-ssh/scripts/ssh_ncw.py"
spec = importlib.util.spec_from_file_location("ssh_ncw", SSH_HELPER)
ssh_ncw = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(ssh_ncw)


FILES = {
    "undoped_OH": "sfs/CoOH/cp2k/thermo_vib_5OH_U100_current_20260704/undoped_001333/site01_surface_Co32/OH/retry2_resubmit/Undoped_currvib_OH.inp",
    "al16_co_OH": "sfs/CoOH/cp2k/thermo_vib_5OH_U100_current_20260704/Al16/site03_bulk_Co7_adjAl/OH/valid_O120_coupled_110606_vib_rerun_20260720/Al16_currvib_s03_OH_O120coupled.inp",
    "al16_al_OH": "sfs/CoOH/cp2k/thermo_vib_5OH_U100_current_20260704/Al16/site02_surface_Al47/OH/retry2_resubmit/Al16_currvib_s02_OH.inp",
    "al16_co_OH_old": "sfs/CoOH/cp2k/thermo_vib_5OH_U100_current_20260704/Al16/site03_bulk_Co7_adjAl/OH/retry2_resubmit/Al16_currvib_s03_OH.inp",
    "al16_al_OH_old": "sfs/CoOH/cp2k/thermo_vib_5OH_U100_current_20260704/Al16/site02_surface_Al47/OH/Al16_currvib_s02_OH.inp",
}


def section(text: str, name: str) -> str:
    match = re.search(rf"&{name}\b(.*?)&END\s+{name}\b", text, re.I | re.S)
    if not match:
        raise ValueError(f"Missing {name} section")
    return match.group(1)


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
        for label, rel_path in FILES.items():
            remote = f"{ssh_ncw.REMOTE_ROOT}/{rel_path}"
            with sftp.open(remote, "r") as handle:
                text = handle.read().decode()
            cell_text = section(text, "CELL")
            lengths = []
            for axis in "ABC":
                match = re.search(
                    rf"^\s*{axis}\s+([-+\d.E]+)\s+([-+\d.E]+)\s+([-+\d.E]+)",
                    cell_text,
                    re.I | re.M,
                )
                if not match:
                    raise ValueError(f"Missing cell vector {axis}")
                vector = tuple(map(float, match.groups()))
                lengths.append(math.sqrt(sum(value * value for value in vector)))
            atoms = []
            for line in section(text, "COORD").splitlines():
                fields = line.split()
                if len(fields) < 4:
                    continue
                try:
                    atoms.append((fields[0], *map(float, fields[1:4])))
                except ValueError:
                    continue
            mode = section(text, "MODE_SELECTIVE")
            selected = list(
                map(int, re.search(r"\bATOMS\s+([\d\s]+)", mode, re.I).group(1).split())
            )
            ads_o = next(index for index in selected if atoms[index - 1][0].upper() == "O")

            def distance(i: int, j: int) -> float:
                delta = [atoms[i - 1][k] - atoms[j - 1][k] for k in range(1, 4)]
                delta = [d - round(d / length) * length for d, length in zip(delta, lengths)]
                return math.sqrt(sum(d * d for d in delta))

            metals = sorted(
                (distance(i, ads_o), i, atoms[i - 1][0])
                for i in range(1, len(atoms) + 1)
                if atoms[i - 1][0] in {"Co", "Al"}
            )
            print(
                label,
                f"natoms={len(atoms)}",
                f"selected={selected}",
                "selected_elements=" + ",".join(atoms[index - 1][0] for index in selected),
                f"adsO={ads_o}",
                "nearest=" + ",".join(f"{i}:{element}:{dist:.4f}" for dist, i, element in metals[:10]),
                sep="\t",
            )
    finally:
        client.close()


if __name__ == "__main__":
    main()
