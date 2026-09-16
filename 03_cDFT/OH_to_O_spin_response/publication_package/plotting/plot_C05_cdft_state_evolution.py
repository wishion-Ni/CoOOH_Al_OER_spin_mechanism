from pathlib import Path
import pandas as pd, numpy as np, matplotlib.pyplot as plt

BASE = Path(__file__).resolve().parent.parent
df = pd.read_csv(BASE / 'source_data/C05_full_cdft_constraint_matrix.csv')
states = ['OH','O','OOH']; x = np.arange(3)
fig, axes = plt.subplots(1,2,figsize=(7.0,3.55),sharey=True)
for ax,direction in zip(axes,['N-1','N+1']):
    sub = df[(df.direction==direction)&(df.constraint_scope.isin(['Co-only','Co+adsorbate']))]
    for col,label in [('pristine_eV','Pristine CoOOH'),('Al16_eV','Al-substituted CoOOH')]:
        for scope,ls,marker in [('Co-only','-','o'),('Co+adsorbate','--','s')]:
            vals=[float(sub[(sub.state==st)&(sub.constraint_scope==scope)][col].iloc[0]) for st in states]
            ax.plot(x,vals,linestyle=ls,marker=marker,linewidth=1.35,markersize=4.8,label=f'{label} / {scope}')
    ax.set_xticks(x,['*OH','*O','*OOH'])
    ax.set_title(direction,fontsize=9.2)
    ax.set_ylim(2.35,5.55)
    ax.tick_params(direction='in',top=True,right=True,labelsize=8)
    for s in ax.spines.values(): s.set_linewidth(0.8)
axes[0].set_ylabel('cDFT constraint penalty (eV)')
h,l = axes[1].get_legend_handles_labels()
fig.legend(h,l,frameon=False,fontsize=6.6,ncol=2,loc='upper center',bbox_to_anchor=(0.5,0.98))
fig.subplots_adjust(left=0.10,right=0.985,bottom=0.16,top=0.76,wspace=0.08)
out = BASE / 'figures/C05_constraint_state_evolution'
for ext in ['png','tif','pdf','svg','eps']:
    fig.savefig(out.with_suffix('.'+ext),dpi=600 if ext in {'png','tif'} else None)
plt.close(fig)
