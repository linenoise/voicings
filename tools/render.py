#!/usr/bin/env python3
"""Turn data/ into LaTeX. Writes build/body.tex.

The LaTeX side owns page geometry and typography; this file owns what goes
on which page and in what order. Nothing here does music theory beyond
asking tools/theory.py which chords sit in a key.
"""

import argparse
import glob
import os
import sys

import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import theory  # noqa: E402

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
                  "7b9", "7#9", "m11", "11", "13"]),
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

CHORDS_PER_PAGE = 34      # fret grids, one line each
PIANO_PER_PAGE = 34       # two columns; a key fits one page
WORSHIP_PER_PAGE = 8      # name, notes, and a line of description


def tex_escape(s):
    return (s.replace("\\", r"\textbackslash{}")
             .replace("#", r"\#").replace("&", r"\&")
             .replace("_", r"\_").replace("%", r"\%")
             .replace("°", r"\degsign{}"))


def frets_tex(text):
    """Set a fret string in the monospaced chord face."""
    body = text.replace("[", r"{\smaller[").replace("]", "]}")
    # Two digits per string is wider than a column allows at full size.
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
    def __init__(self, data="data"):
        self.data = data
        with open(os.path.join(data, "instruments.yaml")) as fh:
            self.instruments = yaml.safe_load(fh)
        with open(os.path.join(data, "banjo-spikes.yaml")) as fh:
            self.spikes = yaml.safe_load(fh)
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
        not "whichever fret is lowest" -- that lands G on the open G string,
        an octave up and thin, when the whole point of the instrument is the
        bottom. Work up from the lowest string and take the first one that
        falls inside first position: C at the third fret of the A string,
        not the eighth of the E; G at the third fret of the E, not the open
        G. Name the string as well as the fret, since a bare number says
        nothing on its own.
        """
        root, _, _ = theory.parse_chord(symbol)
        name = theory.spell(root)
        row = self.bass["root_map"]["notes"].get(name)
        if not row:
            return None
        strings = self.bass["root_map"]["strings"]
        for string, fret in zip(strings, row):
            if fret <= FIRST_POSITION:
                return "%s%d" % (string, fret)
        string, fret = min(zip(strings, row), key=lambda sf: sf[1])
        return "%s%d" % (string, fret)

    def voicing_for(self, instrument, symbol):
        if instrument == "bass":
            return self.bass_root(symbol)
        return self.lookup(instrument, symbol)

    # -- emit ------------------------------------------------------------

    def w(self, line=""):
        self.out.append(line)

    def render(self):
        self.front_matter()
        self.contents()
        for inst in CHART_INSTRUMENTS:
            self.circle_of_fifths(inst)
        for inst in ["mandolin", "guitar", "ukulele"]:
            self.chord_section(inst)
        self.piano_section()
        self.banjo_section()
        self.bass_section()
        self.back_matter()
        return "\n".join(self.out) + "\n"

    # -- front -----------------------------------------------------------

    def front_matter(self):
        # No instrument owns the front matter, so its sample voicings are
        # set in plain ink rather than borrowing whichever colour happens
        # to be current -- a green x on the contents page reads as a
        # mandolin instruction.
        self.w(r"\usevoicingcolor{ink}")
        self.w(r"\coverpage")

    def contents(self):
        self.w(r"\begin{bookpage}{Table of Chords}")
        self.w(r"\begin{tocdirectory}")
        self.w(r"\tocline{Circle of Fifths}{one per instrument}")
        for inst, label in [("mandolin", "Mandolin Chords"),
                            ("guitar", "Guitar Chords"),
                            ("ukulele", "Ukulele Chords"),
                            ("piano", "Piano Chords"),
                            ("banjo", "Banjo Chords"),
                            ("bass", "Bass")]:
            self.w(r"\tocline{%s}{%s}" % (label, self.section_hint(inst)))
        self.w(r"\tocline{Tunings \& Credits}{back sheet}")
        self.w(r"\end{tocdirectory}")
        self.w(r"\vfill")
        self.w(r"\begin{tocnote}")
        # One sentence per line: three short rules read as three rules
        # when they are stacked, and as a paragraph when they are not.
        self.w(r"Fret numbers read from the lowest string.\\")
        self.w(r"\frets{x} means don't play that string.\\")
        self.w(r"Tunings are on the back sheet.")
        self.w(r"\end{tocnote}")
        self.w(r"\end{bookpage}")

    def section_hint(self, inst):
        if inst == "bass":
            return "roots \\& patterns"
        if inst == "piano":
            return "360 voicings, 12 keys"
        doc = self.voicings.get(inst)
        if not doc:
            return ""
        n = sum(len(k["chords"]) for k in doc["keys"])
        return "%d chords, 12 keys" % n

    # -- circle of fifths ------------------------------------------------

    def circle_of_fifths(self, instrument):
        title = self.instruments[instrument]["name"]
        self.w(r"\usevoicingcolor{%s}" % INK[instrument])
        self.w(r"\begin{bookpage}{Circle of Fifths}")
        self.w(r"\pagesubtitle{%s}" % tex_escape(title))
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
            self.w(r"\circlefootnote{String and fret for each root.\\ "
                   r"\frets{A3} is the third fret of the A string.\\ "
                   r"Whichever sits lowest on the neck.}")
        else:
            self.w(r"\circlefootnote{Outer ring: major.\\ "
                   r"Inner ring: relative minor.\\ "
                   r"Both show the most common voicing.}")
        self.w(r"\end{bookpage}")

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
            return "-".join(
                tex_escape(n[:1]) + "".join(
                    r"$\flat$" if a == "b" else r"$\sharp$" for a in n[1:])
                for n in notes)
        return tex_escape(str(text))

    def signature(self, key):
        sharps = {"C": "", "G": "1\\#", "D": "2\\#", "A": "3\\#", "E": "4\\#",
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
        by_key = {k["key"]: k for k in doc["keys"]}
        for key in CHROMATIC:
            block = by_key.get(key)
            if not block:
                continue
            ordered = self.ordered_chords(block["chords"])
            for n, chunk in enumerate(paginate(ordered, CHORDS_PER_PAGE)):
                self.chord_page(instrument, key, chunk,
                                continued=(n > 0))

    def chord_page(self, instrument, key, chords, continued):
        heading = self.key_heading(key)
        self.w(r"\begin{chordpage}{%s}{%s}{%s}{}" % (
            tex_escape(self.instruments[instrument]["name"]),
            heading, "cont" if continued else ""))
        self.emit_chords(chords)
        self.w(r"\end{chordpage}")

    def emit_chords(self, chords):
        """Rows, with a gap wherever the kind of chord changes."""
        last = None
        for entry in chords:
            g = group_index(entry["chord"])
            if last is not None and g != last:
                self.w(r"  \chordgap")
            last = g
            cells = r"\voicingnext ".join(
                frets_tex(f) for f in entry["frets"])
            self.w(r"  \chordrow{%s}{%s}" % (
                tex_escape(entry["chord"]), cells))

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
        return " ".join(t[:-1] for t in self.instruments[instrument]["tuning"])

    # -- piano -----------------------------------------------------------

    def piano_section(self):
        self.w(r"\usevoicingcolor{%s}" % INK["piano"])
        self.w(r"\sectiondivider{Piano Chords}{notes, low to high}")
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
                for entry in chunk:
                    self.w(r"  \pianorow{%s}{%s}" % (
                        tex_escape(entry["chord"]),
                        r" \voicingsep ".join(
                            notes_tex(f) for f in entry["frets"])))
                self.w(r"\end{pianopage}")

    # -- banjo -----------------------------------------------------------

    def banjo_section(self):
        """Banjo pages, plus where to spike the drone for each key.

        Paginated like the other instruments -- it carries the full
        vocabulary now, which is far more than fits four keys to a page --
        with the drone instruction repeated at the head of every key, since
        that is the thing you need before you play a note in it.
        """
        self.w(r"\usevoicingcolor{%s}" % INK["banjo"])
        self.w(r"\sectiondivider{Banjo Chords}{gDGBD, open G}")
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
                self.w(r"\begin{chordpage}{Banjo}{%s}{%s}{%s}"
                       % (self.key_heading(key), "cont" if n else "", drone))
                self.emit_chords(chunk)
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
        self.w(r"\sectiondivider{Bass}{E A D G}")
        self.w(r"\begin{bookpage}{Where the Roots Are}")
        self.w(r"\pagesubtitle{Bass}")
        self.w(r"\begin{rootmap}")
        self.w(r"\rootmaphead{%s}"
               % "}{".join(self.bass["root_map"]["strings"]))
        for note in ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A",
                     "Bb", "B"]:
            frets = self.bass["root_map"]["notes"][note]
            self.w(r"\rootmaprow{%s}{%s}"
                   % (tex_escape(note),
                      "}{".join(str(f) for f in frets)))
        self.w(r"\end{rootmap}")
        self.w(r"\begin{rootmapnote}")
        self.w(r"Fret numbers for the root of each key on each string.\\")
        self.w(r"Everything else is measured from there.")
        self.w(r"\end{rootmapnote}")
        self.w(r"\end{bookpage}")

        self.bass_vocabulary()
        self.w(r"\begin{bookpage}{Patterns}")
        self.w(r"\pagesubtitle{Bass}")
        self.w(r"\begin{patternlist}")
        for p in self.bass["patterns"]:
            degs = ", ".join(
                r"\frets{%s}~%s" % (d["degree"], self.offset_phrase(d))
                for d in p["degrees"])
            self.w(r"\patternitem{%s}{%s}{%s}"
                   % (tex_escape(p["name"]), degs, tex_escape(p["use"])))
        self.w(r"\end{patternlist}")
        self.w(r"\end{bookpage}")

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
        for quality in theory.VOCABULARY:
            label = ("major" if quality == "" else
                     quality.replace("o", "°"))
            degrees = [self.degree_name(i)
                       for i in theory.QUALITIES[quality]]
            self.w(r"\degreerow{%s}{%s}" % (
                tex_escape(label),
                " ".join(r"\frets{%s}" % tex_escape(d) for d in degrees)))
        self.w(r"\end{degreetable}")
        self.w(r"\begin{rootmapnote}")
        # One sentence per line: three separate rules, not a paragraph.
        self.w(r"Play the root, and the fifth if there is one.\\")
        self.w(r"Add the tone that names the chord --- the \frets{3b}, "
               r"the \frets{7b} --- only when it wants hearing.\\")
        self.w(r"The rest belongs to whoever is playing chords.")
        self.w(r"\end{rootmapnote}")
        self.w(r"\end{bookpage}")

    # Number first, then the accidental that modifies it: 3b, not b3.
    # Chord symbols keep their conventional spelling -- Am7b5 stays Am7b5 --
    # this is only how the degrees are named on the bass pages.
    DEGREE_NAMES = {0: "R", 1: "9b", 2: "9", 3: "3b", 4: "3", 5: "4",
                    6: "5b", 7: "5", 8: "5#", 9: "6", 10: "7b", 11: "7"}

    def degree_name(self, interval):
        return self.DEGREE_NAMES[interval % 12]

    def offset_phrase(self, d):
        names = ["same string", "next string", "two over", "three over"]
        where = names[d["string"]] if d["string"] < len(names) else ""
        if d["offset"] == 0:
            return "(%s)" % where
        return "(%+d, %s)" % (d["offset"], where)

    # -- back ------------------------------------------------------------

    def back_matter(self):
        rows = []
        for name in ["mandolin", "guitar", "bass", "ukulele", "banjo"]:
            meta = self.instruments[name]
            rows.append((meta["name"], self.tuning_label(name),
                         meta.get("note", "")))
        self.w(r"\begin{backsheet}")
        for name, tuning, note in rows:
            self.w(r"\tuningrow{%s}{%s}{%s}"
                   % (tex_escape(name), tex_escape(tuning), tex_escape(note)))
        self.w(r"\end{backsheet}")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data", default="data")
    ap.add_argument("--out", default="build/body.tex")
    args = ap.parse_args()
    book = Book(args.data)
    text = book.render()
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w") as fh:
        fh.write("% Generated by tools/render.py -- do not edit.\n")
        fh.write(text)
    print("wrote %s (%d lines)" % (args.out, text.count("\n")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
