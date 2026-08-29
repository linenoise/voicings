#!/usr/bin/env python3
"""Propose a correction for every voicing the validator rejects.

For each failing voicing, search the neighbourhood of what is written for
the closest fingering that actually spells the chord, and is playable.
"Closest" is deliberately conservative, in this priority order:

  1. fewest strings changed
  2. smallest total movement in frets
  3. narrowest stretch
  4. lowest position on the neck

A one-digit fix is almost always the intended shape -- either a slip in the
notebook or a slip reading the photograph of it. Anything needing three or
more changes is reported but NOT applied, because at that distance the
search is guessing rather than repairing; those go on the proofreading list.

Usage:
    tools/repair.py                 # report only
    tools/repair.py --apply         # rewrite data/voicings/*.yaml in place
    tools/repair.py --max-changes 2 # how far a fix may reach (default 2)
"""

import argparse
import glob
import itertools
import os
import sys

import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import theory  # noqa: E402
from validate import check_voicing, ERROR, WARNING  # noqa: E402

MAX_SPAN = 4          # frets a hand comfortably covers
FRET_WINDOW = 4       # how far a single string may be moved
MAX_FRET = 12


def is_clean(instrument, tuning, key, symbol, frets_text):
    return not any(
        f.severity == ERROR
        for f in check_voicing(instrument, tuning, key, symbol, frets_text)
    )


def incompleteness(instrument, tuning, key, symbol, frets_text):
    """How many defining tones a candidate leaves out.

    Without this the search happily "fixes" a seventh chord by deleting its
    seventh: dropping the note makes the error go away and costs only one
    string. The result spells nothing wrong and is useless -- in a chord
    book, A7 and A must not be the same grip. So a candidate that spells the
    whole chord always beats one that doesn't, however far it has to reach.
    """
    return sum(
        1 for f in check_voicing(instrument, tuning, key, symbol, frets_text)
        if f.severity == WARNING
    )


def render(frets):
    out = []
    for f in frets:
        if f is None:
            out.append("x")
        elif f > 9:
            out.append("[%d]" % f)
        else:
            out.append(str(f))
    return "".join(out)


def playable(frets):
    fretted = [f for f in frets if f]
    if not fretted:
        return False
    if max(fretted) > MAX_FRET:
        return False
    if max(fretted) - min(fretted) > MAX_SPAN:
        return False
    return True


MUTE_PENALTY = 6  # silencing a string is a bigger change than moving it


def cost(original, candidate):
    changed = sum(1 for a, b in zip(original, candidate) if a != b)
    movement = 0
    for a, b in zip(original, candidate):
        if a is None or b is None:
            # Muting a string that rang, or ringing one that was muted, is
            # a real change to the sound of the chord -- not a free move to
            # fret zero, which is what treating None as 0 would imply.
            movement += 0 if a == b else MUTE_PENALTY
        else:
            movement += abs(a - b)
    fretted = [f for f in candidate if f]
    span = (max(fretted) - min(fretted)) if fretted else 0
    position = min(fretted) if fretted else 0
    return (changed, movement, span, position)


def candidates_for(position, current):
    """Fret values to try on one string."""
    base = current if current is not None else 0
    lo = max(0, base - FRET_WINDOW)
    hi = min(MAX_FRET, base + FRET_WINDOW)
    vals = list(range(lo, hi + 1))
    vals.append(None)  # muting is always an option
    return vals


def repair(instrument, tuning, key, symbol, frets_text, max_changes):
    """Return (best_frets_text, n_changed) or (None, None)."""
    n = len(tuning)
    try:
        original = theory.parse_frets(frets_text, n)
    except theory.ChordError:
        return None, None

    best = None
    for k in range(1, max_changes + 1):
        for positions in itertools.combinations(range(n), k):
            options = [candidates_for(p, original[p]) for p in positions]
            for combo in itertools.product(*options):
                cand = list(original)
                for p, v in zip(positions, combo):
                    cand[p] = v
                if cand == original or not playable(cand):
                    continue
                text = render(cand)
                if not is_clean(instrument, tuning, key, symbol, text):
                    continue
                gaps = incompleteness(instrument, tuning, key, symbol, text)
                c = (gaps,) + cost(original, cand)
                if best is None or c < best[0]:
                    best = (c, text)
        # Stop as soon as the chord is fully spelled. Searching wider only
        # buys something when everything found so far is missing a tone --
        # a two-string fix that turns Gm into a bare G5 is worse than a
        # three-string one that actually sounds the flat third.
        if best is not None and best[0][0] == 0:
            break

    if best is None:
        return None, None
    return best[1], best[0][1]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data", default="data")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--max-changes", type=int, default=3)
    ap.add_argument("--log", default="CORRECTIONS.md")
    args = ap.parse_args()

    with open(os.path.join(args.data, "instruments.yaml")) as fh:
        instruments = yaml.safe_load(fh)

    applied, unresolved = [], []

    for path in sorted(glob.glob(os.path.join(args.data, "voicings", "*.yaml"))):
        with open(path) as fh:
            doc = yaml.safe_load(fh)
        name = doc["instrument"]
        tuning = instruments[name]["tuning"]
        source = doc.get("source", "")
        dirty = False

        for keyblock in doc["keys"]:
            for entry in keyblock["chords"]:
                if entry.get("check") is False:
                    continue
                for idx, frets_text in enumerate(list(entry["frets"])):
                    if is_clean(name, tuning, keyblock["key"],
                                entry["chord"], frets_text):
                        continue
                    fixed, changed = repair(
                        name, tuning, keyblock["key"], entry["chord"],
                        frets_text, args.max_changes,
                    )
                    row = (name, source, keyblock.get("pages",
                           keyblock.get("page")), keyblock["key"],
                           entry["chord"], frets_text, fixed, changed)
                    if fixed is None:
                        unresolved.append(row)
                        continue
                    applied.append(row)
                    if args.apply:
                        entry["frets"][idx] = fixed
                        dirty = True

        if args.apply and dirty:
            with open(path, "w") as fh:
                fh.write("# Repaired by tools/repair.py"
                         " -- see CORRECTIONS.md.\n")
                yaml.safe_dump(doc, fh, sort_keys=False, allow_unicode=True,
                               width=100)

    width = max([len(r[4]) for r in applied + unresolved] + [5])
    print("%-9s %-3s %-*s %-9s %-9s %s"
          % ("INSTR", "KEY", width, "CHORD", "WRITTEN", "CORRECTED", "EDIT"))
    for r in applied:
        print("%-9s %-3s %-*s %-9s %-9s %d string%s"
              % (r[0], r[3], width, r[4], r[5], r[6], r[7],
                 "" if r[7] == 1 else "s"))
    for r in unresolved:
        print("%-9s %-3s %-*s %-9s %-9s NEEDS PROOFREADING"
              % (r[0], r[3], width, r[4], r[5], "?"))

    print("\n%d corrected, %d need proofreading against the notebook"
          % (len(applied), len(unresolved)))

    if args.apply:
        with open(args.log, "w") as fh:
            fh.write(CORRECTIONS_HEADER)
            fh.write("\n## Corrected automatically\n\n")
            fh.write("| Instrument | Page | Key | Chord | Notebook |"
                     " Printed | Strings changed |\n")
            fh.write("|---|---|---|---|---|---|---|\n")
            for r in applied:
                fh.write("| %s | %s | %s | `%s` | `%s` | `%s` | %d |\n"
                         % (r[0], r[2], r[3], r[4], r[5], r[6], r[7]))
            if unresolved:
                fh.write("\n## Needs proofreading against the paper notebook\n\n")
                fh.write("These could not be repaired within the edit budget,"
                         " which usually means the photograph was misread"
                         " rather than the notebook being wrong.\n\n")
                fh.write("| Instrument | Page | Key | Chord | As read |\n")
                fh.write("|---|---|---|---|---|\n")
                for r in unresolved:
                    fh.write("| %s | %s | %s | `%s` | `%s` |\n"
                             % (r[0], r[2], r[3], r[4], r[5]))
        print("wrote %s" % args.log)

    return 0


CORRECTIONS_HEADER = """# Corrections

Generated by `tools/repair.py`. Do not edit by hand -- rerun `make repair`.

Every voicing in `data/voicings/` is checked against the chord it claims to
be (see `tools/validate.py`). Where a voicing sounded a note outside its
chord, the closest playable fingering that does spell the chord was
substituted. "Strings changed" is how far the correction had to reach: one
string is a single mis-copied digit, which is the overwhelming majority.
"""


if __name__ == "__main__":
    sys.exit(main())
