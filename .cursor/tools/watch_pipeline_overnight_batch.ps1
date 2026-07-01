# Long-run watch: pipeline overnight batch Exp 10 -> 11 -> 12 -> 13
# Hourly status to message-queue; polls every 120s.

$ErrorActionPreference = "Continue"
$Repo = "D:\code\sem-proj-asc"
$Mq = Join-Path $Repo ".cursor\agents-discussion\message-queue.md"
$Lock = Join-Path $Repo "backend\scripts\experiments\.pipeline_run.lock"
$ActiveRun = Join-Path $Repo "docs\experiments\pipeline\.active_run.json"

$BatchDir = Join-Path $Repo "backend\scripts\experiments"
$BatchScript = "run_pipeline_overnight_batch.py"
$BatchLog = Join-Path $BatchDir "results\pipeline_overnight_batch.log"
$BatchSummary = Join-Path $BatchDir "results\pipeline_overnight_batch.json"

$WatchLog = Join-Path $Repo ".cursor\debug_logs\watch-pipeline-overnight-batch.log"
$PollSec = 120
$ReportSec = 3600

function Write-WatchLog([string]$Msg) {
    $logDir = Split-Path $WatchLog -Parent
    if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }
    $ts = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    $line = "[$ts] $Msg"
    Add-Content -Path $WatchLog -Value $line -Encoding utf8
    Write-Host $line
}

function Test-BatchOrchestrator {
    Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -and ($_.CommandLine -match 'run_pipeline_overnight_batch\.py') }
}

function Test-ChildRunner {
    Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
        Where-Object {
            $_.CommandLine -and (
                $_.CommandLine -match 'ml_mpo_safe_mode_penalty|ml_mpo_decoupled_dual_vector|ml_mpo_vector_torque_effort|ml_mpo_learn_cadence_hparams'
            )
        }
}

function Get-BatchTail {
    if (Test-Path $BatchLog) {
        return (Get-Content $BatchLog -Tail 5 -ErrorAction SilentlyContinue) -join " | "
    }
    return "no batch log yet"
}

function Get-ActiveRunProgress {
    $runsRoot = Join-Path $Repo "backend\autonomous_control\runs"
    $latest = Get-ChildItem $runsRoot -Directory -ErrorAction SilentlyContinue |
        Where-Object {
            $_.Name -match 'ml_mpo_safe_mode_penalty|ml_mpo_decoupled_dual|ml_mpo_vector_torque|ml_mpo_learn_cadence'
        } |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1
    if (-not $latest) { return "no matching run dir" }
    $step = Join-Path $latest.FullName "telemetry\current_step.json"
    if (Test-Path $step) {
        try {
            $j = Get-Content $step -Raw | ConvertFrom-Json
            return "$($latest.Name): ep $($j.episode_idx) step $($j.step_idx)/516 ret=$([math]::Round($j.episode_return,1))"
        } catch { }
    }
    return $latest.Name
}

function Remove-StaleLockIfSafe {
    if (-not (Test-Path $Lock)) { return }
    $lines = Get-Content $Lock
    $lockPid = [int]$lines[0]
    $proc = Get-Process -Id $lockPid -ErrorAction SilentlyContinue
    if (-not $proc) {
        Remove-Item $Lock -Force
        Write-WatchLog "Removed stale pipeline lock (pid $lockPid dead)"
    }
}

function Append-MessageQueue(
    [string]$Status,
    [string]$StatusPara,
    [string]$Artifacts,
    [string]$Action = "none",
    [string]$Errors = "none",
    [string]$Fixes = "none",
    [string]$Question = ""
) {
    $ts = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    $block = @"

---
timestamp_utc: $ts
agent: long-run-watch
profile: ml-pipeline-overnight-batch-10-13
status: $Status
---

## Status

$StatusPara

## Artifacts

$Artifacts

## Action taken

$Action

## Errors encountered

$Errors

## Fixes applied

$Fixes
"@
    if ($Question) {
        $block += "`n`n## Question for user`n`n$Question"
    }
    Add-Content -Path $Mq -Value $block -Encoding utf8
}

function Launch-Batch {
    if (Test-Path $BatchSummary) {
        try {
            $s = Get-Content $BatchSummary -Raw | ConvertFrom-Json
            $failed = @($s.results | Where-Object { $_.status -eq 'error' })
            if ($failed.Count -eq 0 -and -not (Test-BatchOrchestrator) -and -not (Test-ChildRunner)) {
                Write-WatchLog "Batch summary exists with no failures and no process - skip relaunch"
                return $false
            }
        } catch { }
    }
    Write-WatchLog "Launching overnight batch (10->13)..."
    Remove-StaleLockIfSafe
    $py = (Get-Command python -ErrorAction SilentlyContinue).Source
    if (-not $py) { $py = "python" }
    $args = @(
        $BatchScript,
        "--show-progress",
        "--git-sync-runs",
        "--skip-not-ready",
        "--continue-on-error"
    )
    Start-Process -FilePath $py -ArgumentList $args -WorkingDirectory $BatchDir -WindowStyle Hidden
    Start-Sleep -Seconds 30
    $p = Test-BatchOrchestrator
    if ($p) {
        Write-WatchLog "Batch orchestrator started pid $($p.ProcessId)"
        return $true
    }
    Write-WatchLog "WARN: batch launch may have failed - no orchestrator process"
    return $false
}

$batchLaunched = $false
$lastReport = Get-Date
Write-WatchLog "Watch started (pipeline overnight batch 10-13)"

# Auto-launch if nothing running and user invoked watch
if (-not (Test-BatchOrchestrator) -and -not (Test-ChildRunner)) {
    if (Launch-Batch) { $batchLaunched = $true }
}

while ($true) {
    $orch = Test-BatchOrchestrator
    $child = Test-ChildRunner
    $batchDone = (Test-Path $BatchSummary) -and (-not $orch) -and (-not $child)

    $now = Get-Date
    if (($now - $lastReport).TotalSeconds -ge $ReportSec) {
        if ($batchDone) {
            $summaryLine = Get-Content $BatchSummary -Raw -ErrorAction SilentlyContinue
            Append-MessageQueue -Status "completed" `
                -StatusPara "Pipeline overnight batch complete. No orchestrator or child runner process." `
                -Artifacts "- completion: pipeline_overnight_batch.json yes`n- log tail: $(Get-BatchTail)" `
                -Action "none"
            Write-WatchLog "Batch complete - exiting watch loop"
            break
        }

        if ($orch -or $child) {
            $prog = Get-ActiveRunProgress
            $pidInfo = if ($child) { "child pid $($child.ProcessId)" } elseif ($orch) { "orchestrator pid $($orch.ProcessId)" }
            Append-MessageQueue -Status "running" `
                -StatusPara "Overnight batch running ($pidInfo). Progress: $prog. Log: $(Get-BatchTail)" `
                -Artifacts "- batch log: $(Get-BatchTail)`n- lock: $(Test-Path $Lock)" `
                -Action "none"
        }
        else {
            Append-MessageQueue -Status "unknown" `
                -StatusPara "No batch orchestrator or child process; summary missing or run crashed." `
                -Artifacts "- summary: $(Test-Path $BatchSummary)`n- log: $(Get-BatchTail)" `
                -Action "none" `
                -Errors "Process lost before batch summary written" `
                -Question "Re-launch batch or resume with --from-slug?"
        }
        $lastReport = $now
    }

    if ($batchDone) { break }
    Start-Sleep -Seconds $PollSec
}
