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

# Reading order for the chord sections: chromatic, as the notebook has it.
CHROMATIC = ["A", "Bb", "B", "C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab"]

# Scale degrees of a major key, in Nashville columns.
DEGREES = [(0, ""), (2, "m"), (4, "m"), (5, ""), (7, ""), (9, "m"), (11, "°")]
DEGREE_LABELS = ["1", "2m", "3m", "4", "5", "6m", "7°"]

# Instruments that get their own circle of fifths and Nashville chart.
CHART_INSTRUMENTS = ["mandolin", "banjo", "guitar", "bass", "ukulele"]

# Rows per page. These are tuned against the real compiled PDF -- see
# `make pagecheck`, which fails if any page overflows onto an unheaded
# continuation. Change the type size in voicings.cls and these move.
CHORDS_PER_PAGE = 34      # fret grids, one line each
PIANO_PER_PAGE = 34       # note lists, one line each
WORSHIP_PER_PAGE = 8      # name, notes, and a line of description


def tex_escape(s):
    return (s.replace("\\", r"\textbackslash{}")
             .replace("#", r"\#").replace("&", r"\&")
             .replace("_", r"\_").replace("%", r"\%")
             .replace("°", r"\degsign{}"))


def frets_tex(text):
    """Set a fret string in the monospaced chord face."""
    return r"\frets{%s}" % text.replace("[", r"{\smaller[").replace("]", "]}")


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
    return r"\notes{%s}" % "\,--\,".join(parts)


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

    def bass_fret(self, symbol):
        """Where the root of a chord sits on the bass's E string."""
        root, _, _ = theory.parse_chord(symbol)
        name = theory.spell(root)
        row = self.bass["root_map"]["notes"].get(name)
        return str(row[0]) if row else None

    def voicing_for(self, instrument, symbol):
        if instrument == "bass":
            f = self.bass_fret(symbol)
            return ("E%s" % f) if f is not None else None
        return self.lookup(instrument, symbol)

    # -- emit ------------------------------------------------------------

    def w(self, line=""):
        self.out.append(line)

    def render(self):
        self.front_matter()
        self.contents()
        for inst in CHART_INSTRUMENTS:
            self.circle_of_fifths(inst)
        for inst in CHART_INSTRUMENTS:
            self.nashville(inst)
        self.worship_page()
        for inst in ["mandolin", "guitar", "ukulele"]:
            self.chord_section(inst)
        self.banjo_section()
        self.piano_section()
        self.bass_section()
        self.back_matter()
        return "\n".join(self.out) + "\n"

    # -- front -----------------------------------------------------------

    def front_matter(self):
        self.w(r"\coverpage")
        self.w(r"\nameplatepage")

    def contents(self):
        self.w(r"\begin{bookpage}{Table of Chords}")
        self.w(r"\begin{tocdirectory}")
        self.w(r"\tocline{Circle of Fifths}{one per instrument}")
        self.w(r"\tocline{Nashville Numbers}{one per instrument}")
        self.w(r"\tocline{Core Worship Voicings}{the ones to know}")
        for inst, label in [("mandolin", "Mandolin Chords"),
                            ("guitar", "Guitar Chords"),
                            ("ukulele", "Ukulele Chords"),
                            ("banjo", "Banjo Chords"),
                            ("piano", "Piano Chords"),
                            ("bass", "Bass")]:
            self.w(r"\tocline{%s}{%s}" % (label, self.section_hint(inst)))
        self.w(r"\tocline{Tunings \& Credits}{back sheet}")
        self.w(r"\end{tocdirectory}")
        self.w(r"\vfill")
        self.w(r"\begin{tocnote}")
        self.w(r"Fret numbers read from the lowest string. "
               r"\frets{x} means don't play that string. "
               r"Tunings are on the back sheet.")
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
        self.w(r"\begin{bookpage}{Circle of Fifths}")
        self.w(r"\pagesubtitle{%s}" % tex_escape(title))
        self.w(r"\begin{circleoffifths}{%s}" % tex_escape(title))
        for i, key in enumerate(CIRCLE):
            major = key
            flat = key not in SHARP_KEYS
            minor = theory.spell((theory.NOTE_TO_PC[key] + 9) % 12, flat) + "m"
            mv = self.voicing_for(instrument, major) or ""
            nv = self.voicing_for(instrument, minor) or ""
            self.w(r"  \cofsegment{%d}{%s}{%s}{%s}{%s}{%s}" % (
                i, tex_escape(major), frets_tex(mv) if mv else "",
                tex_escape(minor), frets_tex(nv) if nv else "",
                self.signature(key)))
        self.w(r"\end{circleoffifths}")
        if instrument == "banjo":
            self.w(r"\circlefootnote{Outer ring: major. Inner ring: "
                   r"relative minor. Spike the drone as shown on the "
                   r"banjo pages.}")
        elif instrument == "bass":
            self.w(r"\circlefootnote{Numbers are the fret on the E string. "
                   r"The A string is the same note five frets lower.}")
        else:
            self.w(r"\circlefootnote{Outer ring: major. Inner ring: "
                   r"relative minor. Both show the most common voicing.}")
        self.w(r"\end{bookpage}")

    def signature(self, key):
        sharps = {"C": "", "G": "1\\#", "D": "2\\#", "A": "3\\#", "E": "4\\#",
                  "B": "5\\#", "Gb": "6$\\flat$", "Db": "5$\\flat$",
                  "Ab": "4$\\flat$", "Eb": "3$\\flat$", "Bb": "2$\\flat$",
                  "F": "1$\\flat$"}
        return sharps.get(key, "")

    # -- nashville -------------------------------------------------------

    def nashville(self, instrument):
        """The chart, split across two pages the way the notebook has it.

        Seven degrees of six-string fret numbers will not fit across 3.5
        inches, and shrinking them until they do defeats the purpose of a
        book you read on a dark stage. So: 1-4 on one page, 5-7 on the next.
        """
        title = self.instruments[instrument]["name"]
        for first, last, part in ((0, 4, "1--4"), (4, 7, "5--7")):
            span = list(zip(DEGREES, DEGREE_LABELS))[first:last]
            self.w(r"\begin{bookpage}{Nashville Numbers}")
            self.w(r"\pagesubtitle{%s \quad %s}"
                   % (tex_escape(title), part))
            self.w(r"\begin{nashvilletable}{%d}" % len(span))
            self.w(r"\nashvillehead{%s}"
                   % "".join(r"\nashvillehcell{%s}" % tex_escape(lab)
                             for _, lab in span))
            for key in CIRCLE:
                root = theory.NOTE_TO_PC[key]
                prefer_flat = key not in SHARP_KEYS
                cells = []
                for (interval, suffix), _ in span:
                    sym = theory.spell(root + interval, prefer_flat) + suffix
                    v = self.voicing_for(instrument, sym)
                    cells.append(r"\nashvillecell{%s}{%s}" % (
                        tex_escape(sym),
                        frets_tex(v) if v else r"\notlisted"))
                self.w(r"\nashvillerow{%s}{%s}"
                       % (tex_escape(key), "".join(cells)))
            self.w(r"\end{nashvilletable}")
            if part == "1--4":
                self.w(r"\begin{tocnote}")
                self.w(r"Degrees 5, 6m and 7\degsign{} are overleaf.")
                self.w(r"\end{tocnote}")
            self.w(r"\end{bookpage}")

    # -- chord sections --------------------------------------------------

    def chord_section(self, instrument):
        doc = self.voicings[instrument]
        meta = self.instruments[instrument]
        self.w(r"\sectiondivider{%s Chords}{%s}" % (
            tex_escape(meta["name"]), tex_escape(meta["tuning_label"])
            if "tuning_label" in meta else self.tuning_label(instrument)))
        by_key = {k["key"]: k for k in doc["keys"]}
        for key in CHROMATIC:
            block = by_key.get(key)
            if not block:
                continue
            for n, chunk in enumerate(paginate(block["chords"],
                                               CHORDS_PER_PAGE)):
                self.chord_page(instrument, key, chunk,
                                continued=(n > 0))

    def chord_page(self, instrument, key, chords, continued):
        heading = self.key_heading(key)
        self.w(r"\begin{chordpage}{%s}{%s}{%s}" % (
            tex_escape(self.instruments[instrument]["name"]),
            heading, "cont" if continued else ""))
        for entry in chords:
            marks = r"\derived" if entry.get("derived") else ""
            cells = " ".join(frets_tex(f) for f in entry["frets"])
            self.w(r"  \chordrow{%s%s}{%s}" % (
                tex_escape(entry["chord"]), marks, cells))
        self.w(r"\end{chordpage}")

    def key_heading(self, key):
        enh = {"Bb": "A\\#", "Db": "C\\#", "Eb": "D\\#",
               "Gb": "F\\#", "Ab": "G\\#", "B": "C$\\flat$"}
        if key in enh:
            return r"%s\,/\,%s" % (tex_escape(key), enh[key])
        return tex_escape(key)

    def tuning_label(self, instrument):
        return " ".join(t[:-1] for t in self.instruments[instrument]["tuning"])

    # -- worship voicings ------------------------------------------------

    def worship_page(self):
        """The handful of shapes that carry most of a worship set.

        These are the ones worth knowing cold, so they get their own pages
        rather than being buried in the key-by-key tables. Shown in C,
        because the shape is the point -- every key has them on its own page.
        """
        shapes = yaml.safe_load(open(
            os.path.join(self.data, "piano-shapes.yaml")))
        rows = []
        for quality, shape in shapes["shapes"].items():
            if not shape.get("note"):
                continue
            rows.append((("C" + quality.replace("o", "°")),
                         shape["intervals"], shape["note"],
                         shape.get("star", False), quality))
        for slash in shapes["slashes"]:
            q = slash["quality"]
            bass = theory.spell_in_key("C", slash["bass"], q)
            rows.append(("C%s/%s" % (q, bass),
                         slash["intervals"], slash.get("note", ""), False, q))

        pages = paginate(rows, WORSHIP_PER_PAGE)
        for n, chunk in enumerate(pages):
            self.w(r"\begin{bookpage}{Core Worship Voicings}")
            self.w(r"\pagesubtitle{Shown in C%s}"
                   % (", continued" if n else ""))
            self.w(r"\begin{worshiplist}")
            for symbol, intervals, note, star, quality in chunk:
                self.w(r"\worshiprow{%s}{%s}{%s}{%s}" % (
                    tex_escape(symbol),
                    notes_tex("-".join(
                        theory.spell_in_key("C", i, quality)
                        for i in intervals)),
                    tex_escape(note),
                    "star" if star else ""))
            self.w(r"\end{worshiplist}")
            if n == len(pages) - 1:
                self.w(r"\begin{tocnote}")
                self.w(r"Root and fifth low, colour above, the third high "
                       r"and out of the bass player's way. Leave room: a "
                       r"three- or four-note voicing sounds larger than a "
                       r"dense one. Every key has these on its own page.")
                self.w(r"\end{tocnote}")
            self.w(r"\end{bookpage}")

    # -- piano -----------------------------------------------------------

    def piano_section(self):
        self.w(r"\sectiondivider{Piano Chords}{notes, low to high}")
        doc = self.voicings["piano"]
        by_key = {k["key"]: k for k in doc["keys"]}
        for key in CHROMATIC:
            block = by_key.get(key)
            if not block:
                continue
            for n, chunk in enumerate(paginate(block["chords"],
                                               PIANO_PER_PAGE)):
                self.w(r"\begin{pianopage}{%s}{%s}"
                       % (self.key_heading(key), "cont" if n else ""))
                for entry in chunk:
                    self.w(r"  \pianorow{%s}{%s}" % (
                        tex_escape(entry["chord"]),
                        r" \quad ".join(notes_tex(f) for f in entry["frets"])))
                self.w(r"\end{pianopage}")

    # -- banjo -----------------------------------------------------------

    def banjo_section(self):
        """Banjo pages, plus where to spike the drone for each key.

        Paginated like the other instruments -- it carries the full
        vocabulary now, which is far more than fits four keys to a page --
        with the drone instruction repeated at the head of every key, since
        that is the thing you need before you play a note in it.
        """
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
                self.w(r"\begin{chordpage}{Banjo}{%s}{%s}"
                       % (self.key_heading(key), "cont" if n else ""))
                if n == 0:
                    spike = spikes[key]
                    self.w(r"\dronenote{%s}{%s}"
                           % (self.spike_phrase(spike["major"]),
                              self.spike_phrase(spike["minor"])))
                for entry in chunk:
                    marks = r"\derived" if entry.get("derived") else ""
                    self.w(r"  \chordrow{%s%s}{%s}" % (
                        tex_escape(entry["chord"]), marks,
                        " ".join(frets_tex(f) for f in entry["frets"])))
                self.w(r"\end{chordpage}")
        self.spike_page()

    def spike_phrase(self, s):
        if s["open"]:
            return r"open \frets{g}"
        return r"fret~\frets{%d} (%s)" % (s["fret"], tex_escape(s["note"]))

    def spike_page(self):
        self.w(r"\begin{bookpage}{Spiking the Drone}")
        self.w(r"\pagesubtitle{Banjo, 5th string}")
        self.w(r"\begin{spikeintro}")
        self.w(r"The 5th string rings open every time you brush it, so it "
               r"has to belong to the chord. It isn't fretted --- catch it "
               r"under a spike and leave it there. The string starts at the "
               r"5th fret, so a spike at fret \frets{7} raises the open "
               r"\frets{g} by two semitones, to \frets{A}.")
        self.w(r"\end{spikeintro}")
        self.w(r"\begin{spiketable}")
        for row in self.spikes["keys"]:
            self.w(r"\spikerow{%s}{%s}{%s}{%s}{%s}" % (
                tex_escape(row["key"]),
                self.spike_phrase(row["major"]),
                tex_escape(row["major"]["degree"]),
                self.spike_phrase(row["minor"]),
                tex_escape(row["minor"]["degree"])))
        self.w(r"\end{spiketable}")
        self.w(r"\begin{spikenote}")
        self.w(r"Most necks carry spikes at frets \frets{7}, \frets{9} and "
               r"\frets{10}; \frets{8} and \frets{12} are common additions. "
               r"A fret not on your neck means moving a 5th-string capo. "
               r"Where the drone is the third of the key it colours the "
               r"chord --- move it to the root or the fifth if the tune "
               r"crosses between major and minor.")
        self.w(r"\end{spikenote}")
        self.w(r"\end{bookpage}")

    # -- bass ------------------------------------------------------------

    def bass_section(self):
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
        self.w(r"Fret numbers for the root of each key on each string. "
               r"Everything else is measured from there.")
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
        self.w(r"Play the root, and the fifth if there is one. Add the tone "
               r"that names the chord --- the \frets{b3}, the \frets{b7} "
               r"--- only when it wants hearing. The rest belongs to "
               r"whoever is playing chords.")
        self.w(r"\end{rootmapnote}")
        self.w(r"\end{bookpage}")

    DEGREE_NAMES = {0: "R", 1: "b9", 2: "9", 3: "b3", 4: "3", 5: "4",
                    6: "b5", 7: "5", 8: "#5", 9: "6", 10: "b7", 11: "7"}

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
