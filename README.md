# Entropic attractor networks: white paper

*A scale-agnostic, first-principles route to inference and learning in brains and machines.*
Tamas Spisak, Predictive Neuroscience Lab, University Medicine Essen, University of Duisburg-Essen.

### White paper:

- html: https://pni-lab.github.io/eann-whitepaper/

- pdf: https://raw.githubusercontent.com/pni-lab/eann-whitepaper/main/exports/whitepaper.pdf

This repository builds the white paper with [MyST](https://mystmd.org) into

- a website (GitHub Pages), and
- a one-column, arXiv-style PDF (`exports/whitepaper.pdf`), also linked from the website.

## Build locally

```bash
npm install -g mystmd
python3 tools/build.py          # live website preview while editing (myst start)
python3 tools/build.py html     # static website in _build/html
python3 tools/build.py pdf      # PDF -> exports/whitepaper.pdf (needs XeLaTeX and latexmk); always build the PDF this way
python3 tools/build.py all      # PDF, then the website with the PDF included
python3 tools/build.py pdf --prepare-only   # only write the PDF source to _build/pdf/ for inspection
```

The PDF is built from a transformed copy in `_build/pdf/`; the source files are never modified.

On Debian/Ubuntu, the LaTeX packages are:
`texlive-xetex texlive-latex-extra texlive-fonts-recommended texlive-science lmodern latexmk`.

## Licence

Text and figures: CC BY 4.0.
