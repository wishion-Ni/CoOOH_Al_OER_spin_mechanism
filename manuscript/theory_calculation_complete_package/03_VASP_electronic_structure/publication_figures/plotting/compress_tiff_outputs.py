#!/usr/bin/env python3
"""Losslessly compress rendered publication TIFFs using LZW."""
from pathlib import Path
from PIL import Image

ROOT = Path.cwd()
FIG = ROOT / "04_VASP_analysis" / "electronic_structure_publication_figures" / "figures"

for path in sorted(FIG.glob("*.tif")):
    with Image.open(path) as im:
        dpi = im.info.get("dpi", (600, 600))
        tmp = path.with_suffix(".tmp.tif")
        im.save(tmp, format="TIFF", compression="tiff_lzw", dpi=dpi)
    old_size = path.stat().st_size
    new_size = tmp.stat().st_size
    tmp.replace(path)
    print(f"{path.name}: {old_size} -> {new_size} bytes")
