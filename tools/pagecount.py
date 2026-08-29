#!/usr/bin/env python3
"""Page count of a PDF.

XeLaTeX writes object streams, so the page tree is compressed and cannot be
found by reading the file as text. Prefer a real tool when one is around --
poppler's pdfinfo, mutool, or Ghostscript -- and fall back to the text scan
for uncompressed PDFs.
"""

import re
import subprocess
import sys


def _from_pdfinfo(path):
    out = subprocess.check_output(["pdfinfo", path],
                                  stderr=subprocess.DEVNULL).decode()
    m = re.search(r"^Pages:\s+(\d+)", out, re.M)
    return int(m.group(1)) if m else None


def _from_mutool(path):
    out = subprocess.check_output(["mutool", "info", path],
                                  stderr=subprocess.DEVNULL).decode()
    m = re.search(r"Pages:\s+(\d+)", out)
    return int(m.group(1)) if m else None


def _from_ghostscript(path):
    out = subprocess.check_output(
        ["gs", "-q", "-dNODISPLAY", "-dNOSAFER", "-c",
         "(%s) (r) file runpdfbegin pdfpagecount = quit" % path],
        stderr=subprocess.DEVNULL).decode()
    return int(out.strip().split()[-1])


def _from_text(path):
    with open(path, "rb") as fh:
        data = fh.read()
    pages = len(re.findall(rb"/Type\s*/Page[^s]", data))
    if pages:
        return pages
    counts = [int(m) for m in re.findall(rb"/Count\s+(\d+)", data)]
    return max(counts) if counts else None


def count(path):
    for probe in (_from_pdfinfo, _from_mutool, _from_ghostscript, _from_text):
        try:
            n = probe(path)
        except Exception:
            continue
        if n:
            return n
    raise RuntimeError("could not determine the page count of %s" % path)


if __name__ == "__main__":
    print(count(sys.argv[1]))
