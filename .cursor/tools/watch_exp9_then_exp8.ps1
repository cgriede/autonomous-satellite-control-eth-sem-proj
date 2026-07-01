# Long-run watch: Exp 9 (SAC shutter split) -> auto-launch Exp 8 (MPO dual fix)
# Hourly status to message-queue; polls every 120s for completion / launch.

$ErrorActionPreference = "Continue"
$Repo = "D:\code\sem-proj-asc"
$Mq = Join-Path $Repo ".cursor\agents-discussion\message-queue.md"
$Lock = Join-Path $Repo "backend\scripts\experiments\.pipeline_run.lock"
$ActiveRun = Join-Path $Repo "docs\experiments\pipeline\.active_run.json"

$Exp9Script = "ml_sac_shutter_reward_split\run_sac_shutter_reward_split.py"
$Exp9Summary = Join-Path $Repo "backend\scripts\experiments\ml_sac_shutter_reward_split\results\sac_shutter_reward_split.json"
$Exp9Log = Join-Path $Repo "backend\scripts\experiments\ml_sac_shutter_reward_split\results\shutter_reward_split.log"
$Exp9RunDir = Join-Path $Repo "backend\autonomous_control\runs\9998217165798903_ml_sac_shutter_split_15-43-20"

$Exp8Dir = Join-Path $Repo "backend\scripts\experiments\ml_mpo_decoupled_dual_torque"
$Exp8Script = "ml_mpo_decoupled_dual_torque\run_mpo_torque.py"
$Exp8Summary = Join-Path $Repo "backend\scripts\experiments\ml_mpo_decoupled_dual_torque\results\mpo_torque.json"
$Exp8Log = Join-Path $Repo "backend\scripts\experiments\ml_mpo_decoupled_dual_torque\results\mpo_torque.log"

$WatchLog = Join-Path $Repo ".cursor\debug_logs\watch-exp9-exp8.log"
$PollSec = 120
$ReportSec = 3600

function Write-WatchLog([string]$Msg) {
    $ts = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    $line = "[$ts] $Msg"
    Add-Content -Path $WatchLog -Value $line -Encoding utf8
    Write-Host $line
}

function Test-PythonRunner([string]$Pattern) {
    Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -and ($_.CommandLine -match $Pattern) }
}

function Get-Exp9Progress {
    $step = Join-Path $Exp9RunDir "telemetry\current_step.json"
    if (Test-Path $step) {
        try {
            $j = Get-Content $step -Raw | ConvertFrom-Json
            return "train ep $($j.episode_idx) step $($j.step_idx)/516 return=$([math]::Round($j.episode_return,1))"
        } catch { }
    }
    if (Test-Path $Exp9Log) {
        return (Get-Content $Exp9Log -Tail 1 -ErrorAction SilentlyContinue)
    }
    return "unknown"
}

function Get-Exp8Progress {
    if (Test-Path $Exp8Log) {
        return (Get-Content $Exp8Log -Tail 3 -ErrorAction SilentlyContinue) -join " | "
    }
    $runs = Get-ChildItem (Join-Path $Repo "backend\autonomous_control\runs") -Directory -Filter "*ml_mpo_decoupled*" |
        Where-Object { $_.Name -notmatch "smoke" } |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1
    if ($runs) {
        $step = Join-Path $runs.FullName "telemetry\current_step.json"
        if (Test-Path $step) {
            try {
                $j = Get-Content $step -Raw | ConvertFrom-Json
                return "$($runs.Name): ep $($j.episode_idx) step $($j.step_idx)"
            } catch { }
        }
    }
    return "not started"
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
    [string]$Profile,
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
profile: $Profile
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

function Launch-Exp8 {
    if (Test-Path $Exp8Summary) {
        Write-WatchLog "Exp 8 summary already exists - skip launch"
        return $true
    }
    Write-WatchLog "Launching Exp 8 (MPO dual fix torque)..."
    Remove-StaleLockIfSafe
    $py = (Get-Command python -ErrorAction SilentlyContinue).Source
    if (-not $py) { $py = "python" }
    Start-Process -FilePath $py -ArgumentList "run_mpo_torque.py", "--show-progress" -WorkingDirectory $Exp8Dir -WindowStyle Hidden
    Start-Sleep -Seconds 30
    $p = Test-PythonRunner $Exp8Script
    if ($p) {
        Write-WatchLog "Exp 8 started pid $($p.ProcessId)"
        return $true
    }
    Write-WatchLog "WARN: Exp 8 launch may have failed - no matching process"
    return $false
}

$exp8Launched = Test-Path $Exp8Summary
$lastReport = Get-Date
Write-WatchLog "Watch started (Exp9 -> Exp8)"

while ($true) {
    $exp9Proc = Test-PythonRunner $Exp9Script
    $exp8Proc = Test-PythonRunner $Exp8Script
    $exp9Done = (Test-Path $Exp9Summary) -and (-not $exp9Proc)
    $exp8Done = (Test-Path $Exp8Summary) -and (-not $exp8Proc)

    if ($exp9Done -and (-not $exp8Launched) -and (-not $exp8Proc) -and (-not (Test-Path $Exp8Summary))) {
        Append-MessageQueue -Profile "ml-sac-shutter-reward-split" -Status "completed" `
            -StatusPara "Exp 9 finished; summary JSON present. Auto-launching Exp 8 per operator request." `
            -Artifacts "- completion: sac_shutter_reward_split.json yes`n- log: $(Get-Content $Exp9Log -Tail 1)" `
            -Action "auto-launch Exp 8"
        if (Launch-Exp8) { $exp8Launched = $true }
    }

    $now = Get-Date
    if (($now - $lastReport).TotalSeconds -ge $ReportSec) {
        if ($exp8Done) {
            Append-MessageQueue -Profile "ml-mpo-decoupled-dual-torque" -Status "completed" `
                -StatusPara "Exp 8 MPO dual-fix torque run complete. No matching process." `
                -Artifacts "- completion: mpo_torque.json yes`n- log: $(Get-Content $Exp8Log -Tail 1 -ErrorAction SilentlyContinue)" `
                -Action "none"
            Write-WatchLog "Both experiments complete - exiting watch loop"
            break
        }

        if ($exp8Proc -or $exp8Launched) {
            $prog = Get-Exp8Progress
            Append-MessageQueue -Profile "ml-mpo-decoupled-dual-torque" -Status "running" `
                -StatusPara "Exp 8 MPO torque running (pid $($exp8Proc.ProcessId)). Progress: $prog" `
                -Artifacts "- log: $(Get-Content $Exp8Log -Tail 1 -ErrorAction SilentlyContinue)`n- completion: mpo_torque.json $(if(Test-Path $Exp8Summary){'yes'}else{'no'})" `
                -Action "none"
        }
        elseif ($exp9Proc) {
            $prog = Get-Exp9Progress
            Append-MessageQueue -Profile "ml-sac-shutter-reward-split" -Status "running" `
                -StatusPara "Exp 9 SAC shutter split running (pid $($exp9Proc.ProcessId)). $prog (~50 train eps + eval)." `
                -Artifacts "- log: $(Get-Content $Exp9Log -Tail 1)`n- completion: sac_shutter_reward_split.json no" `
                -Action "none"
        }
        elseif ($exp9Done) {
            Append-MessageQueue -Profile "ml-sac-shutter-reward-split" -Status "failed" `
                -StatusPara "Exp 9 summary exists but Exp 8 not launched and no Exp 8 process." `
                -Artifacts "- completion: sac_shutter_reward_split.json yes`n- exp8: not started" `
                -Action "attempting Exp 8 launch on next poll" `
                -Question "Confirm Exp 8 should proceed if launch keeps failing."
        }
        else {
            Append-MessageQueue -Profile "ml-sac-shutter-reward-split" -Status "unknown" `
                -StatusPara "No Exp 9 or Exp 8 process; Exp 9 summary missing. Possible crash." `
                -Artifacts "- exp9 summary: $(Test-Path $Exp9Summary)`n- lock: $(Test-Path $Lock)" `
                -Action "none" `
                -Errors "Exp 9 process lost before completion JSON" `
                -Question "Re-run Exp 9 or resume from checkpoint?"
        }
        $lastReport = $now
    }

    if ($exp8Done) {
        Write-WatchLog "Exp 8 complete - exiting"
        break
    }

    Start-Sleep -Seconds $PollSec
}
