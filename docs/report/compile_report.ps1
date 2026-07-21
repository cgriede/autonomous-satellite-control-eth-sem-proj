# Compile semester-project report and fail on large Overfull \hbox (margin overflow).
$ErrorActionPreference = "Stop"
$reportDir = Join-Path $PSScriptRoot "semester-project"
Set-Location $reportDir

function Invoke-PdfLatex {
    pdflatex -interaction=nonstopmode main.tex | Out-Host
    if ($LASTEXITCODE -ne 0) {
        throw "pdflatex failed with exit code $LASTEXITCODE"
    }
}

Invoke-PdfLatex
bibtex main | Out-Host
Invoke-PdfLatex
Invoke-PdfLatex

# LaTeX already writes Overfull \hbox to main.log; surface them and gate on size.
$logPath = Join-Path $reportDir "main.log"
if (-not (Test-Path $logPath)) {
    throw "main.log missing after compile"
}

$log = Get-Content -Path $logPath -Raw
$rx = [regex]'Overfull \\hbox \(([0-9.]+)pt too wide\)'
$hits = @()
foreach ($m in $rx.Matches($log)) {
    $hits += [double]$m.Groups[1].Value
}

Write-Host ""
Write-Host "=== Overfull \\hbox gate (main.log) ==="
if ($hits.Count -eq 0) {
    Write-Host "OK: no Overfull \\hbox warnings."
    exit 0
}

$sorted = $hits | Sort-Object -Descending
$maxPt = $sorted[0]
Write-Host ("Count: {0}  Max: {1:N1} pt" -f $hits.Count, $maxPt)
Write-Host "Largest (pt):"
$sorted | Select-Object -First 15 | ForEach-Object { Write-Host ("  {0:N2}" -f $_) }

# Visible clipping / path overflow risk; small stretch leftovers (<20pt) are nits.
$thresholdPt = 20.0
$bad = @($hits | Where-Object { $_ -ge $thresholdPt })
if ($bad.Count -gt 0) {
    Write-Host ""
    Write-Host ("FAIL: {0} Overfull \\hbox >= {1} pt (text may clip the margin)." -f $bad.Count, $thresholdPt)
    Write-Host "Fix wrapping (prefer \\path/\\url via xurl, p{} columns) then recompile."
    exit 1
}

Write-Host ("OK: all Overfull \\hbox below {0} pt." -f $thresholdPt)
exit 0
