from pathlib import Path
import pandas as pd, numpy as np, matplotlib.pyplot as plt

BASE = Path(__file__).resolve().parent.parent
df = pd.read_csv(BASE / 'source_data/V07_neighbor_frontier_pdos_integrals.csv')
x = np.arange(len(df)); width = 0.30
up = df['spin_up_integral_states'].to_numpy(); dn = df['spin_down_integral_states'].to_numpy()
fig, ax = plt.subplots(figsize=(3.95,3.15))
ax.bar(x-width/2,up,width=width,label='Spin up',edgecolor='black',linewidth=0.6)
ax.bar(x+width/2,dn,width=width,label='Spin down',edgecolor='black',linewidth=0.6)
ax.set_yscale('log')
ax.set_ylabel('Integrated neighbor-site PDOS (states)')
ax.set_xticks(x,['Neighbor Co\n(pristine)','Neighbor Al\n(Al-substituted)'])
ax.set_ylim(0.003,5.5)
ax.legend(frameon=False,fontsize=7.5,loc='upper right')
ax.tick_params(direction='in',top=True,right=True,labelsize=8)
for s in ax.spines.values(): s.set_linewidth(0.8)
for i,total in enumerate(df['total_integral_states']):
    y=max(up[i],dn[i])*(1.65 if i==0 else 2.0)
    ax.text(i,y,f'total = {total:.4f}',ha='center',va='bottom',fontsize=7.1)
ratio=float(df.loc[0,'total_integral_states']/df.loc[1,'total_integral_states'])
ax.text(0.55,0.48,f'~{ratio:.0f}x lower total\nfrontier weight',ha='center',va='center',fontsize=7.3,transform=ax.transAxes)
fig.tight_layout()
out=BASE/'figures/V07_neighbor_frontier_boundary'
for ext in ['png','tif','pdf','svg','eps']:
    fig.savefig(out.with_suffix('.'+ext),dpi=600 if ext in {'png','tif'} else None)
plt.close(fig)
