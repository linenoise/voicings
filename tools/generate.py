#!/usr/bin/env python3
"""Generate a canonical voicing for a chord on an instrument, from theory.

Used in two places:

  * the bass section, which the notebook does not have yet;
  * the handful of notebook entries whose photograph could not be read, and
    which have no legible alternate voicing to fall back on.

Anything this produces is marked `derived: true` in the data so it is never
mistaken for something transcribed from the paper notebook.

Selection is ranked: all defining tones present, root in the bass, as many
strings sounding as possible, narrow stretch, low on the neck.
"""

import itertools
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import theory  # noqa: E402

MAX_SPAN = 4
MAX_FRET = 12


def generate(tuning, symbol, max_fret=MAX_FRET, require_root_bass=None):
    """Best playable voicing of `symbol` on `tuning`, or None.

    An explicitly named bass -- the E of C/E -- is a hard requirement: get
    it wrong and the chord is a different chord. An *unnamed* root in the
    bass is only a preference. Treating it as a requirement pushed
    Gb7#5 to the eleventh fret when 3-2-5-2 sounds all four tones in third
    position, which is not a trade a chord book should make: nobody reaches
    for the eleventh fret to avoid a first inversion.
    """
    root, quality, bass_pc = theory.parse_chord(symbol)
    if require_root_bass is None:
        require_root_bass = bass_pc is not None
    wanted = {(root + i) % 12 for i in theory.QUALITIES[quality]}
    allowed = set(wanted)
    if bass_pc is not None:
        allowed.add(bass_pc)
    needed = {(root + i) % 12 for i in theory.CHARACTERISTIC.get(quality, ())}

    # The root is required only when there is room for it. A five-note
    # chord on four strings has to give something up, and the root is the
    # first thing to go -- the bass player has it, and the tones that name
    # the chord do not. Insisting on it put mandolin E7b9 at the tenth
    # fret when 1-0-x-1 sounds the third, the flat ninth and the flat
    # seventh in first position.
    if len(theory.QUALITIES[quality]) <= len(tuning):
        needed.add(root)
    want_bass = bass_pc if bass_pc is not None else root

    open_pcs = [theory.parse_note(t) for t in tuning]

    # Per string, the frets that land on a chord tone, plus mute.
    per_string = []
    for pc in open_pcs:
        opts = [f for f in range(0, max_fret + 1) if (pc + f) % 12 in allowed]
        per_string.append(opts + [None])

    best = None
    for combo in itertools.product(*per_string):
        sounding = [(i, f) for i, f in enumerate(combo) if f is not None]
        if len(sounding) < max(2, len(tuning) - 2):
            continue
        fretted = [f for _, f in sounding if f]
        if fretted and max(fretted) - min(fretted) > MAX_SPAN:
            continue
        pcs = {(open_pcs[i] + f) % 12 for i, f in sounding}
        if not needed <= pcs:
            continue
        lowest_i, lowest_f = sounding[0]
        in_bass = (open_pcs[lowest_i] + lowest_f) % 12 == want_bass
        if require_root_bass and not in_bass:
            continue
        # A chord book wants the shape a player would actually grab: as
        # many strings ringing as the chord can fill, low on the neck,
        # without a stretch. Ranking narrowness first produced things like
        # x-x-x-0-1-0 for C/E, which is technically a C/E and nothing
        # anyone would play.
        rank = (
            0 if len(sounding) >= len(tuning) - 1 else 1,     # full-ish
            min(fretted) if fretted else 0,                   # low position
            0 if in_bass else 1,                              # then root low
            -len(sounding),                                   # ring out
            (max(fretted) - min(fretted)) if fretted else 0,  # easy stretch
            sum(1 for f in fretted),                          # fewer fingers
        )
        if best is None or rank < best[0]:
            best = (rank, combo)

    if best is None:
        if require_root_bass:
            return generate(tuning, symbol, max_fret, require_root_bass=False)
        return None

    out = []
    for f in best[1]:
        if f is None:
            out.append("x")
        elif f > 9:
            out.append("[%d]" % f)
        else:
            out.append(str(f))
    return "".join(out)


if __name__ == "__main__":
    import yaml
    with open("data/instruments.yaml") as fh:
        instruments = yaml.safe_load(fh)
    inst, chord = sys.argv[1], sys.argv[2]
    print(generate(instruments[inst]["tuning"], chord))
