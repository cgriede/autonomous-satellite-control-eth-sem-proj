# Detached runner: c2 -> c3 only (c1 backfilled from prior run)
$ErrorActionPreference = "Stop"
$Root = "c:\Users\cedri\code\autonomous-satellite-control-eth-sem-proj"
$Log = Join-Path $Root "backend\scripts\experiments\ml_learning_signal\results\c_hparam_detached.log"
$Py = "C:\Users\cedri\miniconda3\envs\auto-sat\python.exe"
$env:KMP_DUPLICATE_LIB_OK = "TRUE"
$env:PYTHONIOENCODING = "utf-8"
Set-Location $Root
foreach ($v in @("c2", "c3")) {
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Add-Content $Log "`n=== $ts START $v ===`n"
    & $Py backend/scripts/experiments/ml_learning_signal/c_hparam_search/run_c1.py --variant $v *>> $Log
    $code = $LASTEXITCODE
    Add-Content $Log "=== $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') END $v exit=$code ===`n"
    if ($code -ne 0) { exit $code }
}
Add-Content $Log "=== ALL DONE c2-c3 $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ===`n"
