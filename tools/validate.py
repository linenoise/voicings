#!/usr/bin/env python3
"""Check every voicing in data/voicings/ against music theory.

Three severities:

  ERROR    the voicing sounds a pitch that is not in the chord. Something is
           wrong -- a mis-copied digit, an open string that should be muted.
           These fail the build.

  WARNING  every sounded pitch belongs to the chord, but a defining tone is
           missing (usually the third). Mandolin chop chords and rootless
           jazz grips do this on purpose, so these are reported and allowed.

  INFO     structural notes -- out-of-range frets, wide stretches.

Exit status is non-zero if any ERROR is found, so `make` stops before
typesetting a wrong number.
"""

import argparse
import glob
import os
import sys

import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import theory  # noqa: E402
import playability  # noqa: E402

ERROR, WARNING, INFO = "ERROR", "WARNING", "INFO"

MAX_STRETCH = 5  # frets between the lowest and highest fretted note


class Finding(object):
    def __init__(self, severity, instrument, key, chord, frets, message):
        self.severity = severity
        self.instrument = instrument
        self.key = key
        self.chord = chord
        self.frets = frets
        self.message = message

    def __str__(self):
        return "%-7s %-9s %-3s %-9s %-8s %s" % (
            self.severity, self.instrument, self.key,
            self.chord, self.frets, self.message,
        )


def check_voicing(instrument, tuning, key, symbol, frets_text, kind="frets",
                  reentrant=False, max_span=None, max_diagonal=None):
    """Yield Findings for one written voicing.

    A voicing is either fret numbers against a tuning, or -- for a keyboard
    -- note names low to high. Both come down to a list of pitch classes and
    a lowest note, so the checks below are shared.
    """
    if kind == "notes":
        try:
            names = [t for t in str(frets_text).split("-") if t]
            sounded = [theory.parse_note(t) for t in names]
        except (theory.ChordError, KeyError) as exc:
            yield Finding(ERROR, instrument, key, symbol, frets_text,
                          "cannot read note list: %s" % exc)
            return
        frets = None
        lowest_pc = sounded[0] if sounded else None
    else:
        n = len(tuning)
        try:
            frets = theory.parse_frets(frets_text, n)
        except theory.ChordError as exc:
            yield Finding(ERROR, instrument, key, symbol, frets_text, str(exc))
            return
        sounded = theory.sounded_pitch_classes(tuning, frets)
        lowest_pc = None
        for open_note, fret in zip(tuning, frets):
            if fret is not None:
                lowest_pc = (theory.parse_note(open_note) + fret) % 12
                break

    try:
        root, quality, bass_pc = theory.parse_chord(symbol)
    except theory.ChordError as exc:
        yield Finding(ERROR, instrument, key, symbol, frets_text, str(exc))
        return

    wanted = {(root + i) % 12 for i in theory.QUALITIES[quality]}

    if not sounded:
        yield Finding(ERROR, instrument, key, symbol, frets_text,
                      "every string muted")
        return

    # A slash chord licenses its bass note even when it is not a chord tone.
    allowed = set(wanted)
    if bass_pc is not None:
        allowed.add(bass_pc)

    foreign = sorted({pc for pc in sounded if pc not in allowed})
    if foreign:
        yield Finding(
            ERROR, instrument, key, symbol, frets_text,
            "sounds %s, not in %s (%s)" % (
                "/".join(theory.spell(p) for p in foreign),
                symbol,
                " ".join(theory.spell(p) for p in sorted(wanted)),
            ),
        )

    # Defining tones.
    present = set(sounded)
    missing = [
        i for i in theory.CHARACTERISTIC.get(quality, ())
        if (root + i) % 12 not in present
    ]
    if missing:
        names = {1: "b9", 2: "9", 3: "b3", 4: "3", 5: "4", 6: "b5",
                 8: "#5", 9: "6", 10: "b7", 11: "maj7"}
        yield Finding(
            WARNING, instrument, key, symbol, frets_text,
            "omits the %s" % ", ".join(names.get(i, str(i)) for i in missing),
        )

    if root not in present and bass_pc is None:
        yield Finding(WARNING, instrument, key, symbol, frets_text,
                      "rootless")

    # Slash chords: the named bass must actually be the lowest sounding note.
    # Except on a re-entrant instrument, where the lowest-pitched string is
    # not the first one -- a ukulele's 4th string sounds above its 3rd, so
    # "in the bass" has no meaning there and the bass player has the note
    # anyway.
    if reentrant:
        bass_pc = None
    if bass_pc is not None:
        # The named note has to be in the chord. Where it can be underneath
        # it should be -- but a mandolin's lowest string is G, so C/E has
        # no E to sit on, and an inversion that contains the E is what a
        # player uses. That is a note, not an error.
        if bass_pc not in set(sounded):
            yield Finding(
                ERROR, instrument, key, symbol, frets_text,
                "%s is not in this voicing at all"
                % theory.spell(bass_pc),
            )
        elif lowest_pc is not None and lowest_pc != bass_pc:
            yield Finding(
                WARNING, instrument, key, symbol, frets_text,
                "inversion: %s is present but %s is lowest"
                % (theory.spell(bass_pc), theory.spell(lowest_pc)),
            )

    # Can a hand make this shape? Four fingers, and only so much reach.
    if frets is not None and max_span is not None:
        why = playability.unplayable_reason(frets, max_span, 4, max_diagonal)
        if why:
            yield Finding(WARNING, instrument, key, symbol, frets_text,
                          "hard to finger: %s" % why)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data", default="data")
    ap.add_argument("--quiet", action="store_true",
                    help="only print errors")
    ap.add_argument("--strict", action="store_true",
                    help="treat warnings as errors too")
    args = ap.parse_args()

    with open(os.path.join(args.data, "instruments.yaml")) as fh:
        instruments = yaml.safe_load(fh)

    findings = []
    counts = {ERROR: 0, WARNING: 0, INFO: 0}
    n_voicings = 0

    for path in sorted(glob.glob(os.path.join(args.data, "voicings", "*.yaml"))):
        with open(path) as fh:
            doc = yaml.safe_load(fh)
        name = doc["instrument"]
        meta = instruments[name]
        tuning = meta.get("tuning", [])
        kind = meta.get("kind", "frets")
        reentrant = bool(meta.get("reentrant"))
        for keyblock in doc["keys"]:
            for entry in keyblock["chords"]:
                if entry.get("check") is False:
                    continue
                seen = set()
                for frets_text in entry["frets"]:
                    if frets_text in seen:
                        findings.append(Finding(
                            WARNING, name, keyblock["key"], entry["chord"],
                            frets_text, "listed twice"))
                        counts[WARNING] += 1
                    seen.add(frets_text)
                    n_voicings += 1
                    for f in check_voicing(name, tuning, keyblock["key"],
                                           entry["chord"], frets_text, kind,
                                           reentrant, meta.get("max_span"),
                                           meta.get("max_diagonal")):
                        findings.append(f)
                        counts[f.severity] += 1

    order = {ERROR: 0, WARNING: 1, INFO: 2}
    for f in sorted(findings, key=lambda f: (order[f.severity], f.instrument,
                                             f.key, f.chord)):
        if args.quiet and f.severity != ERROR:
            continue
        print(f)

    print("\n%d voicings checked: %d errors, %d warnings, %d notes"
          % (n_voicings, counts[ERROR], counts[WARNING], counts[INFO]))

    if counts[ERROR]:
        return 1
    if args.strict and counts[WARNING]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())


def marks_for(tuning, symbol, frets_text, reentrant=False):
    """Which caveats apply to one printed voicing: 'r', 'i', or neither.

    The book prints these as superscripts. They are not defects: a four
    string instrument physically cannot sound a five note chord, so a
    rootless shape is the only shape there is, and it works under a band
    where the bass has the root. What matters is that the page says so
    rather than letting a player find out.
    """
    out = []
    try:
        root, quality, bass_pc = theory.parse_chord(symbol)
        frets = theory.parse_frets(frets_text, len(tuning))
        sounded = set(theory.sounded_pitch_classes(tuning, frets))
    except theory.ChordError:
        return out
    if root not in sounded and bass_pc is None:
        out.append("r")
    # On a re-entrant instrument the lowest-pitched string is not the first
    # one, so "in the bass" has no meaning and nothing is an inversion.
    if bass_pc is not None and not reentrant:
        lowest = None
        for string, fret in zip(tuning, frets):
            if fret is None:
                continue
            lowest = (theory.parse_note(string) + fret) % 12
            break
        if lowest is not None and lowest != bass_pc:
            out.append("i")
    return out
