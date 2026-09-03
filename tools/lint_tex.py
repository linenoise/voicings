#!/usr/bin/env python3
"""Check the generated LaTeX against the class before handing it to TeX.

LaTeX's failure mode for a typo'd macro is a wall of noise a hundred lines
after the real problem, so it is worth catching here: every command and
environment build/body.tex uses must be defined in tex/voicings.cls or be
a LaTeX primitive we expect.
"""

import re
import sys

PRIMITIVES = {
    "begin", "end", "input", "documentclass", "usepackage", "par", "vfill",
    "vspace", "hfill", "clearpage", "newpage", "textbackslash", "flat",
    "sharp", "natural", "quad", "qquad", "textsuperscript", "footnotesize",
    "scriptsize", "tiny", "small", "large", "Large", "bfseries", "itshape",
    "ttfamily", "color", "textbf", "textit", "makebox", "null", "item",
    "hrule", "rule", "linewidth", "href", "dagger", "cdot", "protect",
    "relax", "space", "thispagestyle", "pagestyle", "hline", "smaller",
    "rightarrow", "flat", "sharp", "bigstar", "dag",
    "hskip", "kern", "hbox", "vbox", "hsize", "smash", "nobreak",
    "allowbreak", "rlap", "llap", "hfil", "raisebox", "textcolor",
    "centerline", "nointerlineskip",
}


def defined_in(path):
    text = open(path).read()
    cmds = set(re.findall(
        r"\\(?:newcommand|renewcommand|providecommand)\s*\{?\\(\w+)", text))
    envs = set(re.findall(r"\\newenvironment\s*\{(\w+)\}", text))
    cmds |= set(re.findall(r"\\newlength\{\\(\w+)\}", text))
    cmds |= set(re.findall(r"\\def\\(\w+)", text))
    return cmds, envs


def used_in(path):
    text = open(path).read()
    text = re.sub(r"(?m)^\s*%.*$", "", text)
    envs = set(re.findall(r"\\begin\{(\w+)\}", text))
    envs |= set(re.findall(r"\\end\{(\w+)\}", text))
    cmds = set(re.findall(r"\\([A-Za-z@]+)", text))
    return cmds, envs


def main():
    cls, body = "tex/voicings.cls", "build/body.tex"
    dc, de = defined_in(cls)
    uc, ue = used_in(body)

    missing_cmds = sorted(uc - dc - PRIMITIVES - de - {"begin", "end"})
    missing_envs = sorted(ue - de - {"center", "tabular", "list", "tikzpicture"})

    for name in missing_envs:
        print("UNDEFINED ENVIRONMENT: %s" % name)
    for name in missing_cmds:
        print("UNDEFINED COMMAND: \\%s" % name)

    # And the reverse: macros the class defines that nothing uses. Not an
    # error, but dead code in a document class is worth knowing about.
    unused = sorted((dc | de) - uc - ue)
    unused = [u for u in unused if not u.startswith(("cof@", "banjo@",
                                                     "nameplate@", "book",
                                                     "voicings@"))]
    if unused:
        print("\nunused in the class (fine, but note): %s"
              % ", ".join(unused))

    total = len(missing_cmds) + len(missing_envs)
    print("\n%d undefined, %d commands and %d environments defined"
          % (total, len(dc), len(de)))
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
