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
import playability  # noqa: E402

MAX_FRET = 12

# Chords big enough that the shape is the point. See generate().
EXTENDED_ROOTED = {"11", "13", "m13", "maj13", "7#11"}


def power_chord(tuning, root_pc, max_span, max_diagonal, diagonal_step=2):
    """The shape a player means by a 5 chord: root, fifth, octave.

    Not something the ranked search will ever find. It prefers shapes with
    as many strings ringing as the chord can fill, and a power chord is
    deliberately the opposite -- three strings and the rest damped, rooted
    low on the neck. Asking the search for C5 gave x-3-x-0-1-3, which
    sounds the right two notes and is not what anyone plays.

    Rooted on one of the two lowest strings, because that register is what
    makes it a power chord rather than a thin high fifth.
    """
    opens = [theory.parse_note(t) for t in tuning]
    fifth = (root_pc + 7) % 12
    best = None
    for i in range(min(2, len(tuning) - 1)):
        fret = (root_pc - opens[i]) % 12
        shape = [None] * len(tuning)
        shape[i] = fret
        f5 = (fifth - opens[i + 1]) % 12
        while f5 < fret:
            f5 += 12
        shape[i + 1] = f5
        if i + 2 < len(tuning):
            f8 = (root_pc - opens[i + 2]) % 12
            while f8 < fret:
                f8 += 12
            trial = list(shape)
            trial[i + 2] = f8
            # The octave has to be within reach of the root, measured
            # directly. is_playable takes its span from the fretted notes
            # alone, so an open root hid a tenth-fret octave and mandolin
            # G5 came out 0-0-10-x.
            if (f8 - fret <= max_span
                    and playability.is_playable(trial, max_span, 4,
                                                max_diagonal,
                                                diagonal_step)):
                shape = trial
        if not playability.is_playable(shape, max_span, 4, max_diagonal,
                                       diagonal_step):
            continue
        if best is None or fret < best[0]:
            best = (fret, shape)
    if best is None:
        return None
    return "".join("x" if f is None else ("[%d]" % f if f > 9 else str(f))
                   for f in best[1])


def generate(tuning, symbol, max_fret=MAX_FRET, require_root_bass=None,
             max_span=4, max_diagonal=None, require_bass_lowest=None,
             diagonal_step=2):
    """Best playable voicing of `symbol` on `tuning`, or None.

    An explicitly named bass -- the E of C/E -- is a hard requirement: get
    it wrong and the chord is a different chord. An *unnamed* root in the
    bass is only a preference. Treating it as a requirement pushed
    Gb7#5 to the eleventh fret when 3-2-5-2 sounds all four tones in third
    position, which is not a trade a chord book should make: nobody reaches
    for the eleventh fret to avoid a first inversion.
    """
    root, quality, bass_pc = theory.parse_chord(symbol)
    if quality == "5" and bass_pc is None:
        shape = power_chord(tuning, root, max_span, max_diagonal,
                            diagonal_step)
        if shape is not None:
            return shape
    if require_root_bass is None:
        require_root_bass = bass_pc is not None
    if require_bass_lowest is None:
        # Five and six note chords get the root underneath by default.
        # Without it the ranking finds the cheapest correct shape, which
        # for these means open strings: G13 came out 0-0-0-0-0-1, every
        # tone present and nothing a guitarist would recognize. Rooted,
        # it comes out 3-0-2-0-0-1, which is the chord as it is played.
        require_bass_lowest = (bass_pc is not None
                               or quality in EXTENDED_ROOTED)
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
        shape = list(combo)
        if not playability.is_playable(shape, max_span, 4, max_diagonal,
                                       diagonal_step):
            continue
        fretted = [f for _, f in sounding if f]
        pcs = {(open_pcs[i] + f) % 12 for i, f in sounding}
        if not needed <= pcs:
            continue
        lowest_i, lowest_f = sounding[0]
        in_bass = (open_pcs[lowest_i] + lowest_f) % 12 == want_bass
        # Putting the named bass underneath is a preference, not a rule.
        # A mandolin can get E below C -- at the ninth fret. Nobody does
        # that when 0-0-3-0 is sitting right there in first position, so
        # this is ranked, not required, and an inversion wins when the
        # in-bass option means climbing the neck.
        # A named bass is binding. The inner test used to be inverted --
        # it only rejected a shape when there was no named bass, which is
        # the one case where the bass is a preference -- so F/A came out
        # 1-3-3-2-1-1, which is F with F underneath and not F/A at all.
        if require_bass_lowest and not in_bass:
            continue
        # A named bass note must at least be in the chord somewhere, even
        # when the instrument cannot put it underneath.
        if bass_pc is not None and bass_pc not in pcs:
            continue
        # What makes a shape the one a player reaches for, in order:
        #
        #   full      as many strings ringing as the chord can fill --
        #             muting half the instrument to save a finger gives
        #             0-x-x-0-0-0 for E minor, which is thin and wrong
        #   easy      how far up the neck plus how many fingers. Position
        #             alone picked 5-2-5-0 for a mandolin Csus2/E over
        #             0-0-3-0, three fingers against one; fingers alone
        #             picks barre chords over open ones, which is worse.
        #             The sum behaves on both counts.
        #   low       ties broken downward
        #   in bass   the named bass note underneath, where it can be
        #
        # This will not always reproduce the shape convention settled on --
        # conventions are not derivable -- but the conventional shapes for
        # the common chords come from the notebook. This only fills gaps.
        position = min(fretted) if fretted else 0
        n_fingers = playability.fingers_needed(shape)
        # Muting counts against a shape, but not all mutes are equal.
        # Damping the low string is something a player does without
        # thinking, and a slash chord often wants it: G/B is x-2-0-0-0-3,
        # not 7-5-0-0-0-3. A mute *between* two ringing strings is a
        # different matter, and pricing every mute alike made E minor come
        # out 0-x-x-0-0-0 -- no fingers, no effort, far too thin to use.
        first = min(i for i, f in enumerate(combo) if f is not None)
        last = max(i for i, f in enumerate(combo) if f is not None)
        inner = sum(1 for i in range(first, last) if combo[i] is None)
        edge = sum(1 for f in combo if f is None) - inner
        difficulty = position + n_fingers + 3 * inner + edge
        rank = (
            difficulty,
            -len(sounding),
            position,
            0 if in_bass else 1,
            (max(fretted) - min(fretted)) if fretted else 0,
        )
        if best is None or rank < best[0]:
            best = (rank, combo)

    if best is None:
        if require_bass_lowest:
            # The named bass will not go underneath on this instrument --
            # a mandolin's lowest string is G, so C/E has no E to sit on.
            # Take an inversion that contains the note instead of nothing.
            return generate(tuning, symbol, max_fret, require_root_bass,
                            max_span, max_diagonal, False, diagonal_step)
        if require_root_bass:
            return generate(tuning, symbol, max_fret, False,
                            max_span, max_diagonal, False, diagonal_step)
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


def for_instrument(meta, symbol, max_fret=MAX_FRET):
    """Generate using an instrument's own reach limits."""
    return generate(meta["tuning"], symbol, max_fret,
                    max_span=meta.get("max_span", 4),
                    max_diagonal=meta.get("max_diagonal"),
                    diagonal_step=meta.get("max_diagonal_step", 2))


if __name__ == "__main__":
    import yaml
    with open("data/instruments.yaml") as fh:
        instruments = yaml.safe_load(fh)
    inst, chord = sys.argv[1], sys.argv[2]
    print(for_instrument(instruments[inst], chord))
