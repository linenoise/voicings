# Fancy Chords and their Voicings

**[⬇️ Read or print the book (PDF)](https://github.com/linenoise/voicings/blob/main/build/voicings-screen.pdf)** — 3.5″ × 5.5″, one key to a page. Good on a phone, a tablet, or an e-reader.

**[🖨️ Print-and-sew edition (PDF)](https://github.com/linenoise/voicings/blob/main/build/voicings-print.pdf)** — US Letter, four pages to a sheet. Print double-sided, cut into quarters, sew. See [Printing, cutting, and sewing](#printing-cutting-and-sewing).

*Arrived here from the QR code on the cover? Those two links are what you want.*

<img src="assets/qr.png" alt="QR code linking to https://github.com/linenoise/voicings" width="140">

*Point a phone at this to bring the repository up on it — the same code that's on the book's cover.*

---

A pocket chord book for the instruments in a church band — mandolin, fiddle,
banjo, guitar, bass, ukulele, and piano — typeset from a handwritten notebook
into something you can print on an ordinary duplex printer, cut apart with
scissors, and sew by hand.

Every instrument carries the same 29 kinds of chord in all twelve keys, so
whatever you are holding when the singer calls a flat-six major-nine, it is
on the page.

Two PDFs come out of the build, and both are checked in under `build/` so
they can be read or printed without installing anything:

| File | Size | For |
|---|---|---|
| [`build/voicings-screen.pdf`](https://github.com/linenoise/voicings/blob/main/build/voicings-screen.pdf) | 3.5″ × 5.5″, one page per page | Reading on a phone, tablet, or e-reader |
| [`build/voicings-print.pdf`](https://github.com/linenoise/voicings/blob/main/build/voicings-print.pdf) | US Letter, 4-up double-sided | Printing, cutting, and sewing |

3.5″ × 5.5″ is the trim size of the original notebook, so the screen edition
is the book at actual size.

Source and a printable copy: <https://github.com/linenoise/voicings>

## Quick start

```bash
make
```

That validates the chord data, builds both PDFs, and stops with a clear
message if LaTeX isn't installed. Without LaTeX, everything except the two
PDF targets still works.

## What's in the book

- **Front cover**, with a QR code to this repository.
- **Table of chords.**
- **Circle of fifths**, one per instrument (mandolin, banjo, guitar, bass,
  ukulele), each showing the most common voicing of every major key on the
  outer ring and its relative minor on the inner ring. For bass it gives the
  string and fret a player actually uses — `A3`, the third fret of the A
  string, not the eighth of the E.
- **Banjo drone spikes** on every banjo key page: where to catch the 5th
  string, and — since a neck with spikes at 5, 7 and 9 cannot reach a chord
  tone in five of the twelve keys — when to just tune the string a half step
  instead.
- **Nashville number chart**, one per instrument: twelve keys down the side,
  the seven diatonic degrees across, each cell carrying both the chord name
  and its fingering.
- **Chord sections** — mandolin, guitar, ukulele, piano, and banjo, each
  covering the full vocabulary in all twelve keys: around 350 voicings per
  instrument, 1,934 in all. One key to a page, two columns.
- **Banjo drone spikes**: where to spike the 5th string for every key, major
  and minor, repeated on each banjo page and collected in one table.
- **Piano**: one voicing per chord — close root position, the chord as you
  spell it at a keyboard. The open worship voicings from `piano.pdf` are
  kept in `data/piano-shapes.yaml` rather than printed beside them.
- **Bass**: where every root sits on each string, the movable arpeggio
  patterns measured from it, and which degrees to play under every chord in
  the book. Bass players don't finger chord grids.
- **Back sheet**: every tuning, the credit line, and the download URL.

Fiddle and tenor banjo share the mandolin's GDAE tuning, so the mandolin
section serves all three. A baritone ukulele is the top four strings of a
guitar (D G B E), so guitar shapes with the lowest two strings muted
transfer directly.

## Printing, cutting, and sewing

1. **Print** `build/voicings-print.pdf` on US Letter, **double-sided, flipped
   on the long edge**, at 100% scale — no "fit to page", which would shrink
   the pages and throw the cut lines off.
2. **Cut** each sheet into four 3.5″ × 5.5″ rectangles: trim ¾″ of waste off
   each side, then one cut down the middle and one across. Two pages tall by
   two wide is exactly 11″, so there is no waste top or bottom. A guillotine
   trimmer is squarer than scissors, but scissors work.
3. **Stack** the rectangles in the order they came off the sheet — top-left,
   top-right, bottom-left, bottom-right — keeping the sheets in order.
4. **Sew** along the left edge. A three- or five-hole pamphlet stitch about
   6 mm in from the spine holds well; the inner margin is 9 mm to leave room
   for it.

Run `make print CROP_MARKS=1` to draw a box around each rectangle to cut
along.

Because the pages stack two-high to exactly 11″, they run to the top and
bottom edges of the paper. The book's own top and bottom margins (8 mm and
7 mm) are wider than the unprintable border on a typical laser printer — a
Brother HL-2270DW reserves about 4.2 mm — so nothing is clipped, but don't
let the driver scale the page to "fit".

The imposition puts consecutive pages on the two faces of each rectangle, so
the stack collates in reading order with no folding. Run `make print
SCHEME=saddle` instead if you'd rather fold sheets into signatures and sew
through the fold.

At present the book is **90 pages — 12 sheets of Letter**, one key to a page
for the fretted instruments and two for the piano, whose note lists are too
wide to set in two columns.

## Colour

One pen per instrument, matching the notebook: **green** mandolin, **blue**
guitar, **purple** ukulele, **red** piano, **orange** banjo, and for bass the
darkest yellow that still reads as yellow. Every voicing on a page is in its
instrument's ink, and the cover lists them in those colours.

These are ordinary pen inks rather than a designed palette, but each was
checked against the page colour for contrast: all six clear 4.5:1, the WCAG
AA threshold for 12pt bold, because this book gets read in bad light on a
dark stage. The orange is a shade deeper than a gel pen for exactly that
reason — a true orange sits at 4.1:1 and misses.

On a mono laser printer the inks all render as mid greys and stop
distinguishing the instruments. The section dividers and page headings still
say which instrument you are looking at, so nothing is lost but the colour
coding.

## Layout and typography

One LaTeX page is one notebook page, 3.5″ × 5.5″ — the trim size of the
paper original. `tex/voicings.cls` owns geometry and type; `tools/render.py`
owns what goes on which page.

The body is set in **12pt sans**, two columns on the chord pages. That size
is not a preference — it is the largest the class offers at which nothing
overflows, found by building the book at each size and checking. 14pt is the
next step `extarticle` supports and it fails badly. In two columns the
binding constraint is *width*, not height: a nine-character name like
`Bbsus2/D` beside a six-character fingering like `x13321` is all a 36 mm
column will take. So the chord name sets one size down and the fingering
stays full size — the fingering is what you read from a music stand, the
name is what you scan for once.

Alternate voicings stack under the first rather than running on beside it.
At this measure `2200 2245` on one line reads as a single eight-digit
fingering, which is the opposite of helpful.

Rows per page are tuned against the *compiled* PDF, not guessed:
`tools/pagecheck.py` compares the pages the renderer intended against the
pages TeX produced, and fails if any of them overflowed. A `tabular` can't
break across pages, so an over-tall table doesn't wrap — it jumps whole to
the next page and leaves its heading stranded, which is exactly the kind of
silent breakage that check exists to catch.

The circle of fifths is a fixed diagram, so its labels are sized in points
rather than following the body. Within each ring the name and fingering sit
in one node, ordered so the fingering falls on the outward side of the wedge
where there is more arc. They are deliberately *not* placed at two different
radii: at three and nine o'clock "further out" is sideways, so radial
separation puts both items on the same horizontal line and a six-character
fingering lands on top of its own key name.

## The build pipeline

```
data/*.yaml ──▶ validate.py ──▶ render.py ──▶ body.tex ──┐
   │                 │                                    │
   │                 └── repair.py ──▶ resolve.py         ├──▶ voicings-screen.pdf
   │                          └──▶ CORRECTIONS.md         │            │
   └── spikes.py ──▶ banjo-spikes.yaml                    ┘            ▼
                                                            impose.py ──▶ voicings-print.pdf
```

The YAML under `data/` is the source of truth. The PDFs are generated, and
are committed under `build/` so the QR code on the cover leads somewhere
readable — rerun `make` and commit the result after changing the data.

### `make` targets

| Target | Does |
|---|---|
| `make` | Validate, then build both PDFs |
| `make screen` | Just the 3.5″ × 5.5″ reading edition |
| `make print` | Just the imposed Letter edition |
| `make validate` | Check every voicing against the chord it names |
| `make lint` | Check the generated LaTeX for undefined macros |
| `make pagecheck` | Verify no page overflowed onto an unheaded continuation |
| `make repair` | Propose fixes for anything that fails (add `APPLY=1` to write them) |
| `make resolve` | Drop or regenerate what repair couldn't reach (`APPLY=1`) |
| `make revert` | Restore the data to its transcription, to replay the pass |
| `make spikes` | Regenerate the banjo drone positions |
| `make piano` | Regenerate the piano pages from the shape table |
| `make complete` | Fill every instrument out to the full vocabulary (`APPLY=1`) |
| `make clean` | Remove `build/` |

### Layout

```
data/
  instruments.yaml     tunings, string counts, fret ranges
  banjo-spikes.yaml    generated by tools/spikes.py
  bass-patterns.yaml   root map and movable arpeggio patterns
  notebook-source.yaml frozen record of what the paper notebook held
  piano-shapes.yaml    piano voicings as interval patterns
  voicings/            one file per instrument: chord → fingerings
tools/
  theory.py            pitch classes, chord formulas, fret arithmetic
  validate.py          does each voicing spell the chord it claims to?
  repair.py            nearest playable fix for the ones that don't
  resolve.py           drop or regenerate what repair couldn't reach
  generate.py          canonical voicing for a chord, from theory
  spikes.py            banjo 5th-string spike positions per key
  playability.py       can a hand actually make this shape?
  checkgen.py          score the generator against the notebook
  provenance.py        which voicings came off the paper
  piano.py             expands piano-shapes.yaml into all twelve keys
  complete.py          fills every instrument out to the full vocabulary
  render.py            data → LaTeX
  impose.py            page order for printing; verified arithmetic
  lint_tex.py          catch undefined macros before TeX does
  pagecheck.py         verify nothing overflowed its page
  revert.py            restore the data to its transcription
tex/
  voicings.cls         page geometry, type, chord and circle macros
  screen.tex           the reading edition
  pages.tex            the same pages, for imposition
(notebook/)            photographs of the original pages -- NOT in version
                       control; the inside cover carries a home address.
                       data/notebook-source.yaml records what they held.
```

### Requirements

- Python 3 with PyYAML (`pip install pyyaml`)
- XeLaTeX, for the PDF targets only. The Makefile finds MacTeX and BasicTeX
  in `/Library/TeX/texbin` on its own.
- Poppler (`brew install poppler`) or Ghostscript, so the build can count
  pages in its own output. Optional; only `make pagecheck` needs it.

```bash
# macOS
brew install --cask basictex
sudo tlmgr update --self
sudo tlmgr install extsizes pdfpages geometry microtype fontspec xcolor

# Debian / Ubuntu
sudo apt install texlive-xetex texlive-latex-extra
```

## How the notebook was checked

Every voicing is checked against the chord it claims to be. `tools/theory.py`
knows what notes each chord contains; `tools/validate.py` works out what a
fingering actually sounds on that instrument's tuning and compares:

- **Error** — the voicing sounds a note that isn't in the chord. Something is
  wrong. These fail the build, so a wrong number can't reach the printer.
- **Warning** — every note belongs, but a defining tone is missing. A mandolin
  chop chord that drops the third, or a rootless jazz grip, does this on
  purpose. Reported and allowed.
- **Note** — wide stretches and other things worth an eyebrow.

The current state is **2,127 voicings, 0 errors, 291 warnings** — 103 entries corrected (48 needed one string moved, 36 two, 19 three), and 6 left for proofreading.

Where a voicing failed, `tools/repair.py` searched the neighbourhood of what
was written for the closest playable fingering that does spell the chord —
fewest strings moved, then least movement, then narrowest stretch. A
one-string fix is a single mis-copied digit and is almost always the intended
shape. Everything it changed is in **[CORRECTIONS.md](CORRECTIONS.md)**, with
the notebook's value beside the printed one.

The search stops as soon as the chord is fully spelled, and only reaches
further when it has to. That distinction matters: a two-string fix that
turns `Gm` into a bare `G5` is worse than a three-string one that actually
sounds the flat third — in a chord book, `A7` and `A` must not be the same
grip. So completeness outranks closeness, and closeness breaks the ties.

Six entries couldn't be repaired at all. At that distance the search is
guessing rather than repairing, and it would print an invented fingering as
though the author had written it. Those were either dropped in favour of
another voicing of the same chord, or — where they were the only one given
— replaced with a shape generated from theory. They're listed at the end of
`CORRECTIONS.md` and are the first things to check against the paper, if you
still have the photographs locally.

Because the pipeline records what was originally transcribed,
`tools/revert.py` can restore the data and replay the whole correction pass.
That's what makes the repair heuristics tunable: changing how a fix is scored
doesn't mean re-reading the photographs.

## Playability

A chord book is no use if a hand cannot make the shapes. `tools/playability.py`
is the constraint the generator was missing: four fingers, with a barre
counting as one — but only when no open string lies underneath it, since the
barre would stop that string too — and a reach limit that depends on the
instrument, because a mandolin's twelfth fret sits where a guitar's seventh
does.

Reach is not a single number. `1-3-5-7` is an ordinary diminished shape on a
mandolin: one finger per string, climbing two frets at a time, and the hand
lies across it. The same seven-fret span with the frets in a different order
is not playable at all. So a *diagonal* — one finger per string, frets
climbing no more than two per string crossed — gets a longer allowance than a
shape that asks two fingers to share a string pair.

`tools/checkgen.py` scores the generator against the notebook: for every
chord a person voiced by hand, it asks the generator for the same chord and
compares. The generator picks something harder than the human in about 1% of
cases. That is the number to watch when changing how shapes are ranked.

## The chord vocabulary

The notebook grew unevenly — twenty-nine kinds of chord on the mandolin
pages, eighteen on the guitar, twelve on the ukulele, three on the banjo.
That's fine in a notebook you wrote yourself; it's useless in a reference
someone else picks up mid-song.

`theory.VOCABULARY` is the union of what the mandolin pages, the piano
worksheet, and the core worship voicings use, and `make complete` makes sure
every instrument has all of it in all twelve keys. Anything transcribed from
the notebook is left exactly as written; anything missing is generated from
theory. The book doesn't mark which is which -- a player wants the chord,
not its provenance -- but the data records it and `CORRECTIONS.md` lists
every one.

Generated shapes are chosen the way a player would: as many strings ringing
as the chord can fill, low on the neck, without a stretch. Slash voicings are
skipped for the ukulele — it's re-entrant, so its fourth string sounds above
its third and there is no bass to put a bass note in.

### Degree labels

On the bass pages the degrees are written number first, accidental second --
`3b`, `7b`, `5#`. Chord *symbols* keep their conventional spelling, so a
half-diminished chord is still `Am7b5`; this is only how the intervals are
named when the page is telling a bass player which notes to reach for.

### Spelling on the circle

The piano circle of fifths respells its notes to the key you actually put a
finger on, matching whichever side of the circle the label is on: `G#m` shows
`G#-B-D#`, not `Ab-Cb-Eb`. The chord pages keep the strict spelling -- the
minor third of G-flat minor is B-double-flat and saying so is the point of
those pages -- but a circle is read at a glance, and nobody hunts a keyboard
for B-double-flat.

### Spelling

Notes are spelled by their function in the chord, not by whatever is
convenient. The augmented fifth of `C+` is G♯, not A♭. The diminished fifth
of `C°` is G♭, not F♯. Three semitones above C is the flat third of `Cm9`
and the sharp ninth of `C7♯9`, and gets written E♭ in one and D♯ in the
other. A minor seventh above G♭ is B𝄫. These sound identical and mean
different things, and a chord chart that gets them wrong is telling you the
wrong thing about the harmony. `theory.DEGREE_MAP` carries this per quality.

## Adding an instrument

1. Add its tuning to `data/instruments.yaml`, low string first.
2. Add `data/voicings/<instrument>.yaml` in the same shape as the others.
3. `make validate` — it will tell you about anything that doesn't spell.
4. Add it to `CHART_INSTRUMENTS` in `tools/render.py` if it should get its
   own circle of fifths and Nashville chart.

An instrument whose voicings are note names rather than fret numbers — as
the piano's are — sets `kind: notes` in `data/instruments.yaml`. Everything
in the pipeline branches on that and nothing else.

## Credits

Danne Stayskal, Orcas Island — <danne@stayskal.com> —
<http://danne.stayskal.com/>

MIT licensed. See [LICENSE.md](LICENSE.md).
