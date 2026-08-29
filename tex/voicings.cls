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
\LoadClass[9pt]{extarticle}

\RequirePackage{geometry}
\RequirePackage{tikz}
\RequirePackage{xcolor}
\RequirePackage{fontspec}
\RequirePackage{microtype}
\RequirePackage{array}
\RequirePackage{calc}
\RequirePackage{ifthen}
\RequirePackage[hidelinks]{hyperref}
\usetikzlibrary{calc}

% ---------------------------------------------------------------- geometry
% The trim size is the notebook's own. Margins are asymmetric: the spine
% edge needs room for the sewing, the outer edge is where a thumb goes.
\newlength{\bookwidth}\setlength{\bookwidth}{3.5in}
\newlength{\bookheight}\setlength{\bookheight}{5.5in}

\geometry{
  paperwidth=\bookwidth, paperheight=\bookheight,
  top=8mm, bottom=7mm, inner=9mm, outer=6mm,
  twoside, includehead=false, includefoot=false,
}

\pagestyle{empty}
\setlength{\parindent}{0pt}
\setlength{\parskip}{0pt}
\raggedbottom

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
% Fall back gracefully: these are the families most likely to be installed,
% and the book still sets if fontspec picks the default.
\IfFontExistsTF{Charter}{\setmainfont{Charter}}{%
  \IfFontExistsTF{Georgia}{\setmainfont{Georgia}}{}}
\IfFontExistsTF{Menlo}{\setmonofont[Scale=0.92]{Menlo}}{%
  \IfFontExistsTF{DejaVu Sans Mono}{\setmonofont[Scale=0.88]{DejaVu Sans Mono}}{}}

\newcommand{\degsign}{\textsuperscript{o}}
\newcommand{\smaller}[1]{{\footnotesize #1}}

% Fret numbers. Monospaced so columns of digits line up down the page,
% which is most of what makes a chord book readable at arm's length.
\newcommand{\frets}[1]{{\ttfamily\color{fretgreen}\bfseries #1}}
\newcommand{\notlisted}{{\color{rule}\ttfamily--}}
\newcommand{\derived}{\textsuperscript{\color{faint}\tiny$\dagger$}}

% ------------------------------------------------------------- page frames
\newcommand{\pagerule}{\par\vspace{2pt}%
  {\color{rule}\hrule height 0.4pt}\par\vspace{4pt}}

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

\newenvironment{tocnote}{\footnotesize\color{faint}}{\par\vspace{2mm}}

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
\newenvironment{chordpage}[3]{%
  \clearpage
  \pagetitle{\color{keyred}#2}%
  \vspace{-1mm}%
  {\footnotesize\color{faint}#1\ifthenelse{\equal{#3}{cont}}{, continued}{}\par}
  \pagerule
  \begin{list}{}{%
    \setlength{\leftmargin}{0pt}\setlength{\itemsep}{0pt}
    \setlength{\parsep}{0pt}\setlength{\topsep}{0pt}}%
}{\end{list}}

\newcommand{\chordrow}[2]{%
  \item[]\makebox[15mm][l]{\bfseries #1}#2%
  \par\vspace{0.6mm}{\color{rule!45}\hrule height 0.2pt}\vspace{0.6mm}}

% ------------------------------------------------------- circle of fifths
% Twelve segments, major on the outside, relative minor inside. Drawn
% rather than tabulated because the whole point of the circle is that
% neighbours are a fifth apart and you can see it.
\newlength{\cof@outer}\setlength{\cof@outer}{31mm}
\newlength{\cof@mid}\setlength{\cof@mid}{21mm}
\newlength{\cof@inner}\setlength{\cof@inner}{11mm}

\newenvironment{circleoffifths}{%
  \vspace{1mm}
  \begin{center}
  \begin{tikzpicture}[every node/.style={inner sep=0pt}]
    \draw[rule,line width=0.4pt] (0,0) circle (\cof@outer);
    \draw[rule,line width=0.4pt] (0,0) circle (\cof@mid);
    \draw[rule,line width=0.4pt] (0,0) circle (\cof@inner);
}{%
  \end{tikzpicture}
  \end{center}}

% #1 index 0-11 (0 = C at twelve o'clock)  #2 major  #3 major frets
% #4 minor  #5 minor frets  #6 key signature
\newcommand{\cofsegment}[6]{%
  \pgfmathsetmacro{\cof@a}{90 - 30*#1}%
  \pgfmathsetmacro{\cof@edge}{90 - 30*#1 - 15}%
  \draw[rule,line width=0.3pt]
    (\cof@edge:\cof@inner) -- (\cof@edge:\cof@outer);
  \node at (\cof@a:27.6mm) {\scriptsize\bfseries\color{keyred}#2};
  \node at (\cof@a:24.2mm) {\tiny#3};
  \node at (\cof@a:17.8mm) {\scriptsize\bfseries#4};
  \node at (\cof@a:14.2mm) {\tiny#5};
  \node at (\cof@a:6.2mm)  {\tiny\color{faint}#6};}

\newcommand{\circlefootnote}[1]{%
  \vspace{1mm}{\footnotesize\color{faint}#1\par}}

% ----------------------------------------------------- nashville numbers
% Keys down the side, degrees across, exactly as the notebook has it.
\newenvironment{nashvilletable}[1]{%
  \vspace{0.5mm}
  \setlength{\tabcolsep}{2.2pt}
  \renewcommand{\arraystretch}{1.3}
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
  & \begin{tabular}{@{}c@{}}{\scriptsize\bfseries#1}\\[-1pt]%
    {\tiny#2}\end{tabular}}

% ------------------------------------------------------------ banjo pages
\newenvironment{banjopage}{%
  \clearpage
  \pagetitle{\color{keyred}Banjo}%
  \vspace{-1mm}{\footnotesize\color{faint}gDGBD, open G\par}
  \pagerule
  \begin{list}{}{%
    \setlength{\leftmargin}{0pt}\setlength{\itemsep}{0pt}
    \setlength{\parsep}{0pt}\setlength{\topsep}{0pt}}%
}{\end{list}}

\newcommand{\banjokey}[1]{%
  \item[]\vspace{0.8mm}{\bfseries\color{keyred}#1}\vspace{0.4mm}}

\newcommand{\dronerow}[2]{%
  \item[]{\scriptsize\color{faint}Drone: major \textbf{#1}\quad
   minor \textbf{#2}}%
  \par\vspace{0.8mm}{\color{rule}\hrule height 0.3pt}\vspace{0.4mm}}

% ------------------------------------------------------------ spike table
\newenvironment{spikeintro}{\footnotesize\color{faint}}{\par\vspace{2mm}}
\newenvironment{spikenote}{\par\vspace{2mm}\footnotesize\color{faint}}{\par}

\newenvironment{spiketable}{%
  \setlength{\tabcolsep}{2pt}
  \renewcommand{\arraystretch}{1.25}
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
    \setlength{\leftmargin}{0pt}\setlength{\itemsep}{2.4mm}
    \setlength{\parsep}{0pt}\setlength{\topsep}{0pt}}%
}{\end{list}}

\newcommand{\patternitem}[3]{%
  \item[]{\bfseries#1}\par\vspace{0.5mm}
  {\scriptsize#2}\par\vspace{0.5mm}
  {\scriptsize\color{faint}#3}}

% -------------------------------------------------------------- back sheet
% Everything that is reference rather than content lives here, so the
% inside front can be the recipient's.
\newenvironment{backsheet}{%
  \clearpage\thispagestyle{empty}%
  \pagetitle{Tunings}\pagerule
  \begin{list}{}{%
    \setlength{\leftmargin}{0pt}\setlength{\itemsep}{2.2mm}
    \setlength{\parsep}{0pt}\setlength{\topsep}{0pt}}%
}{%
  \end{list}
  \vfill
  {\color{rule}\hrule height 0.4pt}
  \vspace{2mm}
  {\footnotesize
   \textbf{Fancy Chords and their Voicings}\par
   \vspace{1mm}
   {\color{faint}%
    Danne Stayskal, Orcas Island\\
    \href{mailto:danne@stayskal.com}{danne@stayskal.com}\\
    http://danne.stayskal.com/\par}
   \vspace{2mm}
   {\color{faint}Source, corrections and a printable copy:\par}
   \bookurl\par
   \vspace{2mm}
   {\color{faint}\scriptsize MIT licensed. Print it, cut it, sew it,
    give it away.\par}}
  \vspace{1mm}
  \clearpage}

\newcommand{\tuningrow}[3]{%
  \item[]{\bfseries#1}\quad{\ttfamily\color{fretgreen}\bfseries#2}%
  \par\vspace{0.6mm}{\scriptsize\color{faint}#3}}
