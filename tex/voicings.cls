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

% ------------------------------------------------------------------ colour
% Chosen to stay legible on a mono laser printer: everything carries in
% grey value alone, colour only reinforces it.
\definecolor{ink}{HTML}{1A1A1A}
\definecolor{keyred}{HTML}{B3261E}
\definecolor{fretgreen}{HTML}{1F6F43}
\definecolor{rule}{HTML}{B8B8B8}
\definecolor{faint}{HTML}{6E6E6E}
\definecolor{paper}{HTML}{FFFFFF}
\ifvoicings@screen
  \definecolor{paper}{HTML}{FDFCF8}
\fi
\pagecolor{paper}
\color{ink}

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
\newcommand{\frets}[1]{{\ttfamily\color{fretgreen}\bfseries #1}}
\newcommand{\notlisted}{{\color{rule}\ttfamily--}}

% A fingering above the ninth fret needs two digits per string and runs
% wider than a column allows, so it sets one size down. Rare enough that
% the inconsistency costs nothing.
\newcommand{\fretswide}[1]{{\small\ttfamily\color{fretgreen}\bfseries #1}}

% Between alternate voicings of the same chord. A single space let 2200 and
% 2245 read as one long number; this is a gap plus a faint divider, so the
% eye stops without the page filling up with punctuation.
\newcommand{\voicingsep}{%
  \hspace{1.6mm}{\color{rule}\rule[-0.15ex]{0.4pt}{1.1ex}}\hspace{1.6mm}}

% ------------------------------------------------------------- page frames
\newcommand{\pagerule}{\par\vspace{1.5pt}%
  {\color{rule}\hrule height 0.4pt}\par\vspace{3pt}}

\newcommand{\pagetitle}[1]{%
  {\large\bfseries\color{ink}#1\par}}
\newcommand{\pagesubtitle}[1]{%
  \vspace{-1pt}{\footnotesize\color{faint}#1\par}\pagerule}

\newenvironment{bookpage}[1]{%
  \clearpage\pagetitle{#1}%
}{\par}

% ------------------------------------------------------------------- cover
\newcommand{\bookurl}{https://github.com/linenoise/voicings}

\newcommand{\coverpage}{%
  \thispagestyle{empty}%
  \begin{center}
    \vspace*{6mm}
    {\fontsize{15}{17}\selectfont\bfseries Fancy\par}
    {\fontsize{30}{32}\selectfont\bfseries Chords\par}
    \vspace{1mm}
    {\fontsize{13}{15}\selectfont and their Voicings\par}
    \vspace{5mm}
    {\color{ink}\rule{\linewidth}{5mm}}
    \vspace{6mm}

    {\large Mandolin\, $\cdot$\, Fiddle\, $\cdot$\, Banjo\par}
    \vspace{2mm}
    {\large Guitar\, $\cdot$\, Bass\par}
    \vspace{2mm}
    {\large Ukulele\par}
    \vfill
    % Vector, generated at compile time by the qrcode package -- no image
    % file to keep in step with the URL beneath it, and it stays sharp at
    % any size a phone camera cares about. Error correction is left at the
    % default: the code is small on the page and this book gets carried in
    % a pocket, so it will be read creased and in poor light.
    \qrcode[height=18mm,padding]{\bookurl}\par
    \vspace{1.5mm}
    {\footnotesize\color{faint}\bookurl\par}
    \vspace{3mm}
  \end{center}
  \clearpage}

% ------------------------------------------------------- nameplate (inside)
% Deliberately blank. This book gets hand-sewn and given away; the person
% holding it should be able to put their own name in the front.
\newcommand{\nameplate@line}[1]{%
  \par\vspace{4.5mm}
  {\footnotesize\color{faint}#1}\par\vspace{1.5mm}
  {\color{rule}\hrule height 0.4pt}}

\newcommand{\nameplatepage}{%
  \thispagestyle{empty}%
  \vspace*{4mm}
  {\large\bfseries This book belongs to\par}
  \vspace{1mm}
  {\footnotesize\color{faint}%
   If found, the owner would very much like it back.\par}
  \vspace{5mm}
  \nameplate@line{Name}
  \nameplate@line{Phone}
  \nameplate@line{Email}
  \nameplate@line{Band}
  \vfill
  {\footnotesize\color{faint}%
   Fret numbers read from the lowest string.\\
   \frets{x} means don't play that string.\\
   Tunings are on the back sheet.\par}
  \vspace{2mm}
  \clearpage}

% -------------------------------------------------------- table of contents
\newenvironment{tocdirectory}{%
  \pagerule
  \begin{list}{}{%
    \setlength{\leftmargin}{0pt}\setlength{\itemsep}{2.2mm}
    \setlength{\parsep}{0pt}\setlength{\topsep}{0pt}}%
}{\end{list}}

\newcommand{\tocline}[2]{%
  \item[]\makebox[0pt][l]{\bfseries #1}\hfill{\footnotesize\color{faint}#2}}

\newenvironment{tocnote}{\par\vspace{2mm}\footnotesize\color{faint}}%
  {\par\vspace{2mm}}

% ------------------------------------------------------- section dividers
\newcommand{\sectiondivider}[2]{%
  \clearpage\thispagestyle{empty}%
  \null\vfill
  \begin{center}
    {\fontsize{20}{23}\selectfont\bfseries\color{keyred}#1\par}
    \vspace{3mm}
    {\ttfamily\color{faint}#2\par}
  \end{center}
  \vfill\null
  \clearpage}

% ------------------------------------------------------------ chord pages
% Two columns of the same shape as the notebook: the chord name on the
% left, its voicings running right. Rows are ruled faintly so the eye can
% track across on a dark stage.
\newlength{\chord@name}\setlength{\chord@name}{20mm}

\setlength{\columnsep}{3mm}
\setlength{\columnseprule}{0pt}

\newenvironment{chordpage}[4]{%
  \clearpage
  \pagetitle{\color{keyred}#2}%
  \vspace{-1mm}%
  {\footnotesize\color{faint}#1\ifthenelse{\equal{#3}{cont}}{, continued}{}\par}
  \pagerule
  #4%
  \raggedright
  \begin{multicols}{2}%
}{\end{multicols}}

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
\newcommand{\chordrow}[2]{%
  \par\makebox[\chord@name][l]{\small\bfseries #1}#2%
  \par\vspace{0.6mm}{\color{rule!45}\hrule height 0.2pt}\vspace{0.6mm}}

%% An alternate voicing goes under the first, pulled up tight so the pair
% reads as one chord rather than drifting toward the next one.
\newcommand{\voicingnext}{\par\vspace{-1.1mm}\hspace*{\chord@name}}

% ------------------------------------------------------- circle of fifths
% Twelve segments, major on the outside, relative minor inside. Drawn
% rather than tabulated because the whole point of the circle is that
% neighbours are a fifth apart and you can see it.
% Sized to the page, not to habit. The binding constraint is width: a
% six-character fingering like xx0231 is eight millimetres wide, and the
% ring it sits in has to give it more arc than that. The circle was drawn
% at 62mm across on a page that allows 72mm, which is where the guitar
% page's collisions came from. Signatures move back inside the hub, since
% "1b" is two characters and needs almost nothing.
\newlength{\cof@outer}\setlength{\cof@outer}{36mm}
\newlength{\cof@mid}\setlength{\cof@mid}{24mm}
\newlength{\cof@inner}\setlength{\cof@inner}{13mm}

% Absolute sizes: a diagram this dense cannot follow the body size.
\newcommand{\cof@name}{\fontsize{8}{8.6}\selectfont}
\newcommand{\cof@frets}{\fontsize{6.4}{6.8}\selectfont}
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
  % three millimetres is a horizontal gap of three millimetres and the
  % fret numbers are six millimetres wide.
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
  \node[align=center] at (\cof@a:30.2mm) {%
    \ifthenelse{\equal{#7}{up}}%
      {\cof@frets\ttfamily\color{fretgreen}#3\\[-2.4pt]%
       \cof@name\bfseries\color{keyred}#2}%
      {\cof@name\bfseries\color{keyred}#2\\[-2.4pt]%
       \cof@frets\ttfamily\color{fretgreen}#3}};
  \node[align=center] at (\cof@a:18.6mm) {%
    \ifthenelse{\equal{#7}{up}}%
      {\cof@frets\ttfamily\color{fretgreen}#5\\[-2.4pt]%
       \cof@minor\bfseries#4}%
      {\cof@minor\bfseries#4\\[-2.4pt]%
       \cof@frets\ttfamily\color{fretgreen}#5}};
  % Key signatures sit outside the rim: twelve of them around a hub the
  % size of a thumbnail was unreadable.
  \node at (\cof@a:8.4mm) {\cof@sig\color{faint}#6};}

\newcommand{\circlefootnote}[1]{%
  \vspace{1mm}{\footnotesize\color{faint}#1\par}}

% ----------------------------------------------------- nashville numbers
% Keys down the side, degrees across, exactly as the notebook has it.
% A tabular cannot break across pages: if it does not fit, the whole thing
% moves to the next one and leaves its heading stranded. Thirteen rows of
% two-line cells has to stay under the text height, so the leading is set
% tight here rather than left to \arraystretch.
\newenvironment{nashvilletable}[1]{%
  \vspace{0.5mm}
  \setlength{\tabcolsep}{2.4pt}
  \renewcommand{\arraystretch}{1.05}
  \begin{tabular}{@{}l|*{#1}{c}@{}}
}{%
  \end{tabular}}

% Header cells arrive already concatenated, each starting with an ampersand.
\newcommand{\nashvillehead}[1]{%
  {\scriptsize\bfseries} #1 \\[1pt] \hline}

\newcommand{\nashvillehcell}[1]{& {\scriptsize\bfseries #1}}

\newcommand{\nashvillerow}[2]{%
  {\scriptsize\bfseries\color{keyred}#1} #2 \\}

\newcommand{\nashvillecell}[2]{%
  & \begin{tabular}{@{}c@{}}{\scriptsize\bfseries#1}\\[-3.5pt]%
    {\tiny#2}\end{tabular}}

% ------------------------------------------------------------ banjo pages
% Where to spike the 5th string for this key, at the head of its pages.
\newcommand{\dronenote}[2]{%
  \par{\scriptsize\color{faint}%
    Drone: major \textbf{#1}\quad minor \textbf{#2}}%
  \par\vspace{0.8mm}{\color{rule}\hrule height 0.3pt}\vspace{1mm}}

% ------------------------------------------------------------ spike table
\newenvironment{spikeintro}{\footnotesize\color{faint}}{\par\vspace{2mm}}
\newenvironment{spikenote}{\par\vspace{2mm}\footnotesize\color{faint}}{\par}

\newenvironment{spiketable}{%
  \setlength{\tabcolsep}{2pt}
  \renewcommand{\arraystretch}{1.1}
  \begin{tabular}{@{}l l l@{}}
  {\scriptsize\bfseries Key} & {\scriptsize\bfseries Major} &
  {\scriptsize\bfseries Minor} \\ \hline
}{\end{tabular}}

\newcommand{\spikerow}[5]{%
  {\scriptsize\bfseries\color{keyred}#1} &
  {\scriptsize #2 {\color{faint}#3}} &
  {\scriptsize #4 {\color{faint}#5}} \\}

% -------------------------------------------------------------- bass pages
\newenvironment{rootmap}{%
  \setlength{\tabcolsep}{3pt}
  \renewcommand{\arraystretch}{1.2}
  \begin{tabular}{@{}l|*{4}{c}@{}}
}{\end{tabular}}

\newcommand{\rootmaphead}[4]{%
  {\scriptsize\bfseries} & {\scriptsize\bfseries#1} &
  {\scriptsize\bfseries#2} & {\scriptsize\bfseries#3} &
  {\scriptsize\bfseries#4} \\[1pt] \hline}

\newcommand{\rootmaprow}[5]{%
  {\scriptsize\bfseries\color{keyred}#1} & \frets{#2} & \frets{#3} &
  \frets{#4} & \frets{#5} \\}

\newenvironment{rootmapnote}{\par\vspace{2mm}\footnotesize\color{faint}}{\par}

\newenvironment{patternlist}{%
  \pagerule
  \begin{list}{}{%
    \setlength{\leftmargin}{0pt}\setlength{\itemsep}{1.6mm}
    \setlength{\parsep}{0pt}\setlength{\topsep}{0pt}}%
}{\end{list}}

% Two lines apiece, not three: the name carries what the pattern is for,
% and the degrees go underneath. Six patterns then fit on one page at the
% book's size.
\newcommand{\patternitem}[3]{%
  \item[]{\small\bfseries#1}\quad{\scriptsize\color{faint}#3}%
  \par\vspace{0.4mm}{\footnotesize#2}}

% -------------------------------------------------------------- piano
% Note names rather than fret numbers, so they need room to breathe and a
% face that keeps accidentals legible. Not monospaced: the lists vary in
% length and lining them up would waste the width.
\newcommand{\notes}[1]{{\color{fretgreen}\bfseries #1}}

\newenvironment{pianopage}[2]{%
  \clearpage
  \pagetitle{\color{keyred}#1}%
  \vspace{-1mm}%
  {\footnotesize\color{faint}Piano\ifthenelse{\equal{#2}{cont}}{, continued}{}%
   \par}
  \pagerule
  \begin{list}{}{%
    \setlength{\leftmargin}{0pt}\setlength{\itemsep}{0pt}
    \setlength{\parsep}{0pt}\setlength{\topsep}{0pt}}%
}{\end{list}}

% Name above, notes below: a five-note voicing in a flat key is too wide to
% share a line with its name at this trim size.
% Name and notes share a line where they fit; a five-note voicing in a
% flat key is set below its name instead.
% Note names run wider than fret digits -- two four-note sus4 shapes in a
% flat key is the widest thing in the book -- so they set one step down
% from the chord names beside them, which keeps every row on one line.
\newcommand{\pianorow}[2]{%
  \item[]{\small\makebox[20mm][l]{\bfseries #1}\footnotesize #2}%
  \par\vspace{0.1mm}{\color{rule!45}\hrule height 0.2pt}\vspace{0.1mm}}

% ------------------------------------------------------ worship voicings
\newcommand{\stargl}{{\color{keyred}$\bigstar$}}

\newenvironment{worshiplist}{%
  \begin{list}{}{%
    \setlength{\leftmargin}{0pt}\setlength{\itemsep}{1.6mm}
    \setlength{\parsep}{0pt}\setlength{\topsep}{1mm}}%
}{\end{list}}

\newcommand{\worshiprow}[4]{%
  \item[]\makebox[16mm][l]{\bfseries\small #1}%
  \ifthenelse{\equal{#4}{}}{}{\stargl}%
  \par\vspace{0.4mm}
  \hspace*{1mm}{\small #2}\par\vspace{0.2mm}
  \hspace*{1mm}{\scriptsize\color{faint}#3}}

% ------------------------------------------------------- bass vocabulary
\newenvironment{degreetable}{%
  \begin{list}{}{%
    \setlength{\leftmargin}{0pt}\setlength{\itemsep}{0pt}
    \setlength{\parsep}{0pt}\setlength{\topsep}{0pt}}%
}{\end{list}}

\newcommand{\degreerow}[2]{%
  \item[]\makebox[13mm][l]{\bfseries\footnotesize #1}{\footnotesize #2}%
  \par\vspace{0.5mm}{\color{rule!45}\hrule height 0.2pt}\vspace{0.5mm}}

% -------------------------------------------------------------- back sheet
% Everything that is reference rather than content lives here, so the
% inside front can be the recipient's.
\newenvironment{backsheet}{%
  \clearpage\thispagestyle{empty}%
  \pagetitle{Tunings}\pagerule
  \begin{list}{}{%
    \setlength{\leftmargin}{0pt}\setlength{\itemsep}{0.9mm}
    \setlength{\parsep}{0pt}\setlength{\topsep}{0pt}}%
}{%
  \end{list}
  \vfill
  {\color{rule}\hrule height 0.4pt}
  \vspace{1.5mm}
  {\footnotesize
   \textbf{Fancy Chords and their Voicings}\par
   \vspace{0.8mm}
   {\color{faint}%
    Danne Stayskal, Orcas Island\\
    \href{mailto:danne@stayskal.com}{danne@stayskal.com}\\
    http://danne.stayskal.com/\par}
   \vspace{1.2mm}
   {\color{faint}Source, corrections and a printable copy:\par}
   \bookurl\par
   \vspace{1.2mm}
   {\color{faint}\scriptsize MIT licensed. Print it, cut it, sew it,
    give it away.\par}}
  \vspace{0.5mm}
  \clearpage}

\newcommand{\tuningrow}[3]{%
  \item[]{\small\bfseries#1}\quad{\ttfamily\color{fretgreen}\bfseries\small#2}%
  \par\vspace{0.5mm}{\scriptsize\color{faint}#3}}
