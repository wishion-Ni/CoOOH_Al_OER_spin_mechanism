#!/usr/bin/env python3
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

BASE = Path(__file__).resolve().parents[1]
POP = pd.read_csv(BASE / 'source_data' / 'C01_C02_C03_population_data.csv')
CON = pd.read_csv(BASE / 'source_data' / 'C04_O_constrained_state_fingerprints.csv')
OUT = BASE / 'figures'
OUT.mkdir(parents=True, exist_ok=True)

COLORS = {'Pristine CoOOH':'#374151', 'Al-substituted':'#2A9D8F'}
ALPHA_COLOR = '#4C78A8'
BETA_COLOR = '#E08B45'
ROLES = ['Coact','Oads','Obridge','neighbor']
ROLE_LABELS = [r'Co$_{act}$', r'O$_{ads}$', r'O$_{bridge}$', 'Neighbor\n(Co/Al)']
SYS_OFF = {'Pristine CoOOH':-0.14, 'Al-substituted':0.14}

plt.rcParams.update({
    'font.family':'Liberation Sans',
    'font.size':8.1,
    'axes.labelsize':8.8,
    'xtick.labelsize':7.7,
    'ytick.labelsize':7.8,
    'legend.fontsize':6.8,
    'pdf.fonttype':42,
    'ps.fonttype':42,
})

def finish(ax):
    for sp in ax.spines.values():
        sp.set_visible(True)
        sp.set_linewidth(0.9)
    ax.tick_params(direction='out', width=0.8, length=3)

def save(fig, stem):
    fig.savefig(OUT / f'{stem}.png', dpi=600, bbox_inches='tight')
    fig.savefig(OUT / f'{stem}.tif', dpi=600, bbox_inches='tight')
    fig.savefig(OUT / f'{stem}.pdf', bbox_inches='tight')
    fig.savefig(OUT / f'{stem}.svg', bbox_inches='tight')
    fig.savefig(OUT / f'{stem}.eps', bbox_inches='tight')
    plt.close(fig)

# C01: charge redistribution
fig, ax = plt.subplots(figsize=(3.55,2.75))
x = np.arange(len(ROLES))
meth_off = {'Hirshfeld':-0.03, 'Mulliken':0.03}
for ri, role in enumerate(ROLES):
    for system in COLORS:
        xs, ys = [], []
        for method in ['Hirshfeld','Mulliken']:
            row = POP[(POP.system==system)&(POP.atom_role==role)&(POP.partition==method)].iloc[0]
            xs.append(x[ri] + SYS_OFF[system] + meth_off[method])
            ys.append(row.delta_N_total_e)
        ax.plot(xs, ys, color=COLORS[system], lw=0.75, alpha=0.6, zorder=1)
for system, color in COLORS.items():
    h = POP[(POP.system==system)&(POP.partition=='Hirshfeld')].set_index('atom_role').loc[ROLES]
    m = POP[(POP.system==system)&(POP.partition=='Mulliken')].set_index('atom_role').loc[ROLES]
    ax.scatter(x+SYS_OFF[system]+meth_off['Hirshfeld'], h.delta_N_total_e, s=34, color=color,
               edgecolor='white', linewidth=0.55, zorder=3)
    ax.scatter(x+SYS_OFF[system]+meth_off['Mulliken'], m.delta_N_total_e, s=28, marker='D',
               facecolors='white', edgecolors=color, linewidth=1.15, zorder=3)
for system in COLORS:
    for role in ['Coact','Oads']:
        r = POP[(POP.system==system)&(POP.atom_role==role)&(POP.partition=='Hirshfeld')].iloc[0]
        xi = x[ROLES.index(role)] + SYS_OFF[system] + meth_off['Hirshfeld']
        yi = r.delta_N_total_e
        dy = 0.045 if yi >= 0 else -0.055
        ax.text(xi, yi+dy, f'{yi:+.2f}', color=COLORS[system], ha='center',
                va='bottom' if yi>=0 else 'top', fontsize=6.4, fontweight='semibold')
ax.axhline(0, color='#888888', lw=0.72, ls=(0,(2.2,2.2)))
ax.set_xticks(x, ROLE_LABELS)
ax.set_ylabel(r'$\Delta N$  (*O $-$ *OH) (e)')
ax.set_xlim(-0.45,3.45); ax.set_ylim(-0.62,0.34)
handles = [
    Line2D([0],[0],color=COLORS['Pristine CoOOH'],lw=2.2,label='Pristine'),
    Line2D([0],[0],color=COLORS['Al-substituted'],lw=2.2,label='Al-substituted'),
    Line2D([0],[0],marker='o',color='none',markerfacecolor='#666',markeredgecolor='white',markersize=5.1,label='Hirshfeld'),
    Line2D([0],[0],marker='D',color='none',markerfacecolor='white',markeredgecolor='#666',markersize=4.8,label='Mulliken'),
]
ax.legend(handles=handles, frameon=False, loc='lower right', handlelength=1.45, labelspacing=0.28)
finish(ax); fig.tight_layout(pad=0.42); save(fig,'C01_charge_redistribution')

# C02: local-spin evolution
fig, ax = plt.subplots(figsize=(3.55,2.82))
x = np.arange(len(ROLES)); state_off = {'*OH':-0.035,'*O':0.035}
for ri, role in enumerate(ROLES):
    for system in COLORS:
        r = POP[(POP.system==system)&(POP.atom_role==role)&(POP.partition=='Hirshfeld')].iloc[0]
        xx = x[ri] + SYS_OFF[system]
        ax.plot([xx+state_off['*OH'],xx+state_off['*O']], [r.OH_spin_muB,r.O_spin_muB],
                color=COLORS[system], lw=1.35, zorder=2)
        ax.scatter(xx+state_off['*OH'], r.OH_spin_muB, s=25, facecolors='white', edgecolors=COLORS[system], linewidth=1.1, zorder=3)
        ax.scatter(xx+state_off['*O'], r.O_spin_muB, s=28, color=COLORS[system], edgecolor='white', linewidth=0.45, zorder=3)
for system in COLORS:
    for role in ['Coact','Oads']:
        r = POP[(POP.system==system)&(POP.atom_role==role)&(POP.partition=='Hirshfeld')].iloc[0]
        xx = x[ROLES.index(role)] + SYS_OFF[system]
        ym = (r.OH_spin_muB+r.O_spin_muB)/2
        ax.text(xx+0.07, ym, f'{r.delta_spin_muB:+.2f}', color=COLORS[system], fontsize=6.3,
                ha='left', va='center', fontweight='semibold')
ax.axhline(0, color='#888888', lw=0.72, ls=(0,(2.2,2.2)))
ax.set_xticks(x, ROLE_LABELS)
ax.set_ylabel(r'Local spin ($\mu_B$)')
ax.set_xlim(-0.45,3.45); ax.set_ylim(-0.72,3.55)
handles = [
    Line2D([0],[0],color=COLORS['Pristine CoOOH'],lw=2.2,label='Pristine'),
    Line2D([0],[0],color=COLORS['Al-substituted'],lw=2.2,label='Al-substituted'),
    Line2D([0],[0],marker='o',color='#666',markerfacecolor='white',markersize=5,label='*OH'),
    Line2D([0],[0],marker='o',color='none',markerfacecolor='#666',markersize=5,label='*O'),
]
ax.legend(handles=handles, frameon=False, loc='upper right', handlelength=1.35, labelspacing=0.28)
finish(ax); fig.tight_layout(pad=0.42); save(fig,'C02_local_spin_evolution')

# C03: spin-change partition
fig, ax = plt.subplots(figsize=(3.45,2.75))
cats = [('Pristine CoOOH','Coact'),('Al-substituted','Coact'),('Pristine CoOOH','Oads'),('Al-substituted','Oads')]
cat_labels = ['Pristine\nCo$_{act}$','Al-sub.\nCo$_{act}$','Pristine\nO$_{ads}$','Al-sub.\nO$_{ads}$']
x = np.arange(len(cats)); w=0.28; a=[]; b=[]
for system,role in cats:
    r = POP[(POP.system==system)&(POP.atom_role==role)&(POP.partition=='Hirshfeld')].iloc[0]
    a.append(r.delta_N_alpha_e); b.append(r.delta_N_beta_e)
bars1=ax.bar(x-w/2,a,w,color=ALPHA_COLOR,label=r'$\Delta N_\alpha$')
bars2=ax.bar(x+w/2,b,w,color=BETA_COLOR,label=r'$\Delta N_\beta$')
for bars in [bars1,bars2]:
    for bar in bars:
        yy=bar.get_height(); off=0.025 if yy>=0 else -0.025
        ax.text(bar.get_x()+bar.get_width()/2, yy+off, f'{yy:+.2f}', ha='center',
                va='bottom' if yy>=0 else 'top', fontsize=6.1)
ax.axhline(0,color='#777',lw=0.75)
ax.set_xticks(x,cat_labels); ax.set_ylabel('Population change (e)'); ax.set_ylim(-0.72,0.64)
ax.legend(frameon=False, loc='upper right', handlelength=1.1)
finish(ax); fig.tight_layout(pad=0.42); save(fig,'C03_spin_change_partition')

# C04: constrained-state fingerprints for *O
fig, ax = plt.subplots(figsize=(3.72,3.05))
labels_y = [r'Co-only  $N-1$',r'Co-only  $N+1$',r'Co+ads.  $N-1$',r'Co+ads.  $N+1$',r'Co spin  $M+2$']
y=np.arange(len(labels_y))[::-1]; pr=CON.pristine_eV.to_numpy(); al=CON.Al16_eV.to_numpy()
for yi,pv,av in zip(y,pr,al): ax.plot([pv,av],[yi,yi],color='#B7BDC5',lw=1.4,zorder=1)
ax.scatter(pr,y,s=35,color=COLORS['Pristine CoOOH'],edgecolor='white',linewidth=0.5,zorder=3,label='Pristine')
ax.scatter(al,y,s=35,color=COLORS['Al-substituted'],edgecolor='white',linewidth=0.5,zorder=3,label='Al-substituted')
for yi,pv,av,dv in zip(y,pr,al,CON.Al_minus_pristine_eV):
    ax.text(pv, yi+0.16, f'{pv:.2f}', color=COLORS['Pristine CoOOH'], ha='center', va='bottom', fontsize=6.2)
    ax.text(av, yi-0.16, f'{av:.2f}', color=COLORS['Al-substituted'], ha='center', va='top', fontsize=6.2)
    if abs(dv)>0.5:
        ax.text(max(pv,av)+0.26, yi, rf'$\Delta$={dv:+.2f}', color='#5D6470', ha='left', va='center', fontsize=6.2, fontweight='semibold')
ax.set_yticks(y,labels_y); ax.set_xlabel('cDFT constraint penalty (eV)')
ax.set_xlim(2.45,5.80); ax.set_ylim(-0.55,4.55)
ax.legend(frameon=False, loc='upper left', handlelength=1.0, labelspacing=0.3)
finish(ax); fig.tight_layout(pad=0.42); save(fig,'C04_O_constrained_state_fingerprints')
