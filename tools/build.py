#!/usr/bin/env python3
"""Build the white paper as a website (default) or as a PDF.

The source, whitepaper.md, is written for the website: long reference material
sits in collapsed dropdown admonitions marked with the class "appendix":

    ::::{admonition} Setting, notation and the assumption–result map
    :class: dropdown appendix
    ...
    ::::

For the PDF, this script writes a transformed copy into _build/pdf/ in which
  * every "appendix" admonition is moved to the end of the document as
    "Appendix A: <title>", "Appendix B: <title>", ... (in order of appearance);
  * every mention of such a box in the text, written as the italic title
    (*<title>*), becomes "Appendix X (*<title>*)"; a box that is not
    mentioned anywhere leaves a short pointer at its original place;
  * the author name "White Paper by <name>" (used on the website, where it
    tells readers what the page is) becomes just "<name>".
It then runs `myst build --pdf` there and copies the result to
exports/whitepaper.pdf. The source files are never modified.

Usage:
    python3 tools/build.py            # live website preview (myst start)
    python3 tools/build.py html       # static website in _build/html
    python3 tools/build.py pdf        # PDF -> exports/whitepaper.pdf
    python3 tools/build.py all        # PDF, then website with the PDF in it
    python3 tools/build.py pdf --prepare-only   # write _build/pdf/ only
"""

import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = "whitepaper.md"
PDF_DIR = ROOT / "_build" / "pdf"  # inside _build, which MyST ignores
PDF_OUT = Path("exports") / "whitepaper.pdf"
COPY = ["myst.yml", "references.bib", "style.css", "figures", "_templates"]

OPEN = re.compile(r"^(:{3,})\{([\w-]+)\}\s*(.*)$")
CLOSE = re.compile(r"^(:{3,})\s*$")
OPTION = re.compile(r"^:([\w-]+):\s*(.*)$")


def find_appendix_blocks(lines):
    """Return (start, end, title, body_lines) for top-level appendix admonitions."""
    blocks, stack = [], []
    in_code = False
    for i, line in enumerate(lines):
        if line.lstrip().startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        m = OPEN.match(line)
        if m:
            stack.append((i, len(m.group(1)), m.group(2), m.group(3).strip()))
            continue
        m = CLOSE.match(line)
        if m and stack:
            start, ncol, name, title = stack.pop()
            if len(m.group(1)) < ncol:  # not the closing fence of this block
                stack.append((start, ncol, name, title))
                continue
            if stack or name != "admonition":
                continue
            j, classes = start + 1, ""
            while j < i and OPTION.match(lines[j]):
                opt = OPTION.match(lines[j])
                if opt.group(1) == "class":
                    classes = opt.group(2)
                j += 1
            if "appendix" in classes.split():
                blocks.append((start, i, title, lines[j:i]))
    return blocks


def to_pdf_markdown(text):
    lines = text.split("\n")
    blocks = find_appendix_blocks(lines)
    letters = [chr(ord("A") + k) for k in range(len(blocks))]
    removed = set()
    marker = {}
    for (start, end, title, _), letter in zip(blocks, letters):
        removed.update(range(start, end + 1))
        marker[start] = f"@@APPENDIX-{letter}@@"

    out = []
    for i, line in enumerate(lines):
        if i in marker:
            out.append(marker[i])
        if i not in removed:
            out.append(line)
    body = "\n".join(out)

    for (_, _, title, _), letter in zip(blocks, letters):
        mention = f"*{title}*"
        tag = f"@@APPENDIX-{letter}@@"
        if mention in body:
            body = body.replace(mention, f"Appendix {letter} ({mention})")
            body = body.replace(tag + "\n", "")
        else:
            body = body.replace(tag, f"See Appendix {letter}: {mention}.\n")

    appendix = []
    for (_, _, title, inner), letter in zip(blocks, letters):
        appendix.append(f"\n## Appendix {letter}. {title}\n")
        appendix.extend(inner)
    body = body.rstrip() + "\n" + "\n".join(appendix) + "\n"
    body = re.sub(r"\n{3,}", "\n\n", body)
    return body, [(l, b[2]) for l, b in zip(letters, blocks)]


def pdf_myst_yml(text):
    return re.sub(r"(name:\s*)White Paper by\s+", r"\1", text)


def run(cmd, cwd):
    print("$", " ".join(cmd), f"(in {cwd})", flush=True)
    return subprocess.call(cmd, cwd=cwd)


def prepare_pdf():
    if PDF_DIR.exists():  # keep _build (DOI cache), refresh everything else
        for item in PDF_DIR.iterdir():
            if item.name != "_build":
                shutil.rmtree(item) if item.is_dir() else item.unlink()
    PDF_DIR.mkdir(exist_ok=True)
    for name in COPY:
        src = ROOT / name
        if src.is_dir():
            shutil.copytree(src, PDF_DIR / name, dirs_exist_ok=True)
        elif src.exists():
            shutil.copy2(src, PDF_DIR / name)
    main_cache = ROOT / "_build" / "cache"
    if main_cache.exists():
        shutil.copytree(main_cache, PDF_DIR / "_build" / "cache", dirs_exist_ok=True)
    (PDF_DIR / "myst.yml").write_text(pdf_myst_yml((ROOT / "myst.yml").read_text()))
    md, apps = to_pdf_markdown((ROOT / SOURCE).read_text())
    (PDF_DIR / SOURCE).write_text(md)
    for letter, title in apps:
        print(f"  Appendix {letter}: {title}")
    print(f"Prepared {PDF_DIR.relative_to(ROOT)}/")


def build_pdf():
    prepare_pdf()
    code = run(["myst", "build", "--pdf"], PDF_DIR)
    built = PDF_DIR / PDF_OUT
    if code != 0 or not built.exists():
        print("PDF build failed. LaTeX log, if any: _build/pdf/_build/temp/*/whitepaper.log")
        return code or 1
    (ROOT / PDF_OUT).parent.mkdir(exist_ok=True)
    shutil.copy2(built, ROOT / PDF_OUT)
    cache = PDF_DIR / "_build" / "cache"
    if cache.exists():
        shutil.copytree(cache, ROOT / "_build" / "cache", dirs_exist_ok=True)
    print(f"Wrote {PDF_OUT}")
    return 0


def main(argv):
    target = argv[1] if len(argv) > 1 else "start"
    if target == "start":
        return run(["myst", "start"], ROOT)
    if target == "html":
        return run(["myst", "build", "--html"], ROOT)
    if target == "pdf":
        if "--prepare-only" in argv:
            prepare_pdf()
            return 0
        return build_pdf()
    if target == "all":
        code = build_pdf()
        if code:
            return code
        code = run(["myst", "build", "--html"], ROOT)
        if code == 0:
            shutil.copy2(ROOT / PDF_OUT, ROOT / "_build" / "html" / "whitepaper.pdf")
        return code
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
