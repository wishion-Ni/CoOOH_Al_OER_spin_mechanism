#!/usr/bin/env python3
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image

BASE = Path(__file__).resolve().parents[1]
SOURCE = BASE / "source_data" / "staircase_source.csv"
STEPWISE = BASE / "source_data" / "stepwise_dG.csv"
OUTDIR = BASE / "figures"
ORDER = ["CoOOH_pristine", "Al16_Co7_adjAl", "Al16_Al47_control"]
LABELS = {"CoOOH_pristine":"Pristine CoOOH","Al16_Co7_adjAl":"Al-substituted Co site","Al16_Al47_control":"Al-site control"}
COLORS = {"CoOOH_pristine":"#374151","Al16_Co7_adjAl":"#2A9D8F","Al16_Al47_control":"#E76F51"}
STATE_LABELS = ["*","*OH","*O","*OOH","O$_2$"]
TEXT_OFFSETS = {"CoOOH_pristine":[(-0.01,-0.12),(-0.02,-0.13),(-0.01,0.10),(0.03,0.11)],"Al16_Co7_adjAl":[(-0.03,0.13),(-0.02,0.11),(-0.01,0.12),(-0.04,0.14)],"Al16_Al47_control":[(-0.03,0.19),(-0.03,-0.20),(-0.03,0.17),(-0.03,-0.12)]}
plt.rcParams.update({"font.family":"Liberation Sans","font.size":8.0,"axes.labelsize":8.8,"xtick.labelsize":7.9,"ytick.labelsize":7.9,"legend.fontsize":6.9,"pdf.fonttype":42,"ps.fonttype":42})
data = pd.read_csv(SOURCE); steps = pd.read_csv(STEPWISE)
fig, ax = plt.subplots(figsize=(3.50,3.00)); xs=np.arange(5); seg_half=0.215
for system in ORDER:
    frame=data[data.system==system].sort_values("step"); y=frame.dG_eV.to_numpy(); dg=steps[steps.system==system].step_dG_eV.to_numpy(); color=COLORS[system]
    for i,yi in enumerate(y): ax.plot([xs[i]-seg_half,xs[i]+seg_half],[yi,yi],color=color,lw=2.0,solid_capstyle="round",label=LABELS[system] if i==0 else None,zorder=3)
    for i in range(4):
        ax.plot([xs[i]+seg_half,xs[i+1]-seg_half],[y[i],y[i+1]],color=color,lw=1.45,ls=(0,(3.2,2.3)),zorder=2)
        dx,dy=TEXT_OFFSETS[system][i]
        ax.text((xs[i]+xs[i+1])/2+dx,(y[i]+y[i+1])/2+dy,f"{dg[i]:.2f}",color=color,ha="center",va="center",fontsize=6.8,fontweight="semibold",bbox=dict(boxstyle="round,pad=0.13",fc="white",ec="none"),zorder=5)
    ax.scatter(xs,y,s=18,color=color,edgecolor="white",linewidth=0.45,zorder=4)
ax.set_xlim(-0.35,4.35); ax.set_ylim(-0.30,5.18); ax.set_xticks(xs); ax.set_xticklabels(STATE_LABELS)
ax.set_xlabel("Reaction coordinate",labelpad=4); ax.set_ylabel("Relative electronic energy (eV)",labelpad=3)
ax.legend(frameon=False,loc="upper left",handlelength=1.8,borderaxespad=0.2,labelspacing=0.48)
for spine in ax.spines.values(): spine.set_visible(True); spine.set_linewidth(0.9)
ax.tick_params(direction="out",width=0.8,length=3); fig.tight_layout(pad=0.36); OUTDIR.mkdir(parents=True,exist_ok=True)
fig.savefig(OUTDIR/"T01_OER_free_energy_staircase_comparison.png",dpi=600,bbox_inches="tight")
fig.savefig(OUTDIR/"T01_OER_free_energy_staircase_comparison.pdf",bbox_inches="tight")
fig.savefig(OUTDIR/"T01_OER_free_energy_staircase_comparison.svg",bbox_inches="tight")
fig.savefig(OUTDIR/"T01_OER_free_energy_staircase_comparison.eps",bbox_inches="tight")
im=Image.open(OUTDIR/"T01_OER_free_energy_staircase_comparison.png")
im.save(OUTDIR/"T01_OER_free_energy_staircase_comparison_600dpi.tif",format="TIFF",compression="tiff_lzw",dpi=(600,600))
