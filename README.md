# Fancy Chords and Their Voicings

A pocket chord book you can print, cut up, and sew. Mandolin, guitar,
ukulele, piano, banjo, and bass — every chord in all twelve keys.

| Edition | Read | Print | Pages | Sheets | |
|---|---|---|---|---|---|
| **Everything** | [screen](https://github.com/linenoise/voicings/blob/main/build/Fancy%20Chords%20and%20Their%20Voicings.pdf) | [4-up](https://github.com/linenoise/voicings/blob/main/build/Fancy%20Chords%20and%20Their%20Voicings%20%28print%29.pdf) | 78 | 10 | All six instruments |
| Mandolin | [screen](https://github.com/linenoise/voicings/blob/main/build/Fancy%20Mandolin%20Chords%20and%20Their%20Voicings.pdf) | [4-up](https://github.com/linenoise/voicings/blob/main/build/Fancy%20Mandolin%20Chords%20and%20Their%20Voicings%20%28print%29.pdf) | 16 | 2 | Also fiddle, tenor banjo |
| Guitar | [screen](https://github.com/linenoise/voicings/blob/main/build/Fancy%20Guitar%20Chords%20and%20Their%20Voicings.pdf) | [4-up](https://github.com/linenoise/voicings/blob/main/build/Fancy%20Guitar%20Chords%20and%20Their%20Voicings%20%28print%29.pdf) | 16 | 2 | Also baritone ukulele |
| Ukulele | [screen](https://github.com/linenoise/voicings/blob/main/build/Fancy%20Ukulele%20Chords%20and%20Their%20Voicings.pdf) | [4-up](https://github.com/linenoise/voicings/blob/main/build/Fancy%20Ukulele%20Chords%20and%20Their%20Voicings%20%28print%29.pdf) | 16 | 2 |  |
| Piano | [screen](https://github.com/linenoise/voicings/blob/main/build/Fancy%20Piano%20Chords%20and%20Their%20Voicings.pdf) | [4-up](https://github.com/linenoise/voicings/blob/main/build/Fancy%20Piano%20Chords%20and%20Their%20Voicings%20%28print%29.pdf) | 16 | 2 |  |
| Banjo | [screen](https://github.com/linenoise/voicings/blob/main/build/Fancy%20Banjo%20Chords%20and%20Their%20Voicings.pdf) | [4-up](https://github.com/linenoise/voicings/blob/main/build/Fancy%20Banjo%20Chords%20and%20Their%20Voicings%20%28print%29.pdf) | 16 | 2 | With drone spikes |
| Bass | [screen](https://github.com/linenoise/voicings/blob/main/build/Fancy%20Bass%20Chords%20and%20Their%20Voicings.pdf) | [4-up](https://github.com/linenoise/voicings/blob/main/build/Fancy%20Bass%20Chords%20and%20Their%20Voicings%20%28print%29.pdf) | 7 | 1 | Roots and patterns |

**Screen** is 3.5in x 5.5in, one page per page: good on a phone or an
e-reader. **4-up** is US Letter, four pages to a sheet, for printing and
sewing. Per-instrument editions carry that instrument's circle of fifths,
its chords, and the credits — nothing else.

<img src="assets/qr.png" alt="QR code linking to https://github.com/linenoise/voicings" width="120">

## Build it yourself

```bash
make
```

Validates the data and builds all fourteen PDFs. Needs Python 3 with PyYAML,
and XeLaTeX for the PDFs — the Makefile finds MacTeX and BasicTeX on its own.
Poppler or Ghostscript is optional, for counting pages.

```bash
brew install --cask basictex          # macOS
sudo apt install texlive-xetex texlive-latex-extra   # Debian
```

| Target | Does |
|---|---|
| `make` | Validate, then build every edition |
| `make validate` | Check every voicing against the chord it names |
| `make repair` | Propose fixes for anything that fails (`APPLY=1` writes them) |
| `make complete` | Fill every instrument out to the full vocabulary (`APPLY=1`) |
| `make piano` | Regenerate the piano pages from the shape table |
| `make spikes` | Regenerate the banjo drone positions |
| `make lint` / `make pagecheck` | Catch undefined macros; catch page overflow |
| `make clean` / `make distclean` | Remove TeX debris; remove all of `build/` |

## Printing, cutting, and sewing

1. Print the 4-up PDF on US Letter, **double-sided, flipped on the long
   edge**, at 100% — no "fit to page".
2. Cut each sheet into four 3.5in x 5.5in rectangles: trim 3/4in of waste
   from each side, then one cut down the middle and one across. Two pages
   tall is exactly 11in, so there's no waste top or bottom.
3. Stack the rectangles in the order they came off the sheet — top-left,
   top-right, bottom-left, bottom-right.
4. Sew the left edge. A three- or five-hole pamphlet stitch about 6mm in
   holds well; the inner margin is 8.5mm to leave room.

Consecutive pages land on the two faces of each rectangle, so the stack
collates with no folding. `make print SCHEME=saddle` gives folded
signatures instead; `CROP_MARKS=1` draws cut lines.

The pages run to the top and bottom edges of the paper. The book's own
margins (6mm and 5mm) clear the unprintable border on a typical laser
printer — a Brother HL-2270DW reserves about 4.2mm — so nothing is
clipped, but don't let the driver scale to fit.

## How the data is checked

Every voicing is checked against the chord it claims to be.
`tools/theory.py` knows what notes each chord contains; `tools/validate.py`
works out what a fingering actually sounds on that tuning and compares.

- **Error** — sounds a note outside the chord. Fails the build.
- **Warning** — every note belongs, but a defining tone is missing. A
  mandolin chop chord drops the fifth on purpose. Allowed.

**2,122 voicings, 0 errors, 288 warnings.**

Where a voicing failed, `tools/repair.py` searched near what was written
for the closest playable fingering that does spell the chord — fewest
strings moved, then least movement. Everything it changed is in
[CORRECTIONS.md](CORRECTIONS.md), with the notebook's value beside the
printed one. The search stops as soon as the chord is fully spelled: a
two-string fix that turns `Gm` into a bare `G5` is worse than a
three-string one that sounds the flat third.

Six entries couldn't be repaired and were either dropped in favor of
another voicing or replaced with a generated shape. They're listed at the
end of `CORRECTIONS.md`.

Provenance lives in `data/notebook-source.yaml`, which is frozen. It used
to be a flag on each entry and kept getting stripped, after which stale
generated shapes survived rounds of improvement unnoticed.
`tools/provenance.py --sync` rebuilds the flags from the record.

## Playability

Four fingers, with a barre counting as one — but only when no open string
lies under it, since the barre would stop that string too. Reach is per
instrument: a mandolin's twelfth fret sits where a guitar's seventh does.

Reach isn't one number. `1-3-5-7` is an ordinary diminished shape on a
mandolin — one finger per string, climbing two frets at a time. The same
span with the frets jumbled is unplayable. So a diagonal gets a longer
allowance than a shape asking two fingers to share a string pair.

`tools/checkgen.py` scores the generator against the notebook: for every
chord a person voiced by hand, it asks the generator for the same chord and
compares. The generator picks something harder about 1% of the time.

## The chord vocabulary

`theory.VOCABULARY` is the union of what the mandolin pages, the piano
worksheet, and the core worship voicings use. `make complete` gives every
instrument all of it in all twelve keys. Transcribed voicings are left
exactly as written; missing ones are generated. Slash voicings on the
ukulele are inversions — it's re-entrant, so it has no bass.

**Spelling.** Notes are spelled by function: the augmented fifth of `C+` is
G#, not Ab. Three semitones above C is the flat third of `Cm9` and the
sharp ninth of `C7#9`. `theory.DEGREE_MAP` carries this per quality. The
piano pages are the exception — they name the key you actually play, `A`
rather than `Bbb`, because nobody hunts a keyboard for a double flat.

**Degrees** are written number first: `3b`, `7b`, `5#`. Chord symbols keep
their conventional spelling, so `Am7b5` stays `Am7b5`.

## Layout

One LaTeX page is one notebook page, 3.5in x 5.5in. `tex/voicings.cls` owns
geometry and type; `tools/render.py` owns what goes where.

The body is 12pt sans, two columns on the chord pages — the largest size at
which nothing overflows, found by building at each size and checking. In
two columns the binding constraint is width, not height: a nine-character
name beside a six-character fingering is all a 36mm column takes, so the
name sets one size down and the fingering stays full size.

Rows per page are tuned against the compiled PDF, not guessed:
`tools/pagecheck.py` compares intended pages against what TeX produced and
fails on overflow. `tools/editions.py` runs the same check on all fourteen.

Each instrument has its own pen — green mandolin, blue guitar, purple
ukulele, red piano, orange banjo, dark yellow bass — all clearing 4.5:1
against the page. A true orange gel pen sits at 4.1:1 and misses, so the
banjo ink is a shade deeper. On a mono printer they all render as mid
grays; the headings still name the instrument.

## Layout of the repository

```
data/
  instruments.yaml       tunings, reach limits
  notebook-source.yaml   frozen record of what the paper held
  banjo-spikes.yaml      generated by tools/spikes.py
  bass-patterns.yaml     root map and arpeggio patterns
  piano-shapes.yaml      piano voicings as interval patterns
  voicings/              one file per instrument
tools/
  theory.py              pitch classes, chord formulas, fret arithmetic
  playability.py         can a hand make this shape?
  validate.py            does each voicing spell its chord?
  repair.py resolve.py   fix what doesn't; drop or regenerate the rest
  generate.py complete.py  canonical voicings; full vocabulary
  piano.py spikes.py     generated sections
  render.py              data to LaTeX
  impose.py editions.py  page order; all fourteen PDFs
  checkgen.py            score the generator against the notebook
  provenance.py revert.py  what came off the paper; replay corrections
tex/                     the document class and its entry points
(notebook/)              photographs -- NOT in version control; the inside
                         cover carries a home address
```

## Adding an instrument

Add its tuning to `data/instruments.yaml`, add
`data/voicings/<instrument>.yaml` in the same shape as the others, then
`make validate`. Add it to `CHART_INSTRUMENTS` in `tools/render.py` for a
circle of fifths. An instrument whose voicings are note names rather than
frets sets `kind: notes`.

## Credits

Danne Stayskal — <danne@stayskal.com> — <http://danne.stayskal.com/>

MIT licensed. See [LICENSE.md](LICENSE.md).
