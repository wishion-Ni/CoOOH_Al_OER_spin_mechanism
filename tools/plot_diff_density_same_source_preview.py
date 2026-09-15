"""Preview local sphere integrals of the same VASP fields used in the maps."""
import csv
import argparse
import hashlib
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.axes_grid1.inset_locator import inset_axes

import plot_diff_density_evidence_preview as preview
from plot_diff_density_subfigures import read_overlay, save_figure
from sync_diff_density_publication import CASES, SOURCE, read_density, read_poscar

OUT = Path('artifacts/diff_density_same_source_preview_20260915')


def integrate():
    records = []
    hashes = []
    for case_name, case in CASES.items():
        fields = []
        lattice, coords, species = read_poscar(SOURCE / f'{case_name}_O_at_OHgeom_POSCAR')
        for kind, magic in [('charge', b'CHGDIFF1'), ('spin', b'MAGDIFF1')]:
            path = SOURCE / f'{case_name}_O_minus_OH_{kind}_ds2.raw'
            field, cell, volume, ds = read_density(path, magic)
            assert np.allclose(cell, lattice)
            fields.append(field)
            hashes.append(f'{path}\t{hashlib.sha256(path.read_bytes()).hexdigest()}')
        assert fields[0].shape == fields[1].shape
        nz, ny, nx = fields[0].shape
        dv = volume / fields[0].size
        indices = {'Co(act)': case['active_co'], 'Oads': case['active_o'],
                   'Obridge': case['bridge_o'], case['neighbor_label']: case['neighbor']}
        for label, index in indices.items():
            center = coords[index - 1]
            for radius in (0.6, 0.7, 0.8):
                # Inverse-cell column norms bound a Cartesian sphere in fractional coordinates.
                bounds = radius * np.linalg.norm(np.linalg.inv(cell), axis=0)
                ranges = [np.arange(int(np.floor((c-b)*n))-1, int(np.ceil((c+b)*n))+2)
                          for c, b, n in zip(center, bounds, (nx, ny, nz))]
                iz, iy, ix = np.meshgrid(ranges[2], ranges[1], ranges[0], indexing='ij')
                displacement = np.stack([ix/nx-center[0], iy/ny-center[1], iz/nz-center[2]], axis=-1) @ cell
                mask = np.sum(displacement**2, axis=-1) <= radius**2
                n, m = [float(f[iz % nz, iy % ny, ix % nx][mask].sum(dtype=np.float64)*dv) for f in fields]
                up, down = (n+m)/2, (n-m)/2
                assert abs(up+down-n) < 1e-12 and abs(up-down-m) < 1e-12
                records.append(dict(system=case['system'], atom=label, index=index,
                                    radius_A=radius, delta_N=n, delta_m=m,
                                    delta_up=up, delta_down=down, sampled_volume_A3=int(mask.sum())*dv))
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT/'sphere_integrals.tsv').open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(records[0]), delimiter='\t')
        writer.writeheader()
        writer.writerows(records)
    (OUT/'source_hashes.tsv').write_text('\n'.join(hashes), encoding='utf-8')
    return records


def main():
    global OUT
    parser = argparse.ArgumentParser()
    parser.add_argument('--output-dir', type=Path, default=OUT)
    parser.add_argument('--integrals', type=Path)
    args = parser.parse_args()
    OUT = args.output_dir
    OUT.mkdir(parents=True, exist_ok=True)
    if args.integrals:
        with args.integrals.open(encoding='utf-8') as handle:
            records = list(csv.DictReader(handle, delimiter='\t'))
        for record in records:
            for key in ('radius_A', 'delta_N', 'delta_m', 'delta_up', 'delta_down'):
                record[key] = float(record[key])
    else:
        records = integrate()
    columns = dict(charge_density='delta_N', magnetization='delta_m', spin_up='delta_up', spin_down='delta_down')
    specs = [
        ('charge_density', '', r'$\Delta\rho$', r'e $\AA^{-3}$', .05, 'RdBu_r'),
        ('magnetization', '', r'$\Delta m$', r'$\mu_B$ $\AA^{-3}$', .08, 'PuOr'),
        ('spin_up', '', r'$\Delta\rho_\uparrow$', r'e $\AA^{-3}$', .05, 'RdBu_r'),
        ('spin_down', '', r'$\Delta\rho_\downarrow$', r'e $\AA^{-3}$', .05, 'RdBu_r'),
    ]
    for name, column in columns.items():
        preview.ANNOTATIONS[name]['values'] = {'pristine': {}, 'Al16': {}}
        for row in records:
            if row['radius_A'] != .8:
                continue
            unit = 'μB' if name == 'magnetization' else 'e'
            number = f"{row[column]:+.3f}" if abs(row[column]) >= .0005 else '0.000'
            preview.ANNOTATIONS[name]['values'][row['system']][row['atom']] = (number + ' ' + unit).replace('-', '−')
    fig, axes = plt.subplots(4, 2, figsize=(9.2, 10.6))
    for row, spec in zip(axes, specs):
        im = preview.render_pair(fig, row, read_overlay(), spec[0], spec)
        row[0].set_title(spec[2], loc='left', fontsize=10)
        cbar = fig.colorbar(im, ax=list(row), fraction=.022, pad=.025, shrink=.85)
        cbar.set_ticks([-spec[4], 0, spec[4]])
        cbar.set_label(spec[3], fontsize=8)
        cbar.ax.tick_params(labelsize=8)
    fig.savefig(OUT/'four_map_same_source.png', dpi=300, bbox_inches='tight')
    plt.close(fig)
    for spec in specs:
        for system, case_name in [('pristine', 'undoped_control'), ('Al16', 'Al16_adjacent')]:
            fig, ax = plt.subplots(figsize=(3.65, 2.8))
            x, y, field = preview.read_field(spec[0], case_name)
            im = preview.style_axis(ax, x, y, field, '', spec[3], spec[4], spec[5], read_overlay()[system], '')
            preview.add_evidence(ax, system, read_overlay()[system], spec[0])
            cax = inset_axes(ax, width='3.5%', height='86%', loc='center left',
                             bbox_to_anchor=(1.04, 0, 1, 1), bbox_transform=ax.transAxes, borderpad=0)
            cbar = fig.colorbar(im, cax=cax)
            cbar.set_ticks([-spec[4], 0, spec[4]])
            cbar.set_label(spec[3], fontsize=8)
            cbar.ax.tick_params(labelsize=7)
            save_figure(fig, OUT/'single_panel'/f'{spec[0]}_{case_name}')
    (OUT/'README.md').write_text(
        '# Same-source VASP preview\n\n'
        'Left: undoped; right: Al16. Labels integrate the same 3D fields as the slice, '
        'within radius 0.8 Angstrom spheres centered on the indicated atoms. '
        'They are local sphere changes, not full atomic populations or Bader charges. '
        'Positive delta N denotes electron gain. Delta m = delta N_up - delta N_down. '
        'No spin-channel flip is applied. TSV includes 0.6/0.7/0.8 Angstrom sensitivity. '
        'Input is the existing downsampled grid; no new electronic-structure calculation.\n', encoding='utf-8')
    print(OUT)


if __name__ == '__main__':
    main()
