% voicings.cls -- Fancy Chords and their Voicings
%
% A pocket chord book. One LaTeX page = one notebook page, 3.5in x 5.5in,
% matching the paper notebook this is set from. Imposition for printing is
% a separate step (tex/impose.tex), so this file never has to think about
% paper.
%
% Requires: xelatex or lualatex (for system fonts), tikz, geometry.

\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{voicings}[2026/08/28 Pocket chord book]

\newif\ifvoicings@screen \voicings@screenfalse
\DeclareOption{screen}{\voicings@screentrue}
\DeclareOption*{\PassOptionsToClass{\CurrentOption}{article}}
\ProcessOptions\relax
\LoadClass[12pt]{extarticle}

\RequirePackage{geometry}
\RequirePackage{tikz}
\RequirePackage{xcolor}
\RequirePackage{fontspec}
\RequirePackage{microtype}
\RequirePackage{array}
\RequirePackage{calc}
\RequirePackage{ifthen}
\RequirePackage{amssymb}
\RequirePackage{multicol}
\RequirePackage{qrcode}
\RequirePackage[hidelinks]{hyperref}
\usetikzlibrary{calc}

% ---------------------------------------------------------------- geometry
% The trim size is the notebook's own. Margins are asymmetric: the spine
% edge needs room for the sewing, the outer edge is where a thumb goes.
\newlength{\bookwidth}\setlength{\bookwidth}{3.5in}
\newlength{\bookheight}\setlength{\bookheight}{5.5in}

\geometry{
  paperwidth=\bookwidth, paperheight=\bookheight,
  % Tight, but every margin still clears the unprintable border of a
  % typical laser printer (a Brother HL-2270DW reserves about 4.2mm), and
  % the inner margin leaves room for the sewing.
  top=6mm, bottom=5mm, inner=8.5mm, outer=5mm,
  twoside, includehead=false, includefoot=false,
}

\pagestyle{empty}
\setlength{\parindent}{0pt}
\setlength{\parskip}{0pt}
\raggedbottom

% Ragged right throughout. At a 60mm measure, justification opens rivers
% and forces overfull lines rather than admitting defeat; a ragged edge is
% both more honest and easier to read at a glance.
\raggedright

% ------------------------------------------------------------------ color
% Matched contrast is exactly what makes colors identical in grayscale, so
% on a mono printer these six all land on much the same gray. Nothing
% depends on color alone: every page names its instrument in the header.
\definecolor{ink}{HTML}{1A1A1A}
\definecolor{keyred}{HTML}{AA0019}      % key titles, and piano
% One pen per instrument, matching the notebook: green for mandolin, blue
% for guitar, purple for ukulele, red for piano, orange for banjo,
% yellow for bass, brown for cello. These are colors you can buy a
% fineliner in, so the same coding works when writing voicings onto a
% sheet of music by hand. The cello's brown sits between the bass's
% yellow and the black of the words, which is where a seventh pen has
% room left: it is a long way from both in OKLab even though it looks
% like a darker relative of each.
%
% Each is picked for two things at once: legible on the page, and telling
% apart from the other five. Every pair is at least 0.13 apart in OKLab.
% Five clear 4.5:1 against the page, the threshold for 12pt bold, because
% a chord book gets read in bad light. Yellow clears only 3.5:1: contrast
% here is a matter of darkness, and yellow stops looking yellow well
% before it gets dark enough, so the bass pen trades a little rather than
% turn olive.
\definecolor{fretgreen}{HTML}{00873C}   % mandolin, green pen
\definecolor{fretblue}{HTML}{0060BB}    % guitar, blue pen
\definecolor{fretbrown}{HTML}{63421F}   % cello, brown pen
\definecolor{fretpurple}{HTML}{9600D5}  % ukulele, purple pen
\definecolor{fretorange}{HTML}{C05500}  % banjo, orange pen
\definecolor{fretyellow}{HTML}{9A8800}  % bass, darkest legible yellow
% Both grays run at twice the contrast they used to. The old faint sat
% at 4.97:1 and the old rule at 1.93:1, which reads on a screen and
% washes out on a laser printer: this book is meant to be printed at
% home and carried, so the page it makes there is the one that counts.
\definecolor{rule}{HTML}{7E7E7E}   % 3.95:1, was 1.93:1
\definecolor{faint}{HTML}{404040}  % 10.10:1, was 4.97:1
\definecolor{paper}{HTML}{FFFFFF}
\ifvoicings@screen
  \definecolor{paper}{HTML}{FDFCF8}
\fi
\pagecolor{paper}
\color{ink}

% ------------------------------------------------------------- punch guides
% Five targets down the binding edge, at the holes of the pamphlet stitch
% in the README.
%
% Holes 1, 3 and 5 sit where a US three-ring binder punches, scaled to this
% page. A binder puts its holes 4.25in apart on an 11in sheet, half an inch
% in, so the ratios are 1.25/11, 5.5/11 and 9.75/11 down and 0.5/8.5 across.
% On a 3.5in by 5.5in page that is 15.875mm, 69.85mm and 123.825mm from the
% head, 5.23mm from the fold. Holes 2 and 4 fall halfway between, which
% makes all four gaps 26.9875mm and the whole set evenly spaced.
%
% The inset stays inside the 8.5mm inner margin, so the marks never touch a
% text block.
%
% The binding edge alternates, so these follow the page parity rather than
% sitting on a fixed side. On a sheet printed both ways the recto mark and
% the verso mark land on the same physical spot, which is what lets a
% single punch serve both faces.
\newlength{\punch@in}  \setlength{\punch@in}{5.23mm}
\newlength{\punch@gap} \setlength{\punch@gap}{26.9875mm}

\newcommand{\punchguides}{%
  \begin{tikzpicture}[remember picture, overlay]
    \ifodd\value{page}
      \coordinate (punch@base) at ([xshift=\punch@in]current page.west);
    \else
      \coordinate (punch@base) at ([xshift=-\punch@in]current page.east);
    \fi
    \foreach \punch@i in {-2,-1,0,1,2}{%
      \draw[color=faint, line width=0.3pt]
        ([yshift={\punch@i*\punch@gap}]punch@base) circle (0.75mm);}
  \end{tikzpicture}}

\AddToHook{shipout/background}{\punchguides}

% ------------------------------------------------------------------- fonts
% Sans throughout. A chord book is read in glances, on a stand, in bad
% light -- serifs buy nothing at these sizes and cost clarity in the fret
% digits, where 1 and 7 and 0 have to stay apart at six points.
%
% Falls back gracefully down a chain of families likely to be installed;
% the book still sets, in the default face, if none of them are.
\IfFontExistsTF{Helvetica Neue}{\setsansfont{Helvetica Neue}}{%
  \IfFontExistsTF{Avenir Next}{\setsansfont{Avenir Next}}{%
    \IfFontExistsTF{Arial}{\setsansfont{Arial}}{%
      \IfFontExistsTF{TeX Gyre Heros}{\setsansfont{TeX Gyre Heros}}{}}}}
\IfFontExistsTF{Menlo}{\setmonofont[Scale=0.94]{Menlo}}{%
  \IfFontExistsTF{DejaVu Sans Mono}{\setmonofont[Scale=0.90]{DejaVu Sans Mono}}{}}

% Sans is the body face, not an alternative to it.
\renewcommand{\familydefault}{\sfdefault}

\newcommand{\degsign}{\textsuperscript{o}}
\newcommand{\smaller}[1]{{\footnotesize #1}}

% Fret numbers. Monospaced so columns of digits line up down the page,
% which is most of what makes a chord book readable at arm's length.
% Set per section by \usevoicingcolor; every voicing on a page is in its
% instrument's ink.
\newcommand{\voicingcolor}{fretgreen}
\newcommand{\usevoicingcolor}[1]{\renewcommand{\voicingcolor}{#1}}

\newcommand{\frets}[1]{{\ttfamily\color{\voicingcolor}\bfseries #1}}
\newcommand{\notlisted}{{\color{rule}\ttfamily--}}
% Caveats on a voicing, set as a superscript beside the fingering:
% r where the shape has no root, i where a named bass is present but
% not underneath. Explained on the contents page.
\newcommand{\vmark}[1]{\raisebox{0.75ex}{\scriptsize\bfseries\color{faint}#1}}
% The same mark in body ink, for the contents page, where it is being
% named rather than applied and reads beside \frets{x}.
\newcommand{\vmarkink}[1]{\raisebox{0.75ex}{\scriptsize\bfseries\color{ink}#1}}

% A fingering above the ninth fret needs two digits per string and runs
% wider than a column allows, so it sets one size down. Rare enough that
% the inconsistency costs nothing.
% A shape with two-digit positions in it. The cello reaches the tenth
% and eleventh often enough -- its strings are a fifth apart and a
% named bass can force the hand up -- that three of them in one row
% overran a 36mm column, so this sets a size down again.
\newcommand{\fretswide}[1]{{\footnotesize\ttfamily\color{\voicingcolor}\bfseries #1}}
% A two-digit fret, kept in its brackets so the string it belongs to
% stays countable, and set down a size so the pair takes one column.
\newcommand{\fretbig}[1]{{\fontsize{5.5}{5.5}\selectfont[#1]}}

% Between alternate voicings of the same chord. A single space let 2200 and
% 2245 read as one long number; this is a gap plus a faint divider, so the
% eye stops without the page filling up with punctuation.
\newcommand{\voicingsep}{%
  \hspace{1.6mm}{\color{rule}\rule[-0.15ex]{0.4pt}{1.1ex}}\hspace{1.6mm}}

% ------------------------------------------------------------- page frames
% The optional argument lifts the rule without changing the space it
% occupies: whatever comes off the top is given back underneath. A banjo
% page needs it, because the drone caption that follows the rule sits
% closer under it than a row of fret digits would, which left the rule
% looking low even though the glue above and below was unchanged.
\newif\ifpage@drone \page@dronefalse
\newcommand{\dronepage}{\global\page@dronetrue}
\newcommand{\pagerule}[1][0pt]{\par\vspace{\dimexpr1.5pt-#1\relax}%
  {\color{rule}\hrule height 0.4pt}\par\vspace{\dimexpr3pt+#1\relax}}

\newcommand{\pagetitle}[1]{%
  {\large\bfseries\color{ink}#1\par}}

% Instrument on the left, key centered on the page, one line. Built from
% fixed-width boxes rather than glue: \raggedright is on throughout the
% book and \hfil under it does not center reliably.
% The key is the thing you hunt for when flipping through, so it is set at
% twice the size of everything else on the line. It centers in the space
% the instrument name leaves, not on the page: a zero-width label would
% center the key perfectly and then "Gb / F#" at this size would run
% straight over "Piano, continued". The label is nudged up so it sits
% against the middle of the key rather than on its baseline.
% Instrument hard left, key centered on the page, "continued" hard right.
% The two labels sit in zero-width boxes so neither shifts the key: it
% lands in the same place on every page, which is what makes the book
% flippable. Putting "continued" on the right rather than after the
% instrument name is what keeps it clear of a wide key like Gb / F#.
%
% A 21pt line would claim 8mm of a 129mm page just for its own leading,
% which costs two chords off the bottom of every key. The key is smashed
% to zero height and the line given an explicit strut instead, so the
% heading is as tall as it needs to look and no taller.
% #1 point size for the centered text, #2 left, #3 center, #4 right.
\newcommand{\pageheaderat}[4]{%
  \par\noindent
  % \hbox to, not \makebox: \makebox centers its own contents, so its
  % glue competes with the \hfil pair below and the whole heading bunches
  % into the middle of the line instead of spreading across it.
  \hbox to \linewidth{%
    \rule[-1.9mm]{0pt}{6.6mm}%
    \rlap{\raisebox{0.6mm}{\footnotesize\bfseries\color{faint}#2}}%
    \hfil\smash{\fontsize{#1}{#1}\selectfont\bfseries\color{keyred}#3}\hfil
    \llap{\raisebox{0.6mm}{\footnotesize\bfseries\color{faint}#4}}}%
  \par}

\newcommand{\pageheader}[3]{\pageheaderat{21}{#1}{#2}{#3}}

% A circle-of-fifths page carries the same heading as a chord page --
% instrument bold on the left, subject centered -- but "Circle of Fifths"
% is sixteen characters where a key is at most seven. At 21pt it would run
% straight over the instrument name, and even 18pt leaves under a point of
% air. 16pt is as large as clears the label comfortably on both sides,
% which is what keeps the two kinds of page looking like the same book.
\newcommand{\circleheader}[1]{%
  \pageheaderat{16}{#1}{\textcolor{ink}{Circle of Fifths}}{}}
\newcommand{\pagesubtitle}[1]{%
  \vspace{-1pt}{\footnotesize\color{faint}#1\par}\pagerule}

\newenvironment{circlepage}[1]{%
  \clearpage\circleheader{#1}\pagerule
}{\par}

\newenvironment{bookpage}[1]{%
  \clearpage\pagetitle{#1}%
}{\par}

% ------------------------------------------------------------------- cover
% Where the book lives now. The QR code and the cover carry this.
\newcommand{\bookurl}{https://fancychords.com}
% Where it is built. Kept apart from \bookurl because they stopped
% being the same place: one is for a reader with a phone, the other
% for someone who wants to correct a chord.
\newcommand{\sourceurl}{http://github.com/linenoise/voicings}

% #1 names the instrument for a single-instrument edition, or is empty for
% the whole book. #2 is the line (or lines) of instrument names beneath the
% rule. #3 is centered in the space between the rule and the QR code, and
% carries the tuning on a single-instrument cover; it is empty for the
% whole book, where no one tuning belongs on the front. Both editions
% share one cover so they cannot drift apart.
\newcommand{\coverpage}[3]{%
  \thispagestyle{empty}%
  \begin{center}
    \vspace*{6mm}
    {\fontsize{15}{17}\selectfont\bfseries Fancy\par}
    #1%
    {\fontsize{30}{32}\selectfont\bfseries Chords\par}
    \vspace{1mm}
    {\fontsize{13}{15}\selectfont and Their Voicings\par}
    \vspace{5mm}
    {\color{ink}\rule{\linewidth}{5mm}}

    % Exactly one of these is ever set: the instrument list on the whole
    % book, the tuning on a single-instrument edition. They share one slot
    % so that whichever it is sits centered in the space between the rule
    % and the QR code rather than hanging off the bottom of the rule.
    \vfill
    #2%
    #3%
    \vfill
    % Vector, generated at compile time by the qrcode package -- no image
    % file to keep in step with the URL beneath it, and it stays sharp at
    % any size a phone camera cares about. Error correction is left at the
    % default: the code is small on the page and this book gets carried in
    % a pocket, so it will be read creased and in poor light.
    \qrcode[height=27mm,padding]{\bookurl}\par
    \vspace{1.5mm}
    {\footnotesize\color{faint}\bookurl\par}
    \vspace{3mm}
  \end{center}
  \clearpage}

% The instrument name above "Chords", for a single-instrument edition.
\newcommand{\coversubject}[2]{%
  {\fontsize{22}{24}\selectfont\bfseries\color{#2}#1\par}\vspace{0.5mm}}

% The tuning on a single-instrument cover. Monospaced and in the
% instrument's own pen, the way tunings are set on the back sheet, so the
% cover states the same fact in the same voice the rest of the book uses.
\newcommand{\covertuning}[2]{%
  {\fontsize{15}{18}\selectfont\ttfamily\bfseries\color{#2}#1\par}}

% -------------------------------------------------------- table of contents
\newenvironment{tocdirectory}{%
  \pagerule
  \begin{list}{}{%
    \setlength{\leftmargin}{0pt}\setlength{\itemsep}{2.2mm}
    \setlength{\parsep}{0pt}\setlength{\topsep}{0pt}}%
}{\end{list}}

\newcommand{\tocline}[2]{%
  \item[]\makebox[0pt][l]{\bfseries #1}\hfill{\footnotesize\color{faint}#2}}

\newenvironment{tocnote}{\par\vfill\footnotesize\color{faint}}%
  {\par\vspace*{\note@floor}}

% Sits under the contents list, at the size of the entries above it: it is
% the last line of the same table, not a footnote.
\newenvironment{toctotal}{%
  \par\vspace{3mm}{\color{rule}\hrule height 0.4pt}\par\vspace{2.5mm}
  \color{ink}}{\par}

% ------------------------------------------------------- section dividers
\newcommand{\sectiondivider}[2]{%
  \clearpage\thispagestyle{empty}%
  \null\vfill
  \begin{center}
    {\fontsize{20}{23}\selectfont\bfseries\color{\voicingcolor}#1\par}
    \vspace{3mm}
    {\ttfamily\color{faint}#2\par}
  \end{center}
  \vfill\null
  \clearpage}

% ----------------------------------------------------------- theory pages
% The only pages here that argue rather than list. Body text is set a
% little smaller than a chord row and ragged right: these are read in a
% chair, not glanced at on a stand, and a justified 75mm measure at this
% size opens rivers.
\newenvironment{theorypage}[1]{%
  \clearpage\pagetitle{#1}\raggedright\footnotesize
}{\par}

\newcommand{\theorypara}[1]{\par\vskip1.1mm #1\par}

% What a drawing is showing. Centred under it, in the faint gray the
% footnotes use, so it reads as a label rather than another sentence.
\newcommand{\theorycaption}[1]{%
  \par\vspace{-0.6mm}
  {\centering\scriptsize\color{faint}#1\par}\vskip0.6mm}

% A term and what it means, hung the way \degreerow hangs a chord name,
% so the terms line up down the left edge and the eye can find one
% without reading the sentences.
\newlength{\theory@term}\setlength{\theory@term}{16mm}
\newcommand{\theoryterm}[2]{%
  \par\vskip1.3mm\nointerlineskip
  \vtop{\hsize=\linewidth
    \hangindent=\theory@term\hangafter=1
    \makebox[\theory@term][l]{\bfseries #1}#2\par}}

% The same, one column and a wider gutter, for lists whose terms are
% words rather than symbols. "thirteenth" does not fit beside a chord
% degree in a 16mm box.
\newenvironment{widetermlist}{%
  \setlength{\theory@term}{22mm}%
}{\setlength{\theory@term}{16mm}}

% A chord quality: what it is called, the degrees it stacks, and what it
% is for. The degrees are set in the voicing face because they are the
% same alphabet the chord pages use.
\newcommand{\qualityrow}[3]{%
  \par\vskip1.4mm\nointerlineskip
  \vtop{\hsize=\linewidth
    \hangindent=\theory@term\hangafter=1
    \makebox[\theory@term][l]{\bfseries #1}#2\par
    \vspace{0.2mm}{\scriptsize\color{faint}#3\par}}}

% Two columns, for the pages that are a list of short definitions.
\newenvironment{theorycols}{%
  \begin{multicols}{2}\raggedright
}{\end{multicols}}

% ------------------------------------------------- theory diagrams
% Drawn with TikZ, which the class already loads for the circle of
% fifths. Every one of these is small enough to sit inside a 75mm
% column with the prose that explains it.

% A chord box: the thing every other chord book prints, drawn once here
% so the reader can see that it and a row of digits say the same thing.
% #1 number of strings, #2 fret of the top line (0 = nut),
% #3 comma list of fret numbers low string first, x for muted.
\newcommand{\chordbox}[3]{%
  \begingroup
  \def\cb@strings{#1}\def\cb@base{#2}%
  \begin{tikzpicture}[x=3.4mm,y=-3.6mm,line width=0.3pt]
    \foreach \s in {0,...,\numexpr#1-1\relax}
      \draw[color=rule] (\s,0) -- (\s,4);
    \foreach \f in {1,...,4}
      \draw[color=rule] (0,\f) -- (\numexpr#1-1\relax,\f);
    \ifnum#2=0\relax
      \draw[line width=1.1pt,color=ink] (0,0) -- (\numexpr#1-1\relax,0);
    \else
      \draw[color=rule] (0,0) -- (\numexpr#1-1\relax,0);
      \node[anchor=east,color=faint,font=\fontsize{5}{5}\selectfont]
        at (-0.35,0.5) {#2};
    \fi
    \cb@dots{#3}%
  \end{tikzpicture}%
  \endgroup}

% One dot, or an x above the nut, per string.
\newcommand{\cb@dots}[1]{%
  \foreach \pos [count=\si from 0] in {#1} {%
    \ifthenelse{\equal{\pos}{x}}{%
      \node[color=faint,font=\fontsize{5}{5}\selectfont]
        at (\si,-0.45) {$\times$};
    }{\ifthenelse{\equal{\pos}{0}}{%
      \node[draw,color=ink,circle,inner sep=0.35mm,line width=0.3pt]
        at (\si,-0.45) {};
    }{%
      \fill[color=ink] (\si,\pos-0.5) circle (0.85mm);
    }}%
  }}

% The twelve semitones as a strip, with some of them named. #1 is a
% comma list of twelve labels; an empty one leaves the box blank.
\newcommand{\chromastrip}[1]{%
  \begin{tikzpicture}[x=5.2mm,y=-4.4mm,line width=0.3pt]
    \foreach \lab [count=\i from 0] in {#1} {%
      \draw[color=rule] (\i,0) rectangle (\i+1,1);
      \node[font=\fontsize{5.6}{6}\selectfont\ttfamily\bfseries,
            color=\voicingcolor] at (\i+0.5,0.5) {\lab};
    }
  \end{tikzpicture}}

% A stack of thirds, drawn as the notes it stacks. #1 comma list of
% degree labels, bottom first.
\newcommand{\thirdstack}[1]{%
  \begin{tikzpicture}[x=4.6mm,y=-4.0mm,line width=0.3pt]
    \foreach \lab [count=\i from 0] in {#1} {%
      \node[font=\fontsize{6}{6.4}\selectfont\ttfamily\bfseries,
            color=\voicingcolor] at (0,-\i) {\lab};
      \ifnum\i>0
        \draw[color=rule,->,>=stealth,line width=0.25pt]
          (0.9,-\i+0.75) -- (0.9,-\i+0.25);
        \node[anchor=west,font=\fontsize{5}{5.4}\selectfont,color=faint]
          at (1.15,-\i+0.5) {a third};
      \fi
    }
  \end{tikzpicture}}

% A row of boxed labels with an arrow between each -- progressions,
% substitutions, inversions. Built by the caller rather than looped over
% here, because only the caller knows which box is the last one and so
% which arrow not to draw.
\newcommand{\chainbox}[1]{%
  \tikz[baseline=-0.9mm]{
    \node[draw,color=rule,rounded corners=0.4mm,
          inner xsep=1.1mm,inner ysep=0.7mm,line width=0.3pt,
          font=\fontsize{6}{6.4}\selectfont\ttfamily\bfseries]
      {\textcolor{\voicingcolor}{#1}};}}
\newcommand{\chainarrow}{\,{\color{faint}\tiny$\to$}\,}

% ------------------------------------------------------------ chord pages
% Two columns of the same shape as the notebook: the chord name on the
% left, its voicings running right. Rows are ruled faintly so the eye can
% track across on a dark stage.
\newlength{\chord@name}\setlength{\chord@name}{20mm}
\newlength{\chord@rowsep}\setlength{\chord@rowsep}{0.10mm}
% Tall enough to clear a degree ring and a sharp, so no glyph ever
% pushes its own row taller than its neighbors.
\newcommand{\chord@strut}{\vrule height 3.24mm depth 0.58mm width 0pt}

\setlength{\columnsep}{3mm}
% The space between a page heading and the first row. It has to be set
% here: multicol discards glue placed just before the environment, so a
% \vspace there does nothing and only \multicolsep is left holding it.
% LaTeX's default of 12pt put 23pt between the heading and the first row;
% this halves it.
\setlength{\multicolsep}{0.5pt}
\setlength{\columnseprule}{0pt}

% Instrument on the left, key centered on the same line. The instrument is
% set in a zero-width box so it does not push the key off center: the key
% is what the eye hunts for when flipping, and it should sit in the same
% place on every page.
\newenvironment{chordpage}[4]{%
  \clearpage
  \pageheader{#1}{#2}{\ifthenelse{\equal{#3}{cont}}{continued}{}}%
  \ifpage@drone\pagerule[1.8pt]\global\page@dronefalse\else\pagerule\fi
  #4%
  \raggedright
  \begin{multicols}{2}%
}{\end{multicols}}

% Between one kind of chord and the next.
% One blank line between one kind of chord and the next -- the same height
% a row would occupy, so the groups read as separate blocks rather than as
% rows that happen to sit slightly further apart.
% Space below a finished group. Ordinary glue, so it vanishes if the group
% happens to end a column.
% \nobreak first: it makes the glue that follows an illegal breakpoint,
% so a column can never break immediately before a group and leave that
% group's rule stranded at the top of the next column.
% The rule sits centered in the white it opens, which is not the same as
% centering it between the two baselines. Fret digits sit on the baseline
% and rise about 2.9mm above it, so the space under the rule is nearly all
% glyph while the space over it is nearly all air. These two numbers look
% lopsided for that reason: the small one below is glue that the next row's
% digits then fill. Measured ink to ink, the gap is even.
\newcommand{\chordgap}{\par\nobreak\vskip0.46\baselineskip}
% The piano rows are \footnotesize and sit on a wider row separation,
% so the same rule needs different glue on either side of it there.
\newcommand{\pianogap}{\par\nobreak\vskip0.33\baselineskip}

% The first row of a group carries the rule that heads it. Drawing the rule
% between rows instead would leave it stranded at the top of a column
% whenever the break fell there: an \hrule is not discardable, and glue is.
% Same weight and color as the rule under the page heading.
\newcommand{\chordrowfirst}[2]{%
  \par\vskip\chord@rowsep\nointerlineskip
  \vtop{\hsize=\linewidth
    {\color{rule}\hrule height 0.4pt}\vskip0.54\baselineskip
    \chord@strut\makebox[\chord@name][l]{\small\bfseries #1}#2\chord@strut\par}}

% Tight enough that a whole key -- around thirty chords -- lands on one
% page. Two half-empty pages per key would double the sheet count, and
% flipping mid-song is exactly what this book exists to avoid.
% In a column this narrow a chord and two alternates will not share a
% line at any size worth reading, so alternates stack under the first
% instead of running on. That also settles the question of whether
% "2200 2245" is one fingering or two: they are on separate lines.
% The name is set a size down from the fingering. The fingering is what
% you read at a glance from a music stand; the name is what you scan for
% once. Names run to nine characters (Bbsus2/D), fingerings to six
% (x13321), and at 12pt both will not fit a 36mm column -- so the name
% gives way and the numbers stay full size.
% One chord, one unbreakable block. Without this a chord with two
% voicings could take the column break between them, leaving 0000 at the
% foot of one column and 2555 at the head of the next with no label -- it
% reads as a different chord entirely. A vbox cannot be broken.
% \vtop, not \vbox. A \vbox sits on the baseline of its LAST line, so a
% chord with two voicings hung higher than its neighbors and the top of a
% column came out ragged wherever the first row happened to have an
% alternate. \vtop sits on the baseline of its FIRST line, which is what
% top-justifying a cell means: every row starts level whatever it holds.
% Banjo and ukulele never showed the fault because no chord of theirs has
% a second voicing.
%
% The box is placed in VERTICAL mode: no \noindent, which would wrap it in
% a paragraph and put a legal breakpoint in the interline glue before the
% \nobreak could stop it. That is how a rule ended up stranded at the head
% of column two. In vertical mode the order reads exactly as it behaves:
% box, then a penalty that welds the rule to it, then the rule, then
% ordinary glue -- and glue at the top of a column is discarded, so both
% columns start level.
%
% \vtop, not \vbox: a \vbox sits on the baseline of its LAST line, so a
% chord with two voicings hung higher than its neighbors and the top of a
% column came out ragged. A \vtop sits on its FIRST baseline, which is
% what top-justifying a cell means.
% Rows are separated by space alone. A hairline under every chord turned
% a page of thirty into a ledger; the group rules carry the structure, and
% the rows only need enough air to read as separate.
% \nointerlineskip because the rule that used to sit between rows also
% suppressed TeX's interline glue. Take the rule away and that glue comes
% back, silently adding a couple of points to every row.
\newcommand{\chordrow}[2]{%
  \par\vskip\chord@rowsep\nointerlineskip
  \vtop{\hsize=\linewidth
    \chord@strut\makebox[\chord@name][l]{\small\bfseries #1}#2\chord@strut\par}}

%% An alternate voicing goes under the first, pulled up tight so the pair
% reads as one chord rather than drifting toward the next one.
\newcommand{\voicingnext}{\chord@strut\par\vspace{-1.11mm}\hspace*{\chord@name}\chord@strut}

% ------------------------------------------------------- circle of fifths
% Twelve segments, major on the outside, relative minor inside. Drawn
% rather than tabulated because the whole point of the circle is that
% neighbors are a fifth apart and you can see it.
% Sized to the page, not to habit. The binding constraint is width: a
% six-character fingering like xx0231 is eight millimeters wide, and the
% ring it sits in has to give it more arc than that. The circle was drawn
% at 62mm across on a page that allows 72mm, which is where the guitar
% page's collisions came from. Signatures move back inside the hub, since
% "1b" is two characters and needs almost nothing.
% The bands are sized by arc, not by looks. A wedge is 30 degrees, so the
% room a label has is 2*pi*r/12: the inner ring has to sit far enough out
% that four digits at body size still fit across it. Pushing the middle
% circle out from 24mm to 26mm and shrinking the hub buys the minor ring
% the millimetre it was short.
\newlength{\cof@outer}\setlength{\cof@outer}{36mm}
\newlength{\cof@mid}\setlength{\cof@mid}{26mm}
\newlength{\cof@inner}\setlength{\cof@inner}{12mm}

% Absolute sizes: a diagram this dense cannot follow the body size.
\newcommand{\cof@name}{\fontsize{8}{8.6}\selectfont}
% Voicings inside a circle. Four frets or a two-character string-and-fret
% fit at the body size; six guitar digits and a five-note piano list do
% not, so those keep the small setting. \usecofsize picks per instrument.
\newcommand{\cof@fretsize}{6.4}
\newcommand{\usecofsize}[1]{\renewcommand{\cof@fretsize}{#1}}
\newcommand{\cof@frets}{%
  \fontsize{\cof@fretsize}{\cof@fretsize}\bfseries\selectfont}

% A voicing that runs to two lines -- the bass circle gives a five-string
% position with the four-string one beneath it -- has to restate its face
% after the break: a tikz node typesets each line on its own, so the font
% and color set before the \\ do not carry across it.
\newcommand{\cofline}{\cof@frets\ttfamily\color{\voicingcolor}}
\newcommand{\cof@minor}{\fontsize{7.2}{7.6}\selectfont}
\newcommand{\cof@sig}{\fontsize{6}{6.4}\selectfont}

% #1 goes in the hub, where there is a hole and nothing else to put in it.
\newenvironment{circleoffifths}[1]{%
  \vspace{1mm}
  \begin{center}
  \begin{tikzpicture}[every node/.style={inner sep=0pt}]
    \draw[rule,line width=0.4pt] (0,0) circle (\cof@outer);
    \draw[rule,line width=0.4pt] (0,0) circle (\cof@mid);
    \draw[rule,line width=0.4pt] (0,0) circle (\cof@inner);
    \node[align=center] at (0,0) {\cof@sig\bfseries\color{faint}#1};
}{%
  \end{tikzpicture}
  \end{center}}

% #1 index 0-11 (0 = C at twelve o'clock)  #2 major  #3 major frets
% #4 minor  #5 minor frets  #6 key signature  #7 "up" or "down": which way
% the outward side of this wedge points, so the stack can be ordered.
\newcommand{\cofsegment}[7]{%
  \pgfmathsetmacro{\cof@a}{90 - 30*#1}%
  \pgfmathsetmacro{\cof@edge}{90 - 30*#1 - 15}%
  \draw[rule,line width=0.3pt]
    (\cof@edge:\cof@inner) -- (\cof@edge:\cof@outer);
  % Name and fingering go in ONE node, stacked. Putting them at two radii
  % made them collide at three and nine o'clock, where a radial gap of
  % three millimeters is a horizontal gap of three millimeters and the
  % fret numbers are six millimeters wide.
  % Name and voicing stay in one node so the pair occupies a single compact
  % block, but the stack is ordered so the voicing falls on the outward
  % side of the band -- where the wedge is wider, and where the longer of
  % the two strings needs the room.
  %
  % They are not placed at two different radii, which is the obvious way to
  % do it and is wrong: at three and nine o'clock "further out" is
  % sideways, so radial separation puts the two items on the same
  % horizontal line and xx0231 lands on top of its own key name. Ordering
  % within one node buys the same thing at top and bottom and costs nothing
  % at the sides.
  \node[align=center] at (\cof@a:31.2mm) {%
    \ifthenelse{\equal{#7}{up}}%
      {\cof@frets\ttfamily\color{\voicingcolor}#3\\[-2.4pt]%
       \cof@name\bfseries\color{keyred}#2}%
      {\cof@name\bfseries\color{keyred}#2\\[-2.4pt]%
       \cof@frets\ttfamily\color{\voicingcolor}#3}};
  \node[align=center] at (\cof@a:20.4mm) {%
    \ifthenelse{\equal{#7}{up}}%
      {\cof@frets\ttfamily\color{\voicingcolor}#5\\[-2.4pt]%
       \cof@minor\bfseries#4}%
      {\cof@minor\bfseries#4\\[-2.4pt]%
       \cof@frets\ttfamily\color{\voicingcolor}#5}};
  % Key signatures sit outside the rim: twelve of them around a hub the
  % size of a thumbnail was unreadable.
  \node at (\cof@a:7.8mm) {\cof@sig\color{faint}#6};}

% Footnotes are bottom-justified: pushed to the floor of the page, with
% the same space beneath the last line as there is between the text and
% the left edge of the page. The page's bottom margin is 5mm and its inner
% margin 8.5mm, so 3.5mm makes up the difference.
\newlength{\note@floor}\setlength{\note@floor}{3.5mm}

\newcommand{\circlefootnote}[1]{%
  \vfill{\footnotesize\color{faint}#1\par}\vspace*{\note@floor}}

% ------------------------------------------------------------ banjo pages
% Where to spike the 5th string for this key, at the head of its pages.
% Where to catch the 5th string for this key. Most keys want the same
% drone whether the tune is major or minor, and saying so twice just makes
% the line longer to read.
% Set at the size of the instrument name in the header above it: this is
% a note about the page, not one of the chords on it.
% Where major and minor disagree, minor goes on its own line with its "m"
% under the "m" of major, so the two answers read as a short column rather
% than one run-on sentence. The hanging indent is the width of the label,
% measured at the size it is actually set in.
% Two stacked boxes rather than a hanging indent: the label sets the width
% of a column, and both answers start at its right edge, so the "m" of minor
% lands under the "m" of major.
\newlength{\drone@lead}
\newcommand{\dronenote}[2]{%
  \par{\footnotesize\color{faint}%
    \settowidth{\drone@lead}{Drone spike: }%
    \hbox to \linewidth{\makebox[\drone@lead][l]{Drone spike:}major \textbf{#1}\hfil}%
    \hbox to \linewidth{\hskip\drone@lead minor \textbf{#2}\hfil}}%
  \vspace{1.6mm}{\color{rule}\hrule height 0.3pt}\vspace{0.2mm}}

\newcommand{\dronenoteboth}[1]{%
  \par{\footnotesize\color{faint}Drone spike: \textbf{#1}}%
  \par\vspace{1.6mm}{\color{rule}\hrule height 0.3pt}\vspace{0.2mm}}

% -------------------------------------------------------------- bass pages
% Twelve rows and five columns on a page that can hold far more, so the
% type is set up to fill it: this is a lookup table read at a glance, and
% there is no reason for it to sit small in the top third of the page.
% One column per string, so the same table serves a four-course mandolin
% and a six-string guitar. The caller passes the count and the column
% padding, because six columns will not take the padding five will.
% Full width and full height. These are lookup tables read at arm's
% length off a music stand, and there is no reason for one to sit small in
% the top corner of a page that has nothing else on it. tabular* with a
% stretching intercolumn skip spreads the strings across the measure; the
% row stretch is what fills the rest. #2 is kept for callers but the
% padding now comes out of the fill.
\newenvironment{rootmap}[2]{%
  \setlength{\tabcolsep}{0pt}
  \renewcommand{\arraystretch}{\rootmap@stretch}
  \begin{tabular*}{\linewidth}{@{\extracolsep{\fill}}l|*{#1}{c}c@{}}
}{\end{tabular*}}
\newcommand{\rootmap@stretch}{1.6}

% The trailing & feeds an empty final column. It has no width of its
% own, so the stretched gutter in front of it becomes a right margin
% the same size as the gaps between the columns, instead of the last
% column sitting flush against the measure.
\newcommand{\rootmaphead}[1]{{\bfseries} & #1 & \\[1pt] \hline}
\newcommand{\rootmaprow}[2]{{\bfseries\color{keyred}#1} & #2 & \\}

% Movable shapes: the relative fingering, which string carries the root,
% and one worked example. Four narrow columns rather than the root map's
% grid, because the shape column is wide and the rest are not.
\newenvironment{movablelist}{%
  \setlength{\tabcolsep}{3pt}
  \renewcommand{\arraystretch}{1.15}
  \begin{tabular}{@{}llll@{}}
}{\end{tabular}}
\newcommand{\movablehead}[4]{%
  {\bfseries\footnotesize#1} & {\bfseries\footnotesize#2} &
  {\bfseries\footnotesize#3} & {\bfseries\footnotesize#4} \\[1pt] \hline}
\newcommand{\movablerow}[4]{%
  \frets{#1} & {\footnotesize#2} & {\footnotesize#3} & \frets{#4} \\}
\newcommand{\movablehdr}[1]{%
  \multicolumn{4}{@{}l@{}}{\vrule height 3.6mm depth 1.4mm width 0pt
    {\bfseries\color{keyred}#1}} \\}

% The number chart, for the instruments that play notes rather than
% chords. Seven degrees across, twelve keys down, so the padding goes to
% almost nothing and the cells set a size down.
\newenvironment{numberchart}{%
  \setlength{\tabcolsep}{0pt}
  \renewcommand{\arraystretch}{\numberchart@stretch}
  \begin{tabular*}{\linewidth}{@{\extracolsep{\fill}}l|*{7}{c}c@{}}
}{\end{tabular*}}
\newcommand{\numberchart@stretch}{1.5}
\newcommand{\numberhead}[1]{{} & #1 & \\[1pt] \hline}
\newcommand{\numberrow}[2]{{\bfseries\color{keyred}\small#1} & #2 & \\}
\newcommand{\numbercell}[1]{{\small\color{\voicingcolor}\bfseries#1}}

\newenvironment{rootmapnote}{\par\vfill\footnotesize\color{faint}}%
  {\par\vspace*{\note@floor}}

\newenvironment{patternlist}{%
  \pagerule
  \begin{list}{}{%
    \setlength{\leftmargin}{0pt}\setlength{\itemsep}{0.5mm}
    \setlength{\parsep}{0pt}\setlength{\topsep}{0pt}}%
}{\end{list}}

% Two lines apiece, not three: the name carries what the pattern is for,
% and the degrees go underneath. Six patterns then fit on one page at the
% book's size.
% Every step twice over: the string it falls on, counted from the root's,
% and the fret, counted from the root's. A bass is tuned in fourths, so
% 1+R is already five semitones up before the fret offset applies, which
% is why b7 at 2+R sits at the root's own fret rather than above it.
% The "when to use it" note runs on after the name and wraps back to the
% margin. Hanging it under itself reads better but costs a line per wrap,
% and the page has 4.8mm of slack, not the 7mm that would take.
\newcommand{\patternitem}[3]{%
  \item[]{\small\bfseries#1}\quad{\scriptsize\color{faint}#3}%
  \par\vspace{0.2mm}{\renewcommand{\arraystretch}{0.82}#2}}
\newcommand{\patternrow}[1]{{\scriptsize\color{faint}#1}}
\newcommand{\patterncell}[1]{{\scriptsize#1}}

% -------------------------------------------------------------- piano
% Note names rather than fret numbers, so they need room to breathe and a
% face that keeps accidentals legible. Not monospaced: the lists vary in
% length and lining them up would waste the width.
\newcommand{\notes}[1]{{\color{\voicingcolor}\bfseries #1}}

% Between two notes of a voicing: a space, wide enough to separate the
% notes without a dash doing the work. It is glue rather than a kern, so a
% long list can still wrap here in a narrow column -- and between notes is
% the only place it can, since an accidental is set as one token with the
% letter it belongs to.
% A middot between notes rather than a bare gap. Sized so the pair of
% thin spaces plus the dot comes to the width the plain space used to be,
% because the column is only 36mm and any widening starts wrapping chords
% that used to fit on their line.
\newcommand{\notesep}{\hskip 0.16em plus 0.05em minus 0.02em
  {\color{rule}\textperiodcentered}%
  \hskip 0.16em plus 0.05em minus 0.02em\relax}

% The spread voicing goes under the close one. A line break rather than a
% new paragraph: the row's hanging indent already pushes every line after
% the first past the name, and starting a paragraph would throw it away
% and drop the wraps back to the margin.
\newcommand{\pianonext}{\\}

% One column, not two. A six-note spread voicing needs about 50mm of
% note names; a 36mm column gives it 16mm after the chord name and the
% list wraps. Half as many rows to a page and twice the width fits every
% voicing on its own line, which is the whole point of a lookup table.
\newenvironment{pianopage}[2]{%
  \clearpage
  \pageheader{Piano}{#1}{\ifthenelse{\equal{#2}{cont}}{continued}{}}%
  \pagerule
  \raggedright
}{}

% Name above, notes below: a five-note voicing in a flat key is too wide to
% share a line with its name at this trim size.
% Name and notes share a line where they fit; a five-note voicing in a
% flat key is set below its name instead.
% Note names run wider than fret digits -- two four-note sus4 shapes in a
% flat key is the widest thing in the book -- so they set one step down
% from the chord names beside them, which keeps every row on one line.
% Two voicings per chord -- the close spelling and the open worship one --
% run wider than the page in the flat keys, so the second wraps under the
% name rather than off the edge.
\newlength{\piano@name}\setlength{\piano@name}{20mm}
% Wider than the chord pages' because the type is smaller: a note list
% at eight points needs proportionally more air to read as its own row.
\newlength{\piano@rowsep}\setlength{\piano@rowsep}{2.0mm}
% Kept under \scriptsize's baselineskip: a taller strut than the line
% spacing makes TeX fall back to \lineskip and a wrapped voicing drifts
% away from its own chord name.
\newcommand{\piano@strut}{\vrule height 3.24mm depth 0.58mm width 0pt}
% A voicing may wrap inside its own column -- there is no room not to --
% but never across columns, which would leave half a chord at the foot of
% one and half at the head of the next with no name on it. The vbox is
% what forbids it: TeX cannot break one. Continuation lines hang under the
% name so the notes stay in a block.
% The \par sits INSIDE the size group on purpose. TeX sets each line with
% the \baselineskip in force when that line ends, so closing the group
% first left the final line of a wrapped voicing taking the 12pt body's
% leading -- a visible hole above the continuation. Ending the paragraph
% while \scriptsize is still active keeps the two lines tight together,
% and the space that separates one chord from the next then sits below the
% pair, where it belongs.
% Separated by space, like the chord pages: no hairline under every row.
% \nointerlineskip because the rule that used to sit between rows also
% suppressed TeX's interline glue, and taking it away lets that glue back
% in unnoticed.
% The close voicing sits in a fixed box so the spread one beside it
% starts at the same place on every row. Set flush, the divider
% wandered with the length of whatever was to its left.
\newlength{\piano@first}\setlength{\piano@first}{24mm}
% Public: the body file is read with @ as an ordinary character.
\newcommand{\pianoclose}[1]{\makebox[\piano@first][l]{#1}}
\newlength{\piano@col}
% Name in a fixed box, voicings in a parbox beside it. The parbox is what
% makes every line after the first sit under the first one: a hanging
% indent does not survive the \\ between the close voicing and the spread
% one, and the second voicing was dropping back to the margin.
\newcommand{\piano@body}[2]{%
  \setlength{\piano@col}{\linewidth-\piano@name}%
  \noindent{\footnotesize\makebox[\piano@name][l]{\bfseries #1}}%
  \parbox[t]{\piano@col}{\scriptsize\baselineskip=11.34pt\raggedright
    \piano@strut #2\piano@strut\par}\par}

\newcommand{\pianorow}[2]{%
  \par\vskip\piano@rowsep\nointerlineskip
  \vtop{\hsize=\linewidth\piano@body{#1}{#2}}}

\newcommand{\pianorowfirst}[2]{%
  \par\vskip\piano@rowsep\nointerlineskip
  \vtop{\hsize=\linewidth
    {\color{rule}\hrule height 0.4pt}\vskip0.71\baselineskip
    \piano@body{#1}{#2}}}

% ------------------------------------------------------- bass vocabulary
% Twenty-six kinds of chord will not fit one column at a size worth
% reading, and they do not need the full measure -- "R 9 b3 4 5 b7" is
% short. Two columns, and the type can be as large as the page allows.
\newenvironment{degreetable}{%
  \raggedright
  \begin{multicols}{2}%
}{\end{multicols}}

% Set like the chord pages: space between rows rather than a hairline
% under each, a rule heading every group, and \nointerlineskip so the
% spacing below is the only thing separating them.
\newlength{\degree@rowsep}\setlength{\degree@rowsep}{1.6mm}

\newcommand{\degreerow}[2]{%
  \par\vskip\degree@rowsep\nointerlineskip
  \vtop{\hsize=\linewidth
    \hangindent=15mm\hangafter=1
    \makebox[15mm][l]{\bfseries #1}#2\par}}

\newcommand{\degreerowfirst}[2]{%
  \par\vskip\degree@rowsep\nointerlineskip
  \vtop{\hsize=\linewidth
    {\color{rule}\hrule height 0.4pt}\vskip0.15\baselineskip
    \hangindent=15mm\hangafter=1
    \makebox[15mm][l]{\bfseries #1}#2\par}}

% -------------------------------------------------------------- back sheet
% Everything that is reference rather than content lives here, so the
% inside front can be the recipient's.
\newcommand{\backsheet@title}{}
% How to read the fingerings, for the solo editions. The whole book says
% this on its contents page; a single-instrument booklet has no contents
% page, so it says it here instead, above the credits.
\newcommand{\readingnotes}[1]{%
  \item[]\vspace{1.4mm}{\color{rule}\hrule height 0.4pt}\vspace{1.6mm}
  {\footnotesize\color{faint}#1\par}}

% The same thing the reading notes say, drawn once: a chord box beside
% the digits that mean it. A booklet with no contents page has nowhere
% else to show a reader what a row of numbers is a picture of.
% #1 the chord's name, #2 the box, #3 the digits.
\newcommand{\readingfigure}[3]{%
  \item[]\vspace{1.8mm}
  \centerline{%
    \begin{tabular}{@{}c@{\hskip 4mm}c@{\hskip 4mm}c@{}}
      #2 & \raisebox{4.2mm}{\color{faint}$=$}
         & \raisebox{4.2mm}{\frets{#3}}\\
    \end{tabular}}%
  \vspace{1.2mm}
  {\footnotesize\color{faint}\centering
   The same #1 chord, drawn and written.\par}}

\newenvironment{backsheet}[1]{%
  \renewcommand{\backsheet@title}{#1}%
  \clearpage\thispagestyle{empty}%
  \pagetitle{Tunings}\pagerule
  \begin{list}{}{%
    \setlength{\leftmargin}{0pt}\setlength{\itemsep}{0.15mm}
    \setlength{\parsep}{0pt}\setlength{\topsep}{0pt}}%
}{%
  \end{list}
  \vfill
  {\color{rule}\hrule height 0.4pt}
  \vspace{1.2mm}
  {\footnotesize
   \textbf{\backsheet@title}\par
   \vspace{0.8mm}
   {\color{faint}%
    Danne Stayskal\\
    \href{mailto:danne@stayskal.com}{danne@stayskal.com}\\
    http://danne.stayskal.com\par}
   \vspace{0.9mm}
   {\color{faint}Downloads and a printable copy:\par}
   \bookurl\par
   \vspace{0.9mm}
   {\color{faint}Source and corrections:\par}
   \sourceurl\par
   \vspace{0.9mm}
   {\color{faint}\scriptsize MIT licensed. Print it, cut it, sew it,
    give it away.\par}}
  \vspace{0.5mm}
  \clearpage}

% #4 is the instrument's own pen. Without it the whole list inherited
% whichever color the last section happened to leave current, so every
% tuning on the back of the whole book came out in the bass's yellow.
%
% Set tight: seven instruments and the credits have to share one page.
% The name sits in a fixed box so every tuning starts at the same place
% down the list: the G of G D A E lands above the E of E A D G B E rather
% than wherever the instrument's name happened to end.
\newlength{\tuning@name}\setlength{\tuning@name}{21mm}
\newcommand{\tuningrow}[4]{%
  \item[]\makebox[\tuning@name][l]{\small\bfseries#1}%
  {\ttfamily\color{#4}\bfseries\small#2}%
  \par\vspace{0.15mm}{\scriptsize\color{faint}\linespread{0.86}\selectfont#3\par}}
