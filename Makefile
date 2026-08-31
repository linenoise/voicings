# Fancy Chords and their Voicings -- build pipeline.
#
#   make            validate the data, then build both PDFs
#   make screen     just build/voicings-screen.pdf (3.5x5.5, for reading)
#   make print      just build/voicings-print.pdf  (US Letter, 4-up)
#   make validate   check every voicing spells the chord it claims to be
#   make repair     propose fixes for anything that doesn't
#   make clean      remove build/
#
# The data is the source of truth. The PDFs are generated and are not
# checked in; `make` rebuilds them from data/ in one step.

PYTHON      ?= python3

# MacTeX and BasicTeX install here but only add it to interactive shells,
# so find it ourselves rather than failing in a fresh make.
TEXBIN      := $(firstword $(wildcard /Library/TeX/texbin /usr/local/texlive/*/bin/*))
export PATH := $(if $(TEXBIN),$(TEXBIN):,)$(PATH)

LATEX       ?= xelatex
BUILD       ?= build
DATA        ?= data
SCHEME      ?= flat          # flat = cut and side-sew, saddle = fold and sew
CROP_MARKS  ?=               # set to 1 to draw cut lines

SCREEN  := $(BUILD)/voicings-screen.pdf
PRINT   := $(BUILD)/voicings-print.pdf
BODY    := $(BUILD)/body.tex

SOURCES := $(wildcard $(DATA)/*.yaml) $(wildcard $(DATA)/voicings/*.yaml)
TOOLS   := $(wildcard tools/*.py)
TEXSRC  := tex/voicings.cls tex/screen.tex tex/pages.tex

LATEXOPTS := -interaction=nonstopmode -halt-on-error

ifeq ($(CROP_MARKS),1)
  IMPOSEOPTS := --crop-marks
endif

.PHONY: site all screen print validate lint repair resolve revert spikes \
        piano qr complete editions pagecheck clean check-latex help

all: validate editions

# -- checks ---------------------------------------------------------------

## Every voicing is checked against the chord it names. A voicing that
## sounds a note outside its chord is an error and stops the build.
validate: $(SOURCES) $(TOOLS)
	@$(PYTHON) tools/validate.py --data $(DATA)

## Propose the nearest playable fix for anything validate rejects.
## `make repair APPLY=1` writes the fixes back and updates CORRECTIONS.md.
repair:
	@$(PYTHON) tools/repair.py --data $(DATA) $(if $(APPLY),--apply,)

## Drop or regenerate whatever repair could not reach, then log it.
resolve:
	@$(PYTHON) tools/resolve.py --data $(DATA) $(if $(APPLY),--apply,)

## Restore the data to what was transcribed, so the correction pass can be
## replayed after changing how repair scores a fix.
revert:
	@$(PYTHON) tools/revert.py

## Regenerate the banjo 5th-string spike positions from theory.
spikes:
	@$(PYTHON) tools/spikes.py

## Regenerate the piano pages from data/piano-shapes.yaml.
piano:
	@$(PYTHON) tools/piano.py

## Build the static site for fancychords.com into docs/. Needs the PDFs,
## which it copies into docs/downloads/. GitHub Pages serves a branch
## from the repository root or from docs/, and this is the latter.
site: editions
	@$(PYTHON) tools/site.py

## Build all fourteen PDFs: the whole book and each instrument, screen and
## print. This is what `make` does, and what lands in editions/.
editions: $(SOURCES) $(TOOLS) $(TEXSRC) | check-latex
	@$(PYTHON) tools/editions.py

## Regenerate the README's QR code from the same URL the cover uses.
## Committed, because GitHub cannot generate one at render time.
qr: | check-latex
	@mkdir -p $(BUILD) assets
	@cp tex/qr.tex $(BUILD)/
	@cd $(BUILD) && $(LATEX) $(LATEXOPTS) -jobname=qr qr.tex >/dev/null
	@pdftoppm -png -r 220 -singlefile $(BUILD)/qr.pdf assets/qr
	@echo "wrote assets/qr.png"

## Give every instrument the full chord vocabulary in all twelve keys,
## generating whatever the notebook doesn't have. `APPLY=1` writes it.
complete:
	@$(PYTHON) tools/complete.py --data $(DATA) $(if $(APPLY),--apply,)

## Catch undefined macros in the generated LaTeX before TeX buries them in
## a hundred lines of noise.
lint: $(BODY)
	@$(PYTHON) tools/lint_tex.py

## Check no page overflowed onto an unheaded continuation. Runs as part of
## `make screen`; the row counts in tools/render.py are tuned against it.
pagecheck: $(SCREEN)
	@$(PYTHON) tools/pagecheck.py $(BODY) $(SCREEN)

# -- generated LaTeX ------------------------------------------------------

$(BODY): $(SOURCES) tools/render.py tools/theory.py data/piano-shapes.yaml
	@mkdir -p $(BUILD)
	@$(PYTHON) tools/render.py --data $(DATA) --out $@

# -- the book -------------------------------------------------------------

## One PDF page per notebook page, 3.5in x 5.5in. Read it on a phone or an
## e-reader, or feed it to the imposition step below.
screen: $(SCREEN)

$(SCREEN): $(BODY) $(TEXSRC) | lint check-latex
	@cp $(TEXSRC) $(BUILD)/
	@cd $(BUILD) && $(LATEX) $(LATEXOPTS) -jobname=voicings-screen screen.tex >/dev/null
	@cd $(BUILD) && $(LATEX) $(LATEXOPTS) -jobname=voicings-screen screen.tex >/dev/null
	@$(PYTHON) tools/pagecheck.py $(BODY) $@
	@echo "built $@ ($$($(PYTHON) tools/pagecount.py $@) pages)"

## The same pages laid 4-up on US Letter for double-sided printing.
print: $(PRINT)

$(PRINT): $(SCREEN) tools/impose.py | check-latex
	@$(PYTHON) tools/impose.py \
		--pages $$($(PYTHON) tools/pagecount.py $(SCREEN)) \
		--source voicings-screen.pdf \
		--scheme $(SCHEME) $(IMPOSEOPTS) \
		--out $(BUILD)/impose.tex
	@cd $(BUILD) && $(LATEX) $(LATEXOPTS) -jobname=voicings-print impose.tex >/dev/null
	@echo "built $@"

# -- housekeeping ---------------------------------------------------------

check-latex:
	@command -v $(LATEX) >/dev/null 2>&1 || { \
	  echo "$(LATEX) not found."; \
	  echo ""; \
	  echo "  macOS:   brew install --cask basictex"; \
	  echo "           sudo tlmgr update --self"; \
	  echo "           sudo tlmgr install extsizes pdfpages geometry \\"; \
	  echo "                               microtype fontspec xcolor"; \
	  echo "  Debian:  sudo apt install texlive-xetex texlive-latex-extra"; \
	  echo ""; \
	  echo "Then run make again. Everything except the two PDF targets"; \
	  echo "(validate, repair, spikes) works without LaTeX."; \
	  exit 1; }

## Remove what TeX leaves behind, but keep the generated .tex and the
## PDFs: those are committed, and deleting them would show up as fourteen
## deletions in git rather than as a clean tree.
clean:
	@find $(BUILD) -type f ! -name '*.tex' ! -name '*.pdf' -delete 2>/dev/null || true
	@echo "removed build intermediates; .tex and .pdf kept"

## Remove build/ entirely, PDFs included. `make` rebuilds them.
distclean:
	rm -rf $(BUILD)

help:
	@grep -B1 -E '^[a-z-]+:' Makefile | grep -E '^##|^[a-z-]+:' | \
	  sed -e 's/^## //' -e 's/:.*//'
