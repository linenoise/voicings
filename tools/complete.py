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
from theory and marked `derived: true` in the data. The book itself
does not mark them: a player wants the chord, not its provenance.

Slash voicings are skipped for the ukulele: it is re-entrant, so it has no
bass string to put a bass note on.
"""

import argparse
import glob
import os
import sys

import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import playability
import theory  # noqa: E402
import generate as gen  # noqa: E402
import provenance  # noqa: E402

KEYS = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]
SHARP_KEYS = {"G", "D", "A", "E", "B"}

# "2" is the same chord as "add9"; the notebook writes it both ways and we
# keep whichever it wrote, but we only require one of them.
ALIASES = {"2": "add9", "add2": "add9"}


def required(reentrant=False, extra=()):
    """(quality, bass_interval or None) pairs every key must carry.

    Slash chords are included for the ukulele too. It is re-entrant, so it
    cannot put any note in the bass -- but the shape that contains the note
    is what gets played regardless, and leaving the ukulele short of chords
    the other instruments have is worse than labeling an inversion.
    """
    return ([(q, None) for q in theory.VOCABULARY]
            + [(q, None) for q in extra]
            + list(theory.SLASH_FORMS))


def rooted_variant(meta, symbol, shape):
    """The same chord again with its root underneath, where that differs.

    The ranked search treats the root in the bass as a preference, which
    is right: it is what keeps Gb7#5 out of the eleventh fret. But the
    shape it settles on is sometimes not the one anyone plays. Guitar C9
    came out 0-1-0-0-1-0, every tone present, when the shape a guitarist
    means by C9 is x-3-0-3-1-0.

    Rather than choose between them, print both. The open one is easier
    and the rooted one is the movable form, and which you want depends on
    what you are playing.
    """
    if "root_variants" not in meta or not meta["root_variants"]:
        return None
    tuning = meta["tuning"]
    root, quality, bass_pc = theory.parse_chord(symbol)
    if bass_pc is not None:
        return None
    frets = theory.parse_frets(shape, len(tuning))
    lowest = next(((theory.parse_note(t) + f) % 12
                   for t, f in zip(tuning, frets) if f is not None), None)
    if lowest == root:
        return None
    alt = gen.generate(tuning, symbol, max_span=meta.get("max_span", 4),
                       max_diagonal=meta.get("max_diagonal"),
                       require_bass_lowest=True)
    if not alt or alt == shape:
        return None
    # Hold the variant to the plain span, without the wider allowance a
    # diagonal shape gets. That allowance is meant for a shape with one
    # finger per string climbing across the neck; any two-note shape is
    # trivially monotonic and collects it by accident, which offered
    # 8-0-0-0-3-0 for C6/9, a five-fret reach for two fingers.
    if playability.span(theory.parse_frets(alt, len(tuning))) > \
            meta.get("max_span", 4):
        return None
    return alt


def symbol_for(key, quality, bass_interval):
    flat = key not in SHARP_KEYS
    sym = key + quality.replace("o", "°")
    if bass_interval is not None:
        root = theory.NOTE_TO_PC[key]
        # Spell the bass by its function where that is readable. G minor's
        # third is Bb, never A#, and a chord symbol that says A# under a Gm
        # reads as a mistake. The functional spelling is not always usable
        # though: the third of Gbm is Bbb, and the third of Dbm is Fb. A
        # double accidental, or a flat named onto a white key, costs more
        # in confusion than the wrong letter does, so those keep the plain
        # enharmonic.
        JARRING = {"Fb", "Cb", "E#", "B#"}
        functional = theory.spell_in_key(key, bass_interval, quality)
        plain = theory.spell(root + bass_interval, flat)
        usable = ("bb" not in functional and "##" not in functional
                  and functional not in JARRING)
        sym += "/" + (functional if usable else plain)
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
    ap.add_argument("--refresh", action="store_true",
                    help="regenerate every derived entry, not just missing "
                         "ones -- use after changing how generate.py ranks")
    args = ap.parse_args()

    with open(os.path.join(args.data, "instruments.yaml")) as fh:
        instruments = yaml.safe_load(fh)
    record = provenance.load_record()

    added, failed, deduped = [], [], []

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
            if args.refresh:
                # Judge by the frozen record, not by the flag: the flag has
                # been lost more than once and stale shapes then survived.
                block["chords"] = [
                    c for c in block["chords"]
                    if provenance.from_notebook(record, name, key, c["chord"])
                ]
            have = existing(block)
            for quality, bass_interval in required(
                    extra=meta.get("extra_vocabulary", ())):
                root = theory.NOTE_TO_PC[key]
                bass_pc = ((root + bass_interval) % 12
                           if bass_interval is not None else None)
                if (quality, bass_pc) in have:
                    continue
                sym = symbol_for(key, quality, bass_interval)
                shape = gen.for_instrument(meta, sym)
                if shape is None:
                    failed.append((name, key, sym))
                    continue
                shapes = [shape]
                alt = rooted_variant(meta, sym, shape)
                if alt is not None:
                    shapes.append(alt)
                block["chords"].append({
                    "chord": sym, "frets": shapes, "derived": True,
                })
                added.append((name, key, sym, shape))

        for block in doc["keys"]:
            # A chord listing the same fingering twice reads as a mistake.
            for entry in block["chords"]:
                seen, unique = set(), []
                for t in entry["frets"]:
                    if t not in seen:
                        unique.append(t)
                        seen.add(t)
                if len(unique) != len(entry["frets"]):
                    deduped.append((name, block["key"], entry["chord"]))
                entry["frets"] = unique
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
    for name, key, chord in deduped:
        print("DEDUPED: %-9s %-3s %s" % (name, key, chord))
    print("\n%d added, %d deduplicated, %d could not be voiced"
          % (len(added), len(deduped), len(failed)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
