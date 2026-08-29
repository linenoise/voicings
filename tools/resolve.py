#!/usr/bin/env python3
"""Deal with voicings that survive `repair.py` still failing validation.

By this point the entry could not be brought into line by moving one or two
strings, which means the photograph of the notebook was misread rather than
the notebook being wrong. Guessing further would invent a fingering and
print it as though the author wrote it, so instead:

  * if the chord has another voicing that validates, drop the illegible one
    and keep the good one;
  * if it was the only voicing, substitute a canonical shape from
    tools/generate.py and mark the entry `derived: true`, so it prints with
    a marker and is listed for proofreading.

Either way the entry lands in CORRECTIONS.md.
"""

import argparse
import glob
import os
import sys

import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import theory  # noqa: E402
import generate as gen  # noqa: E402
from validate import check_voicing, ERROR  # noqa: E402


def is_clean(instrument, tuning, key, symbol, frets_text, meta=None):
    """Right notes, and a hand can make it.

    Playability belongs here rather than in the validator's error list: a
    shape that spells correctly but needs five fingers is still wrong for
    a book someone plays from.
    """
    meta = meta or {}
    for f in check_voicing(instrument, tuning, key, symbol, frets_text,
                           meta.get("kind", "frets"),
                           bool(meta.get("reentrant")),
                           meta.get("max_span"), meta.get("max_diagonal")):
        if f.severity == ERROR:
            return False
        if f.message.startswith("hard to finger"):
            return False
    return True


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data", default="data")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--log", default="build/resolved.yaml")
    args = ap.parse_args()

    with open(os.path.join(args.data, "instruments.yaml")) as fh:
        instruments = yaml.safe_load(fh)

    actions = []

    for path in sorted(glob.glob(os.path.join(args.data, "voicings", "*.yaml"))):
        with open(path) as fh:
            doc = yaml.safe_load(fh)
        name = doc["instrument"]
        meta = instruments[name]
        if meta.get("kind", "frets") != "frets":
            continue  # note-based instruments are generated, not transcribed
        tuning = meta["tuning"]
        changed = False

        for keyblock in doc["keys"]:
            for entry in keyblock["chords"]:
                if entry.get("check") is False:
                    continue
                good, bad = [], []
                for t in entry["frets"]:
                    (good if is_clean(name, tuning, keyblock["key"],
                                      entry["chord"], t, meta)
                     else bad).append(t)
                if not bad:
                    continue
                page = keyblock.get("pages", keyblock.get("page"))
                if good:
                    entry["frets"] = good
                    for t in bad:
                        actions.append(dict(
                            instrument=name, page=page, key=keyblock["key"],
                            chord=entry["chord"], written=t, action="dropped",
                            note="unusable as written -- misread, or a shape "
                             "no hand can make; another voicing was kept",
                        ))
                else:
                    made = gen.for_instrument(meta, entry["chord"])
                    entry["frets"] = [made] if made else []
                    entry["derived"] = True
                    actions.append(dict(
                        instrument=name, page=page, key=keyblock["key"],
                        chord=entry["chord"], written=bad[0],
                        action="derived", replacement=made,
                        note="unusable as written and the only voicing "
                             "given; a playable shape was generated",
                    ))
                changed = True

        if args.apply and changed:
            with open(path, "w") as fh:
                fh.write(HEADER.get(name, ""))
                yaml.safe_dump(doc, fh, sort_keys=False,
                               default_flow_style=False, allow_unicode=True,
                               width=100)

    for a in actions:
        print("%-9s %-3s %-9s %-8s %-9s %s"
              % (a["instrument"], a["key"], a["chord"], a["written"],
                 a.get("replacement", "--"), a["action"]))
    print("\n%d entries resolved" % len(actions))

    if args.apply:
        os.makedirs(os.path.dirname(args.log), exist_ok=True)
        with open(args.log, "w") as fh:
            yaml.safe_dump(actions, fh, sort_keys=False, allow_unicode=True)
        append_to_corrections(actions)
    return 0


def append_to_corrections(actions, path="CORRECTIONS.md"):
    """Add this pass's section to the log repair.py started."""
    if not actions:
        return
    dropped = [a for a in actions if a["action"] == "dropped"]
    derived = [a for a in actions if a["action"] == "derived"]
    with open(path, "a") as fh:
        fh.write("\n## Could not be read from the photograph\n\n")
        fh.write("These entries could not be brought into line by moving one"
                 " or two strings, which almost always means the photograph"
                 " of the page was misread rather than the notebook being"
                 " wrong. Guessing further would invent a fingering and print"
                 " it as though it were the author's, so instead:\n\n")
        if dropped:
            fh.write("### Dropped, another voicing of the chord kept\n\n")
            fh.write("| Instrument | Page | Key | Chord | As read |\n")
            fh.write("|---|---|---|---|---|\n")
            for a in dropped:
                fh.write("| %s | %s | %s | `%s` | `%s` |\n"
                         % (a["instrument"], a["page"], a["key"],
                            a["chord"], a["written"]))
            fh.write("\n")
        if derived:
            fh.write("### Replaced with a generated shape\n\n")
            fh.write("The only voicing given, so a canonical fingering was"
                     " generated from theory. These are the ones worth"
                     " checking against the paper notebook first.\n\n")
            fh.write("| Instrument | Page | Key | Chord | As read | Printed |\n")
            fh.write("|---|---|---|---|---|---|\n")
            for a in derived:
                fh.write("| %s | %s | %s | `%s` | `%s` | `%s` |\n"
                         % (a["instrument"], a["page"], a["key"],
                            a["chord"], a["written"], a["replacement"]))
            fh.write("\n")


HEADER = {
    "mandolin": "# Mandolin voicings, from the notebook (pages 1-24).\n"
                "# Fret digits low string first: G D A E.\n"
                "# Rewritten by tools/resolve.py -- see CORRECTIONS.md.\n",
    "guitar": "# Guitar voicings, from the notebook (pages 25-36).\n"
              "# Fret digits low string first: E A D G B E.\n"
              "# Rewritten by tools/resolve.py -- see CORRECTIONS.md.\n",
    "ukulele": "# Ukulele voicings, from the notebook (pages 37-42).\n"
               "# Fret digits 4th string first: G C E A.\n"
               "# Rewritten by tools/resolve.py -- see CORRECTIONS.md.\n",
    "banjo": "# Banjo voicings, from the notebook (page 43).\n"
             "# Fret digits low string first: D G B D (drone handled apart).\n"
             "# Rewritten by tools/resolve.py -- see CORRECTIONS.md.\n",
}

if __name__ == "__main__":
    sys.exit(main())
