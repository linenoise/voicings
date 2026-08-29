#!/usr/bin/env python3
"""Restore data/voicings/ to what was transcribed from the notebook.

CORRECTIONS.md and build/resolved.yaml both record the value originally
read off the page, so the whole correction pass can be replayed from
scratch after changing how repair.py scores a fix. Without this, tuning
the repair heuristics would mean re-transcribing the photographs.
"""

import glob
import os
import re
import sys

import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import theory  # noqa: E402

ROW = re.compile(
    r"^\|\s*(\w+)\s*\|[^|]*\|\s*(\S+)\s*\|\s*`([^`]+)`\s*\|"
    r"\s*`([^`]+)`\s*\|\s*`([^`]+)`\s*\|")


def originals():
    """(instrument, key, chord, printed) -> notebook value."""
    out = {}
    if os.path.exists("CORRECTIONS.md"):
        for line in open("CORRECTIONS.md"):
            m = ROW.match(line.strip())
            if m:
                inst, key, chord, was, now = m.groups()
                out[(inst, key, chord, now)] = was
    path = "build/resolved.yaml"
    if os.path.exists(path):
        for a in yaml.safe_load(open(path)) or []:
            now = a.get("replacement")
            out[(a["instrument"], a["key"], a["chord"], now)] = a["written"]
            if a["action"] == "dropped":
                out.setdefault(
                    ("+drop", a["instrument"], a["key"], a["chord"]), []
                ).append(a["written"])
    return out


def main():
    table = originals()
    restored = 0
    instruments = yaml.safe_load(open("data/instruments.yaml"))
    for path in sorted(glob.glob("data/voicings/*.yaml")):
        doc = yaml.safe_load(open(path))
        inst = doc["instrument"]
        if instruments[inst].get("kind", "frets") != "frets":
            continue
        for keyblock in doc["keys"]:
            for entry in keyblock["chords"]:
                new, changed = [], False
                for f in entry["frets"]:
                    was = table.get((inst, keyblock["key"], entry["chord"], f))
                    new.append(was if was else f)
                    if was:
                        restored += 1
                        changed = True
                back = table.get(("+drop", inst, keyblock["key"],
                                  entry["chord"]), [])
                for f in back:
                    if f not in new:
                        new.append(f)
                        restored += 1
                        changed = True
                entry["frets"] = new
                if changed:
                    entry.pop("derived", None)
        with open(path, "w") as fh:
            fh.write("# Restored by tools/revert.py to the transcription.\n")
            yaml.safe_dump(doc, fh, sort_keys=False, allow_unicode=True,
                           width=100)
    print("restored %d voicings to their transcribed values" % restored)
    return 0


if __name__ == "__main__":
    sys.exit(main())
