from pathlib import Path
import pandas as pd, numpy as np, matplotlib.pyplot as plt

BASE = Path(__file__).resolve().parent.parent
df = pd.read_csv(BASE / 'source_data/V08_orbital_population_OH_to_O.csv')
summary = df.groupby(['material','atom','population','spin'], as_index=False)['delta_e'].sum()
summary.to_csv(BASE / 'source_data/V08_spin_channel_summary.csv', index=False)

# V08a: orbital-summed spin-channel population response
fig, axes = plt.subplots(1, 2, figsize=(6.3, 3.55), sharey=True)
titles = [('Co','Active Co 3d manifold'),('Oads','Adsorbate O 2p manifold')]
labels = {'Undoped':'Pristine CoOOH','Al16':'Al-substituted CoOOH'}
markers = {'Mulliken':'o','Loewdin':'D'}
xb = np.array([0,1])
for ax,(atom,title) in zip(axes,titles):
    for mi,mat in enumerate(['Undoped','Al16']):
        off = -0.10 if mi == 0 else 0.10
        for method in ['Mulliken','Loewdin']:
            vals = [float(summary[(summary.material==mat)&(summary.atom==atom)&(summary.population==method)&(summary.spin==sp)]['delta_e'].iloc[0]) for sp in ['up','down']]
            ax.plot(xb+off, vals, marker=markers[method], linestyle='-' if method=='Mulliken' else '--', linewidth=1.15, markersize=5.0, label=f'{labels[mat]} / {method}')
    ax.axhline(0, linewidth=0.8)
    ax.set_xticks([0,1],[r'$\uparrow$',r'$\downarrow$'])
    ax.set_title(title, fontsize=9)
    ax.tick_params(direction='in', top=True, right=True, labelsize=8)
    for s in ax.spines.values(): s.set_linewidth(0.8)
axes[0].set_ylabel(r'$\Delta n = n(*O)-n(*OH)$ (e)')
h,l = axes[1].get_legend_handles_labels()
fig.legend(h[:4], l[:4], frameon=False, fontsize=6.6, ncol=2, loc='upper center', bbox_to_anchor=(0.5,0.98))
fig.subplots_adjust(left=0.11,right=0.985,bottom=0.17,top=0.75,wspace=0.08)
out = BASE / 'figures/V08a_spin_channel_population_crosscheck'
for ext in ['png','tif','pdf','svg','eps']:
    fig.savefig(out.with_suffix('.'+ext), dpi=600 if ext in {'png','tif'} else None)
plt.close(fig)

# V08b: orbital-resolved Mulliken fingerprint; global-axis projections only
fig, axes = plt.subplots(2,2,figsize=(6.4,5.3))
panels = [
    ('Undoped','Co','Pristine CoOOH - Co 3d'),
    ('Al16','Co','Al-substituted CoOOH - Co 3d'),
    ('Undoped','Oads',r'Pristine CoOOH - O$_{ads}$ 2p'),
    ('Al16','Oads',r'Al-substituted CoOOH - O$_{ads}$ 2p')
]
label_map = {
    '3d_xy':r'$3d_{xy}$','3d_yz':r'$3d_{yz}$','3d_z^2':r'$3d_{z^2}$',
    '3d_xz':r'$3d_{xz}$','3d_x^2-y^2':r'$3d_{x^2-y^2}$',
    '2p_x':r'$2p_x$','2p_y':r'$2p_y$','2p_z':r'$2p_z$'
}
vmax = 0.50
for ax,(mat,atom,title) in zip(axes.flat,panels):
    sub = df[(df.material==mat)&(df.atom==atom)&(df.population=='Mulliken')]
    orbs = list(dict.fromkeys(sub['orbital'].tolist()))
    arr = np.array([[float(sub[(sub.orbital==orb)&(sub.spin==sp)]['delta_e'].iloc[0]) for sp in ['up','down']] for orb in orbs])
    im = ax.imshow(arr, aspect='auto', vmin=-vmax, vmax=vmax, cmap='RdBu_r')
    ax.set_xticks([0,1],[r'$\uparrow$',r'$\downarrow$'])
    ax.set_yticks(range(len(orbs)),[label_map[o] for o in orbs])
    ax.set_title(title,fontsize=8.8)
    ax.tick_params(labelsize=7.8)
    for i in range(arr.shape[0]):
        for j in range(arr.shape[1]):
            ax.text(j,i,f'{arr[i,j]:+.2f}',ha='center',va='center',fontsize=6.8)
c = fig.colorbar(im, ax=axes.ravel().tolist(), fraction=0.027, pad=0.03)
c.set_label(r'$\Delta n$ (e)',fontsize=8.5)
fig.text(0.5,0.015,'LOBSTER Mulliken populations; orbital labels are global-axis projections',ha='center',fontsize=7.4)
fig.subplots_adjust(left=0.15,right=0.89,top=0.92,bottom=0.09,wspace=0.33,hspace=0.34)
out = BASE / 'figures/V08b_orbital_resolved_population'
for ext in ['png','tif','pdf','svg','eps']:
    fig.savefig(out.with_suffix('.'+ext), dpi=600 if ext in {'png','tif'} else None)
plt.close(fig)
