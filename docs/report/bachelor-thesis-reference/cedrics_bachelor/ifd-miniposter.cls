\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{ifd-miniposter}[Student project miniposter class.]


% base class
\DeclareOption*{\PassOptionsToClass{\CurrentOption}{article}}
\ProcessOptions\relax
\LoadClass[11pt,a4paper]{article}


% packages
\RequirePackage[utf8]{inputenc}
\RequirePackage[T1]{fontenc}
\RequirePackage[ngerman, english]{babel}
\RequirePackage{csquotes}
\RequirePackage{amssymb}
\RequirePackage{amsmath}
\RequirePackage{graphicx}
\RequirePackage[parfill]{parskip}
\RequirePackage{geometry}
\RequirePackage{cmbright}
\RequirePackage{multicol}
\RequirePackage{float}
\RequirePackage{fancyhdr}


% bump pdf version
\pdfminorversion=6


% page margins
\geometry{a4paper,left=10mm,right=10mm,top=25mm,bottom=20mm,headheight=10mm,headsep=\baselineskip}
\setlength{\columnseprule}{0.4pt}
\setlength{\columnsep}{20pt}


% header and footer
\renewcommand{\headrulewidth}{0pt}
\lfoot{\parbox[][\headheight][t]{50mm}{\includegraphics[height=7.2mm]{graphics/eth_logo.pdf}}}
\rfoot{Artificial Intelligence in Mechanics and Manufacturing}
\rhead{31.07.2024}
\cfoot{}


% title parameters
\newcommand{\thesisTitleVar}{<title>}
\newcommand{\thesisStudentVar}{<author name>}
\newcommand{\thesisTypeVar}{<project type>}
\newcommand{\thesisSupervisorVar}{<supervisor name>}

\newcommand{\thesisTitle}[1]{\renewcommand{\thesisTitleVar}{#1}}
\newcommand{\thesisStudent}[1]{\renewcommand{\thesisStudentVar}{#1}}
\newcommand{\thesisType}[1]{\renewcommand{\thesisTypeVar}{#1}}
\newcommand{\thesisSupervisor}[1]{\renewcommand{\thesisSupervisorVar}{#1}}


% title
\renewcommand{\maketitle}{%
    \thispagestyle{fancy}
    \null\vspace{4cm}
    \begin{center}
        \rule{\linewidth}{0.4pt} \\%
        \Huge%
        \thesisTitleVar \\%
        \Large%
        \thesisTypeVar~by~\thesisStudentVar \\%
        supervised by \thesisSupervisorVar \\%
        \rule{\linewidth}{0.4pt} \\
    \end{center}
}
