from pathlib import Path
import math
import re
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'archive_20260910' / '02_DFT_CP2K' / 'validated_sources'
OUT = ROOT / 'structures' / 'key_structures'
OUT.mkdir(parents=True, exist_ok=True)

SOURCES = {
    'pristine_OH': SRC / 'cp2k_undoped_OH_baseline.inp',
    'pristine_O': SRC / 'cp2k_undoped_O_baseline.inp',
    'Al16_OH': SRC / 'cp2k_Al16_OH_baseline.inp',
    'Al16_O': SRC / 'cp2k_Al16_O_baseline.inp',
}


def parse_cp2k_structure(path: Path):
    text = path.read_text(encoding='utf-8', errors='replace').splitlines()
    cell = {}
    atoms = []
    in_cell = False
    in_coord = False
    for line in text:
        s = line.strip()
        up = s.upper()
        if up == '&CELL':
            in_cell = True
            continue
        if up == '&END CELL':
            in_cell = False
            continue
        if up == '&COORD':
            in_coord = True
            continue
        if up == '&END COORD':
            in_coord = False
            continue
        if in_cell:
            m = re.match(r'^([ABC])\s+([-+0-9Ee\.]+)\s+([-+0-9Ee\.]+)\s+([-+0-9Ee\.]+)', s)
            if m:
                cell[m.group(1)] = [float(m.group(i)) for i in range(2, 5)]
        elif in_coord and s and not s.startswith('#'):
            parts = s.split()
            if len(parts) >= 4 and re.match(r'^[A-Za-z][A-Za-z0-9_]*$', parts[0]):
                try:
                    xyz = [float(parts[1]), float(parts[2]), float(parts[3])]
                except ValueError:
                    continue
                # CP2K KIND labels may carry suffixes; retain chemical element prefix only.
                m = re.match(r'^([A-Z][a-z]?)', parts[0])
                if not m:
                    raise ValueError(f'Cannot infer element from coordinate label: {parts[0]}')
                atoms.append((m.group(1), xyz))
    if set(cell) != {'A', 'B', 'C'}:
        raise ValueError(f'Incomplete cell in {path}: {cell.keys()}')
    if not atoms:
        raise ValueError(f'No atoms parsed from {path}')
    return np.array([cell['A'], cell['B'], cell['C']], dtype=float), atoms


def cell_parameters(cell):
    a, b, c = (np.linalg.norm(v) for v in cell)
    def angle(u, v):
        cosang = np.dot(u, v) / (np.linalg.norm(u) * np.linalg.norm(v))
        cosang = max(-1.0, min(1.0, float(cosang)))
        return math.degrees(math.acos(cosang))
    alpha = angle(cell[1], cell[2])
    beta = angle(cell[0], cell[2])
    gamma = angle(cell[0], cell[1])
    return a, b, c, alpha, beta, gamma


def write_cif(name, source, cell, atoms, path):
    inv_cell = np.linalg.inv(cell)
    a, b, c, alpha, beta, gamma = cell_parameters(cell)
    counters = {}
    lines = [
        f'data_{name}',
        "_audit_creation_method 'Converted from validated CP2K baseline input in CoOOH_Al_OER_spin_mechanism'",
        f"_audit_creation_note 'Source: {source.as_posix()}'",
        "_symmetry_space_group_name_H-M 'P 1'",
        '_symmetry_Int_Tables_number 1',
        f'_cell_length_a {a:.10f}',
        f'_cell_length_b {b:.10f}',
        f'_cell_length_c {c:.10f}',
        f'_cell_angle_alpha {alpha:.8f}',
        f'_cell_angle_beta {beta:.8f}',
        f'_cell_angle_gamma {gamma:.8f}',
        '',
        'loop_',
        '_atom_site_label',
        '_atom_site_type_symbol',
        '_atom_site_fract_x',
        '_atom_site_fract_y',
        '_atom_site_fract_z',
        '_atom_site_occupancy',
    ]
    for element, xyz in atoms:
        counters[element] = counters.get(element, 0) + 1
        label = f'{element}{counters[element]}'
        frac = np.asarray(xyz, dtype=float) @ inv_cell
        frac = frac - np.floor(frac)
        lines.append(f'{label:8s} {element:3s} {frac[0]: .10f} {frac[1]: .10f} {frac[2]: .10f} 1.0')
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


summary = []
for name, source in SOURCES.items():
    cell, atoms = parse_cp2k_structure(source)
    out = OUT / f'{name}.cif'
    write_cif(name, source.relative_to(ROOT), cell, atoms, out)
    composition = {}
    for element, _ in atoms:
        composition[element] = composition.get(element, 0) + 1
    summary.append((name, len(atoms), composition, source.relative_to(ROOT), out.relative_to(ROOT)))

readme = [
    '# Key CoOOH structures (CIF)',
    '',
    'These CIF files are converted directly from the validated CP2K baseline input structures archived in this repository.',
    'They are intended for structure visualization, collaborator handoff, and reproducible manuscript graphics.',
    '',
    '| Structure | atoms | composition | CP2K source | CIF |',
    '|---|---:|---|---|---|',
]
for name, nat, comp, src, out in summary:
    compstr = ', '.join(f'{el}{n}' for el, n in sorted(comp.items()))
    readme.append(f'| `{name}` | {nat} | {compstr} | `{src}` | `{out}` |')
readme += [
    '',
    '## Important scope note',
    '',
    '- `pristine_OH` / `pristine_O` and `Al16_OH` / `Al16_O` are the four validated baseline structures used in the current electronic/spin-response analysis.',
    '- The CIF conversion does not alter coordinates except wrapping fractional coordinates into [0,1).',
    '- Space group is intentionally written as `P 1`; no symmetry is imposed during export.',
    '- These files should not be confused with the historical three-site T01 thermodynamic branches, whose raw structures are not all copied into the current repository.',
]
(OUT / 'README.md').write_text('\n'.join(readme) + '\n', encoding='utf-8')

print('Exported key CIF structures:')
for item in summary:
    print(item)
