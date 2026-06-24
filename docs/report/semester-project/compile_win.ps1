# Compile semester-project report (MiKTeX)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

function Invoke-Latex {
    param([string]$Engine, [string]$Job)
    & $Engine -interaction=nonstopmode $Job
    if ($LASTEXITCODE -ne 0) { throw "$Engine failed on $Job (exit $LASTEXITCODE)" }
}

Invoke-Latex pdflatex main.tex
if (Test-Path main.aux) {
    $aux = Get-Content main.aux -Raw
    if ($aux -match '\\citation\{') {
        Invoke-Latex bibtex main
    }
}
Invoke-Latex pdflatex main.tex
Invoke-Latex pdflatex main.tex

Write-Host "Done: $PSScriptRoot\main.pdf"
