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


def check_voicing(instrument, tuning, key, symbol, frets_text):
    """Yield Findings for one written voicing."""
    n = len(tuning)
    try:
        frets = theory.parse_frets(frets_text, n)
    except theory.ChordError as exc:
        yield Finding(ERROR, instrument, key, symbol, frets_text, str(exc))
        return

    try:
        root, quality, bass_pc = theory.parse_chord(symbol)
    except theory.ChordError as exc:
        yield Finding(ERROR, instrument, key, symbol, frets_text, str(exc))
        return

    wanted = {(root + i) % 12 for i in theory.QUALITIES[quality]}
    sounded = theory.sounded_pitch_classes(tuning, frets)

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
    if bass_pc is not None:
        lowest = next((f for f in frets if f is not None), None)
        idx = frets.index(lowest)
        actual = (theory.parse_note(tuning[idx]) + lowest) % 12
        if actual != bass_pc:
            yield Finding(
                ERROR, instrument, key, symbol, frets_text,
                "lowest note is %s, but the symbol says %s in the bass"
                % (theory.spell(actual), theory.spell(bass_pc)),
            )

    fretted = [f for f in frets if f]
    if fretted and max(fretted) - min(fretted) > MAX_STRETCH:
        yield Finding(INFO, instrument, key, symbol, frets_text,
                      "spans %d frets" % (max(fretted) - min(fretted)))


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
        tuning = instruments[name]["tuning"]
        for keyblock in doc["keys"]:
            for entry in keyblock["chords"]:
                if entry.get("check") is False:
                    continue
                for frets_text in entry["frets"]:
                    n_voicings += 1
                    for f in check_voicing(name, tuning, keyblock["key"],
                                           entry["chord"], frets_text):
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
