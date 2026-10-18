#!/usr/bin/env python3
"""Export figures/overview.svg (the graphical abstract) to figures/overview.pdf for the PDF build.

The website uses the SVG directly. For LaTeX, the figure is embedded as a lossless
4000-px raster wrapped in a PDF page of the SVG's physical size: the vector export
renders with blurry, overly thick lines in some PDF viewers (the figure contains
many semi-transparent, clipped elements), whereas a high-resolution raster looks
the same everywhere. At the text width this is about 600 dpi.

Needs Inkscape on the PATH (on macOS e.g. /Applications/Inkscape.app/Contents/MacOS/inkscape),
Pillow and img2pdf (pip install pillow img2pdf).

    python3 tools/export_overview.py [width_px]
"""
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import img2pdf
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SVG, PDF = ROOT / "figures" / "overview.svg", ROOT / "figures" / "overview.pdf"
width = int(sys.argv[1]) if len(sys.argv) > 1 else 4000

inkscape = shutil.which("inkscape") or "/Applications/Inkscape.app/Contents/MacOS/inkscape"
head = SVG.read_text()[:3000]
w_mm = float(re.search(r'width="([\d.]+)mm"', head).group(1))
h_mm = float(re.search(r'height="([\d.]+)mm"', head).group(1))

with tempfile.TemporaryDirectory() as tmp:
    png, rgb = Path(tmp) / "overview.png", Path(tmp) / "overview-rgb.png"
    subprocess.run([inkscape, str(SVG), "--export-type=png", f"--export-width={width}",
                    "--export-background=white", "--export-background-opacity=1",
                    f"--export-filename={png}"], check=True)
    Image.open(png).convert("RGB").save(rgb, optimize=True)
    layout = img2pdf.get_layout_fun((img2pdf.mm_to_pt(w_mm), img2pdf.mm_to_pt(h_mm)))
    PDF.write_bytes(img2pdf.convert(str(rgb), layout_fun=layout))
print(f"wrote {PDF.relative_to(ROOT)} ({width} px wide, {PDF.stat().st_size / 1e6:.1f} MB)")
