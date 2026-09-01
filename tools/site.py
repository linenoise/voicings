#!/usr/bin/env python3
"""Build the static site for fancychords.com into `docs/`.

Static HTML, CSS and images. No JavaScript: the whole thing is a lookup
table and a set of downloads, and neither needs a runtime.

Nothing about the music is worked out here. The page content comes from
the same `render.Book` the PDFs are typeset from, so a chord that changes
in `data/` changes in both places or in neither. What this file owns is
the HTML around it.
"""

import html
import math
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render  # noqa: E402
import theory  # noqa: E402
import validate  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE_URL = "https://fancychords.com"
SOURCE_URL = "http://github.com/linenoise/voicings"
AUTHOR_URL = "https://danne.stayskal.com"

# Every instrument, in the order everything else lists them.
ORDER = render.Book.ALL_INSTRUMENTS

# Which sections a page carries, in the order they appear. Mirrors what
# the book gives each instrument.
SECTIONS = {
    "fretted": ["circle", "roots", "movable", "chords"],
    "piano": ["circle", "chords"],
    "banjo": ["circle", "roots", "movable", "spikes", "chords"],
    "notes": ["circle", "movable", "numbers", "roots", "under", "patterns"],
    # The cello leads with notes like the bass, then carries its chord
    # pages after: a cellist does reach for a grip when the part asks.
    "cello": ["circle", "movable", "numbers", "roots", "under", "patterns",
              "chords"],
}
KIND = {"piano": "piano", "banjo": "banjo", "bass": "notes", "cello": "cello"}

TITLES = {
    "circle": "Circle of Fifths",
    "roots": "Root Positions",
    "movable": "Movable Shapes",
    "numbers": "Numbers",
    "under": "What to Play Under",
    "patterns": "Patterns",
    "spikes": "Drone Spikes",
    "chords": "Chords",
}


def colors():
    """The pen colors, read out of the class file that defines them.

    One definition, so the site and the book cannot drift to different
    greens.
    """
    src = open(os.path.join(ROOT, "tex", "voicings.cls")).read()
    found = dict(re.findall(r"\\definecolor\{(\w+)\}\{HTML\}\{([0-9A-Fa-f]{6})\}",
                            src))
    return {name: "#" + found[macro] for name, macro in render.INK.items()}, found


PENS, RAW = colors()
INK = "#" + RAW.get("ink", "1A1A1A")
FAINT = "#" + RAW.get("faint", "404040")
RULE = "#" + RAW.get("rule", "7E7E7E")
PAPER = "#" + RAW.get("paper", "FDFCF8")


def esc(text):
    return html.escape(str(text), quote=True)


def sym(chord):
    """A chord symbol as the book prints it."""
    return esc(chord.replace("o", "\u00b0") if "o" in chord else chord)


def notes_html(text):
    """A piano voicing: note names with real accidentals, middot between."""
    out = []
    for note in str(text).split("-"):
        body = esc(note[:1])
        for a in note[1:]:
            body += "\u266d" if a == "b" else "\u266f"
        out.append(body)
    return '<span class="sep">\u00b7</span>'.join(out)


class Site(object):
    def __init__(self, book, out):
        self.book = book
        self.out = out
        self._counts = {}

    def edition_counts(self, title):
        """Pages and sheets for one edition, read off the built PDFs.

        Off the files rather than a list kept by hand, so a button cannot
        promise a length the download does not have.
        """
        if title not in self._counts:
            import pagecount
            here = os.path.join(self.out, "downloads")

            def n(suffix):
                f = os.path.join(here, "%s%s.pdf" % (title, suffix))
                return pagecount.count(f) if os.path.exists(f) else None

            pages, letter, a4 = n(""), n(" (print-letter)"), n(" (print-A4)")
            self._counts[title] = (pages,
                                   letter // 2 if letter else None,
                                   a4 // 2 if a4 else None)
        return self._counts[title]

    # -- shell -----------------------------------------------------------

    def nav(self, active):
        items = ['<a href="index.html"%s>Home</a>'
                 % (' class="on"' if active is None else "")]
        for inst in ORDER:
            name = self.book.instruments[inst]["name"]
            items.append('<a href="%s.html" class="pen %s"%s>%s</a>'
                         % (inst, inst, " on" if inst == active else "",
                            esc(name)))
        return '<nav>%s</nav>' % "\n".join(items)

    def page(self, slug, title, body, active):
        doc = [
            "<!doctype html>",
            '<html lang="en">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width,initial-scale=1">',
            "<title>%s</title>" % esc(title),
            '<link rel="stylesheet" href="style.css">',
            "</head>",
            "<body%s>" % (' class="inst-%s"' % active if active else ""),
            '<header><a class="wordmark" href="index.html">'
            "Fancy Chords <span>and Their Voicings</span></a></header>",
            self.nav(active),
            "<main>",
            body,
            "</main>",
            '<footer><p>Copyright &copy; 2026 '
            '<a href="%s">Danne Stayskal</a>.<br>This site and the software '
            "that builds it is open source. Its source code is available at "
            '<a href="%s">%s</a>.</p></footer>'
            % (AUTHOR_URL, SOURCE_URL, esc(SOURCE_URL)),
            "</body>",
            "</html>",
        ]
        path = os.path.join(self.out, slug + ".html")
        with open(path, "w") as fh:
            fh.write("\n".join(doc) + "\n")
        return path

    # -- pieces ----------------------------------------------------------

    def downloads(self, inst=None):
        """The three editions of one book, as buttons.

        These are the point of the site. Someone who lands here wants the
        file in their hand -- nobody wants to stare at a phone during
        rehearsal -- so each edition is a target big enough to hit with a
        thumb, named for what you would do with it and labelled with what
        it costs: pages to read, sheets of paper to print.
        """
        title = ("Fancy %s Chords and Their Voicings"
                 % self.book.instruments[inst]["name"]) if inst else \
                "Fancy Chords and Their Voicings"
        pages, letter, a4 = self.edition_counts(title)

        def meta(n, unit):
            return "%s %s &middot; PDF" % (n, unit) if n else "PDF"

        rows = [
            ("", "To Read on a screen", meta(pages, "pages")),
            (" (print-letter)", "To Print on US Letter", meta(letter, "sheets")),
            (" (print-A4)", "To Print on A4", meta(a4, "sheets")),
        ]
        out = ['<div class="getit">',
               '<p class="edition">Download <cite>%s</cite></p>' % esc(title),
               '<ul class="buttons">']
        for suffix, label, sub in rows:
            f = "%s%s.pdf" % (title, suffix)
            out.append('<li><a class="btn" href="downloads/%s">'
                       '<span class="what">%s</span>'
                       '<span class="meta">%s</span></a></li>'
                       % (esc(f.replace(" ", "%20")), esc(label), sub))
        out.append("</ul></div>")
        return "\n".join(out)

    def picks(self):
        """The seven instrument editions, as their own colored targets.

        Clicking an instrument under a heading that says Download means
        wanting that instrument's book, so these go to the instrument
        page, where its own buttons are the first thing on it.
        """
        items = []
        for inst in ORDER:
            meta = self.book.instruments[inst]
            title = "Fancy %s Chords and Their Voicings" % meta["name"]
            pages = self.edition_counts(title)[0]
            items.append('<li><a class="pick pen %s" href="%s.html">'
                         '<span class="who">%s</span>'
                         '<span class="meta">%s</span></a></li>'
                         % (inst, inst, esc(meta["name"]),
                            "%s pages" % pages if pages else ""))
        return '<ul class="picks">%s</ul>' % "\n".join(items)

    def section_nav(self, sections):
        items = ['<li><a href="#%s">%s</a></li>' % (s, esc(TITLES[s]))
                 for s in sections]
        return ('<section class="contents"><h2>Contents</h2>'
                "<ul>%s</ul></section>" % "\n".join(items))

    def circle_svg(self, inst):
        """The circle of fifths, redrawn as SVG.

        Same geometry as the printed one: an outer ring of majors, an
        inner ring of relative minors, and the key signature in the hub.
        """
        pen = PENS[inst]
        cx = cy = 210.0
        r_out, r_mid, r_in = 195.0, 138.0, 66.0
        parts = ['<svg class="circle" viewBox="0 0 420 420" '
                 'xmlns="http://www.w3.org/2000/svg" role="img" '
                 'aria-label="Circle of fifths for the %s">'
                 % esc(self.book.instruments[inst]["name"])]
        for r in (r_out, r_mid, r_in):
            parts.append('<circle cx="%g" cy="%g" r="%g" fill="none" '
                         'stroke="%s" stroke-width="1"/>' % (cx, cy, r, RULE))
        for i in range(12):
            a = math.radians(90 - 30 * i + 15)
            parts.append('<line x1="%g" y1="%g" x2="%g" y2="%g" stroke="%s" '
                         'stroke-width="1"/>'
                         % (cx + r_in * math.cos(a), cy - r_in * math.sin(a),
                            cx + r_out * math.cos(a), cy - r_out * math.sin(a),
                            RULE))

        def place(radius, angle, lines):
            """A stack of labels centered on a wedge.

            Stacked in screen space rather than along the radius. Stepping
            outward by radius puts the name beside the voicing at three
            and nine o'clock instead of above it, and the two ran into
            each other and into the ring inside them.
            """
            a = math.radians(angle)
            x = cx + radius * math.cos(a)
            y = cy - radius * math.sin(a)
            total = sum(size for _, size, _, _ in lines) + 2 * (len(lines) - 1)
            top = y - total / 2.0
            out = []
            for text, size, color, weight in lines:
                top += size
                out.append('<text x="%g" y="%g" text-anchor="middle" '
                           'font-size="%g" font-weight="%s" fill="%s">%s</text>'
                           % (x, top - size * 0.18, size, weight, color, text))
                top += 2
            return "".join(out)

        for i, key in enumerate(render.CIRCLE):
            angle = 90 - 30 * i
            flat = key not in render.SHARP_KEYS
            minor = theory.spell((theory.NOTE_TO_PC[key] + 9) % 12, flat) + "m"
            mv = self.book.voicing_for(inst, key) or ""
            nv = self.book.voicing_for(inst, minor) or ""
            major = [(esc(key), 18, "#" + RAW["keyred"], "bold")]
            if mv:
                major.append((esc(mv), 12, pen, "bold"))
            parts.append(place((r_out + r_mid) / 2, angle, major))
            small = [(esc(minor), 14, INK, "bold")]
            if nv:
                small.append((esc(nv), 11, pen, "bold"))
            parts.append(place((r_mid + r_in) / 2, angle, small))
            parts.append(place((r_in + 18) / 2 + 14, angle,
                               [(esc(self.signature(key)), 11, FAINT, "normal")]))
        parts.append("</svg>")
        return "".join(parts)

    def signature(self, key):
        table = {"C": "\u266e", "G": "1\u266f", "D": "2\u266f", "A": "3\u266f",
                 "E": "4\u266f", "B": "5\u266f", "Gb": "6\u266d",
                 "Db": "5\u266d", "Ab": "4\u266d", "Eb": "3\u266d",
                 "Bb": "2\u266d", "F": "1\u266d"}
        return table.get(key, "")

    def roots_table(self, inst):
        meta = self.book.instruments[inst]
        tuning = meta["tuning"]
        head = "".join("<th>%s</th>" % esc(t[:-1]) for t in tuning)
        rows = []
        for note in render.ROOT_KEYS:
            pc = theory.NOTE_TO_PC[note]
            cells = "".join(
                '<td class="fret">%d</td>' % ((pc - theory.parse_note(t)) % 12)
                for t in tuning)
            rows.append("<tr><th>%s</th>%s</tr>" % (esc(note), cells))
        return ('<table class="grid"><thead><tr><th></th>%s</tr></thead>'
                "<tbody>%s</tbody></table>" % (head, "".join(rows)))

    def movable_table(self, inst):
        rows = []
        for label, quality, want in self.book.MOVABLE_QUALITIES[inst]:
            rows.append('<tr class="group"><th colspan="4">%s</th></tr>'
                        % esc(label))
            for rel, (pos, degree, where, shape, root) in \
                    self.book.closed_shapes(inst, quality, want):
                rows.append(
                    '<tr><td class="fret">%s</td><td>%s</td><td>%s</td>'
                    '<td class="fret">%s = %s</td></tr>'
                    % ("".join("x" if r is None else str(r) for r in rel),
                       esc(where), esc(degree), esc(shape),
                       sym(root + quality)))
        return ('<table class="grid movable"><thead><tr><th>shape</th>'
                "<th>root on</th><th>bottom</th><th>example</th></tr></thead>"
                "<tbody>%s</tbody></table>" % "".join(rows))

    def numbers_table(self):
        head = "".join("<th>%d</th>" % n for n in range(1, 8))
        rows = []
        for key in render.ROOT_KEYS:
            cells = []
            for interval in (0, 2, 4, 5, 7, 9, 11):
                name = theory.spell_in_key(key, interval)
                if "bb" in name or "##" in name:
                    name = theory.spell(
                        (theory.NOTE_TO_PC[key] + interval) % 12,
                        key not in render.PIANO_SHARP_KEYS)
                cells.append('<td class="fret">%s</td>' % esc(name))
            rows.append("<tr><th>%s</th>%s</tr>" % (esc(key), "".join(cells)))
        return ('<table class="grid"><thead><tr><th></th>%s</tr></thead>'
                "<tbody>%s</tbody></table>" % (head, "".join(rows)))

    def under_table(self):
        rows = []
        last = None
        for quality in theory.VOCABULARY:
            g = render.GROUP_OF.get(quality, render.SLASH_GROUP - 1)
            if last is not None and g != last:
                rows.append('<tr class="gap"><td colspan="2"></td></tr>')
            last = g
            label = "major" if quality == "" else quality.replace("o", "\u00b0")
            degrees = " ".join(self.book.degree_name(i, quality)
                               for i in theory.QUALITIES[quality])
            rows.append('<tr><th>%s</th><td class="fret">%s</td></tr>'
                        % (esc(label), esc(degrees)))
        return '<table class="grid under"><tbody>%s</tbody></table>' % "".join(rows)

    def patterns_list(self, inst):
        data = self.book.cello if inst == "cello" else self.book.bass
        out = []
        for p in data["patterns"]:
            cells = [(d["degree"],
                      "R" if d["string"] == 0 else "%d+R" % d["string"],
                      "R%d" % d["offset"]) for d in p["degrees"]]
            rows = [
                "<tr><th>degree</th>%s</tr>" % "".join(
                    '<td class="fret strong">%s</td>' % esc(c[0]) for c in cells),
                "<tr><th>string</th>%s</tr>" % "".join(
                    "<td>%s</td>" % esc(c[1]) for c in cells),
                "<tr><th>fret</th>%s</tr>" % "".join(
                    "<td>%s</td>" % esc(c[2]) for c in cells),
            ]
            out.append(
                '<div class="pattern"><h3>%s <span class="use">%s</span></h3>'
                '<table class="grid pattern"><tbody>%s</tbody></table></div>'
                % (esc(p["name"]), esc(p["use"]), "".join(rows)))
        return "".join(out)

    def spikes_table(self):
        spikes = {r["key"]: r for r in self.book.spikes["keys"]}
        rows = []
        for key in render.CHROMATIC:
            s = spikes.get(key)
            if not s:
                continue

            def phrase(one):
                where = "open g" if one["open"] else str(one["fret"])
                if one.get("detune"):
                    where += ", tune %s" % ("down" if one["detune"] < 0 else "up")
                return "%s &rarr; %s" % (esc(where), esc(one["note"]))
            rows.append('<tr><th>%s</th><td class="fret">%s</td>'
                        '<td class="fret">%s</td></tr>'
                        % (esc(self.book.key_heading(key).replace("\\,", "")
                               .replace("$\\flat$", "\u266d").replace("\\#", "#")),
                           phrase(s["major"]), phrase(s["minor"])))
        return ('<table class="grid"><thead><tr><th>key</th><th>major</th>'
                "<th>minor</th></tr></thead><tbody>%s</tbody></table>"
                % "".join(rows))

    def chords_for(self, inst):
        """Every key, every chord, in the order the book prints them."""
        doc = self.book.voicings.get(inst)
        if not doc:
            return ""
        by_key = {k["key"]: k for k in doc["keys"]}
        meta = self.book.instruments[inst]
        out = []
        for key in render.CHROMATIC:
            block = by_key.get(key)
            if not block:
                continue
            heading = (self.book.key_heading(key).replace("\\,", "")
                       .replace("$\\flat$", "\u266d").replace("\\#", "#"))
            rows = []
            last = None
            for entry in self.book.ordered_chords(block["chords"]):
                g = render.group_index(entry["chord"])
                if last is not None and g != last:
                    rows.append('<tr class="gap"><td colspan="2"></td></tr>')
                last = g
                cells = []
                for f in entry["frets"]:
                    marks = "".join(
                        '<sup>%s</sup>' % m for m in validate.marks_for(
                            meta["tuning"], entry["chord"], f,
                            meta.get("reentrant", False))) \
                        if meta.get("kind", "frets") == "frets" else ""
                    cells.append('<span class="v pen %s">%s%s</span>'
                                 % (inst, esc(f), marks))
                if meta.get("kind") == "keyboard":
                    shapes = list(entry["frets"])
                    spread = self.book.piano_open(entry["chord"], key)
                    if spread and spread not in shapes:
                        shapes.append(spread)
                    cells = ['<span class="v pen %s">%s</span>'
                             % (inst, notes_html(f)) for f in shapes]
                rows.append('<tr><th>%s</th><td class="fret">%s</td></tr>'
                            % (sym(entry["chord"]),
                               '<span class="alt"></span>'.join(cells)))
            out.append('<section class="key"><h3 id="key-%s">%s</h3>'
                       '<table class="grid chords"><tbody>%s</tbody></table>'
                       "</section>" % (esc(key), esc(heading), "".join(rows)))
        return '<div class="keys">%s</div>' % "".join(out)

    # -- pages -----------------------------------------------------------

    def instrument_page(self, inst):
        meta = self.book.instruments[inst]
        name = meta["name"]
        kind = KIND.get(inst, "fretted")
        sections = SECTIONS[kind]
        body = ['<h1 class="pen %s">%s</h1>' % (inst, esc(name))]
        tuning = (self.book.tuning_label(inst)
                  if "tuning" in meta or "tuning_label" in meta else "")
        if tuning:
            body.append('<p class="tuning pen %s">%s</p>' % (inst, esc(tuning)))
        if meta.get("note"):
            body.append("<p class=\"lede\">%s</p>" % esc(meta["note"]))
        body.append(self.downloads(inst))
        body.append('<p class="booklets">This content is designed to be '
                    "printed into booklets.</p>")
        body.append(self.section_nav(sections))

        for s in sections:
            body.append('<section id="%s"><h2>%s</h2>' % (s, esc(TITLES[s])))
            if s == "circle":
                body.append(self.circle_svg(inst))
            elif s == "roots":
                body.append(self.roots_table(inst))
                body.append('<p class="note">Fret for the root of each key on '
                            "each string. Everything else is measured from "
                            "there.</p>")
            elif s == "movable":
                body.append(self.movable_table(inst))
                body.append('<p class="note">Shape is the fingering above its '
                            "lowest fret. Slide it one fret, the chord rises a "
                            "semitone.</p>")
            elif s == "numbers":
                body.append(self.numbers_table())
                body.append('<p class="note">In the key on the left, the four '
                            "is the note under the 4.</p>")
            elif s == "under":
                body.append(self.under_table())
                body.append('<p class="note">Degrees from the root, for each '
                            "chord you might be asked to play under.</p>")
            elif s == "patterns":
                body.append(self.patterns_list(inst))
            elif s == "spikes":
                body.append(self.spikes_table())
                body.append('<p class="note">Where to catch the fifth string '
                            "for each key.</p>")
            elif s == "chords":
                body.append(self.chords_for(inst))
            body.append("</section>")
        return self.page(inst, "Fancy %s Chords" % name,
                         "\n".join(body), inst)

    def index_page(self):
        # No <h1> here: the wordmark in the header already says it, and
        # printing the title twice on the one page that carries it is the
        # kind of thing that reads as a template showing through.
        body = []
        body.append(
            '<p class="lede">A pocket notebook of chord voicings for seven '
            "instruments, in all twelve keys. Print it, cut it, sew it, give "
            "it away. Every voicing is checked against the chord it claims to "
            "be.</p>")
        body.append("<h2>Download</h2>")
        body.append(self.downloads())
        body.append('<p class="booklets">This content is designed to be '
                    "printed into booklets.<br>Individual instrument "
                    "booklets are also available:</p>")
        body.append(self.picks())
        body.append(self.printing_section())
        return self.page("index", "Fancy Chords and Their Voicings",
                         "\n".join(body), None)

    def printing_section(self):
        return """
<section id="printing"><h2>How to print, cut, and sew a copy</h2>
<ol>
<li>Print the 4-up PDF for your paper, <strong>double-sided, flipped on the
long edge</strong>, at 100%. Don't let the printer fit to page.</li>
<li>Cut along the gray lines, which mark the four 3.5in by 5.5in rectangles.
On US Letter that is three cuts down and one across. On A4 it is three each
way, because the sheet is 18mm taller than two pages.</li>
<li>Stack the rectangles in the order they came off the sheet: top-left,
top-right, bottom-left, bottom-right.</li>
<li>Punch the five holes. Every page carries five small gray circles down its
binding edge, so there is nothing to measure: square up the stack, punch
through the marks, sew.</li>
<li>Sew a five-hole pamphlet stitch, or staple along the punched edge.</li>
</ol>
<p><img src="pamphlet-stitch.svg" alt="Five-hole pamphlet stitch: the spine
outside, the spine inside, and the order of the six passes"></p>
<p class="note">An office hole punch will not do this: it cuts a 6mm hole and
reaches about 12mm in. Use an awl, a pin vise, or a 1.5mm bookbinding screw
punch.</p>
</section>
"""

    def stylesheet(self):
        # Two rules per instrument. The first colors anything explicitly
        # marked with the pen; the second colors every fret number, string
        # position and voicing on that instrument's page, wherever it
        # appears: chords, root positions, movable shapes, patterns, the
        # lot. The monospace face has always meant "a position" here, and
        # the printed book colors all of it the same way.
        pens = "\n".join(
            ".pen.%s, .inst-%s .fret { color: %s; }\n"
            ".inst-%s a.btn { color: %s; border-color: %s; }\n"
            ".inst-%s a.btn:hover, .inst-%s a.btn:focus "
            "{ background: %s; border-color: %s; color: var(--paper); }"
            % (inst, inst, PENS[inst],
               inst, PENS[inst], PENS[inst],
               inst, inst, PENS[inst], PENS[inst])
            for inst in ORDER)
        css = """/* Generated by tools/site.py. */
:root {
  --ink: %(ink)s;
  --faint: %(faint)s;
  --rule: %(rule)s;
  --paper: %(paper)s;
}
* { box-sizing: border-box; }
/* The size lives on the root, not on body. Everything else here is in rem,
   and rem resolves against html: setting it on body scaled the paragraphs
   and left every heading, caption and table header at the browser default.
   19.36px is 16 up a tenth, twice. */
html { font-size: 19.36px; }
body {
  margin: 0;
  background: var(--paper);
  color: var(--ink);
  font: 1rem/1.5 "Helvetica Neue", Helvetica, Arial, sans-serif;
}
/* Header, nav and main share one measure, so the wordmark, the
   instrument links and the content all start on the same left edge. */
header, nav, main { max-width: 54rem; margin: 0 auto; }
header { padding: 1.5rem 1rem 0.5rem; }
.wordmark {
  font-size: 1.5rem; font-weight: 700; color: var(--ink); text-decoration: none;
}
.wordmark span { font-weight: 400; color: var(--faint); }
nav { padding: 0 1rem; border-bottom: 1px solid var(--rule); }
nav.sections { max-width: none; }
nav a {
  display: inline-block; padding: 0.5rem 0.75rem 0.6rem 0;
  font-weight: 700; text-decoration: none; color: var(--ink);
}
nav a:hover { text-decoration: underline; }
nav a.on { text-decoration: underline; text-underline-offset: 4px; }
.contents ul { margin: 0.5rem 0 2rem; padding-left: 1.2rem; }
.contents li { margin: 0.2rem 0; }
.contents a { color: var(--ink); text-decoration: underline; }
main { padding: 1.5rem 1rem 3rem; }
h1 { font-size: 2rem; margin: 1rem 0 0.25rem; }
h2 { font-size: 1.3rem; margin: 2.5rem 0 0.75rem; }
h3 { font-size: 1.05rem; margin: 1.5rem 0 0.5rem; }
.tuning { font-family: ui-monospace, Menlo, Consolas, monospace;
          font-weight: 700; letter-spacing: 0.12em; margin: 0 0 0.5rem; }
/* No narrower measure for prose: the content area is already the
   measure, and capping these again broke lines well short of it. */
.lede { color: var(--faint); }
.note { color: var(--faint); font-size: 0.9rem; }
.use { color: var(--faint); font-weight: 400; font-size: 0.9rem; }
/* The downloads are what the site is for. A plain list of links read as
   something to get past; a button reads as something to press. Each one
   carries the cost of taking it -- pages to read, sheets to print -- so
   the choice can be made without opening the file. */
.getit { margin: 0.5rem 0 2.5rem; }
.getit .edition { font-weight: 700; font-size: 1.1rem; margin: 0 0 0.7rem; }
ul.buttons {
  list-style: none; padding: 0; margin: 0;
  display: flex; flex-wrap: wrap; gap: 0.7rem;
}
ul.buttons li { margin: 0; }
a.btn {
  display: block; min-width: 12rem; padding: 0.7rem 1rem;
  border: 2px solid var(--ink); border-radius: 6px;
  color: var(--ink); text-decoration: none;
}
a.btn .what { display: block; font-weight: 700; }
/* An arrow, so a button that leads to a file cannot be mistaken for one
   that leads to another page. */
a.btn .what::after { content: " \\2193"; }
a.btn .meta { display: block; font-size: 0.85rem; opacity: 0.8; }
a.btn:hover, a.btn:focus {
  background: var(--ink); border-color: var(--ink); color: var(--paper);
}
/* On a phone the buttons go full width: a thumb is a blunt instrument,
   and there is nothing to line them up with at that measure anyway. */
@media (max-width: 30rem) {
  ul.buttons { display: block; }
  ul.buttons li { margin-bottom: 0.7rem; }
  a.btn { min-width: 0; }
}
p.booklets { margin: 0 0 0.9rem; }
ul.picks {
  list-style: none; padding: 0; margin: 0 0 2.5rem;
  display: grid; gap: 0.7rem;
  grid-template-columns: repeat(auto-fill, minmax(13rem, 1fr));
}
ul.picks li { margin: 0; }
a.pick {
  display: block; padding: 0.6rem 0.9rem; text-decoration: none;
  border: 1px solid var(--rule); border-radius: 6px;
}
a.pick .who { display: block; font-weight: 700; font-size: 1.15rem; }
a.pick .meta { display: block; font-size: 0.85rem; color: var(--faint); }
a.pick:hover, a.pick:focus { border-color: currentColor; }
table.grid { border-collapse: collapse; margin: 0.5rem 0 1rem; }
table.grid th, table.grid td {
  padding: 0.2rem 0.7rem 0.2rem 0; text-align: left; vertical-align: baseline;
}
table.grid thead th {
  border-bottom: 1px solid var(--rule); font-size: 0.85rem;
}
table.grid tbody th { font-weight: 700; white-space: nowrap; }
tr.gap td { height: 1.5rem; }
tr.group th { padding-top: 0.8rem; color: %(keyred)s; }
.fret { font-family: ui-monospace, Menlo, Consolas, monospace;
        font-weight: 700; letter-spacing: 0.05em; }
.fret sup { font-size: 0.65em; font-weight: 700; color: var(--faint); }
.sep { color: var(--rule); }
/* Each voicing is its own box with the gap on its right, so one that
   wraps starts at the left edge of the cell rather than carrying an
   indent from the separator in front of it. */
.alt { display: none; }
.v { display: inline-block; margin-right: 0.7rem; }
/* A rule under the key, so each block reads as its own table rather than
   running into the one above it in a multi-column flow. */
.key h3 {
  border-bottom: 1px solid var(--rule); font-size: 1rem;
  padding-bottom: 0.2rem; margin-bottom: 0.4rem;
}
.keys {
  display: grid; gap: 0 2.5rem;
  grid-template-columns: repeat(auto-fill, minmax(15rem, 1fr));
}
/* Full measure. The drawing is a viewBox, so the type inside scales
   with it and needs no separate size. */
svg.circle { width: 100%%; height: auto; display: block; }
footer {
  border-top: 1px solid var(--rule); margin: 3rem auto 0;
  max-width: 54rem; padding: 1rem; color: var(--faint); font-size: 0.9rem;
}
footer a { color: var(--faint); }
%(pens)s
"""
        return css % dict(ink=INK, faint=FAINT, rule=RULE, paper=PAPER,
                          keyred="#" + RAW["keyred"], pens=pens)


def main():
    out = os.path.join(ROOT, "docs")
    downloads = os.path.join(out, "downloads")
    os.makedirs(downloads, exist_ok=True)
    book = render.Book(os.path.join(ROOT, "data"))
    site = Site(book, out)

    # The PDFs travel with the site rather than being linked off GitHub:
    # a download that leaves the domain is a download that breaks when the
    # repository moves.
    build = os.path.join(ROOT, "build")
    copied = 0
    for f in sorted(os.listdir(build)):
        # Only the editions. build/ also holds qr.pdf, which is an
        # intermediate for the QR image and not something to hand a
        # reader.
        if f.startswith("Fancy ") and f.endswith(".pdf"):
            shutil.copy2(os.path.join(build, f), os.path.join(downloads, f))
            copied += 1

    stitch = os.path.join(ROOT, "images", "pamphlet-stitch.svg")
    if os.path.exists(stitch):
        shutil.copy2(stitch, os.path.join(out, "pamphlet-stitch.svg"))

    with open(os.path.join(out, "style.css"), "w") as fh:
        fh.write(site.stylesheet())

    site.index_page()
    for inst in ORDER:
        site.instrument_page(inst)

    pages = len([f for f in os.listdir(out) if f.endswith(".html")])
    print("wrote %d pages and %d downloads to docs/" % (pages, copied))


if __name__ == "__main__":
    main()
