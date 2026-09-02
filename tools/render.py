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
# --------------------------------------------------------------- theory
# The theory chapter's content, once, in a markup small enough to set
# both ways. The booklet and the website both read this: prose that
# disagreed with itself across two files would be worse than no prose.
#
#   `x`     a fret number, degree or chord symbol -- the voicing face
#   **x**   bold
#   ^r ^i   the superscript marks the voicings carry
#
# A block is (kind, payload):
#   para        one paragraph
#   terms       [(term, gloss)] -- a hanging list
#   qualities   [(label, quality, what it is for)]; degrees come from
#               theory.QUALITIES, so a chord cannot be explained one way
#               and voiced another
#   note        the small print at the foot of a page
#   circle      the circle of fifths, drawn with no fingerings
#   numbers     the number chart
INTERVAL_NAMES = {
    0: "root", 1: "flat ninth", 2: "ninth, or second",
    3: "minor third", 4: "major third", 5: "fourth, or eleventh",
    6: "flat fifth, or sharp eleventh", 7: "fifth",
    8: "sharp fifth, or flat thirteenth", 9: "sixth, or thirteenth",
    10: "minor seventh", 11: "major seventh",
}

SCALE_STEPS = [("1", "then a tone"), ("2", "then a tone"),
               ("3", "then a semitone"), ("4", "then a tone"),
               ("5", "then a tone"), ("6", "then a tone"),
               ("7", "then a semitone, and you are home")]

THEORY_PAGES = [
    ("reading", "How to Read a Chord", [
        ("para", "A chord symbol is a root and a quality. **Am7** is an A, "
         "and everything after the A says which notes to stack on it. The "
         "root moves; the quality does not."),
        ("wideterms", [
            ("`2013`", "One digit per string, lowest string first. The "
             "number is the fret."),
            ("`x`", "Don't play that string."),
            ("`0`", "Play it open."),
        ]),
        ("para", "Three more marks sit beside the voicings: a slash, a "
         "small **r** and a small **i**. Each is about which notes a "
         "shape leaves out and which one it puts underneath, so they wait "
         "for the inversions and rootless pages, where there are chords "
         "to leave notes out of."),
        ("para", "Each instrument is printed in its own colour, so you "
         "can find the page by the ink. This chapter is in black: it "
         "belongs to all of them."),
    ]),
    ("boxes", "The Same Chord, Two Ways", [
        ("para", "Most chord books draw a box: a grid of strings and "
         "frets with a dot where a finger goes. This one prints the frets "
         "as digits. They say the same thing."),
        ("figure", ("chordboxes", [
            ("`2013`", 4, 0, "2,0,1,3"),
            ("`x32010`", 6, 0, "x,3,2,0,1,0"),
        ], "Mandolin `2013` and guitar `x32010`. One digit per string, "
           "lowest string first, and a dot where the digit says.")),
        ("para", "Read either the same way. The leftmost digit is the "
         "lowest string, `0` is open, `x` is a string you don't play, and "
         "any other number is the fret to stop it at."),
        ("para", "A box has to be redrawn when the chord moves up the "
         "neck. A digit carries its fret with it, which is why this book "
         "fits in a pocket."),
    ]),
    ("chromatic", "The Chromatic Scale", [
        ("para", "Twelve notes, each one fret or one key apart, and then "
         "the whole thing repeats an octave higher. That is every note "
         "there is."),
        ("figure", ("chroma", ["A", "A#", "B", "C", "C#", "D", "D#", "E",
                               "F", "F#", "G", "G#"],
                    "Sharps going up.")),
        ("figure", ("chroma", ["A", "Bb", "B", "C", "Db", "D", "Eb", "E",
                               "F", "Gb", "G", "Ab"],
                    "The same twelve, spelled with flats.")),
        ("para", "Five of the twelve have two names. **A#** and **Bb** are "
         "one fret, one key, one sound -- which name is right depends on "
         "the key you are in, and this book heads those pages with both."),
        ("para", "On a fretted instrument one fret is one semitone, so the "
         "chromatic scale is just walking up the neck. That is the whole "
         "reason a shape with no open strings can be slid: move every note "
         "the same number of semitones and the chord keeps its shape and "
         "changes its name."),
    ]),
    ("intervals", "Notes and Intervals", [
        ("para", "Twelve notes, each a semitone apart, and then it starts "
         "again. An interval is how many semitones lie between two of "
         "them. Every chord in this book is written as intervals from its "
         "root, and that is what makes a shape movable: slide it up a fret "
         "and every interval in it is unchanged."),
        ("intervals", None),
        ("figure", ("chroma", ["R", "b9", "9", "b3", "3", "4", "b5", "5",
                               "#5", "6", "b7", "7"],
                    "Twelve semitones up from any root. Every chord in "
                    "the book is a handful of these.")),
        ("note", "Accidentals are written before the number, the way a "
         "chord symbol writes them: `b3`, not 3`b`."),
    ]),
    ("scale", "The Major Scale", [
        ("para", "Seven of the twelve notes, in a fixed pattern of tones "
         "and semitones. Everything else on these pages is counted against "
         "it."),
        ("scale", None),
        ("figure", ("chroma", ["1", "", "2", "", "3", "4", "", "5", "",
                               "6", "", "7"],
                    "The major scale inside the chromatic one. The gaps "
                    "are the notes it leaves out.")),
        ("para", "**The relative minor.** Start the same seven notes from "
         "the sixth and you have the natural minor of that key. A minor "
         "and C major are the same notes; which one you are in is decided "
         "by where the music rests."),
        ("para", "**Why some keys are flat.** A scale uses each letter "
         "once. In F that forces B flat rather than A sharp, because the "
         "scale already has an A. The note is one note; the spelling "
         "depends on the key it is in, which is why the same key heads one "
         "page **Bb** and another **A#**."),
    ]),
    ("circle", "The Circle of Fifths", [
        ("circle", None),
        ("para", "Each step clockwise adds a sharp or drops a flat, and "
         "moves the root up a fifth. Neighbours share six of their seven "
         "notes, which is why a song can wander one step either way "
         "without anything sounding wrong, and why the `5` chord sits one "
         "step clockwise of home and the `4` one step counter-clockwise."),
    ]),
    ("nashville", "Nashville Numbers", [
        ("para", "Name the chords by their degree in the key instead of by "
         "letter, and a chart transposes itself. `1 4 5` is the same three "
         "chords in every key; the number chart says which letters they "
         "are."),
        ("terms", [("`1`", "major"), ("`2`", "minor"), ("`3`", "minor"),
                   ("`4`", "major"), ("`5`", "major"), ("`6`", "minor"),
                   ("`7`", "diminished")]),
        ("figure", ("chain", ["1", "4", "5", "1"],
                    "The commonest turn there is, in any key.")),
        ("para", "Those are the chords the major scale builds on its own "
         "degrees, using only notes from the key. A number on its own "
         "means that chord; a quality after it means play that instead, "
         "and `4m` in a major key is a borrowed chord rather than a "
         "mistake."),
        ("para", "In a minor key the same seven chords are counted from "
         "the six. A minor song's home chord is the `6m` of its relative "
         "major, or the `1m` if the chart is written in the minor."),
    ]),
    ("numbers", "The Number Chart", [
        ("numbers", None),
    ]),
    ("building", "How Chords Are Built", [
        ("para", "Take a scale degree and stack thirds on it: skip a note, "
         "take a note. Three of them is a triad, four is a seventh chord, "
         "five is a ninth, and so on up. The chord is named for the "
         "highest third in the stack."),
        ("wideterms", [
            ("triad", "`R 3 5`"),
            ("seventh", "`R 3 5 7`"),
            ("ninth", "`R 3 5 7 9`"),
            ("eleventh", "`R 3 5 7 9 11`"),
            ("thirteenth", "`R 3 5 7 9 11 13`"),
        ]),
        ("figure", ("stack", ["R", "3", "5", "7", "9", "11", "13"],
                    "Read from the bottom. Each step up is a third.")),
        ("para", "A thirteenth chord has seven notes and you have four "
         "fingers, so the stack is a claim about which notes belong, not "
         "an instruction to sound all of them. What to leave out is on the "
         "rootless page."),
        ("para", "**Added against stacked.** An **add9** has no seventh: "
         "the ninth is added to a triad rather than reached by stacking "
         "past a seventh. That is the whole difference between **Cadd9** "
         "and **C9**, and it is why the book prints both."),
    ]),
    ("triads", "Triads", [
        ("qualities", [
            ("major", "", "The default. Three notes, and the one every "
             "other chord is measured against."),
            ("m", "m", "Lower the third a semitone. Everything else "
             "stays."),
            ("5", "5", "Root and fifth, no third: neither major nor minor, "
             "so it sits over either. Loud guitars live here."),
            ("+", "+", "Raise the fifth. Restless -- it wants to rise to "
             "the next chord's root."),
            ("dim", "o", "Lower the third and the fifth. Tense and "
             "unstable; usually passing through on the way somewhere."),
            ("sus2", "sus2", "The third is replaced by the second, not "
             "joined by it. Open and unresolved, and neither major nor "
             "minor."),
            ("sus4", "sus4", "The third replaced by the fourth. Leans hard "
             "on whatever follows it."),
        ]),
    ]),
    ("sixths", "Sixths", [
        ("figure", ("stack", ['R', '3', '5', '6'],
                    "A triad with a sixth on top, not a seventh.")),
        ("qualities", [
            ("6", "6", "A major triad with the sixth added. Warmer and "
             "less final than a seventh: ends a song without closing it."),
            ("m6", "m6", "Minor triad, major sixth. The sixth stays major "
             "-- that is what keeps it from being a m7b5 rooted "
             "elsewhere."),
            ("6/9", "6/9", "Sixth and ninth, no seventh. All colour and no "
             "pull, which makes it a good last chord."),
        ]),
    ]),
    ("sevenths", "Sevenths", [
        ("figure", ("stack", ['R', '3', '5', 'b7'],
                    "The fourth third. Everything above this is colour.")),
        ("qualities", [
            ("7", "7", "Major triad, minor seventh. The blues chord, and "
             "the one that pulls to the fourth."),
            ("maj7", "maj7", "Major triad, major seventh. Still: it is not "
             "pulling anywhere."),
            ("m7", "m7", "Minor triad, minor seventh. The workhorse of the "
             "two chord."),
            ("dim7", "o7", "Minor thirds all the way up. Symmetrical, so "
             "one shape names four chords, three frets apart."),
            ("m7b5", "m7b5", "A diminished triad with a minor seventh. The "
             "two chord of a minor key. Also called half-diminished."),
            ("7sus4", "7sus4", "A seventh with the fourth in place of the "
             "third. Suspends the pull without cancelling it."),
            ("7sus2", "7sus2", "The same idea with the second. Not voiced "
             "in this book."),
            ("7b5", "7b5", "Flatten the fifth of a seventh. It shares "
             "three notes with the 7b5 a tritone away, which is why the "
             "two stand in for each other."),
            ("7#5", "7#5", "Raise it instead. Reads as an altered "
             "dominant, and sits well before a minor chord."),
        ]),
    ]),
    ("ninths", "Ninths", [
        ("figure", ("stack", ['R', '3', '5', 'b7', '9'],
                    "The seventh has to be there for it to be a ninth.")),
        ("qualities", [
            ("9", "9", "A seventh with the ninth stacked on. The seventh "
             "has to be there; without it you have an add9."),
            ("maj9", "maj9", "Major seventh plus ninth. On four strings "
             "the root is the first thing to go."),
            ("m9", "m9", "Minor seventh plus ninth."),
            ("add9", "add9", "The ninth added to a plain triad, no "
             "seventh. Written **2** in some books and **add2** in "
             "others."),
            ("madd9", "madd9", "The same over a minor triad."),
        ]),
    ]),
    ("altered", "Altered Ninths", [
        ("figure", ("chain", ["2m", "5", "5b9", "1"],
                    "An altered dominant does the same job as a plain "
                    "one, with more tension to resolve.")),
        ("qualities", [
            ("7b9", "7b9", "Dominant with the ninth flattened. Four of its "
             "five notes are a diminished seventh."),
            ("7#9", "7#9", "Dominant with the ninth raised -- the same "
             "pitch as a minor third, which is why it sounds like major "
             "and minor at once."),
            ("9b5", "9b5", "A ninth with the fifth flattened. Not voiced "
             "in this book."),
            ("9#5", "9#5", "A ninth with the fifth raised. Not voiced in "
             "this book."),
            ("9sus4", "9sus4", "A ninth suspending the fourth. Not voiced "
             "in this book."),
            ("m11", "m11", "Minor ninth with the eleventh on top. Six "
             "notes, so something is always dropped."),
        ]),
    ]),
    ("extended", "Elevenths and Thirteenths", [
        ("qualities", [
            ("11", "11", "The eleventh over a dominant. The third is "
             "usually dropped: a natural eleventh sits a semitone above it "
             "and the two fight."),
            ("13", "13", "The thirteenth over a dominant. The same note as "
             "the sixth, an octave up, over a chord that has a seventh."),
            ("m13", "m13", "The same over a minor seventh."),
            ("maj13", "maj13", "And over a major seventh."),
            ("7#11", "7#11", "The raised eleventh, which does not fight "
             "the third. The lydian dominant sound."),
        ]),
        ("note", "Only the guitar has strings enough to voice these, so "
         "they appear on its pages and nowhere else."),
    ]),
    ("inversions", "Inversions", [
        ("para", "A chord is its notes, in any order. Put a note other "
         "than the root at the bottom and you have an inversion: the same "
         "chord, sitting differently."),
        ("wideterms", [("root", "`C E G`"), ("first", "`E G C`"),
                       ("second", "`G C E`"),
                       ("**C/E**", "the chord, a slash, and the note that "
                        "goes underneath it"),
                       ("^i", "this book's mark for a voicing whose lowest "
                        "note is not the root")]),
        ("figure", ("chain", ["C", "C/E", "C/G"],
                    "One chord, three bass notes.")),
        ("para", "Written **C/E** and **C/G** -- the chord, a slash, the "
         "note underneath. Use them to give the bass a line to walk: "
         "**C**, **C/B**, **Am** descends by step where three root "
         "positions would jump."),
        ("para", "On four courses the lowest string is often not the root "
         "whether you meant it or not. Where that happens the voicing is "
         "marked ^i. It is not a fault. It is a warning that the bass note "
         "is doing something, and that if someone else is playing the root "
         "you may be hearing a chord neither of you named."),
    ]),
    ("rootless", "Rootless Voicings", [
        ("para", "Four strings, six notes. Something goes. The order to "
         "drop them in:"),
        ("wideterms", [
            ("first", "`5` -- the fifth says nothing the root has not "
             "already said"),
            ("then", "`R` -- if a bass is playing it"),
            ("never", "`3` or `b3`, which decide major or minor"),
            ("never", "`b7` or `7`, which decide which seventh"),
            ("^r", "this book's mark for a voicing with no root in it"),
        ]),
        ("figure", ("chroma", ["R", "3", "5", "b7"],
                    "A seventh chord, whole.")),
        ("figure", ("chroma", ["", "3", "", "b7"],
                    "The same chord with the root and fifth gone. It is "
                    "still a seventh: those two notes were the ones "
                    "naming it.")),
        ("para", "A voicing with no root is marked ^r. In a band it is "
         "often the better chord: the bass has the root covered, and the "
         "notes you have left are the ones carrying the harmony. On your "
         "own it sounds like a different chord, because it is one."),
        ("para", "This is why **Cmaj9** and **Em7** can be the same four "
         "notes. Context, and whoever is playing underneath, decides which "
         "one you have played."),
    ]),
    ("spacing", "Open and Closed Voicings", [
        ("para", "Two ways to arrange the same notes. A **closed** voicing "
         "packs them into a single octave, stacked as tightly as they "
         "go. An **open** voicing lifts one of the inner notes an octave "
         "and lets the chord breathe across a wider span."),
        ("figure", ("chroma", ["C", "E", "G"],
                    "Closed. Three notes inside one octave.")),
        ("figure", ("chroma", ["C", "G", "C", "E"],
                    "Open. The same chord, spread past the octave, with "
                    "the third on top.")),
        ("para", "Closed voicings turn to mud low down, where the "
         "overtones of notes a third apart collide. Open ones give each "
         "note room, and they make the move to the next chord easier, "
         "because a note that is already spread has somewhere to go."),
        ("para", "**On a fretted instrument you get what the tuning "
         "gives you.** A mandolin or a cello is tuned in fifths, so its "
         "shapes come out open whether you meant them or not. A guitar's "
         "barre chords are close voicings with an octave doubled on top. "
         "There is not much choice in it."),
    ]),
    ("pianovoicing", "Two Voicings for Every Chord", [
        ("para", "**On a piano there is nothing but choice**, so the "
         "piano pages print two voicings for every chord. The first is "
         "closed, the notes in order from the root. The second is the "
         "spread voicing: root and fifth low for the left hand, then the "
         "colour above it with the third on top, which is where the ear "
         "goes looking for it."),
        ("wideterms", [
            ("C", "`C E G` closed, `C G C E` open"),
            ("Cmaj7", "`C E G B` closed, `C G B E` open"),
            ("C9", "`C E G Bb D` closed, `C G Bb D E` open"),
        ]),
        ("para", "Split them at the hands. The left takes the root and "
         "the fifth, the right takes what is left. That is why the "
         "spread voicings are written root-and-fifth first: the break in "
         "the list is where your hands part."),
        ("para", "If a bass player has the root, drop it and play the "
         "right hand alone. You are back at a rootless voicing, and the "
         "^r on those pages is telling you the same thing this one is."),
        ("note", "The spread voicings are the ones the notebook was "
         "written from, and the ones a pianist actually reaches for."),
    ]),
    ("progressions", "Progressions", [
        ("para", "Written in numbers, so they work in any key."),
        ("wideterms", [
            ("`1 4 5`", "Almost everything. Folk, blues, country, most "
             "hymns."),
            ("`1 5 6m 4`", "The four chords a great many pop songs are "
             "made of."),
            ("`2m 5 1`", "The turn jazz is built on. The 2m and the 5 "
             "share three notes."),
            ("`1 6m 4 5`", "Fifties doo-wop."),
            ("`6m 4 1 5`", "The same four chords, starting from the "
             "minor."),
            ("`1 4 1 5`", "Twelve-bar blues in outline. Make all three "
             "sevenths."),
        ]),
        ("figure", ("chain", ["1", "5", "6m", "4"],
                    "Four chords, a great many songs.")),
        ("para", "The pull of `5` to `1` is the engine. It comes from the "
         "tritone inside the seventh chord: the third and the flat "
         "seventh are six semitones apart, and both want to move a "
         "semitone."),
    ]),
    ("substitutions", "Substitutions", [
        ("para", "Chords that share notes can stand in for one another."),
        ("wideterms", [
            ("relative", "`1` and `6m` share two notes. So do `4` and "
             "`2m`."),
            ("tritone", "Any `7` chord can be replaced by the `7` a "
             "tritone away. They share the third and the seventh, "
             "swapped."),
            ("sixths", "A `6` will stand in for a `maj7` at the end of a "
             "phrase, and lands softer."),
            ("sus", "A `sus4` before the chord it resolves to buys a "
             "beat."),
            ("dim7", "Four chords at once: every three frets is the same "
             "shape and the same notes, so one grip covers four roots."),
        ]),
        ("figure", ("chain", ["2m", "b2 7", "1"],
                    "The tritone substitution: put a `b2 7` where the "
                    "`5` was and the bass walks down by semitone.")),
        ("para", "None of this is a rule. It is a list of places where "
         "two chords are close enough that an ear will follow you."),
    ]),
]


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
# Matching tools/piano.py: flat keys spelled with flats, sharp keys
# with sharps, so a voicing never mixes the two.
PIANO_SHARP_KEYS = {"G", "D", "A", "E", "B"}

# Instruments whose pages are about notes, not chord grips. They get
# root positions, patterns and a number chart instead of twelve pages
# of fingerings nobody would play on them.
NOTE_INSTRUMENTS = {"bass", "cello"}

ROOT_KEYS = ["C", "Db", "D", "Eb", "E", "F",
             "Gb", "G", "Ab", "A", "Bb", "B"]

CHART_INSTRUMENTS = ["mandolin", "guitar", "ukulele", "piano", "banjo",
                     "bass", "cello"]

# One pen per instrument, matching the notebook. Defined in voicings.cls.
INK = {
    "mandolin": "fretgreen",
    "guitar":   "fretblue",
    "ukulele":  "fretpurple",
    "piano":    "keyred",
    "banjo":    "fretorange",
    "bass":     "fretyellow",
    "cello":    "fretbrown",
    # Not an instrument. The theory booklet is set in plain ink because
    # it belongs to all of them and none of them.
    "theory":   "ink",
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
# What a chord page holds, counted in voicing lines rather than chords --
# see paginate(). Measured on guitar key G, the fullest in the book: 51
# lines sets clean, 52 is 1.8pt overfull, 53 spills onto a page of its
# own. Mandolin key F sets 54 clean, its four-position grids being
# narrower. The default covers every other instrument, whose fullest key
# is 33 lines.
ROWS_PER_PAGE = {"guitar": 51, "mandolin": 54}
DEFAULT_ROWS_PER_PAGE = 54
PIANO_PER_PAGE = 17
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


def paginate(items, capacity, weight=None):
    """Split into as few pages as fit, then even them out.

    Filling each page to capacity and letting the remainder spill leaves a
    key with twenty-eight chords on one page and one lonely chord on the
    next. Splitting the same key fifteen and fourteen reads better and
    costs nothing.

    `weight` is what an item costs on the page, defaulting to one each.
    Chords are not all one line: a guitar chord with two voicings wraps to
    two, which is how key G came to overflow its page while still counting
    39 chords of a possible 40. Measuring lines instead of chords is the
    difference between a page that splits and a page that spills.
    """
    if not items:
        return [[]]
    if weight is None:
        def weight(_):
            return 1
    total = sum(weight(i) for i in items)
    n_pages = max(1, -(-total // capacity))
    target = -(-total // n_pages)
    pages, page, load = [], [], 0
    for item in items:
        w = weight(item)
        if page and load + w > target:
            pages.append(page)
            page, load = [], 0
        page.append(item)
        load += w
    if page:
        pages.append(page)
    return pages


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
        with open(os.path.join(data, "cello-patterns.yaml")) as fh:
            self.cello = yaml.safe_load(fh)
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

    def string_root(self, instrument, symbol):
        """String and fret for a root, for an instrument that plays notes.

        Same reasoning as the bass: work up from the lowest string and
        take the first that falls under the hand, rather than whichever
        fret happens to be smallest.
        """
        root, _, _ = theory.parse_chord(symbol)
        tuning = self.instruments[instrument]["tuning"]
        pairs = [(t[:-1], (root - theory.parse_note(t)) % 12) for t in tuning]
        for name, fret in pairs:
            if fret <= FIRST_POSITION:
                return "%s%d" % (name, fret)
        return "%s%d" % min(pairs, key=lambda sf: sf[1])

    def voicing_for(self, instrument, symbol):
        if instrument == "bass":
            return self.bass_root(symbol)
        if instrument in NOTE_INSTRUMENTS:
            return self.string_root(instrument, symbol)
        return self.lookup(instrument, symbol)

    # -- emit ------------------------------------------------------------

    def w(self, line=""):
        self.out.append(line)

    def render(self):
        self.front_matter()
        if self.only:
            self.one_instrument(self.only)
            # No number charts in a solo edition. They name chords
            # rather than fingerings, so there is nothing on them that
            # belongs to the instrument the reader picked, and for the
            # bass they cost a second sheet to say so.
            self.back_matter()
            return "\n".join(self.out) + "\n"
        self.contents()
        for inst in ["mandolin", "guitar", "ukulele"]:
            self.chord_section(inst)
        self.piano_section()
        self.banjo_section()
        self.bass_section()
        self.cello_section()
        self.theory_section()
        self.back_matter()
        return "\n".join(self.out) + "\n"

    # -- front -----------------------------------------------------------

    # The order everything lists instruments in: the cover, the tunings on
    # the back sheet, the contents. One list, so the three cannot drift
    # out of step with each other the way they had.
    ALL_INSTRUMENTS = ["mandolin", "guitar", "ukulele",
                       "piano", "banjo", "bass", "cello"]

    def front_matter(self):
        # No instrument owns the front matter, so its sample voicings are
        # set in plain ink rather than borrowing whichever color happens
        # to be current -- a green x on the contents page reads as a
        # mandolin instruction.
        self.w(r"\usevoicingcolor{ink}")
        if self.only:
            name = self.instruments[self.only]["name"]
            # "Fancy / Theory of / Chords and Their Voicings". The other
            # covers read as a compound noun -- Fancy Mandolin Chords --
            # and this one needs the preposition to do the same work.
            if self.only == "theory":
                name += " of"
            subject = r"\coversubject{%s}{%s}" % (tex_escape(name),
                                                  INK[self.only])
            # The title already names the instrument; repeating it under
            # the rule just says the same thing twice.
            listing = ""
        else:
            subject = ""
            # Each in its own pen, the way the notebook is written.
            # Seven names will not sit three and four on a 75mm cover
            # without crowding, so the seventh takes a line of its own.
            names_in_order = self.ALL_INSTRUMENTS
            rows = [names_in_order[i:i + 3]
                    for i in range(0, len(names_in_order), 3)]
            lines = []
            for row in rows:
                names = [r"\textcolor{%s}{%s}"
                         % (INK[i], tex_escape(self.instruments[i]["name"]))
                         for i in row]
                lines.append(r"{\large\bfseries %s\par}"
                             % r"\, $\cdot$\, ".join(names))
            listing = r"\vspace{2.5mm}".join(lines)
        if self.only:
            # The divider page that used to carry the tuning is gone from
            # the solo editions, so the cover carries it instead.
            meta = self.instruments[self.only]
            tuning = r"\covertuning{%s}{%s}" % (
                tex_escape(self.tuning_label(self.only)), INK[self.only]
            ) if meta.get("kind", "frets") == "frets" else ""
        else:
            tuning = ""
        self.w(r"\coverpage{%s}{%s}{%s}" % (subject, listing, tuning))

    def one_instrument(self, inst):
        """A single-instrument edition: that section and nothing else."""
        if inst == "piano":
            self.piano_section()
        elif inst == "banjo":
            self.banjo_section()
        elif inst == "bass":
            self.bass_section()
        elif inst == "cello":
            self.cello_section()
        elif inst == "theory":
            self.theory_section()
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
                            ("bass", "Bass"),
                            ("cello", "Cello")]:
            self.w(r"\tocline{%s}{%s}" % (label, self.section_hint(inst)))
        self.w(r"\tocline{Theory}{how the chords are built}")
        self.w(r"\tocline{Tunings \& Credits}{back sheet}")
        self.w(r"\end{tocdirectory}")
        total = sum(self.voicing_count(i) for i in
                    ("mandolin", "guitar", "ukulele", "piano", "banjo",
                     "cello"))
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
        self.w(r"\vmarkink{i} means the voicing given is an inversion.\\")
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
        if inst == "cello":
            return "roots, patterns \\& %d voicings" % self.voicing_count(inst)
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
            # The theory booklet's circle names keys and signatures and
            # stops there: a fingering in a wedge would belong to an
            # instrument, and this section belongs to none of them.
            if instrument == "theory":
                mv = nv = ""
            else:
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
        elif instrument == "cello":
            self.w(r"\circlefootnote{String and fret for each root: "
                   r"\frets{G3} is the third position on the G string.\\ "
                   r"Lowest that falls under the hand.}")
        elif instrument == "theory":
            self.w(r"\circlefootnote{Outer ring: major.\\ "
                   r"Inner ring: its relative minor -- the same seven "
                   r"notes, counted from the sixth.\\ "
                   r"Centre: the key signature.}")
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
        # A solo edition is already about one instrument: its cover says
        # so and carries the tuning, so a divider page announcing the
        # section says nothing the reader does not know, and the root map
        # duplicates what the movable shapes page sends them to.
        if not self.only:
            self.w(r"\sectiondivider{%s Chords}{%s}" % (
                tex_escape(meta["name"]), tex_escape(meta["tuning_label"])
                if "tuning_label" in meta else self.tuning_label(instrument)))
        self.circle_of_fifths(instrument)
        if not self.only:
            self.root_positions(instrument)
        self.movable_shapes(instrument)
        by_key = {k["key"]: k for k in doc["keys"]}
        for key in CHROMATIC:
            block = by_key.get(key)
            if not block:
                continue
            ordered = self.ordered_chords(block["chords"])
            capacity = ROWS_PER_PAGE.get(instrument, DEFAULT_ROWS_PER_PAGE)
            for n, chunk in enumerate(paginate(ordered, capacity,
                                               lambda e: len(e["frets"]))):
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
        "bass":     [("fifths", "5", 4), ("major", "", 3),
                     ("minor", "m", 3)],
        "cello":    [("fifths", "5", 4), ("major", "", 3),
                     ("minor", "m", 3)],
    }

    # How many strings a closed shape has to sound. Four on a guitar or a
    # mandolin, where a shape is a grip. Two on a bass or a cello, where
    # it is a double stop: those players are sounding notes, not chords,
    # and a four-string barre is not a thing either of them reaches for.
    MIN_SOUNDING = {"bass": 2, "cello": 2}

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
                floor = self.MIN_SOUNDING.get(instrument,
                                              max(4, len(tuning) - 2))
                if len(live) < floor or min(live) != 0:
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
        sparse = instrument in self.MIN_SOUNDING

        def cost(item):
            rel, info = item
            live = [r for r in rel if r is not None]
            muted = sum(1 for r in rel if r is None)
            rooted = 0 if info[1] == "R" else 1
            if sparse:
                # A bass or cello wants the smallest shape that spells the
                # thing, with the root underneath: a double stop, not four
                # strings held down at once. Ranking these the other way
                # offered 0-0-2-2 as a fifth, which is a barre.
                return (-muted, rooted, info[0], sum(live))
            # Everywhere else, fewest muted strings first. Ranking by
            # finger effort instead put x-2-0-0-0-x at the top of "major"
            # on guitar and buried the barre forms, which are the shapes
            # the page exists for.
            return (muted, info[0], sum(live))
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
        if self.only:
            self.w(r"Bottom is the degree on the lowest string.")
        else:
            self.w(r"Bottom is the degree on the lowest string. The page "
                   r"before gives the fret.")
        self.w(r"\end{rootmapnote}")
        self.w(r"\end{bookpage}")

    def number_chart(self, instrument):
        """Which note is the four chord here.

        This belongs to the bass and the cello and nowhere else. On the
        fretted pages a number would have to resolve to a chord, and a
        chord book that names chords without voicing them is a theory
        book. On these two the number resolves to a note, which is the
        thing being played, and the fret for it is on the page before.
        """
        meta = self.instruments[instrument]
        self.w(r"\begin{bookpage}{Numbers}")
        self.w(r"\pagesubtitle{%s \quad the major scale, degree by degree}"
               % tex_escape(meta["name"]))
        self.w(r"\begin{numberchart}")
        self.w(r"\numberhead{%s}"
               % " & ".join(r"{\bfseries\small %d}" % n for n in range(1, 8)))
        for key in ROOT_KEYS:
            cells = []
            for interval in (0, 2, 4, 5, 7, 9, 11):
                name = theory.spell_in_key(key, interval)
                if "bb" in name or "##" in name:
                    name = theory.spell((theory.NOTE_TO_PC[key] + interval) % 12,
                                        key not in PIANO_SHARP_KEYS)
                cells.append(r"\numbercell{%s}" % tex_escape(name))
            self.w(r"\numberrow{%s}{%s}"
                   % (tex_escape(key), " & ".join(cells)))
        self.w(r"\end{numberchart}")
        self.w(r"\begin{rootmapnote}")
        self.w(r"Read across: in the key on the left, the four is the note "
               r"under the 4. A minor key borrows the same row, starting "
               r"from its six.")
        self.w(r"\end{rootmapnote}")
        self.w(r"\end{bookpage}")

    # ------------------------------------------------------------ theory
    # THEORY_PAGES, above, holds the words. These turn them into pages.

    def theory_tex(self, text):
        """The little markup THEORY_PAGES is written in, as LaTeX."""
        out = tex_escape(text)
        out = out.replace("--", "\u2013")
        out = re.sub(r"\*\*(.+?)\*\*", r"\\textbf{\1}", out)
        out = re.sub(r"`(.+?)`", r"\\frets{\1}", out)
        out = re.sub(r"\^([ri])", r"\\vmarkink{\1}", out)
        return out

    def theory_degrees(self, quality):
        """A quality's degrees, from the same table that voices it."""
        return " ".join(r"\frets{%s}" % tex_escape(
            self.degree_name(i, quality)) for i in theory.QUALITIES[quality])

    def theory_section(self):
        """The chapter that explains the rest of the book.

        Everything else here answers "where do I put my fingers". This
        answers "why is that the chord", and it is the one section that
        belongs to no instrument -- so it is set in plain ink, and its
        circle of fifths carries no fingerings.
        """
        self.w(r"\usevoicingcolor{ink}")
        if not self.only:
            self.w(r"\sectiondivider{Theory}{how the chords are built}")
        for slug, title, blocks in THEORY_PAGES:
            if slug == "circle":
                self.circle_of_fifths("theory")
                continue
            if slug == "numbers":
                self.number_chart("theory")
                continue
            self.w(r"\begin{theorypage}{%s}" % tex_escape(title))
            for kind, payload in blocks:
                self.theory_block(kind, payload)
            self.w(r"\end{theorypage}")

    def theory_block(self, kind, payload):
        if kind == "para":
            self.w(r"\theorypara{%s}" % self.theory_tex(payload))
        elif kind == "note":
            self.w(r"\begin{rootmapnote}%s\end{rootmapnote}"
                   % self.theory_tex(payload))
        elif kind == "wideterms":
            self.w(r"\begin{widetermlist}")
            for term, gloss in payload:
                self.w(r"\theoryterm{%s}{%s}"
                       % (self.theory_tex(term), self.theory_tex(gloss)))
            self.w(r"\end{widetermlist}")
        elif kind == "terms":
            self.w(r"\begin{theorycols}")
            for term, gloss in payload:
                self.w(r"\theoryterm{%s}{%s}"
                       % (self.theory_tex(term), self.theory_tex(gloss)))
            self.w(r"\end{theorycols}")
        elif kind == "intervals":
            self.w(r"\begin{theorycols}")
            for i in range(12):
                self.w(r"\theoryterm{\frets{%s}}{%s}"
                       % (tex_escape(self.DEGREE_NAMES[i]),
                          tex_escape(INTERVAL_NAMES[i])))
            self.w(r"\end{theorycols}")
        elif kind == "scale":
            self.w(r"\begin{theorycols}")
            for deg, gap in SCALE_STEPS:
                self.w(r"\theoryterm{\frets{%s}}{%s}"
                       % (deg, tex_escape(gap)))
            self.w(r"\end{theorycols}")
        elif kind == "qualities":
            for label, quality, use in payload:
                self.w(r"\qualityrow{%s}{%s}{%s}"
                       % (self.theory_tex(label),
                          self.theory_degrees(quality),
                          self.theory_tex(use)))
        elif kind == "figure":
            self.theory_figure(payload)
        else:
            raise ValueError("unknown theory block %r" % kind)

    def theory_figure(self, payload):
        """A drawing and its caption. One per topic, where one helps."""
        art = payload[0]
        caption = payload[-1]
        self.w(r"\begin{center}")
        if art == "chordboxes":
            cells = []
            for label, strings, base, dots in payload[1]:
                cells.append(r"\begin{tabular}{@{}c@{}}%s\\[0.6mm]"
                             r"{\footnotesize %s}\end{tabular}"
                             % (r"\chordbox{%d}{%d}{%s}"
                                % (strings, base, dots),
                                self.theory_tex(label)))
            self.w(r"\qquad".join(cells))
        elif art == "chroma":
            self.w(r"\chromastrip{%s}"
                   % ",".join(tex_escape(x) for x in payload[1]))
        elif art == "stack":
            self.w(r"\thirdstack{%s}"
                   % ",".join(tex_escape(x) for x in payload[1]))
        elif art == "chain":
            self.w(r"\chainarrow ".join(
                r"\chainbox{%s}" % tex_escape(x) for x in payload[1]))
        else:
            raise ValueError("unknown figure %r" % art)
        self.w(r"\end{center}")
        self.w(r"\theorycaption{%s}" % self.theory_tex(caption))

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
        if not self.only:
            self.w(r"\sectiondivider{Piano Chords}{%s}"
                   % tex_escape(self.tuning_label("piano")))
        self.circle_of_fifths("piano")
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
                    spread = self.piano_open(entry["chord"], key)
                    if spread and spread not in shapes:
                        shapes.append(spread)
                    # The close voicing goes in a fixed-width box, so the
                    # spread one begins on the same vertical line all the
                    # way down the page instead of tracking the length of
                    # the voicing before it.
                    cells = r"\pianoclose{%s}" % notes_tex(shapes[0])
                    if len(shapes) > 1:
                        cells += r"\voicingsep " + r" \voicingsep ".join(
                            notes_tex(f) for f in shapes[1:])
                    self.w(r"  \pianorow%s{%s}{%s}" % (
                        "first" if starts_group else "",
                        tex_escape(entry["chord"]), cells))
                self.w(r"\end{pianopage}")

    def piano_open(self, symbol, key=None):
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
        # Named by the key you put a finger on, never by function. The
        # spread voicing of Gbm functionally contains a B-double-flat and
        # the close voicing beside it says A: two spellings of one note in
        # one row. Flat keys take flats, sharp keys sharps, matching how
        # tools/piano.py wrote the close voicings.
        flat = (key or theory.spell(root)) not in PIANO_SHARP_KEYS
        return "-".join(theory.spell(root + i, flat) for i in shape["open"])

    # -- banjo -----------------------------------------------------------

    def banjo_section(self):
        """Banjo pages, plus where to spike the drone for each key.

        Paginated like the other instruments -- it carries the full
        vocabulary now, which is far more than fits four keys to a page --
        with the drone instruction repeated at the head of every key, since
        that is the thing you need before you play a note in it.
        """
        self.w(r"\usevoicingcolor{%s}" % INK["banjo"])
        if not self.only:
            self.w(r"\sectiondivider{Banjo Chords}{%s}"
                   % tex_escape(self.tuning_label("banjo")))
        self.circle_of_fifths("banjo")
        if not self.only:
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
        if not self.only:
            self.w(r"\sectiondivider{Bass}{%s}"
                   % tex_escape(self.tuning_label("bass")))
        self.circle_of_fifths("bass")
        self.movable_shapes("bass")
        self.number_chart("bass")
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

    def cello_section(self):
        """Built like the bass section, for the same reason.

        A cellist is sounding one note at a time far more often than
        stopping four strings at once, so twelve pages of chord grips
        would be twelve pages nobody plays. What is useful is the same
        thing the bass gets: where the roots are, what to put under a
        chord, and the shapes for getting between them.
        """
        self.w(r"\usevoicingcolor{%s}" % INK["cello"])
        if not self.only:
            self.w(r"\sectiondivider{Cello}{%s}"
                   % tex_escape(self.tuning_label("cello")))
        self.circle_of_fifths("cello")
        self.movable_shapes("cello")
        self.number_chart("cello")
        self.root_positions("cello")
        self.bass_vocabulary("cello")
        self.w(r"\begin{bookpage}{Patterns}")
        self.w(r"\pagesubtitle{Cello \quad counted from the root}")
        self.w(r"\begin{patternlist}")
        for p in self.cello["patterns"]:
            self.w(r"\patternitem{%s}{%s}{%s}"
                   % (tex_escape(p["name"]), self.pattern_grid(p),
                      tex_escape(p["use"])))
        self.w(r"\end{patternlist}")
        self.w(r"\end{bookpage}")

        # The chord pages come after all of that, not instead of it. A
        # cellist reaches for a double stop far more often than a grip,
        # so the reference pages lead; the grips are there for when the
        # part calls for one.
        doc = self.voicings["cello"]
        by_key = {k["key"]: k for k in doc["keys"]}
        for key in CHROMATIC:
            block = by_key.get(key)
            if not block:
                continue
            ordered = self.ordered_chords(block["chords"])
            capacity = PER_PAGE.get("cello", CHORDS_PER_PAGE)
            for n, chunk in enumerate(paginate(ordered, capacity)):
                self.chord_page("cello", key, chunk, continued=(n > 0))

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

    def bass_vocabulary(self, instrument="bass"):
        """Which degrees to play under every chord in the book.

        A bass player doesn't finger chord grids, so the other instruments'
        page of shapes would be no use here. What is useful is knowing which
        notes belong under a chord you have never seen called before, and
        where they sit relative to the root.
        """
        self.w(r"\begin{bookpage}{What to Play Under}")
        self.w(r"\pagesubtitle{%s \quad degrees from the root}"
               % tex_escape(self.instruments[instrument]["name"]))
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
            order = self.ALL_INSTRUMENTS
        rows = []
        for name in order:
            meta = self.instruments[name]
            # Piano has no tuning but does have a label: the seven note
            # names its voicings are written in.
            label = (self.tuning_label(name)
                     if meta.get("kind", "frets") == "frets"
                     or "tuning_label" in meta else "")
            rows.append((meta["name"], label, meta.get("note", ""),
                         INK[name]))
        # The credits name this edition, not the series: someone holding
        # the bass booklet should see what they are holding.
        name = self.instruments[self.only]["name"] + " " if self.only else ""
        self.w(r"\begin{backsheet}{Fancy %sChords and Their Voicings}" % name)
        for name, tuning, note, pen in rows:
            self.w(r"\tuningrow{%s}{%s}{%s}{%s}"
                   % (tex_escape(name), tex_escape(tuning),
                      tex_escape(note), pen))
        notes = self.reading_notes()
        if notes:
            self.w(r"\readingnotes{%s}" % r"\\".join(notes))
        figure = self.reading_figure()
        if figure:
            self.w(figure)
        self.w(r"\end{backsheet}")

    # One chord per instrument, drawn on the back sheet so a reader can
    # see what a row of digits is a picture of. Chosen for being ordinary,
    # inside the first four frets, and for using the marks the notes
    # beside it explain: an open string, a stopped one, and on the guitar
    # a muted one.
    READING_EXAMPLE = {
        "mandolin": ("C", "0230"),
        "guitar":   ("C", "x32010"),
        "ukulele":  ("F", "2010"),
        "banjo":    ("C", "2012"),
        "cello":    ("C", "0023"),
    }

    def reading_figure(self):
        """The chord box for this edition's example, or nothing."""
        example = self.READING_EXAMPLE.get(self.only)
        if not example or r"\chordrow" not in "\n".join(self.out):
            return None
        name, frets = example
        strings = len(self.instruments[self.only]["tuning"])
        dots = ",".join(frets)
        return r"\readingfigure{%s}{\chordbox{%d}{0}{%s}}{%s}" % (
            tex_escape(name), strings, dots, tex_escape(frets))

    def reading_notes(self):
        """How to read a fingering, for a booklet with no contents page.

        Only the lines that apply. Derived from what this edition actually
        emitted rather than from a list per instrument, so a mark that
        stops appearing stops being explained: the piano pages carry note
        names and no marks at all, and telling a pianist what x means on
        a string would be noise."""
        if not self.only:
            return []
        body = "\n".join(self.out)
        lines = []
        # \chordrow, not \frets: the bass pages are full of fret numbers
        # too, but they sit in a table with a column per string, and
        # telling that reader to read left to right explains nothing.
        if r"\chordrow" in body:
            lines.append(r"Fret numbers read from the lowest string.")
        if r"\frets{x" in body:
            lines.append(r"\frets{x} means don't play that string.")
        if r"\vmark{r}" in body:
            lines.append(r"\vmarkink{r} means rootless: for rhythm, "
                         r"not for soloing.")
        if r"\vmark{i}" in body:
            lines.append(r"\vmarkink{i} means the voicing given is an "
                         r"inversion.")
        return lines


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data", default="data")
    ap.add_argument("--out", default="build/body.tex")
    ap.add_argument("--only", choices=Book.ALL_INSTRUMENTS + ["theory"],
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
