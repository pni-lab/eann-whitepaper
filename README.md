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
| `tools/export_overview.py` | Exports the graphical abstract (`figures/overview.svg`) to `figures/overview.pdf` for the PDF build |
| `tools/mystdocs.py` | Round trip between `whitepaper.md` and a two-tab Claude Docs document (main text and appendix boxes) |
| `tools/docs2myst.py` | Former converter from a Claude Docs export (no longer used) |
| `figures/overview.svg`, `figures/overview.pdf` | Graphical abstract: the SVG is the source and is used on the website; the PDF wraps a lossless 4000-px raster of it for the LaTeX/PDF build (MyST picks the right one via `figures/overview.*`; a vector export rendered with blurry, thick lines in some PDF viewers). After editing the SVG, re-export with `python3 tools/export_overview.py` (needs Inkscape, Pillow and img2pdf) |
| `_templates/arxiv-eann/` | The arXiv (NIPS-style) LaTeX template, adapted: compact title block with Fig. 1 on the title page (`title_figure` and `title_figure_caption` options), contributors block, status badges, Unicode symbols, unnumbered sections, page-safe boxes, tables and figures (see below), and a bibliography style without duplicate URLs (`plainnat-eann.bst`) |
| `style.css` | Website styling for the status badges |
| `.github/workflows/deploy.yml` | Builds the PDF and the website and deploys to GitHub Pages |

## Editing workflow

Edit `whitepaper.md` directly, or edit the text in Claude Docs and convert it back with `tools/mystdocs.py` (see below; the old `tools/docs2myst.py` is retired). The source is written for the website; the PDF is derived from it by `tools/build.py`.

- **Reference boxes.** Long reference material (about this document, setting and notation, desiderata, intellectual lineage) sits in admonitions with `:class: dropdown appendix`. On the website they are collapsed dropdowns where they stand. In the PDF they are moved to the end as Appendix A, B, ... in order of appearance. To refer to such a box in the text, write its title in italics, exactly as in the box (`*Setting, notation and the assumption–result map*`); in the PDF this becomes "Appendix B (*Setting, ...*)". A box that is not mentioned leaves a one-line pointer in the PDF. Use four colons (`::::`) for these boxes so that they can contain other directives.
- **PDF layout.** The template makes MyST's LaTeX output page-safe, so `myst build --pdf` and `tools/build.py pdf` both give a clean PDF without post-processing: boxes (admonitions) are breakable, shaded boxes; tables outside boxes break across pages and repeat their header row; figures are at most 55% of the text height, so a figure and its caption always fit on one page. MyST gives all table columns the same width. To set relative widths for the PDF, put a line with an inline raw LaTeX role just before the table, e.g. ``{raw:latex}`\tablecolumns{0.06,0.40,0.22,0.32}` `` (the website shows nothing for it, and `style.css` hides the empty paragraph; `tools/mystdocs.py` keeps it across the Claude Docs round trip, matched by the table's header row).
- **Cross-references.** Every section heading carries a target (`(sec-4-2)=` before `### 4.2 ...`), and every mention of a section or figure is a link: `[Section 4.2](#sec-4-2)`, `Sections [4.3](#sec-4-3)–[4.5](#sec-4-5)`, `[Figure 2A](#fig-rules)`. On the website they are MyST cross-references; `tools/build.py pdf` turns them into LaTeX hyperlinks with the same text (plain `myst build --pdf` would drop the links and the panel letters). In Claude Docs they are plain text, and `tools/mystdocs.py from-docs` links them again automatically (figure numbers follow the order of the figures).
- **Web-only prelude.** The version and DOI line, the graphical abstract and the contributors block at the top of `whitepaper.md` are marked `no-tex`/`no-pdf`; the PDF has them on its title page.
- **Author line.** `myst.yml` names the author "White Paper by Tamas Spisak", which the website shows prominently. The PDF build prints just "Tamas Spisak".

- **Editing in Claude Docs.** `python3 tools/mystdocs.py to-docs` writes `_build/docs/main.md` and `_build/docs/boxes.md` for the doc's two tabs ("White paper" and "Boxes"). After editing, export both tabs as Markdown and run `python3 tools/mystdocs.py from-docs <main export> <boxes export>`; this rewrites `whitepaper.md`, keeping the frontmatter (except title and abstract), the prelude (DOI line, figure, contributors) and the closing comments from the local file. Conventions in the doc: citations are doi.org links, parenthetical ones grouped in round brackets, "([Author, 2020](https://doi.org/...))", narrative ones as "[Author (2020)](https://doi.org/...)" (works without a DOI link to `https://cite.invalid/<bibkey>`); status tags are "[Hypothesis]", "[In preparation; note]" etc.; note boxes are block quotes starting with the bold title; appendix boxes live in the Boxes tab and are marked "[Box: <title>]" in the text; display maths is a `latex` code block, inline maths a code span `` `$...$` ``. While the text is being edited in the doc, do not edit the body of `whitepaper.md` locally.

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
python3 tools/build.py pdf      # PDF -> exports/whitepaper.pdf (needs XeLaTeX and latexmk); always build the PDF this way
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
