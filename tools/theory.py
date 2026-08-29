"""Pitch-class arithmetic and chord spelling.

Everything the validator knows about music lives here. The rest of the
pipeline treats chords as opaque strings.
"""

import re

NOTE_TO_PC = {
    "Cbb": 10, "Dbb": 0, "Ebb": 2, "Fbb": 3, "Gbb": 5, "Abb": 7, "Bbb": 9,
    "C##": 2, "D##": 4, "E##": 6, "F##": 7, "G##": 9, "A##": 11, "B##": 1,
    "C": 0, "B#": 0,
    "C#": 1, "Db": 1,
    "D": 2,
    "D#": 3, "Eb": 3,
    "E": 4, "Fb": 4,
    "F": 5, "E#": 5,
    "F#": 6, "Gb": 6,
    "G": 7,
    "G#": 8, "Ab": 8,
    "A": 9,
    "A#": 10, "Bb": 10,
    "B": 11, "Cb": 11,
}

# Preferred spelling per pitch class, flat-side and sharp-side.
PC_TO_FLAT = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]
PC_TO_SHARP = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

# Chord quality -> intervals in semitones above the root.
#
# Keys are the suffix as written in the notebook, after the root note.
# "" is a bare major triad.
QUALITIES = {
    "":        (0, 4, 7),
    "m":       (0, 3, 7),
    "+":       (0, 4, 8),
    "o":       (0, 3, 6),
    "5":       (0, 7),
    "sus2":    (0, 2, 7),
    "sus4":    (0, 5, 7),
    "6":       (0, 4, 7, 9),
    "m6":      (0, 3, 7, 9),
    "6/9":     (0, 2, 4, 7, 9),
    "7":       (0, 4, 7, 10),
    "maj7":    (0, 4, 7, 11),
    "m7":      (0, 3, 7, 10),
    "o7":      (0, 3, 6, 9),
    "m7b5":    (0, 3, 6, 10),
    "7sus4":   (0, 5, 7, 10),
    "7b5":     (0, 4, 6, 10),
    "7#5":     (0, 4, 8, 10),
    "9":       (0, 2, 4, 7, 10),
    "maj9":    (0, 2, 4, 7, 11),
    "m9":      (0, 2, 3, 7, 10),
    "add9":    (0, 2, 4, 7),
    "madd9":   (0, 2, 3, 7),
    "2":       (0, 2, 4, 7),
    "add2":    (0, 2, 4, 7),
    "7b9":     (0, 1, 4, 7, 10),
    "7#9":     (0, 3, 4, 7, 10),
    "m11":     (0, 2, 3, 5, 7, 10),
    "11":      (0, 2, 4, 5, 7, 10),
    "13":      (0, 2, 4, 7, 9, 10),
}

# The degree that gives each quality its identity. If a voicing omits this,
# the chord is ambiguous -- worth a warning, but not always an error: a
# mandolin "chop" chord routinely drops the fifth or the third, and players
# still call it by the full name.
CHARACTERISTIC = {
    "":      (4,),      "m":     (3,),
    "+":     (4, 8),    "o":     (3, 6),
    "sus2":  (2,),      "sus4":  (5,),
    "6":     (4, 9),    "m6":    (3, 9),
    "6/9":   (9,),      "7":     (4, 10),
    "maj7":  (4, 11),   "m7":    (3, 10),
    "o7":    (3, 6, 9), "m7b5":  (3, 6, 10),
    "7sus4": (5, 10),   "7b5":   (4, 6, 10),
    "7#5":   (4, 8, 10), "9":    (4, 10),
    "maj9":  (4, 11),   "m9":    (3, 10),
    "add9":  (2, 4),    "madd9": (2, 3),
    "2":     (2, 4),    "add2":  (2, 4),
    "7b9":   (1, 10),   "7#9":   (3, 10),
    "m11":   (3, 10),   "11":    (10,),
    "13":    (4, 9, 10),
    "5":     (),
}

# When an instrument has fewer strings than the chord has notes, something
# has to go. This is the order it goes in: the fifth first (it is implied by
# the root and adds nothing to the colour), then the root (the bass player
# has it), then the ninth, and only then a tone that defines the chord.
# Nothing here will drop the third or the seventh -- that would turn one
# chord into another, which is the whole thing a chord book exists to avoid.
OMIT_ORDER = [7, 0, 2, 1, 9, 5]

# The vocabulary every instrument is expected to cover, in the order it is
# printed. "2" is not listed: it is the same chord as "add9", and the
# notebook writes it both ways.
VOCABULARY = [
    "", "m", "5", "+", "o",
    "sus2", "sus4",
    "6", "m6", "6/9",
    "7", "maj7", "m7", "o7", "m7b5", "7sus4", "7b5", "7#5",
    "9", "maj9", "m9", "add9", "madd9",
    "7b9", "7#9", "m11",
]

# Slash voicings worship music leans on: the third in the bass for a smooth
# line, the fifth for weight, and a suspended second over the third.
SLASH_FORMS = [("", 4), ("", 7), ("sus2", 4)]

# Letter names, for spelling a chord the way it is written rather than the
# way it is most convenient.
LETTERS = "CDEFGAB"
LETTER_PC = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}

# Which letter each interval lands on, counting scale degrees from the root.
INTERVAL_DEGREE = {
    0: 0, 1: 1, 2: 1, 3: 2, 4: 2, 5: 3, 6: 3, 7: 4, 8: 5, 9: 5,
    10: 6, 11: 6, 12: 0, 13: 1, 14: 1, 15: 2, 16: 2, 17: 3, 18: 4,
    19: 4, 20: 5, 21: 5, 22: 6, 23: 6, 24: 0,
}


def spell_in_key(root_name, interval):
    """Name the note `interval` semitones above `root_name`, spelled properly.

    A minor seventh above G-flat is B-double-flat, not A: they sound the
    same, but only one of them is the third of a G-flat chord, and a chord
    chart that says A is telling you the wrong thing about the harmony.
    This is what the piano worksheet does, so it is what we do.
    """
    m = _ROOT_RE.match(root_name)
    if not m:
        raise ChordError("cannot parse root %r" % root_name)
    root = m.group(1)
    letter, accidental = root[0], root[1:]

    steps = INTERVAL_DEGREE[interval % 24 if interval > 11 else interval]
    target_letter = LETTERS[(LETTERS.index(letter) + steps) % 7]

    want = (NOTE_TO_PC[root] + interval) % 12
    natural = LETTER_PC[target_letter]
    delta = (want - natural) % 12
    if delta > 6:
        delta -= 12

    if delta == 0:
        return target_letter
    if delta > 0:
        return target_letter + "#" * delta
    return target_letter + "b" * (-delta)


# Longest-first so "maj7" wins over "m", "sus4" over "sus2", etc.
_SUFFIXES = sorted(QUALITIES, key=len, reverse=True)

_ROOT_RE = re.compile(r"^([A-G](?:bb|##|b|#)?)")


class ChordError(ValueError):
    pass


def parse_note(name):
    """'Bb3' or 'Bb' -> pitch class 0-11."""
    m = _ROOT_RE.match(name)
    if not m:
        raise ChordError("cannot parse note %r" % name)
    return NOTE_TO_PC[m.group(1)]


def parse_chord(symbol):
    """'Bbmaj7/D' -> (root_pc, quality, bass_pc or None).

    The degree sign is normalised to 'o' before parsing, so 'A°7' and 'Ao7'
    are the same chord.
    """
    sym = symbol.replace("°", "o").replace("∅", "m7b5").strip()

    bass_pc = None
    if "/" in sym:
        sym, bass = sym.rsplit("/", 1)
        # A slash chord names a bass note; "6/9" is a quality, not a slash.
        if re.match(r"^[A-G][b#]?$", bass):
            bass_pc = NOTE_TO_PC[bass]
        else:
            sym = sym + "/" + bass

    m = _ROOT_RE.match(sym)
    if not m:
        raise ChordError("cannot parse chord %r" % symbol)
    root = m.group(1)
    rest = sym[len(root):]

    for suffix in _SUFFIXES:
        if rest == suffix:
            return NOTE_TO_PC[root], suffix, bass_pc
    raise ChordError("unknown chord quality %r in %r" % (rest, symbol))


def chord_pitch_classes(symbol):
    root, quality, _ = parse_chord(symbol)
    return {(root + i) % 12 for i in QUALITIES[quality]}


def sounded_pitch_classes(tuning, frets):
    """Pitch classes a voicing actually sounds.

    `tuning` is a list of open-string note names, low string first.
    `frets` is a list the same length; None means a muted string.
    """
    out = []
    for open_note, fret in zip(tuning, frets):
        if fret is None:
            continue
        out.append((parse_note(open_note) + fret) % 12)
    return out


def parse_frets(text, n_strings):
    """'x32010' or '2200' -> [None, 3, 2, 0, 1, 0].

    Frets above 9 are written in brackets: '10' would be ambiguous, so
    '[10]' is required. 'x' and 'X' mute a string.
    """
    tokens = []
    i = 0
    s = str(text).strip()
    while i < len(s):
        c = s[i]
        if c == "[":
            j = s.index("]", i)
            tokens.append(int(s[i + 1:j]))
            i = j + 1
        elif c in "xX":
            tokens.append(None)
            i += 1
        elif c.isdigit():
            tokens.append(int(c))
            i += 1
        elif c in " -_":
            i += 1
        else:
            raise ChordError("bad character %r in fret string %r" % (c, text))
    if len(tokens) != n_strings:
        raise ChordError(
            "fret string %r has %d positions, expected %d"
            % (text, len(tokens), n_strings)
        )
    return tokens


def spell(pc, prefer_flat=True):
    return (PC_TO_FLAT if prefer_flat else PC_TO_SHARP)[pc % 12]


def transpose_symbol(symbol, semitones, prefer_flat=True):
    root, quality, bass = parse_chord(symbol)
    out = spell(root + semitones, prefer_flat) + quality.replace("o", "°")
    if bass is not None:
        out += "/" + spell(bass + semitones, prefer_flat)
    return out
