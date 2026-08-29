#!/usr/bin/env python3
"""Page count of a PDF, without pulling in a PDF library.

Counts /Type /Page objects, falling back to the /Count in the page tree.
Good enough for a file we produced ourselves a moment ago.
"""

import re
import sys


def count(path):
    with open(path, "rb") as fh:
        data = fh.read()
    pages = len(re.findall(rb"/Type\s*/Page[^s]", data))
    if pages:
        return pages
    counts = [int(m) for m in re.findall(rb"/Count\s+(\d+)", data)]
    return max(counts) if counts else 0


if __name__ == "__main__":
    print(count(sys.argv[1]))
