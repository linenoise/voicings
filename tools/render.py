#!/usr/bin/env python3
"""Turn data/ into LaTeX. Writes build/body.tex.

The LaTeX side owns page geometry and typography; this file owns what goes
on which page and in what order. Nothing here does music theory beyond
asking tools/theory.py which chords sit in a key.
"""

import argparse
import glob
import itertools
import os
import re
import sys

import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import theory
import playability
import validate  # noqa: E402

# The order keys march around the circle of fifths, starting at C.
CIRCLE = ["C", "G", "D", "A", "E", "B", "Gb", "Db", "Ab", "Eb", "Bb", "F"]

# Keys that a musician writes with sharps rather than flats.
SHARP_KEYS = {"G", "D", "A", "E", "B"}

# How chords group on a key page, in the order a player meets them. Slash
# voicings come last: they are what you reach for to move a bass line, not
# what you reach for to play the chord.
CHORD_GROUPS = [
    ("triads",   ["", "m", "5", "+", "o", "sus2", "sus4"]),
    ("sixths",   ["6", "m6", "6/9"]),
    ("sevenths", ["7", "maj7", "m7", "o7", "m7b5", "7sus4", "7b5", "7#5"]),
    ("ninths",   ["9", "maj9", "m9", "add9", "2", "add2", "madd9",
                  "7b9", "7#9", "m11"]),
    # Five and six note chords, guitar only. Their own block: they are
    # what you reach for when a four-course instrument has run out of
    # strings, and grouping them with the ninths buried them.
    ("extended", ["11", "13", "m13", "maj13", "7#11"]),
]

GROUP_OF = {}
for _n, (_name, _qs) in enumerate(CHORD_GROUPS):
    for _q in _qs:
        GROUP_OF[_q] = _n
SLASH_GROUP = len(CHORD_GROUPS)


def group_index(symbol):
    """Which block on the page this chord belongs in."""
    try:
        _, quality, bass = theory.parse_chord(symbol)
    except theory.ChordError:
        return SLASH_GROUP
    if bass is not None:
        return SLASH_GROUP
    return GROUP_OF.get(quality, SLASH_GROUP - 1)


# Reading order for the chord sections: chromatic, as the notebook has it.
CHROMATIC = ["A", "Bb", "B", "C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab"]

# Scale degrees of a major key, in Nashville columns.
DEGREES = [(0, ""), (2, "m"), (4, "m"), (5, ""), (7, ""), (9, "m"), (11, "°")]
DEGREE_LABELS = ["1", "2m", "3m", "4", "5", "6m", "7°"]

# Instruments that get their own circle of fifths.
NO_NUMBER_CHARTS = {"bass", "piano"}

ROOT_KEYS = ["C", "Db", "D", "Eb", "E", "F",
             "Gb", "G", "Ab", "A", "Bb", "B"]

CHART_INSTRUMENTS = ["mandolin", "guitar", "ukulele", "piano", "banjo", "bass"]

# One pen per instrument, matching the notebook. Defined in voicings.cls.
INK = {
    "mandolin": "fretgreen",
    "guitar":   "fretblue",
    "ukulele":  "fretpurple",
    "piano":    "keyred",
    "banjo":    "fretorange",
    "bass":     "fretyellow",
}

# Rows per page. These are tuned against the real compiled PDF -- see
# `make pagecheck`, which fails if any page overflows onto an unheaded
# continuation. Change the type size in voicings.cls and these move.
# How far up the neck a bassist's hand reaches without shifting.
FIRST_POSITION = 7

CHORDS_PER_PAGE = 34
# Guitar carries five more qualities than the others, and 39 chords split
# two ways leaves both pages half empty. A column holds more rows than
# the shared figure assumed, so guitar gets its own.
PER_PAGE = {"guitar": 40}      # fret grids, one line each
PIANO_PER_PAGE = 32
WORSHIP_PER_PAGE = 8      # name, notes, and a line of description


def tex_escape(s):
    return (s.replace("\\", r"\textbackslash{}")
             .replace("#", r"\#").replace("&", r"\&")
             .replace("_", r"\_").replace("%", r"\%")
             .replace("°", r"\degsign{}"))


def frets_tex(text):
    """Set a fret string in the monospaced chord face."""
    # A fret above the ninth needs two digits, which the data brackets so
    # 10-3-3-1 cannot be read as 1-0-3-3-1. Those digits go through a
    # macro rather than inline: \smaller takes an optional argument, so
    # "{\smaller[10]}" fed it the 10 and printed nothing at all, which
    # turned a four string chord into a two string one on the page.
    body = re.sub(r"\[(\d+)\]", r"\\fretbig{\1}", text)
    macro = r"\fretswide" if "[" in text else r"\frets"
    return r"%s{%s}" % (macro, body)


def notes_tex(text):
    """Set a note list, with real flat and sharp signs."""
    parts = []
    for note in str(text).split("-"):
        body = tex_escape(note[:1])
        accidentals = "".join(r"\flat" if a == "b" else r"\sharp"
                              for a in note[1:])
        if accidentals:
            # One math group, so a double flat sets as a pair rather than
            # two separately spaced glyphs.
            body += "$%s$" % accidentals
        parts.append(body)
    return r"\notes{%s}" % r"\notesep ".join(parts)


def paginate(items, capacity):
    """Split into as few pages as fit, then even them out.

    Filling each page to capacity and letting the remainder spill leaves a
    key with twenty-eight chords on one page and one lonely chord on the
    next. Splitting the same key fifteen and fourteen reads better and
    costs nothing.
    """
    if not items:
        return [[]]
    n_pages = max(1, -(-len(items) // capacity))
    per = -(-len(items) // n_pages)
    return [items[i:i + per] for i in range(0, len(items), per)]


class Book(object):
    def __init__(self, data="data", only=None):
        self.data = data
        # When set, the book covers one instrument: its cover, its
        # section, and the credits. Nothing else.
        self.only = only
        with open(os.path.join(data, "instruments.yaml")) as fh:
            self.instruments = yaml.safe_load(fh)
        with open(os.path.join(data, "banjo-spikes.yaml")) as fh:
            self.spikes = yaml.safe_load(fh)
        with open(os.path.join(data, "piano-shapes.yaml")) as fh:
            self.piano_shapes = yaml.safe_load(fh)
        with open(os.path.join(data, "bass-patterns.yaml")) as fh:
            self.bass = yaml.safe_load(fh)
        self.voicings = {}
        for path in sorted(glob.glob(os.path.join(data, "voicings", "*.yaml"))):
            with open(path) as fh:
                doc = yaml.safe_load(fh)
            self.voicings[doc["instrument"]] = doc
        self.out = []

    # -- lookup ----------------------------------------------------------

    def lookup(self, instrument, symbol):
        """Most common voicing of a chord, or None if the book lacks it."""
        doc = self.voicings.get(instrument)
        if not doc:
            return None
        root, quality, _ = theory.parse_chord(symbol)
        for keyblock in doc["keys"]:
            for entry in keyblock["chords"]:
                try:
                    r, q, _ = theory.parse_chord(entry["chord"])
                except theory.ChordError:
                    continue
                if r == root and q == quality and entry["frets"]:
                    return entry["frets"][0]
        return None

    def bass_root(self, symbol):
        """Where a bassist actually puts this root.

        Every root is available on more than one string, and the choice is
        not "whichever fret is lowest" -- that lands G on the open G
        string, an octave up and thin, when the whole point of the
        instrument is the bottom. Work up from the lowest string and take
        the first that falls inside first position.

        A five-string's low B wins that race for most of the circle, so
        wherever the answer lands on the B string the four-string position
        follows in parentheses: C is B1, or A3 if you have four strings.
        The two are stacked rather than run together, because a wedge is
        only about eleven millimetres across.
        """
        root, _, _ = theory.parse_chord(symbol)
        name = theory.spell(root)
        row = self.bass["root_map"]["notes"].get(name)
        if not row:
            return None
        pairs = list(zip(self.bass["root_map"]["strings"], row))

        def pick(options):
            for string, fret in options:
                if fret <= FIRST_POSITION:
                    return string, fret
            return min(options, key=lambda sf: sf[1])

        best = pick(pairs)
        if best[0] != "B":
            return "%s%d" % best
        four = pick([p for p in pairs if p[0] != "B"])
        return "%s%d (%s%d)" % (best[0], best[1], four[0], four[1])

    def voicing_for(self, instrument, symbol):
        if instrument == "bass":
            return self.bass_root(symbol)
        return self.lookup(instrument, symbol)

    # -- emit ------------------------------------------------------------

    def w(self, line=""):
        self.out.append(line)

    def render(self):
        self.front_matter()
        if self.only:
            self.one_instrument(self.only)
            # The number charts name chords rather than fingerings, so
            # they belong to no instrument. They ride along in the solo
            # editions that have room for them and are left out of the
            # two that do not: a bass player carrying nine pages instead
            # of seven is carrying a second sheet for a page that is not
            # about the bass.
            if self.only not in NO_NUMBER_CHARTS:
                self.number_charts()
            self.back_matter()
            return "\n".join(self.out) + "\n"
        self.contents()
        for inst in ["mandolin", "guitar", "ukulele"]:
            self.chord_section(inst)
        self.piano_section()
        self.banjo_section()
        self.bass_section()
        self.number_charts()
        self.back_matter()
        return "\n".join(self.out) + "\n"

    # -- front -----------------------------------------------------------

    ALL_INSTRUMENTS = ["mandolin", "guitar", "ukulele",
                       "piano", "banjo", "bass"]

    def front_matter(self):
        # No instrument owns the front matter, so its sample voicings are
        # set in plain ink rather than borrowing whichever color happens
        # to be current -- a green x on the contents page reads as a
        # mandolin instruction.
        self.w(r"\usevoicingcolor{ink}")
        if self.only:
            name = self.instruments[self.only]["name"]
            subject = r"\coversubject{%s}{%s}" % (tex_escape(name),
                                                  INK[self.only])
            # The title already names the instrument; repeating it under
            # the rule just says the same thing twice.
            listing = ""
        else:
            subject = ""
            # Each in its own pen, the way the notebook is written.
            rows = [["mandolin", "guitar", "ukulele"],
                    ["piano", "banjo", "bass"]]
            lines = []
            for row in rows:
                names = [r"\textcolor{%s}{%s}"
                         % (INK[i], tex_escape(self.instruments[i]["name"]))
                         for i in row]
                lines.append(r"{\large\bfseries %s\par}"
                             % r"\, $\cdot$\, ".join(names))
            listing = r"\vspace{2.5mm}".join(lines)
        self.w(r"\coverpage{%s}{%s}" % (subject, listing))

    def one_instrument(self, inst):
        """A single-instrument edition: that section and nothing else."""
        if inst == "piano":
            self.piano_section()
        elif inst == "banjo":
            self.banjo_section()
        elif inst == "bass":
            self.bass_section()
        else:
            self.chord_section(inst)

    def contents(self):
        self.w(r"\begin{bookpage}{Table of Chords}")
        self.w(r"\begin{tocdirectory}")
        for inst, label in [("mandolin", "Mandolin Chords"),
                            ("guitar", "Guitar Chords"),
                            ("ukulele", "Ukulele Chords"),
                            ("piano", "Piano Chords"),
                            ("banjo", "Banjo Chords"),
                            ("bass", "Bass")]:
            self.w(r"\tocline{%s}{%s}" % (label, self.section_hint(inst)))
        self.w(r"\tocline{Tunings \& Credits}{back sheet}")
        self.w(r"\end{tocdirectory}")
        total = sum(self.voicing_count(i) for i in
                    ("mandolin", "guitar", "ukulele", "piano", "banjo"))
        self.w(r"\begin{toctotal}")
        self.w(r"\textbf{%s chord voicings} in all." % "{,}".join(
            [str(total)[:-3], str(total)[-3:]] if total >= 1000 else [str(total)]))
        self.w(r"\end{toctotal}")
        self.w(r"\begin{tocnote}")
        # One sentence per line: four short rules read as four rules when
        # they are stacked, and as a paragraph when they are not.
        self.w(r"Twelve keys for every chord on each instrument.\\")
        self.w(r"Fret numbers read from the lowest string.\\")
        self.w(r"\frets{x} means don't play that string.\\")
        self.w(r"\vmarkink{r} means rootless: for rhythm, "
               r"not for soloing.\\")
        self.w(r"\vmarkink{i} means the chord given is an inversion.\\")
        self.w(r"Tunings are on the back sheet.")
        self.w(r"\end{tocnote}")
        self.w(r"\end{bookpage}")

    def voicing_count(self, inst):
        """How many fingerings this instrument's pages carry.

        Chords with more than one voicing count once per voicing: the
        number is what the reader can look up, not how many chord names
        there are.
        """
        doc = self.voicings.get(inst)
        if not doc:
            return 0
        return sum(len(c["frets"]) for k in doc["keys"] for c in k["chords"])

    def section_hint(self, inst):
        # Every instrument covers all twelve keys, so saying so on each
        # line is six repetitions of the same fact. It is stated once,
        # under the list.
        if inst == "bass":
            return "roots \\& patterns"
        return "%d chord voicings" % self.voicing_count(inst)

    # -- circle of fifths ------------------------------------------------

    def circle_of_fifths(self, instrument):
        title = self.instruments[instrument]["name"]
        self.w(r"\usevoicingcolor{%s}" % INK[instrument])
        # Guitar fingerings run to six digits and piano voicings to five
        # notes, so those keep the small setting. For the rest, 9pt is as
        # large as the rings take with air left around it: a wedge at the
        # inner ring is 10.7mm across, and four digits measure 7.6mm at
        # 9pt against 10.2mm at the body's 12pt, which touched the lines.
        # Bass labels carry a five-string position and a four-string one
        # in parentheses -- "B1 (A3)" is seven characters where a mandolin
        # fingering is four -- so they set smaller to clear the wedge.
        self.w(r"\usecofsize{%s}" % {
            "guitar": "6.4", "piano": "6.4", "bass": "7"}.get(instrument, "9"))
        self.w(r"\begin{circlepage}{%s}" % tex_escape(title))
        self.w(r"\begin{circleoffifths}{%s}" % tex_escape(title))
        for i, key in enumerate(CIRCLE):
            major = key
            flat = key not in SHARP_KEYS
            minor = theory.spell((theory.NOTE_TO_PC[key] + 9) % 12, flat) + "m"
            mv = self.voicing_for(instrument, major) or ""
            nv = self.voicing_for(instrument, minor) or ""
            # Which way is "outward" for this wedge: up in the top half of
            # the circle, down in the bottom. Decides the stacking order.
            angle = (90 - 30 * i) % 360
            outward = "up" if angle < 180 else "down"
            self.w(r"  \cofsegment{%d}{%s}{%s}{%s}{%s}{%s}{%s}" % (
                i, tex_escape(major),
                self.circle_voicing(instrument, mv, flat),
                tex_escape(minor),
                self.circle_voicing(instrument, nv, flat),
                self.signature(key), outward))
        self.w(r"\end{circleoffifths}")
        if instrument == "banjo":
            self.w(r"\circlefootnote{Outer ring: major.\\ "
                   r"Inner ring: relative minor.\\ "
                   r"Spike the drone as shown on the banjo pages.}")
        elif instrument == "bass":
            self.w(r"\circlefootnote{String and fret for each root: "
                   r"\frets{A3} is the third fret of the A string.\\ "
                   r"Lowest that falls under the hand.\\ "
                   r"Five-string first, four-string in parentheses.}")
        else:
            self.w(r"\circlefootnote{Outer ring: major.\\ "
                   r"Inner ring: relative minor.\\ "
                   r"Both show the most common voicing.}")
        self.w(r"\end{circlepage}")

    def circle_voicing(self, instrument, text, prefer_flat=True):
        """A voicing as it goes inside the circle.

        The circle sets its own face, so this returns bare text rather than
        a wrapped \frets{...}. Note names carry sharps and flats that have
        to be escaped -- a raw # is a macro parameter to TeX, not a symbol.

        Keyboard notes are respelled to the key you actually put a finger
        on, matching whichever side of the circle the label is on. The
        chord pages keep the strict spelling -- the minor third of G-flat
        minor is B-double-flat and saying so is the point of those pages --
        but a circle of fifths is for finding your way at a glance, and
        nobody hunts the keyboard for B-double-flat.
        """
        if not text:
            return ""
        if self.instruments[instrument].get("kind") == "notes":
            notes = []
            for n in str(text).split("-"):
                pc = theory.parse_note(n)
                notes.append(theory.spell(pc, prefer_flat))
            # Spaces, not dashes, to match the piano pages. Wider than a
            # thin space: at six and a half points the notes need visible
            # air between them or they read as one word.
            return r"\hskip0.34em ".join(
                tex_escape(n[:1]) + "".join(
                    r"$\flat$" if a == "b" else r"$\sharp$" for a in n[1:])
                for n in notes)
        return tex_escape(str(text))

    def signature(self, key):
        # C has neither sharps nor flats; the natural sign marks the top of
        # the circle so the eye has something to start from.
        sharps = {"C": r"$\natural$", "G": "1\\#", "D": "2\\#", "A": "3\\#", "E": "4\\#",
                  "B": "5\\#", "Gb": "6$\\flat$", "Db": "5$\\flat$",
                  "Ab": "4$\\flat$", "Eb": "3$\\flat$", "Bb": "2$\\flat$",
                  "F": "1$\\flat$"}
        return sharps.get(key, "")

    # -- nashville -------------------------------------------------------

    # -- chord sections --------------------------------------------------

    def chord_section(self, instrument):
        doc = self.voicings[instrument]
        meta = self.instruments[instrument]
        self.w(r"\usevoicingcolor{%s}" % INK[instrument])
        self.w(r"\sectiondivider{%s Chords}{%s}" % (
            tex_escape(meta["name"]), tex_escape(meta["tuning_label"])
            if "tuning_label" in meta else self.tuning_label(instrument)))
        self.circle_of_fifths(instrument)
        self.root_positions(instrument)
        self.movable_shapes(instrument)
        by_key = {k["key"]: k for k in doc["keys"]}
        for key in CHROMATIC:
            block = by_key.get(key)
            if not block:
                continue
            ordered = self.ordered_chords(block["chords"])
            capacity = PER_PAGE.get(instrument, CHORDS_PER_PAGE)
            for n, chunk in enumerate(paginate(ordered, capacity)):
                self.chord_page(instrument, key, chunk,
                                continued=(n > 0))

    def chord_page(self, instrument, key, chords, continued):
        heading = self.key_heading(key)
        self.w(r"\begin{chordpage}{%s}{%s}{%s}{}" % (
            tex_escape(self.instruments[instrument]["name"]),
            heading, "cont" if continued else ""))
        self.emit_chords(chords, instrument)
        self.w(r"\end{chordpage}")

    def emit_chords(self, chords, instrument):
        """Rows, grouped by the kind of chord.

        Each group after the first opens with a ruled line, drawn as part
        of its first row so a column break cannot separate the two.
        """
        last = None
        for entry in chords:
            g = group_index(entry["chord"])
            starts_group = last is not None and g != last
            if starts_group:
                self.w(r"  \chordgap")
            last = g
            cells = r"\voicingnext ".join(
                frets_tex(f) + self.voicing_marks(instrument, entry["chord"], f)
                for f in entry["frets"])
            self.w(r"  \chordrow%s{%s}{%s}" % (
                "first" if starts_group else "",
                tex_escape(entry["chord"]), cells))

    def root_positions(self, instrument):
        """Where the root of every key falls, string by string.

        The bass has had this page from the start and it is the most
        thumbed one there: everything else on the instrument is measured
        from the root, so knowing where the root is turns a chord chart
        into something you can move. The same is true of a mandolin neck.
        """
        meta = self.instruments[instrument]
        tuning = meta["tuning"]
        names = [t[:-1] for t in tuning]
        self.w(r"\begin{bookpage}{Root Positions}")
        self.w(r"\pagesubtitle{%s}" % tex_escape(meta["name"]))
        self.w(r"\begin{rootmap}{%d}{%s}"
               % (len(tuning), "4pt" if len(tuning) > 4 else "7pt"))
        self.w(r"\rootmaphead{%s}"
               % " & ".join(r"{\bfseries %s}" % tex_escape(n) for n in names))
        for note in ROOT_KEYS:
            pc = theory.NOTE_TO_PC[note]
            cells = [(pc - theory.parse_note(t)) % 12 for t in tuning]
            self.w(r"\rootmaprow{%s}{%s}"
                   % (tex_escape(note),
                      " & ".join(r"\frets{%d}" % f for f in cells)))
        self.w(r"\end{rootmap}")
        self.w(r"\begin{rootmapnote}")
        self.w(r"Fret for the root of each key on each string.\\")
        self.w(r"Everything else is measured from there.")
        self.w(r"\end{rootmapnote}")
        self.w(r"\end{bookpage}")

    MOVABLE_QUALITIES = {
        "mandolin": [("major", "", 5), ("minor", "m", 3), ("seventh", "7", 3)],
        "guitar":   [("major", "", 4), ("minor", "m", 3), ("seventh", "7", 3)],
        "ukulele":  [("major", "", 4), ("minor", "m", 3), ("seventh", "7", 3)],
        "banjo":    [("major", "", 4), ("minor", "m", 3), ("seventh", "7", 3)],
    }

    def closed_shapes(self, instrument, quality, want):
        """Every shape with no open string in it, lowest positions first.

        A shape that uses an open string is stuck in one key. A closed one
        is the same five fingers in all twelve, which is the whole point:
        learn the handful here and the rest of the book becomes a lookup
        for the keys you have not moved to yet.
        """
        meta = self.instruments[instrument]
        tuning = meta["tuning"]
        span = meta.get("max_span", 4)
        opens = [theory.parse_note(t) for t in tuning]
        wanted = set(theory.QUALITIES[quality])
        seen = {}
        # Walk a base fret and the offsets above it rather than every
        # fret on every string: a closed shape spans at most `span`, so
        # the whole search is twelve positions by a handful of offsets
        # instead of twelve to the power of six.
        for base in range(1, 13):
            # None is a muted string. Guitar shapes want it: the A-shape
            # barre mutes the low E, and a search that insists on six
            # ringing strings finds only the E-shape and calls that the
            # whole of major.
            options = list(range(span + 1)) + [None]
            for offsets in itertools.product(options, repeat=len(tuning)):
                live = [o for o in offsets if o is not None]
                if len(live) < max(4, len(tuning) - 2) or min(live) != 0:
                    continue
                combo = tuple(None if o is None else base + o
                              for o in offsets)
                if not playability.is_playable(list(combo), span, 4,
                                               meta.get("max_diagonal")):
                    continue
                pcs = {(o + f) % 12 for o, f in zip(opens, combo)
                       if f is not None}
                for root in range(12):
                    if {(root + i) % 12 for i in wanted} != pcs:
                        continue
                    rel = tuple(offsets)
                    if rel in seen:
                        continue
                    first = next(i for i, f in enumerate(combo)
                                 if f is not None)
                    low = (opens[first] + combo[first] - root) % 12
                    degree = {0: "R", 3: "b3", 4: "3", 7: "5",
                              10: "b7"}.get(low, "?")
                    where = next((tuning[i][:-1]
                                  for i, (o, f) in enumerate(zip(opens, combo))
                                  if f is not None and (o + f) % 12 == root),
                                 "?")
                    seen[rel] = (base, degree, where,
                                 "".join("x" if c is None else str(c)
                                         for c in combo),
                                 theory.spell(root))
        # Lowest position first, then the least stretch, then the fewest
        # muted strings: a shape that rings six is worth more than one
        # that rings four at the same difficulty.
        def cost(item):
            rel, info = item
            live = [r for r in rel if r is not None]
            # Fewest muted strings first. Ranking by finger effort instead
            # put x-2-0-0-0-x at the top of "major" on guitar and buried
            # the barre forms, which are the shapes the page exists for.
            return (sum(1 for r in rel if r is None), info[0], sum(live))
        best = sorted(seen.items(), key=cost)
        return best[:want]

    def movable_shapes(self, instrument):
        meta = self.instruments[instrument]
        self.w(r"\begin{bookpage}{Movable Shapes}")
        self.w(r"\pagesubtitle{%s \quad closed, so they move}"
               % tex_escape(meta["name"]))
        self.w(r"\begin{movablelist}")
        self.w(r"\movablehead{shape}{root on}{bottom}{example}")
        for label, quality, want in self.MOVABLE_QUALITIES[instrument]:
            self.w(r"\movablehdr{%s}" % label)
            for rel, (pos, degree, where, shape, root) in self.closed_shapes(
                    instrument, quality, want):
                self.w(r"\movablerow{%s}{%s}{%s}{%s}" % (
                    "".join("x" if r is None else str(r) for r in rel),
                    tex_escape(where),
                    tex_escape(degree),
                    "%s = %s" % (shape, tex_escape(root + quality))))
        self.w(r"\end{movablelist}")
        self.w(r"\begin{rootmapnote}")
        self.w(r"Shape is the fingering above its lowest fret. Slide it "
               r"one fret, the chord rises a semitone.\\")
        self.w(r"Bottom is the degree on the lowest string. The page "
               r"before gives the fret.")
        self.w(r"\end{rootmapnote}")
        self.w(r"\end{bookpage}")

    # Degree, semitones from the tonic, and the quality that degree takes.
    MAJOR_NUMBERS = [("1", 0, ""), ("2m", 2, "m"), ("3m", 4, "m"),
                     ("4", 5, ""), ("5", 7, ""), ("6m", 9, "m"),
                     ("7\\textdegree", 11, "o")]
    MINOR_NUMBERS = [("1m", 0, "m"), ("2\\textdegree", 2, "o"),
                     ("b3", 3, ""), ("4m", 5, "m"), ("5m", 7, "m"),
                     ("b6", 8, ""), ("b7", 10, "")]

    def number_chart(self, title, numbers, note):
        """The same twelve keys the book already has, read sideways.

        A chord book answers "what is Bbm7"; a number chart answers "what
        is the four chord here", which is the question a band asks. Both
        are the same twelve rows, so this costs two pages and saves
        transposing in your head on a stage.
        """
        self.w(r"\begin{bookpage}{%s}" % title)
        self.w(r"\pagesubtitle{Any instrument}")
        self.w(r"\begin{numberchart}")
        self.w(r"\numberhead{%s}" % "}{".join(n for n, _, _ in numbers))
        for key in ROOT_KEYS:
            cells = []
            for _, interval, quality in numbers:
                name = theory.spell_in_key(key, interval)
                cells.append(r"\numbercell{%s}"
                             % tex_escape(name + quality.replace("o", "\u00b0")))
            self.w(r"\numberrow{%s}{%s}"
                   % (tex_escape(key), " & ".join(cells)))
        self.w(r"\end{numberchart}")
        self.w(r"\begin{rootmapnote}")
        self.w(note)
        self.w(r"\end{rootmapnote}")
        self.w(r"\end{bookpage}")

    def number_charts(self):
        """Chord names, not fingerings, so this is the same page for all
        six instruments. It sits once at the back rather than four times
        over, and the reader goes from a number to a name here and from a
        name to a shape on the instrument's own pages."""
        self.w(r"\usevoicingcolor{ink}")
        self.number_chart(
            "Numbers, Major", self.MAJOR_NUMBERS,
            r"Read across: in the key on the left, the four chord is the "
            r"column headed 4. Call a song in numbers and it transposes "
            r"itself.")
        self.number_chart(
            "Numbers, Minor", self.MINOR_NUMBERS,
            r"The natural minor. Players often raise the seventh of the "
            r"five chord to make it dominant, which turns 5m into 5.")

    def voicing_marks(self, instrument, symbol, frets_text):
        """Superscript caveats: r for rootless, i for inversion.

        Printed next to the fingering rather than the chord name, because
        a chord can have two voicings where only one of them is rootless.
        """
        meta = self.instruments[instrument]
        marks = validate.marks_for(meta["tuning"], symbol, frets_text,
                                   meta.get("reentrant", False))
        return "".join(r"\vmark{%s}" % m for m in marks)

    def ordered_chords(self, chords):
        """Group first, then the order the group lists them in."""
        def rank(entry):
            g = group_index(entry["chord"])
            try:
                _, quality, bass = theory.parse_chord(entry["chord"])
            except theory.ChordError:
                return (g, 99, entry["chord"])
            if bass is not None:
                return (g, bass, entry["chord"])
            within = CHORD_GROUPS[g][1].index(quality) \
                if g < len(CHORD_GROUPS) and quality in CHORD_GROUPS[g][1] \
                else 99
            return (g, within, entry["chord"])
        return sorted(chords, key=rank)

    def key_heading(self, key):
        enh = {"Bb": "A\\#", "Db": "C\\#", "Eb": "D\\#",
               "Gb": "F\\#", "Ab": "G\\#", "B": "C$\\flat$"}
        if key in enh:
            return r"%s\,/\,%s" % (tex_escape(key), enh[key])
        return tex_escape(key)

    def tuning_label(self, instrument):
        """How the tuning is written on the page.

        Usually just the open strings, but the banjo and the five-string
        bass each have a string the fret numbers do not cover -- the drone
        and the low B -- so those are named in parentheses.
        """
        meta = self.instruments[instrument]
        if "tuning_label" in meta:
            return meta["tuning_label"]
        return " ".join(t[:-1] for t in meta["tuning"])

    # -- piano -----------------------------------------------------------

    def piano_section(self):
        self.w(r"\usevoicingcolor{%s}" % INK["piano"])
        self.w(r"\sectiondivider{Piano Chords}{notes, low to high}")
        self.circle_of_fifths("piano")
        self.piano_shells()
        doc = self.voicings["piano"]
        by_key = {k["key"]: k for k in doc["keys"]}
        for key in CHROMATIC:
            block = by_key.get(key)
            if not block:
                continue
            ordered = self.ordered_chords(block["chords"])
            for n, chunk in enumerate(paginate(ordered, PIANO_PER_PAGE)):
                self.w(r"\begin{pianopage}{%s}{%s}"
                       % (self.key_heading(key), "cont" if n else ""))
                last = None
                for entry in chunk:
                    g = group_index(entry["chord"])
                    starts_group = last is not None and g != last
                    if starts_group:
                        self.w(r"  \pianogap")
                    last = g
                    shapes = list(entry["frets"])
                    spread = self.piano_open(entry["chord"])
                    if spread and spread not in shapes:
                        shapes.append(spread)
                    self.w(r"  \pianorow%s{%s}{%s}" % (
                        "first" if starts_group else "",
                        tex_escape(entry["chord"]),
                        r" \pianonext ".join(
                            notes_tex(f) for f in shapes)))
                self.w(r"\end{pianopage}")

    def piano_shells(self):
        """Shells and inversions, given once as rules rather than per chord.

        Both are mechanical on a keyboard: a shell is the chord with its
        fifth taken out, an inversion is the same notes rotated. Printing
        either one under all twelve keys would cost a dozen pages to say
        the same thing a dozen times, so they are stated once, in C, and
        the reader moves them.
        """
        self.w(r"\begin{bookpage}{Shells and Inversions}")
        self.w(r"\pagesubtitle{Piano \quad shown in C, move them anywhere}")
        rows = [
            ("7",     "R 3 b7",  "C E Bb",  False),
            ("maj7",  "R 3 7",   "C E B",   False),
            ("m7",    "R b3 b7", "C Eb Bb", False),
            ("m7b5",  "R b3 b7", "C Eb Bb", False),
            ("9",     "3 b7 9",  "E Bb D",  False),
            ("maj9",  "3 7 9",   "E B D",   False),
        ]
        for name, degrees, notes, first in rows:
            self.w(r"  \pianorow%s{%s}{%s}" % (
                "first" if first else "", tex_escape(name),
                r"%s \voicingsep %s" % (
                    r"\notes{%s}" % r"\notesep ".join(degrees.split()),
                    notes_tex("-".join(notes.split())))))
        self.w(r"  \pianogap")
        for name, notes, first in [
                ("root", "C-E-G", True),
                ("1st", "E-G-C", False),
                ("2nd", "G-C-E", False),
                ("3rd", "Bb-C-E-G", False)]:
            self.w(r"  \pianorow%s{%s}{%s}"
                   % ("first" if first else "", name, notes_tex(notes)))
        self.w(r"\begin{rootmapnote}")
        self.w(r"A shell is the chord with its fifth taken out. The fifth "
               r"says nothing about the chord, and leaving it out gets the "
               r"third and the seventh, the two notes that do, under one "
               r"hand.\\")
        self.w(r"The ninth chords go further and drop the root as well: the "
               r"bass has it. Third, seventh, ninth is the whole sound.\\")
        self.w(r"For inversions, take whichever one moves least from the "
               r"chord before it. Holding a common tone and stepping the "
               r"rest is what makes a progression sound joined up rather "
               r"than jumped between.")
        self.w(r"\end{rootmapnote}")
        self.w(r"\end{bookpage}")

    def piano_open(self, symbol):
        """The spread voicing for a chord, where the shape table has one.

        These are the worship voicings the notebook was built from: the
        same notes as the close shape, opened out across two hands so the
        third sits on top and the fifth carries the middle. A pianist
        reaches for these far more often than for a root position triad,
        which is why they belong on the page and not only in the data.
        """
        try:
            root, quality, bass = theory.parse_chord(symbol)
        except theory.ChordError:
            return None
        if bass is not None:
            return None
        shape = self.piano_shapes["shapes"].get(quality)
        if not shape or "open" not in shape:
            return None
        if shape["open"] == shape.get("close"):
            return None
        name = theory.spell(root)
        return "-".join(theory.spell_in_key(name, i % 12, quality)
                        for i in shape["open"])

    # -- banjo -----------------------------------------------------------

    def banjo_section(self):
        """Banjo pages, plus where to spike the drone for each key.

        Paginated like the other instruments -- it carries the full
        vocabulary now, which is far more than fits four keys to a page --
        with the drone instruction repeated at the head of every key, since
        that is the thing you need before you play a note in it.
        """
        self.w(r"\usevoicingcolor{%s}" % INK["banjo"])
        self.w(r"\sectiondivider{Banjo Chords}{%s}"
               % tex_escape(self.tuning_label("banjo")))
        self.circle_of_fifths("banjo")
        self.root_positions("banjo")
        self.movable_shapes("banjo")
        doc = self.voicings["banjo"]
        by_key = {k["key"]: k for k in doc["keys"]}
        spikes = {r["key"]: r for r in self.spikes["keys"]}

        for key in CHROMATIC:
            block = by_key.get(key)
            if not block:
                continue
            for n, chunk in enumerate(paginate(block["chords"],
                                               CHORDS_PER_PAGE)):
                spike = spikes[key]
                major = self.spike_phrase(spike["major"])
                minor = self.spike_phrase(spike["minor"])
                if n:
                    drone = ""
                elif major == minor:
                    # Same answer either way, so say it once.
                    drone = r"\dronenoteboth{%s}" % major
                else:
                    drone = r"\dronenote{%s}{%s}" % (major, minor)
                if drone:
                    # Tells the page frame to lift its rule: what follows
                    # is a caption, not a row of fret digits.
                    self.w(r"\dronepage")
                self.w(r"\begin{chordpage}{Banjo}{%s}{%s}{%s}"
                       % (self.key_heading(key), "cont" if n else "", drone))
                self.emit_chords(chunk, "banjo")
                self.w(r"\end{chordpage}")

    def spike_phrase(self, s):
        """Where to catch the 5th string for this key.

        Only three spikes exist on this neck, so for some keys the answer
        is to move the string instead: one peg turn off the nearest spike.
        """
        if s["open"]:
            where = r"open \frets{g}"
        else:
            where = r"\frets{%d}" % s["fret"]
        if s.get("detune"):
            where += r", tune %s" % ("down" if s["detune"] < 0 else "up")
        return r"%s $\rightarrow$ \frets{%s}" % (where, tex_escape(s["note"]))

    # -- bass ------------------------------------------------------------

    def bass_section(self):
        self.w(r"\usevoicingcolor{%s}" % INK["bass"])
        self.w(r"\sectiondivider{Bass}{%s}"
               % tex_escape(self.tuning_label("bass")))
        self.circle_of_fifths("bass")
        self.w(r"\begin{bookpage}{Root Positions}")
        self.w(r"\pagesubtitle{Bass}")
        strings = self.bass["root_map"]["strings"]
        self.w(r"\begin{rootmap}{%d}{7pt}" % len(strings))
        self.w(r"\rootmaphead{%s}"
               % " & ".join(r"{\bfseries %s}" % ("(%s)" % n if n == "B" else n)
                            for n in strings))
        for note in ROOT_KEYS:
            frets = self.bass["root_map"]["notes"][note]
            self.w(r"\rootmaprow{%s}{%s}"
                   % (tex_escape(note),
                      " & ".join(r"\frets{%d}" % f for f in frets)))
        self.w(r"\end{rootmap}")
        self.w(r"\begin{rootmapnote}")
        self.w(r"Fret for the root of each key on each string.\\")
        self.w(r"Everything else is measured from there.")
        self.w(r"\end{rootmapnote}")
        self.w(r"\end{bookpage}")

        self.bass_vocabulary()
        self.w(r"\begin{bookpage}{Patterns}")
        self.w(r"\pagesubtitle{Bass \quad counted from the root}")
        self.w(r"\begin{patternlist}")
        for p in self.bass["patterns"]:
            self.w(r"\patternitem{%s}{%s}{%s}"
                   % (tex_escape(p["name"]), self.pattern_grid(p),
                      tex_escape(p["use"])))
        self.w(r"\end{patternlist}")
        self.w(r"\end{bookpage}")

    def pattern_grid(self, pattern):
        """One pattern as three aligned rows: degree, string, fret.

        Naming the string and the fret separately is what makes the shape
        movable. The degree alone doesn't say where to put a finger, and a
        fret alone doesn't either, because the same fret on the next string
        is a different note.
        """
        degrees = pattern["degrees"]
        cells = [(d["degree"],
                  "R" if d["string"] == 0 else "%d+R" % d["string"],
                  "R%d" % d["offset"]) for d in degrees]
        spec = ("@{}r@{\\hskip 2mm}"
                + "l@{\\hskip 3mm}" * (len(cells) - 1) + "l@{}")
        rows = [
            r"\patternrow{degree} & " + " & ".join(
                r"\frets{%s}" % tex_escape(c[0]) for c in cells),
            r"\patternrow{string} & " + " & ".join(
                r"\patterncell{%s}" % c[1] for c in cells),
            r"\patternrow{fret} & " + " & ".join(
                r"\patterncell{%s}" % c[2] for c in cells)]
        return (r"\begin{tabular}{%s}%s\end{tabular}"
                % (spec, ("\\\\\n".join(rows)) + "\n"))

    def bass_vocabulary(self):
        """Which degrees to play under every chord in the book.

        A bass player doesn't finger chord grids, so the other instruments'
        page of shapes would be no use here. What is useful is knowing which
        notes belong under a chord you have never seen called before, and
        where they sit relative to the root.
        """
        self.w(r"\begin{bookpage}{What to Play Under}")
        self.w(r"\pagesubtitle{Bass \quad degrees from the root}")
        self.w(r"\begin{degreetable}")
        # Grouped like the chord pages: triads, sixths, sevenths, ninths,
        # so a bass player finds the row in the same place they would find
        # the chord on any other instrument's page.
        last = None
        for quality in theory.VOCABULARY:
            g = GROUP_OF.get(quality, SLASH_GROUP - 1)
            starts_group = last is not None and g != last
            if starts_group:
                self.w(r"  \chordgap")
            last = g
            label = ("major" if quality == "" else
                     quality.replace("o", "°"))
            degrees = [self.degree_name(i, quality)
                       for i in theory.QUALITIES[quality]]
            self.w(r"\degreerow%s{%s}{%s}" % (
                "first" if starts_group else "",
                tex_escape(label),
                " ".join(r"\frets{%s}" % tex_escape(d) for d in degrees)))
        self.w(r"\end{degreetable}")
        self.w(r"\begin{rootmapnote}")
        # One sentence per line: three separate rules, not a paragraph.
        self.w(r"Play the root, and the fifth if there is one.\\")
        self.w(r"Add the tone that names the chord, the \frets{b3} or "
               r"the \frets{b7}, only when it wants hearing.\\")
        self.w(r"The rest belongs to whoever is playing chords.")
        self.w(r"\end{rootmapnote}")
        self.w(r"\end{bookpage}")

    # Accidental first, the way a chord symbol writes it: b3, not 3b. This
    # matches Am7b5, Gb, and every other symbol in the book.
    DEGREE_NAMES = {0: "R", 1: "b9", 2: "9", 3: "b3", 4: "3", 5: "4",
                    6: "b5", 7: "5", 8: "#5", 9: "6", 10: "b7", 11: "7"}

    # A suspension replaces the third rather than stacking above the
    # seventh, so its added tone is a 2, not a 9 -- the same reason sus4
    # is written 4 and never 11.
    DEGREE_OVERRIDES = {"sus2": {2: "2"}}

    def degree_name(self, interval, quality=None):
        interval %= 12
        override = self.DEGREE_OVERRIDES.get(quality, {})
        return override.get(interval, self.DEGREE_NAMES[interval])

    def offset_phrase(self, d):
        names = ["same string", "next string",
                 "two over from root", "three over from root"]
        where = names[d["string"]] if d["string"] < len(names) else ""
        if d["offset"] == 0:
            return "(%s)" % where
        return "(%+d, %s)" % (d["offset"], where)

    # -- back ------------------------------------------------------------

    def back_matter(self):
        # A single-instrument edition carries its own tuning and no one
        # else's: a mandolin booklet has no use for the bass tuning, and
        # printing it there is the kind of thing that makes a small book
        # feel like an offcut of a big one.
        if self.only:
            order = [self.only]
        else:
            order = ["mandolin", "guitar", "bass", "ukulele", "banjo", "piano"]
        rows = []
        for name in order:
            meta = self.instruments[name]
            label = (self.tuning_label(name)
                     if meta.get("kind", "frets") == "frets" else "")
            rows.append((meta["name"], label, meta.get("note", "")))
        # The credits name this edition, not the series: someone holding
        # the bass booklet should see what they are holding.
        name = self.instruments[self.only]["name"] + " " if self.only else ""
        self.w(r"\begin{backsheet}{Fancy %sChords and Their Voicings}" % name)
        for name, tuning, note in rows:
            self.w(r"\tuningrow{%s}{%s}{%s}"
                   % (tex_escape(name), tex_escape(tuning), tex_escape(note)))
        self.w(r"\end{backsheet}")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data", default="data")
    ap.add_argument("--out", default="build/body.tex")
    ap.add_argument("--only", choices=Book.ALL_INSTRUMENTS,
                    help="render one instrument's edition instead of the "
                         "whole book")
    args = ap.parse_args()
    book = Book(args.data, args.only)
    text = book.render()
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w") as fh:
        fh.write("% Generated by tools/render.py -- do not edit.\n")
        fh.write(text)
    print("wrote %s (%d lines)" % (args.out, text.count("\n")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
