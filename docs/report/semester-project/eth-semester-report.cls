\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{eth-semester-report}[2026/06/24 ETH MSc semester project report]

\DeclareOption*{\PassOptionsToClass{\CurrentOption}{article}}
\ProcessOptions\relax
\LoadClass[11pt,a4paper]{article}

\RequirePackage[utf8]{inputenc}
\RequirePackage[T1]{fontenc}
\RequirePackage[english]{babel}
\RequirePackage{csquotes}
\RequirePackage{amsmath,amssymb}
% Times-like text/math (Type 1). Default Computer Modern often ships as Type 3
% bitmaps that Chrome's PDF viewer renders as thin/odd strokes.
\RequirePackage{newtxtext}
\RequirePackage{newtxmath}
% newtx mono (t1xtt) is missing on some MiKTeX installs; Courier for \texttt/\path.
\renewcommand{\ttdefault}{pcr}
\RequirePackage{graphicx}
\RequirePackage{booktabs}
\RequirePackage{siunitx}
\RequirePackage[expansion=false]{microtype}
\RequirePackage{geometry}
\RequirePackage{parskip}
\RequirePackage{fancyhdr}
\RequirePackage[numbers,sort&compress]{natbib}
\bibliographystyle{plainnat}
\RequirePackage[colorlinks=true,allcolors=blue]{hyperref}

\geometry{a4paper,left=25mm,right=25mm,top=30mm,bottom=25mm,headheight=14pt}

\sisetup{
  detect-all,
  per-mode=symbol,
}

\newcommand{\reportTitleVar}{<title>}
\newcommand{\reportAuthorVar}{<author>}
\newcommand{\reportSupervisorVar}{<supervisor>}
\newcommand{\reportInstituteVar}{Institute for Dynamic Systems and Control (IDSC)}
\newcommand{\reportProgramVar}{MSc Mechanical Engineering, ETH Z\"urich}

\newcommand{\reportTitle}[1]{\renewcommand{\reportTitleVar}{#1}}
\newcommand{\reportAuthor}[1]{\renewcommand{\reportAuthorVar}{#1}}
\newcommand{\reportSupervisor}[1]{\renewcommand{\reportSupervisorVar}{#1}}
\newcommand{\reportInstitute}[1]{\renewcommand{\reportInstituteVar}{#1}}
\newcommand{\reportProgram}[1]{\renewcommand{\reportProgramVar}{#1}}

\pagestyle{fancy}
\fancyhf{}
\fancyfoot[C]{\thepage}
\renewcommand{\headrulewidth}{0pt}

\renewcommand{\maketitle}{%
  \thispagestyle{empty}
  \null\vspace{3cm}
  \begin{center}
    \includegraphics[height=10mm]{graphics/eth_logo.pdf}\\[1.5cm]
    \rule{0.85\linewidth}{0.4pt}\\[0.6cm]
    {\LARGE\bfseries \reportTitleVar}\\[0.8cm]
    {\large Semester Project}\\[0.4cm]
    {\large \reportProgramVar}\\[1.2cm]
    {\large \reportAuthorVar}\\[0.3cm]
    supervised by \reportSupervisorVar\\[0.3cm]
    \reportInstituteVar\\[0.3cm]
    \today
    \\[0.6cm]
    \rule{0.85\linewidth}{0.4pt}
  \end{center}
  \vfill
}

\setcounter{secnumdepth}{3}
\setcounter{tocdepth}{2}
