from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


OUT = Path(__file__).with_name("bader_oh_to_o_preliminary_20260823.png")

labels = ["Undoped", "Al16"]
colors = ["#6f7782", "#1f8a70"]

metrics = [
    ("Active Co electron change", [0.025873, 0.030430], "Delta N (e)"),
    ("Adsorbate O electron change", [-0.260692, -0.224205], "Delta N (e)"),
    ("Active Co moment change", [-0.107, -0.033], "Delta m (muB)"),
    ("Adsorbate O moment change", [0.654, 0.700], "Delta m (muB)"),
]

fig, axes = plt.subplots(2, 2, figsize=(10.4, 8.0))
for ax, (title, values, ylabel) in zip(axes.flat, metrics):
    x = np.arange(2)
    bars = ax.bar(x, values, color=colors, width=0.62, edgecolor="#27313a", linewidth=0.7)
    ax.axhline(0, color="#27313a", linewidth=0.8)
    ax.set_xticks(x, labels)
    ax.set_ylabel(ylabel)
    ax.set_title(title, fontsize=11)
    ax.grid(axis="y", alpha=0.22, linewidth=0.7)
    low = min(0.0, min(values))
    high = max(0.0, max(values))
    span = high - low
    ax.set_ylim(low - 0.14 * span, high + 0.22 * span)
    pad = span * 0.045
    for bar, value in zip(bars, values):
        y = value + pad
        ax.text(bar.get_x() + bar.get_width() / 2, y, f"{value:+.3f}", ha="center", va="bottom", fontsize=9)

fig.subplots_adjust(left=0.09, right=0.98, top=0.88, bottom=0.13, hspace=0.42, wspace=0.28)
fig.suptitle("Fixed-geometry Bader and local-moment response: *OH to *O", fontsize=14, y=0.965)
fig.text(
    0.5,
    0.035,
    "Al16 reduces O electron loss by 0.036 e and suppresses the Co moment drop by 0.074 muB; "
    "local moments are VASP PAW projections.",
    ha="center",
    fontsize=9,
    color="#3f4b55",
)
fig.savefig(OUT, dpi=220, facecolor="white")
print(OUT)
