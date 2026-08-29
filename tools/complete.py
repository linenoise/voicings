#!/usr/bin/env python3
"""Fill every instrument out to the same chord vocabulary, in every key.

The notebook grew unevenly: the mandolin pages carry twenty-nine kinds of
chord, the guitar pages eighteen, the ukulele twelve, and the banjo three.
That is fine in a notebook you wrote yourself and know your way around, and
useless in a reference someone else picks up mid-song -- if the singer calls
a flat-six major-nine you want it on the page for whatever you are holding.

So: take the union of what the mandolin pages, the piano worksheet and the
core worship voicings use (theory.VOCABULARY), and make sure every
instrument has all of it in all twelve keys. Anything already transcribed
from the notebook is left exactly as it is. Anything missing is generated
from theory and marked `derived: true`, which prints with a dagger.

Slash voicings are skipped for the ukulele: it is re-entrant, so it has no
bass string to put a bass note on.
"""

import argparse
import glob
import os
import sys

import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import theory  # noqa: E402
import generate as gen  # noqa: E402

KEYS = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]
SHARP_KEYS = {"G", "D", "A", "E", "B"}

# "2" is the same chord as "add9"; the notebook writes it both ways and we
# keep whichever it wrote, but we only require one of them.
ALIASES = {"2": "add9", "add2": "add9"}


def required(reentrant=False):
    """(quality, bass_interval or None) pairs every key must carry."""
    out = [(q, None) for q in theory.VOCABULARY]
    if not reentrant:
        out += [(q, b) for q, b in theory.SLASH_FORMS]
    return out


def symbol_for(key, quality, bass_interval):
    flat = key not in SHARP_KEYS
    sym = key + quality.replace("o", "°")
    if bass_interval is not None:
        root = theory.NOTE_TO_PC[key]
        sym += "/" + theory.spell(root + bass_interval, flat)
    return sym


def existing(keyblock):
    """What (quality, bass_pc) pairs this key already has."""
    have = set()
    for entry in keyblock["chords"]:
        try:
            _, q, b = theory.parse_chord(entry["chord"])
        except theory.ChordError:
            continue
        have.add((ALIASES.get(q, q), b))
    return have


def sort_key(entry):
    """Vocabulary order, slash chords last."""
    try:
        _, q, b = theory.parse_chord(entry["chord"])
    except theory.ChordError:
        return (99, 0, entry["chord"])
    q = ALIASES.get(q, q)
    rank = theory.VOCABULARY.index(q) if q in theory.VOCABULARY else 90
    return (rank if b is None else 95, b or 0, entry["chord"])


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data", default="data")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--only", help="just this instrument")
    args = ap.parse_args()

    with open(os.path.join(args.data, "instruments.yaml")) as fh:
        instruments = yaml.safe_load(fh)

    added, failed = [], []

    for path in sorted(glob.glob(os.path.join(args.data, "voicings", "*.yaml"))):
        doc = yaml.safe_load(open(path))
        name = doc["instrument"]
        if args.only and name != args.only:
            continue
        meta = instruments[name]
        if meta.get("kind", "frets") != "frets":
            continue  # the piano is generated wholesale by tools/piano.py
        tuning = meta["tuning"]
        reentrant = bool(meta.get("reentrant"))

        by_key = {k["key"]: k for k in doc["keys"]}
        for key in KEYS:
            block = by_key.get(key)
            if block is None:
                block = {"key": key, "chords": []}
                doc["keys"].append(block)
                by_key[key] = block
            have = existing(block)
            for quality, bass_interval in required(reentrant):
                root = theory.NOTE_TO_PC[key]
                bass_pc = ((root + bass_interval) % 12
                           if bass_interval is not None else None)
                if (quality, bass_pc) in have:
                    continue
                sym = symbol_for(key, quality, bass_interval)
                shape = gen.generate(tuning, sym)
                if shape is None:
                    failed.append((name, key, sym))
                    continue
                block["chords"].append({
                    "chord": sym, "frets": [shape], "derived": True,
                })
                added.append((name, key, sym, shape))

        for block in doc["keys"]:
            block["chords"].sort(key=sort_key)
        doc["keys"].sort(key=lambda b: KEYS.index(b["key"]))

        if args.apply:
            with open(path, "w") as fh:
                fh.write("# %s voicings.\n"
                         "# Entries marked `derived` were generated to complete\n"
                         "# the vocabulary; the rest came from the notebook.\n"
                         % meta["name"])
                yaml.safe_dump(doc, fh, sort_keys=False, allow_unicode=True,
                               width=100)

    counts = {}
    for name, _, _, _ in added:
        counts[name] = counts.get(name, 0) + 1
    for name in sorted(counts):
        print("%-9s +%d generated" % (name, counts[name]))
    for name, key, sym in failed:
        print("CANNOT VOICE: %-9s %-3s %s" % (name, key, sym))
    print("\n%d added, %d could not be voiced" % (len(added), len(failed)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
