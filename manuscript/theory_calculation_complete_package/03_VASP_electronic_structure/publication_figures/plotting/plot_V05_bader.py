from pathlib import Path
import pandas as pd, numpy as np, matplotlib.pyplot as plt

BASE = Path(__file__).resolve().parent.parent
df = pd.read_csv(BASE / 'source_data/V05_bader_OH_to_O.csv')
roles = ['Co_act','O_ads','O_bridge','Neighbor']
systems = ['Pristine CoOOH','Al-substituted CoOOH']
x = np.arange(len(roles)); width = 0.36
fig, ax = plt.subplots(figsize=(4.45,3.15))
for i, system in enumerate(systems):
    vals = [float(df[(df.system==system)&(df.site_role==r)]['delta_N_e'].iloc[0]) for r in roles]
    bars = ax.bar(x+(i-0.5)*width, vals, width=width, label=system, edgecolor='black', linewidth=0.6)
    for j,(bar,val) in enumerate(zip(bars,vals)):
        if j==0: y,va=(0.030 if i==0 else 0.044),'bottom'
        elif j==1: y,va=val-0.006,'top'
        elif j==2: y,va=(val-0.006,'top') if i==0 else (0.010,'bottom')
        else: y,va=(0.010,'bottom') if i==0 else (-0.014,'top')
        ax.text(bar.get_x()+bar.get_width()/2,y,f'{val:+.4f}',ha='center',va=va,fontsize=6.9)
ax.axhline(0,linewidth=0.8)
ax.set_ylabel(r'$\Delta N_{\mathrm{Bader}}$ (e)')
ax.set_xticks(x,[r'Co$_{\mathrm{act}}$',r'O$_{\mathrm{ads}}$',r'O$_{\mathrm{bridge}}$','Neighbor\n(Co/Al)'])
ax.set_ylim(-0.29,0.07)
ax.legend(frameon=False,fontsize=7.4,loc='lower right')
ax.tick_params(direction='in',top=True,right=True,labelsize=8)
for s in ax.spines.values(): s.set_linewidth(0.8)
fig.tight_layout()
out = BASE / 'figures/V05_bader_charge_response'
for ext in ['png','tif','pdf','svg','eps']:
    fig.savefig(out.with_suffix('.'+ext),dpi=600 if ext in {'png','tif'} else None)
plt.close(fig)
