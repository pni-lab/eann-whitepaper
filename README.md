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
| `whitepaper.md` | The MyST source of the white paper (generated, see below) |
| `myst.yml` | Project metadata (title, author, affiliations; keywords are metadata only and not printed) and site settings |
| `source/claude-docs-export.md` | The raw markdown export from Claude Docs, the editing source |
| `tools/docs2myst.py` | Converts the Claude Docs export into `whitepaper.md` |
| `figures/fig1.png` | Graphical abstract (300 dpi) |
| `_templates/arxiv-eann/` | The arXiv (NIPS-style) LaTeX template, adapted: compact title block with Fig. 1 on the title page (`title_figure` option), contributors block, status badges, Unicode symbols, unnumbered sections |
| `style.css` | Website styling for the status badges |
| `.github/workflows/deploy.yml` | Builds the PDF and the website and deploys to GitHub Pages |

## Editing workflow

The text is edited in Claude Docs. To publish a new version:

1. Export the doc as markdown and save it as `source/claude-docs-export.md`.
2. Convert it: `python tools/docs2myst.py source/claude-docs-export.md whitepaper.md`
3. Commit and push. The GitHub Action builds the PDF and the website.

You can also edit `whitepaper.md` directly; just don't re-run step 2 afterwards, or your direct edits are overwritten.

The converter moves the title block into the frontmatter, uses the "*Abstract.*" paragraph (which doubles as the
description of the graphical abstract) as the abstract, turns the boxed
passages into admonitions, turns LaTeX blocks into `{math}` directives, and turns status tags such as `[Hypothesis]` into
coloured badges (PDF and website). The graphical abstract (no caption) is shown at the top of the website and, in the PDF, on the title page below the
abstract (the body copy is marked `no-pdf`).

## Citations

Citations use MyST roles with DOIs, e.g. {cite:t}`10.1038/nrn2787` (narrative, "Friston (2010)")
or {cite:p}`10.1038/nrn2787; 10.1073/pnas.79.8.2554` (parenthetical). MyST fetches the metadata from
doi.org at build time and generates the reference list. The few works without a DOI are in
`references.bib` and are cited by key (e.g. {cite:p}`sutton2018`). Prefixes such as `{cf.}` are not
used, because the LaTeX/PDF export drops them.

## Build locally

```bash
npm install -g mystmd
myst build --pdf     # -> exports/whitepaper.pdf (needs XeLaTeX and latexmk)
myst start           # local preview of the website
```

On Debian/Ubuntu, the LaTeX packages are:
`texlive-xetex texlive-latex-extra texlive-fonts-recommended texlive-science lmodern latexmk`.

## GitHub setup (once)

1. Create the repository and push this folder.
2. Settings → Pages → Build and deployment → Source: **GitHub Actions**.
3. Optionally set `project.github` in `myst.yml` to the repository URL.

The site is then served at `https://<user>.github.io/<repo>/`, with the PDF at `.../whitepaper.pdf`.

## Licence

Text and figures: CC BY 4.0.
