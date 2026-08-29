#!/usr/bin/env python3
"""Build every edition: the whole book, and one per instrument.

Fourteen PDFs come out of this -- a screen and a print edition of the full
book, and of each of the six instruments. The per-instrument editions carry
that instrument's cover, its circle of fifths, its chord pages and the
credits, and nothing else: someone who only plays ukulele should not have
to carry ninety pages to find a chord.

The files are given their display names ("Fancy Mandolin Chords and Their
Voicings.pdf") only at the last step. Everything before that uses safe
names, because a space in a filename is a fight with make, with latexmk,
and with every shell in between.
"""

import argparse
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import pagecount  # noqa: E402
import impose as impose_mod  # noqa: E402

INSTRUMENTS = ["mandolin", "guitar", "ukulele", "piano", "banjo", "bass"]
TITLES = {
    "mandolin": "Fancy Mandolin Chords and Their Voicings",
    "guitar":   "Fancy Guitar Chords and Their Voicings",
    "ukulele":  "Fancy Ukulele Chords and Their Voicings",
    "piano":    "Fancy Piano Chords and Their Voicings",
    "banjo":    "Fancy Banjo Chords and Their Voicings",
    "bass":     "Fancy Bass Chords and Their Voicings",
    None:       "Fancy Chords and Their Voicings",
}

LATEX = "xelatex"
OPTS = ["-interaction=nonstopmode", "-halt-on-error"]


def run(cmd, cwd):
    subprocess.run(cmd, cwd=cwd, check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def build_one(build, slug, only):
    """Render, typeset and impose one edition. Returns (screen, print)."""
    body = os.path.join(build, "body-%s.tex" % slug)
    render = [sys.executable, os.path.join(HERE, "render.py"), "--out", body]
    if only:
        render += ["--only", only]
    subprocess.run(render, cwd=ROOT, check=True, stdout=subprocess.DEVNULL)

    # screen.tex reads "body"; give each edition its own copy to input.
    shutil.copy(os.path.join(ROOT, "tex", "voicings.cls"), build)
    with open(os.path.join(build, "screen-%s.tex" % slug), "w") as fh:
        fh.write("\\documentclass[screen]{voicings}\n"
                 "\\begin{document}\\input{body-%s}\\end{document}\n" % slug)

    screen = "screen-%s" % slug
    for _ in range(2):
        run([LATEX] + OPTS + ["-jobname", screen, screen + ".tex"], build)
    screen_pdf = os.path.join(build, screen + ".pdf")

    pages = pagecount.count(screen_pdf)
    order = impose_mod.flat_order(pages)
    problems = impose_mod.verify_flat(pages)
    if problems:
        raise SystemExit("imposition error in %s: %s" % (slug, problems[0]))
    with open(os.path.join(build, "impose-%s.tex" % slug), "w") as fh:
        fh.write(impose_mod.TEMPLATE % dict(
            description=impose_mod.DESCRIPTIONS["flat"],
            n_pages=pages, n_sheets=len(order) // impose_mod.PER_SHEET,
            pages=",".join("{}" if p is None else str(p) for p in order),
            source=screen + ".pdf", frame="false"))
    printed = "print-%s" % slug
    run([LATEX] + OPTS + ["-jobname", printed, "impose-%s.tex" % slug], build)
    return screen_pdf, os.path.join(build, printed + ".pdf"), pages


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--build", default="build")
    ap.add_argument("--out", default="editions")
    args = ap.parse_args()

    build = os.path.join(ROOT, args.build)
    out = os.path.join(ROOT, args.out)
    os.makedirs(build, exist_ok=True)
    os.makedirs(out, exist_ok=True)

    rows = []
    for only in [None] + INSTRUMENTS:
        slug = only or "all"
        screen_pdf, print_pdf, pages = build_one(build, slug, only)
        title = TITLES[only]
        s_name = "%s.pdf" % title
        p_name = "%s (print).pdf" % title
        shutil.copy(screen_pdf, os.path.join(out, s_name))
        shutil.copy(print_pdf, os.path.join(out, p_name))
        sheets = pagecount.count(print_pdf) // 2
        rows.append((only, title, s_name, p_name, pages, sheets))
        print("%-9s %3d pages, %2d sheets   %s" % (slug, pages, sheets, title))

    return rows


if __name__ == "__main__":
    main()
