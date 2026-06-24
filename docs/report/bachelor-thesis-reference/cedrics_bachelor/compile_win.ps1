# PowerShell script to compile latex to pdf.

# main latex file name
$strDocName = "main.tex"

# latex file name without extension
$Name = [io.path]::GetFileNameWithoutExtension($strDocName)

# list of file extensions to delete when cleaning up
$extensionList = "bbl", "bib.bak", "bib.sav", "blg", "gz", "nav", "out", "snm", "spl", "synctex.gz", "toc", "vrb", "run.xml"

# set environmental variable with path to class files
$env:TEXINPUTS = "..\class-files//;"

# compile
pdflatex.exe $Name".tex"
bibtex.exe $Name".aux"
pdflatex.exe $Name".tex"
pdflatex.exe $Name".tex"

# clean up
Remove-Item *.aux -ErrorAction Ignore
Remove-Item *.log -ErrorAction Ignore
Remove-Item $Name"-blx.bib" -ErrorAction Ignore

foreach ($extension in $extensionList) {
    Remove-Item $Name"."$extension -ErrorAction Ignore
}
