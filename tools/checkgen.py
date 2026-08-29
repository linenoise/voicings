#!/usr/bin/env python3
"""Score the generator against the voicings in the notebook.

The notebook is the ground truth here: every shape in it was chosen by a
player, on the instrument, for use. So for each chord the notebook gives,
ask the generator for the same chord and see what it says. Where the two
agree, the generator is picking shapes a person would pick. Where they
differ, the question is whether it picked something *harder* -- which is a
bug in the ranking -- or merely something different, which is taste.

Difficulty is the generator's own measure: how far up the neck, how many
fingers, how many strings given up.

    tools/checkgen.py            summary per instrument
    tools/checkgen.py --worst 20 the biggest disagreements
"""

import argparse
import glob
import os
import sys

import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import theory  # noqa: E402
import playability  # noqa: E402
import generate as gen  # noqa: E402


def difficulty(frets, n_strings):
    fretted = [f for f in frets if f]
    position = min(fretted) if fretted else 0
    muted = sum(1 for f in frets if f is None)
    return position + playability.fingers_needed(frets) + 2 * muted


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--worst", type=int, default=0)
    ap.add_argument("--unplayable", action="store_true",
                    help="list notebook shapes the model calls unplayable")
    args = ap.parse_args()

    instruments = yaml.safe_load(open("data/instruments.yaml"))
    rows = []

    for path in sorted(glob.glob("data/voicings/*.yaml")):
        doc = yaml.safe_load(open(path))
        name = doc["instrument"]
        meta = instruments[name]
        if meta.get("kind", "frets") != "frets":
            continue
        n = len(meta["tuning"])
        for keyblock in doc["keys"]:
            for entry in keyblock["chords"]:
                if entry.get("derived"):
                    continue          # only judge against the notebook
                for text in entry["frets"][:1]:   # the one they reach for
                    try:
                        book = theory.parse_frets(text, n)
                    except theory.ChordError:
                        continue
                    made = gen.for_instrument(meta, entry["chord"])
                    if made is None:
                        rows.append((name, entry["chord"], text, None, 0, 0))
                        continue
                    mine = theory.parse_frets(made, n)
                    rows.append((name, entry["chord"], text, made,
                                 difficulty(book, n), difficulty(mine, n)))

    per = {}
    for name, chord, book, made, db, dm in rows:
        s = per.setdefault(name, {"n": 0, "same": 0, "easier": 0,
                                  "harder": 0, "none": 0, "gap": 0})
        s["n"] += 1
        if made is None:
            s["none"] += 1
        elif made == book:
            s["same"] += 1
        elif dm < db:
            s["easier"] += 1
        elif dm > db:
            s["harder"] += 1
            s["gap"] += dm - db
        else:
            s["easier"] += 1      # different, equally easy: taste

    print("%-9s %5s %7s %8s %8s %6s   %s"
          % ("INSTR", "chords", "same", "as easy", "harder", "none",
             "avg harder by"))
    for name in sorted(per):
        s = per[name]
        avg = (s["gap"] / s["harder"]) if s["harder"] else 0
        print("%-9s %5d %6d%% %7d%% %7d%% %6d   %.1f"
              % (name, s["n"], 100 * s["same"] // s["n"],
                 100 * s["easier"] // s["n"], 100 * s["harder"] // s["n"],
                 s["none"], avg))

    if args.worst:
        print("\nwhere the generator picks something harder than the book:")
        bad = sorted((r for r in rows if r[3] and r[5] > r[4]),
                     key=lambda r: r[4] - r[5])
        for name, chord, book, made, db, dm in bad[:args.worst]:
            print("  %-9s %-9s book %-8s (%2d)   generated %-8s (%2d)"
                  % (name, chord, book, db, made, dm))

    if args.unplayable:
        print("\nnotebook shapes the playability model rejects:")
        for path in sorted(glob.glob("data/voicings/*.yaml")):
            doc = yaml.safe_load(open(path))
            meta = instruments[doc["instrument"]]
            if meta.get("kind", "frets") != "frets":
                continue
            n = len(meta["tuning"])
            for kb in doc["keys"]:
                for e in kb["chords"]:
                    if e.get("derived"):
                        continue
                    for t in e["frets"]:
                        f = theory.parse_frets(t, n)
                        why = playability.unplayable_reason(
                            f, meta["max_span"], 4, meta["max_diagonal"])
                        if why:
                            print("  %-9s %-9s %-8s %s"
                                  % (doc["instrument"], e["chord"], t, why))
    return 0


if __name__ == "__main__":
    sys.exit(main())
