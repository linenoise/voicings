#!/usr/bin/env python3
"""Compare pages the renderer intended against pages TeX actually produced.

Every page in this book starts with an explicit \\clearpage, so the two
numbers should match. When the PDF has more pages than the body has page
starts, some page's content overflowed and spilled onto a continuation with
no heading on it -- which looks like a mistake to a reader, and is one.

Reports the difference so the per-page row counts in tools/render.py can be
tuned down until it reaches zero.
"""

import re
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pagecount  # noqa: E402

# Every environment and command that opens with a \clearpage.
STARTERS = [r"\begin{bookpage}", r"\begin{chordpage}", r"\begin{pianopage}",
            r"\begin{circlepage}", r"\begin{backsheet}", r"\sectiondivider"]


def main():
    body = open(sys.argv[1] if len(sys.argv) > 1 else "build/body.tex").read()
    pdf = sys.argv[2] if len(sys.argv) > 2 else "build/voicings-screen.pdf"
    # The cover \clearpage's itself; everything else is in STARTERS.
    expected = sum(body.count(s) for s in STARTERS) + 1
    actual = pagecount.count(pdf)
    print("body.tex declares %d pages; %s has %d" % (expected, pdf, actual))
    if actual > expected:
        print("%d page(s) overflowed -- reduce rows per page in render.py"
              % (actual - expected))
        return 1
    print("no overflow")
    return 0


if __name__ == "__main__":
    sys.exit(main())
