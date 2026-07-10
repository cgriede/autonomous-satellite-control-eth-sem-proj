cd "c:\Users\cedri\code\autonomous-satellite-control-eth-sem-proj\docs\report\semester-project";
pdflatex -interaction=nonstopmode main.tex;
bibtex main;
pdflatex -interaction=nonstopmode main.tex;
pdflatex -interaction=nonstopmode main.tex;
