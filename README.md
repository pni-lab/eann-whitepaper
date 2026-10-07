# Entropic attractor networks: white paper

*A scale-agnostic, first-principles route to inference and learning in brains and machines.*
Tamas Spisak, Predictive Neuroscience Lab, University Medicine Essen, University of Duisburg-Essen.

### White paper:

- html: https://pni-lab.github.io/eann-whitepaper/

- pdf: https://raw.githubusercontent.com/pni-lab/eann-whitepaper/main/exports/whitepaper.pdf

This repository builds the white paper with [MyST](https://mystmd.org) into

- a website (GitHub Pages), and
- a one-column, arXiv-style PDF (`exports/whitepaper.pdf`), also linked from the website.

## Layout

| Path | What it is |
| --- | --- |
| `whitepaper.md` | The MyST source of the white paper, written for the website |
| `myst.yml` | Project metadata (title, author, affiliations; keywords are metadata only and not printed) and site settings |
| `source/claude-docs-export.md` | The raw markdown export from Claude Docs, the editing source |
| `tools/build.py` | Builds the website (default: live preview) and the PDF, moving appendix boxes to the end for the PDF |
| `tools/docs2myst.py` | Former converter from a Claude Docs export (no longer used) |
| `figures/fig1.png` | Graphical abstract (300 dpi) |
| `_templates/arxiv-eann/` | The arXiv (NIPS-style) LaTeX template, adapted: compact title block with Fig. 1 on the title page (`title_figure` option), contributors block, status badges, Unicode symbols, unnumbered sections |
| `style.css` | Website styling for the status badges |
| `.github/workflows/deploy.yml` | Builds the PDF and the website and deploys to GitHub Pages |

## Editing workflow

Edit `whitepaper.md` directly (the Claude Docs route via `tools/docs2myst.py` is retired; re-running it would overwrite direct edits). The source is written for the website; the PDF is derived from it by `tools/build.py`.

- **Reference boxes.** Long reference material (about this document, setting and notation, desiderata, intellectual lineage) sits in admonitions with `:class: dropdown appendix`. On the website they are collapsed dropdowns where they stand. In the PDF they are moved to the end as Appendix A, B, ... in order of appearance. To refer to such a box in the text, write its title in italics, exactly as in the box (`*Setting, notation and the assumption–result map*`); in the PDF this becomes "Appendix B (*Setting, ...*)". A box that is not mentioned leaves a one-line pointer in the PDF. Use four colons (`::::`) for these boxes so that they can contain other directives.
- **Author line.** `myst.yml` names the author "White Paper by Tamas Spisak", which the website shows prominently. The PDF build prints just "Tamas Spisak".

## Citations

Citations use MyST roles with DOIs, e.g. {cite:t}`10.1038/nrn2787` (narrative, "Friston (2010)")
or {cite:p}`10.1038/nrn2787; 10.1073/pnas.79.8.2554` (parenthetical). MyST fetches the metadata from
doi.org at build time and generates the reference list. The few works without a DOI are in
`references.bib` and are cited by key (e.g. {cite:p}`sutton2018`). Prefixes such as `{cf.}` are not
used, because the LaTeX/PDF export drops them.

## Build locally

```bash
npm install -g mystmd
python3 tools/build.py          # live website preview while editing (myst start)
python3 tools/build.py html     # static website in _build/html
python3 tools/build.py pdf      # PDF -> exports/whitepaper.pdf (needs XeLaTeX and latexmk)
python3 tools/build.py all      # PDF, then the website with the PDF included
python3 tools/build.py pdf --prepare-only   # only write the PDF source to _build/pdf/ for inspection
```

The PDF is built from a transformed copy in `_build/pdf/`; the source files are never modified.

On Debian/Ubuntu, the LaTeX packages are:
`texlive-xetex texlive-latex-extra texlive-fonts-recommended texlive-science lmodern latexmk`.

## GitHub setup (once)

1. Create the repository and push this folder.
2. Settings → Pages → Build and deployment → Source: **GitHub Actions**.
3. Optionally set `project.github` in `myst.yml` to the repository URL.

The site is then served at `https://<user>.github.io/<repo>/`, with the PDF at `.../whitepaper.pdf`.

## Licence

Text and figures: CC BY 4.0.
