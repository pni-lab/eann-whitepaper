#!/usr/bin/env python3
"""Round trip between the MyST source (whitepaper.md) and a Claude Docs document.

    python3 tools/mystdocs.py to-docs   [whitepaper.md] [outdir]
        -> outdir/main.md  (the main text, for the doc's main tab)
           outdir/boxes.md (the appendix boxes, for a second tab "Boxes")

    python3 tools/mystdocs.py from-docs main_export.md boxes_export.md [whitepaper.md]
        -> rewrites whitepaper.md: the frontmatter, the prelude (DOI line, figure,
           contributors) and the closing comments are kept from the current file;
           the title, the abstract and the body come from the doc.

Conventions in the doc (readable while editing, reversible):
  * Citations are links to doi.org. Parenthetical citations are a group in round
    brackets, "([Spisak & Friston, 2026](https://doi.org/...); [...](...))";
    narrative citations carry the year in brackets, "[Spisak & Friston (2026)](https://doi.org/...)".
    Works without a DOI (references.bib) link to "https://cite.invalid/<bibkey>".
    To add a citation in the doc, write a link in the same form; only the URL counts.
  * Status tags are plain text in square brackets: [Hypothesis], [Published],
    [In preparation], [Speculative], optionally with notes: [Hypothesis; observed in simulations].
  * Note boxes are block quotes whose first line is the bold title.
  * Appendix boxes (dropdowns on the website, appendices in the PDF) live in the
    "Boxes" tab, one "## <title>" section each; the main text holds a placeholder
    paragraph "[Box: <title>]" where the box stands.
  * Display maths is a ```latex block; inline maths is a code span `$...$`.
  * Figures are images followed by a caption paragraph that starts with
    "***Figure N. Title.***". The image's alt text selects the file through
    FIGURES below (alt-text prefix -> (file, label)); the "Figure N." prefix is
    dropped, since MyST numbers figures itself, in order of appearance.
  * Section and figure references ("Section 4.2", "Figures 2C and 5A") are plain
    text in the doc and MyST cross-references in whitepaper.md (see link_refs).
  * PDF column widths for tables (a line "{raw:latex}`\\tablecolumns{...}`" just
    before a table in whitepaper.md) are not shown in the doc. from-docs puts
    them back before the table with the same header row; if a header row was
    changed in the doc, that table falls back to equal column widths.
"""

import glob
import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parent.parent
TAGS = [("In preparation", "in-preparation", "bPrep"), ("Published", "published", "bPub"),
        ("Hypothesis", "hypothesis", "bHyp"), ("Speculative", "speculative", "bSpec")]
TAGWORDS = "In preparation|Published|Hypothesis|Speculative"
BIBURL = "https://cite.invalid/"
DOIURL = "https://doi.org/"

# ---------------------------------------------------------------- helpers


def split_frontmatter(text):
    assert text.startswith("---\n")
    end = text.index("\n---\n", 4)
    return text[: end + 5], text[end + 5:]


def labels():
    """Map DOI (lower case) or bib key -> (authors, year)."""
    out = {}
    for f in glob.glob(str(ROOT / "_build" / "cache" / "*.csl.json")):
        try:
            data = json.load(open(f))
        except Exception:
            continue
        for item in data if isinstance(data, list) else [data]:
            doi = (item.get("DOI") or "").lower()
            if not doi:
                continue
            names = [a.get("family") or a.get("literal") or "" for a in item.get("author", [])]
            names = [n for n in names if n] or [item.get("publisher", "") or "?"]
            year = ""
            for k in ("issued", "published-print", "published-online", "created"):
                dp = (item.get(k) or {}).get("date-parts")
                if dp and dp[0] and dp[0][0]:
                    year = str(dp[0][0])
                    break
            out[doi] = (names, year or "n.d.")
    bib = ROOT / "references.bib"
    if bib.exists():
        for m in re.finditer(r"@\w+\{([^,]+),(.*?)\n\}", bib.read_text(), re.S):
            key, body = m.group(1).strip(), m.group(2)
            au = re.search(r"author\s*=\s*\{(.+?)\},?\n", body)
            yr = re.search(r"year\s*=\s*\{?(\d{4})", body)
            names = [a.split(",")[0].strip(" {}") for a in au.group(1).split(" and ")] if au else [key]
            out[key] = (names, yr.group(1) if yr else "n.d.")
    return out


def authors(names):
    if len(names) == 1:
        return names[0]
    if len(names) == 2:
        return f"{names[0]} & {names[1]}"
    return f"{names[0]} et al."


def url_of(key):
    key = key.replace("(", "%28").replace(")", "%29")
    return (BIBURL + key) if not key.startswith("10.") else DOIURL + key



# ---------------------------------------------------------------- cross-references
# In whitepaper.md, "Section 4.2" and "Figure 2A" are MyST cross-references:
# headings carry targets "(sec-4-2)=", and references are links "[Section 4.2](#sec-4-2)",
# "Sections [4.3](#sec-4-3)–[4.5](#sec-4-5)", "[Figure 2A](#fig-rules)". In the doc they are
# plain text; from-docs links them again (figure numbers follow the order of the figures).

NUM = r"\d+(?:\.\d+)?[A-Z]?"
SEP = r"(?:\s*,\s*|\s+and\s+|\s*–\s*|\s+to\s+)"
REF_RE = re.compile(r"\b(Sections?|Figures?)(\s+)(%s(?:%s%s)*)" % (NUM, SEP, NUM))
HEAD_RE = re.compile(r"^(#{2,3}) (\d+(?:\.\d+)?)\.? ", re.M)
XLINK_RE = re.compile(r"\[([^\[\]\n]*)\]\(#(?:sec|fig)-[\w-]+\)")


def sec_label(num):
    return "sec-" + num.replace(".", "-")


def add_section_targets(text):
    out = []
    for line in text.split("\n"):
        m = HEAD_RE.match(line)
        if m and not (out and re.match(r"^\(sec-[\w-]+\)=$", out[-1])):
            out.append("(%s)=" % sec_label(m.group(2)))
        out.append(line)
    return "\n".join(out)


def figure_labels(text):
    """Figure number -> label, in order of the numbered figures."""
    labels, n = {}, 0
    for m in re.finditer(r"^```\{figure\}[^\n]*\n((?::[\w-]+:[^\n]*\n)*)", text, re.M):
        opts = m.group(1)
        if ":enumerated: false" in opts:
            continue
        lab = re.search(r"^:label:\s*(\S+)", opts, re.M)
        n += 1
        if lab:
            labels[str(n)] = lab.group(1)
    return labels


def _link_segment(seg, sections, figs):
    def rep(m):
        kind, space, body = m.group(1), m.group(2), m.group(3)
        parts = re.split("(%s)" % SEP, body)

        def target(tok):
            if kind.startswith("Section"):
                return sec_label(tok) if tok in sections else None
            return figs.get(re.match(r"\d+", tok).group(0))

        if len(parts) == 1:
            t = target(body)
            return "[%s%s%s](#%s)" % (kind, space, body, t) if t else m.group(0)
        out = [kind, space]
        for i, tok in enumerate(parts):
            t = target(tok) if i % 2 == 0 else None
            out.append("[%s](#%s)" % (tok, t) if t else tok)
        return "".join(out)

    return REF_RE.sub(rep, seg)


PROTECT = re.compile(r"(`[^`\n]*`|\[[^\]\n]*\]\([^)\n]*\)|<[^>\n]*>)")


def link_refs(text):
    """Turn plain 'Section 4.2' / 'Figure 2A' into MyST cross-references (idempotent)."""
    sections = {m.group(2) for m in HEAD_RE.finditer(text)}
    figs = figure_labels(text)
    out, fence = [], None
    for line in text.split("\n"):
        st = line.lstrip()
        if fence:
            if st.startswith("```") and st.strip() == "```":
                fence = None
                out.append(line)
                continue
            if fence != "figure" or re.match(r"^:[\w-]+:", st):
                out.append(line)
                continue
        elif st.startswith("```"):
            fence = "figure" if st.startswith("```{figure}") else "code"
            out.append(line)
            continue
        if line.startswith("#") or re.match(r"^\(.*\)=$", line):
            out.append(line)
            continue
        pieces = PROTECT.split(line)
        out.append("".join(p if i % 2 else _link_segment(p, sections, figs) for i, p in enumerate(pieces)))
    return "\n".join(out)


def unlink_refs(text):
    text = re.sub(r"^\(sec-[\w-]+\)=\n", "", text, flags=re.M)
    return XLINK_RE.sub(r"\1", text)

# ---------------------------------------------------------------- MyST -> doc


def cite_to_links(text, lab):
    def one(key, narrative):
        names, year = lab.get(key.lower(), lab.get(key, ([key], "n.d.")))
        t = f"{authors(names)} ({year})" if narrative else f"{authors(names)}, {year}"
        return f"[{t}]({url_of(key)})"

    def rep(m):
        kind, keys = m.group(1), [k.strip() for k in m.group(2).split(";") if k.strip()]
        if kind == "p":
            return "(" + "; ".join(one(k, False) for k in keys) + ")"
        return "; ".join(one(k, True) for k in keys)

    return re.sub(r"\{cite:([pt])\}`([^`]+)`", rep, text)


TAG_RE = re.compile(r"\{raw:latex\}`\\(bPub|bPrep|bHyp|bSpec|tagnote)\{`\{span[^}]*\}`([^`]*)`\{raw:latex\}`\}`")


def tags_to_text(text):
    # a run of badges/notes separated by spaces -> one bracket
    run = re.compile(r"(?:%s)(?:\s+(?:%s))*" % (TAG_RE.pattern, TAG_RE.pattern))

    def rep(m):
        parts = [p.group(2) for p in TAG_RE.finditer(m.group(0))]
        return "[" + "; ".join(parts) + "]"

    return run.sub(rep, text)


def admonitions(lines, lab, boxes):
    """Convert colon-fence admonitions; appendix boxes go to `boxes`."""
    out, i = [], 0
    while i < len(lines):
        m = re.match(r"^(:{3,})\{admonition\}\s*(.*)$", lines[i])
        if not m:
            out.append(lines[i])
            i += 1
            continue
        fence, title = m.group(1), m.group(2).strip()
        j, classes = i + 1, ""
        while j < len(lines) and re.match(r"^:[\w-]+:", lines[j]):
            if lines[j].startswith(":class:"):
                classes = lines[j][len(":class:"):].strip()
            j += 1
        k = j
        while not re.match(r"^%s\s*$" % fence, lines[k]):
            k += 1
        inner = admonitions(lines[j:k], lab, boxes)
        if "appendix" in classes.split():
            boxes.append((title, inner))
            out.append(f"[Box: {title}]")
        else:
            while inner and not inner[0].strip():
                inner.pop(0)
            out.append(f"> **{title}**")
            out.append(">")
            out.extend(("> " + l) if l.strip() else ">" for l in inner)
        i = k + 1
    return out


COLWIDTHS = re.compile(r"\{raw:latex\}`(\\tablecolumns\{[^}\n]*\})`\n\n?(?=(\|[^\n]*))")


def body_to_docs(body, lab, boxes):
    body = COLWIDTHS.sub("", body)
    body = unlink_refs(body)
    lines = admonitions(body.split("\n"), lab, boxes)
    text = "\n".join(lines)
    text = text.replace("```{math}", "```latex")
    text = re.sub(r"\{math\}`([^`]+)`", r"`$\1$`", text)
    text = tags_to_text(text)
    text = cite_to_links(text, lab)
    return text


def to_docs(src, outdir):
    text = Path(src).read_text()
    fm, rest = split_frontmatter(text)
    title = re.search(r'^title:\s*"(.*)"\s*$', fm, re.M).group(1)
    abstract = re.search(r"^abstract: \|\n((?:  .*\n)+)", fm, re.M).group(1)
    abstract = " ".join(l.strip() for l in abstract.splitlines())
    lines = rest.split("\n")
    start = next(i for i, l in enumerate(lines) if l.startswith("## ") or re.match(r"^:{3,}\{admonition\}", l) or re.match(r"^\(sec-[\w-]+\)=$", l))
    end = len(lines)
    while end > 0 and (lines[end - 1].startswith("%") or not lines[end - 1].strip()):
        end -= 1
    lab, boxes = labels(), []
    body = body_to_docs("\n".join(lines[start:end]), lab, boxes)
    main = f"# {title}\n\n*Abstract.* {cite_to_links(abstract, lab)}\n\n{body.strip()}\n"
    box_md = []
    for t, inner in boxes:
        box_md.append(f"## {t}\n")
        box_md.append(body_to_docs("\n".join(inner), lab, []).strip() + "\n")
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "main.md").write_text(main)
    (out / "boxes.md").write_text("# Boxes\n\nAppendix boxes: collapsed dropdowns on the website, appendices in the PDF. "
                                  "Each section below is one box; the main text marks its place with [Box: <title>].\n\n"
                                  + "\n".join(box_md))
    print(f"wrote {out/'main.md'} and {out/'boxes.md'} ({len(boxes)} boxes)")


# ---------------------------------------------------------------- doc -> MyST

# alt-text prefix of an image in the doc -> (figure file, MyST label)
FIGURES = [
    ("The gap and the two-part approach", "figures/gap-schematic.png", "fig-gap"),
    ("Entropic attractor networks: the two rules", "figures/eann-rules.png", "fig-rules"),
    ("Entropic attractor networks fitted to human fMRI", "figures/fcANN.png", "fig-fmri"),
    ("The minimal inferring and learning unit", "figures/unit.png", "fig-unit"),
    ("Emergent properties of entropic attractor networks", "figures/emergent.png", "fig-emergent"),
    ("One model for brains and machines", "figures/overview.*", "fig-lines"),
]


def images_to_figures(text):
    """'[image: alt]' + '***Figure N. Title.*** caption' -> a MyST figure directive."""
    def rep(m):
        alt, cap = m.group(1).strip(), m.group(2).strip()
        hit = next(((f, l) for p, f, l in FIGURES if alt.startswith(p)), None)
        if not hit:
            print(f"warning: no figure file for image {alt!r}")
            return m.group(0)
        cap = re.sub(r"^\*\*\*Figure \d+\.\s*", "***", cap)
        return f"```{{figure}} {hit[0]}\n:label: {hit[1]}\n:alt: {alt}\n:width: 100%\n\n{cap}\n```"

    return re.sub(r"^\\?\[image:\s*(.+?)\\?\]\s*\n\s*\n(\*\*\*Figure \d+\..*)$", rep, text, flags=re.M)


def clean_export(s):
    s = s.replace("&#91;", "[").replace("&#93;", "]").replace("&#32;", " ").replace("&amp;", "&")
    s = s.replace("&lt;", "<").replace("&gt;", ">").replace(" ", " ")
    s = s.replace("****", "")
    return s


LINK = r"\[([^\[\]]+)\]\((%s[^)\s]+|%s[^)\s]+)\)" % (re.escape(DOIURL), re.escape(BIBURL))
LINK_NC = r"\[[^\[\]]+\]\((?:%s|%s)[^)\s]+\)" % (re.escape(DOIURL), re.escape(BIBURL))


def links_to_cite(text):
    def key(url):
        return unquote(url[len(DOIURL):] if url.startswith(DOIURL) else url[len(BIBURL):])

    def grp(m):  # "(link; link)" -> parenthetical
        keys = [key(u) for _, u in re.findall(LINK, m.group(1))]
        return "{cite:p}`" + "; ".join(keys) + "`"

    text = re.sub(r"\((\s*%s(?:\s*;\s*%s)*\s*)\)" % (LINK_NC, LINK_NC), grp, text)

    def narr(m):  # remaining links (with or without "; " between them) -> narrative
        keys = [key(u) for _, u in re.findall(LINK, m.group(0))]
        return "{cite:t}`" + "; ".join(keys) + "`"

    return re.sub(r"%s(?:;\s*%s)*" % (LINK_NC, LINK_NC), narr, text)


def text_to_tags(text):
    def rep(m):
        c = m.group(1)
        if not re.search(TAGWORDS, c):
            return m.group(0)
        out = []
        for p in re.split(r"(%s)" % TAGWORDS, c):
            hit = [(cls, mac) for k, cls, mac in TAGS if k == p]
            if hit:
                cls, mac = hit[0]
                out.append("{raw:latex}`\\%s{`{span .tag .tag-%s}`%s`{raw:latex}`}`" % (mac, cls, p))
            else:
                t = p.strip(" ;,:")
                if t:
                    out.append("{raw:latex}`\\tagnote{`{span .tag-note}`%s`{raw:latex}`}`" % t)
        return " ".join(out)

    text = re.sub(r"\\\[([^\[\]\n]{1,160}?)\\\](?!\()", rep, text)
    return re.sub(r"(?<![\\!])\[([^\[\]\n]{1,160}?)\](?!\()", rep, text)


def quotes_to_admonitions(lines):
    out, i = [], 0
    while i < len(lines):
        if not lines[i].startswith(">"):
            out.append(lines[i])
            i += 1
            continue
        block = []
        while i < len(lines) and lines[i].startswith(">"):
            block.append(lines[i][2:] if lines[i].startswith("> ") else lines[i][1:])
            i += 1
        first = next((x for x in block if x.strip()), "")
        m = re.match(r"^\*\*(.+?)\*\*\s*(.*)$", first)
        title = m.group(1).rstrip(".") if m else "Note"
        if m:
            idx = block.index(first)
            block = block[:idx] + ([m.group(2)] if m.group(2) else []) + block[idx + 1:]
        while block and not block[0].strip():
            block.pop(0)
        out += [f":::{{admonition}} {title}", ":class: note", ""] + block + [":::"]
    return out


def doc_to_myst(text):
    text = clean_export(text)
    text = images_to_figures(text)
    lines = quotes_to_admonitions(text.split("\n"))
    text = "\n".join(lines)
    text = re.sub(r"^```latex\s*$", "```{math}", text, flags=re.M)
    text = re.sub(r"`\$([^$`\n]+?)\$`", r"{math}`\1`", text)
    text = text_to_tags(text)
    text = links_to_cite(text)
    return text


def parse_boxes(text):
    text = clean_export(text)
    boxes, cur, buf = {}, None, []
    for line in text.split("\n"):
        m = re.match(r"^## (.+?)\s*$", line)
        if m:
            if cur:
                boxes[cur] = "\n".join(buf).strip()
            cur, buf = m.group(1), []
        elif cur:
            buf.append(line)
    if cur:
        boxes[cur] = "\n".join(buf).strip()
    return boxes


def restore_colwidths(body, old):
    """Put the PDF column widths of the current file back before matching tables."""
    widths = {m.group(2).strip(): m.group(1) for m in COLWIDTHS.finditer(old)}
    out, prev = [], ""
    for line in body.split("\n"):
        key = line.strip()
        if key in widths and not prev.startswith("|") and "\\tablecolumns" not in "\n".join(out[-3:]):
            if out and out[-1].strip():
                out.append("")
            out += ["{raw:latex}`%s`" % widths[key], ""]
        out.append(line)
        if line.strip():
            prev = line.strip()
    return "\n".join(out)


def from_docs(main_md, boxes_md, dst):
    cur = Path(dst).read_text()
    fm, rest = split_frontmatter(cur)
    lines = rest.split("\n")
    start = next(i for i, l in enumerate(lines) if l.startswith("## ") or re.match(r"^:{3,}\{admonition\}", l) or re.match(r"^\(sec-[\w-]+\)=$", l))
    end = len(lines)
    while end > 0 and (lines[end - 1].startswith("%") or not lines[end - 1].strip()):
        end -= 1
    prelude, postlude = "\n".join(lines[:start]), "\n".join(lines[end:])

    doc = clean_export(Path(main_md).read_text())
    dl = doc.split("\n")
    title = next((l[2:].strip() for l in dl if l.startswith("# ")), None)
    abs_i = next((i for i, l in enumerate(dl) if l.startswith("*Abstract.*")), None)
    abstract = doc_to_myst(dl[abs_i][len("*Abstract.*"):].strip()) if abs_i is not None else None
    first = next(i for i, l in enumerate(dl) if l.startswith("## ") or l.startswith("[Box:") or l.startswith("\\[Box:"))
    body = doc_to_myst("\n".join(dl[first:]))

    boxes = {t: doc_to_myst(b) for t, b in parse_boxes(Path(boxes_md).read_text()).items()} if boxes_md else {}

    def box(m):
        t = m.group(1).strip()
        if t not in boxes:
            print(f"warning: no box titled {t!r} in the Boxes tab")
            return m.group(0)
        return f"::::{{admonition}} {t}\n:class: dropdown appendix\n\n{boxes[t]}\n::::"

    body = re.sub(r"^\\?\[Box:\s*(.+?)\\?\]\s*$", box, body, flags=re.M)
    body = restore_colwidths(body, cur)
    body = link_refs(add_section_targets(body))

    if title:
        fm = re.sub(r'^title:\s*".*"\s*$', "title: " + json.dumps(title, ensure_ascii=False), fm, count=1, flags=re.M)
    if abstract:
        fm = re.sub(r"^abstract: \|\n(?:  .*\n)+", "abstract: |\n  " + abstract.replace("\\", "\\\\") + "\n", fm,
                    count=1, flags=re.M)
    out = fm + prelude.rstrip() + "\n\n" + body.strip() + "\n\n" + postlude.strip() + "\n"
    out = re.sub(r"\n{3,}", "\n\n", out)
    Path(dst).write_text(out)
    print(f"wrote {dst}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "to-docs":
        to_docs(sys.argv[2] if len(sys.argv) > 2 else ROOT / "whitepaper.md",
                sys.argv[3] if len(sys.argv) > 3 else ROOT / "_build" / "docs")
    elif cmd == "from-docs":
        from_docs(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None,
                  sys.argv[4] if len(sys.argv) > 4 else ROOT / "whitepaper.md")
    else:
        print(__doc__)
