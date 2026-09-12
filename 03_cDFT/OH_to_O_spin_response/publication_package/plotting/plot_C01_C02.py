#!/usr/bin/env python3
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

BASE=Path(__file__).resolve().parents[1]
DATA=pd.read_csv(BASE/'source_data'/'C01_C02_local_population_response.csv')
OUT=BASE/'figures'; OUT.mkdir(parents=True,exist_ok=True)
COLORS={'Pristine CoOOH':'#374151','Al-substituted':'#2A9D8F'}
X={'Co_act':0,'O_ads':1}; SO={'Pristine CoOOH':-0.14,'Al-substituted':0.14}; MO={'Hirshfeld':-0.025,'Mulliken':0.025}
plt.rcParams.update({'font.family':'Liberation Sans','font.size':8.0,'axes.labelsize':8.8,'xtick.labelsize':8.0,'ytick.labelsize':8.0,'legend.fontsize':6.8,'pdf.fonttype':42,'ps.fonttype':42})

def render(col,ylabel,stem,ylim,offsets):
    fig,ax=plt.subplots(figsize=(3.05,2.65))
    for atom in X:
        for sys in COLORS:
            sub=DATA[(DATA.atom_role==atom)&(DATA.system==sys)]
            pts=[]
            for method in ['Hirshfeld','Mulliken']:
                r=sub[sub.partition==method].iloc[0]; pts.append((X[atom]+SO[sys]+MO[method],r[col]))
            ax.plot([pts[0][0],pts[1][0]],[pts[0][1],pts[1][1]],color=COLORS[sys],lw=0.8,alpha=0.55,zorder=1)
    for sys,color in COLORS.items():
        h=DATA[(DATA.system==sys)&(DATA.partition=='Hirshfeld')]; m=DATA[(DATA.system==sys)&(DATA.partition=='Mulliken')]
        ax.scatter([X[a]+SO[sys]+MO['Hirshfeld'] for a in h.atom_role],h[col],s=32,color=color,edgecolor='white',linewidth=0.55,zorder=3)
        ax.scatter([X[a]+SO[sys]+MO['Mulliken'] for a in m.atom_role],m[col],s=26,marker='D',facecolors='white',edgecolors=color,linewidth=1.15,zorder=3)
    for _,r in DATA[DATA.partition=='Hirshfeld'].iterrows():
        xx=X[r.atom_role]+SO[r.system]+MO['Hirshfeld']; yy=r[col]; dx,dy,va=offsets[(r.system,r.atom_role)]
        ax.text(xx+dx,yy+dy,f'{yy:+.2f}',color=COLORS[r.system],ha='center',va=va,fontsize=6.55,fontweight='semibold')
    ax.axhline(0,color='#888888',lw=0.72,ls=(0,(2.2,2.2)),zorder=0)
    ax.set_xticks([0,1],[r'Co$_{act}$',r'O$_{ads}$']); ax.set_ylabel(ylabel); ax.set_xlim(-0.42,1.42); ax.set_ylim(*ylim)
    for s in ax.spines.values(): s.set_visible(True); s.set_linewidth(0.9)
    ax.tick_params(direction='out',width=0.8,length=3)
    handles=[Line2D([0],[0],color=COLORS['Pristine CoOOH'],lw=2.2,label='Pristine'),Line2D([0],[0],color=COLORS['Al-substituted'],lw=2.2,label='Al-substituted'),Line2D([0],[0],marker='o',color='none',markerfacecolor='#5d5d5d',markeredgecolor='white',markersize=5.1,label='Hirshfeld'),Line2D([0],[0],marker='D',color='none',markerfacecolor='white',markeredgecolor='#5d5d5d',markersize=4.8,label='Mulliken')]
    ax.legend(handles=handles,frameon=False,loc='best',handlelength=1.45,labelspacing=0.28); fig.tight_layout(pad=0.42)
    for ext,kw in [('png',{'dpi':600}),('tif',{'dpi':600}),('pdf',{}),('svg',{}),('eps',{})]: fig.savefig(OUT/f'{stem}.{ext}',bbox_inches='tight',**kw)
    plt.close(fig)

charge={('Pristine CoOOH','Co_act'):(0,0.045,'bottom'),('Al-substituted','Co_act'):(0,0.045,'bottom'),('Pristine CoOOH','O_ads'):(0,-0.055,'top'),('Al-substituted','O_ads'):(0,-0.055,'top')}
spin={('Pristine CoOOH','Co_act'):(0,-0.050,'top'),('Al-substituted','Co_act'):(0,-0.050,'top'),('Pristine CoOOH','O_ads'):(0,-0.045,'top'),('Al-substituted','O_ads'):(0,-0.070,'top')}
render('delta_N_e',r'$\Delta N$ (e)','C01_local_electron_population_response',(-0.62,0.35),charge)
render('delta_spin_muB',r'$\Delta m$ ($\mu_B$)','C02_local_spin_response',(-1.00,0.16),spin)
