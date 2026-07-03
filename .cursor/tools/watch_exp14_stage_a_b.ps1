$ErrorActionPreference = "Stop"

$repoRoot = "D:\code\sem-proj-asc"
$expDir = Join-Path $repoRoot "backend\scripts\experiments\ml_mpo_multienv_target_select"
$queuePath = Join-Path $repoRoot ".cursor\agents-discussion\message-queue.md"
$screenSummaryPath = Join-Path $expDir "results\screen_summary.json"
$stageBSummaryPath = Join-Path $expDir "results\stage_b_summary.json"
$lockPath = Join-Path $repoRoot "backend\scripts\experiments\.pipeline_run.lock"
$activeRunPath = Join-Path $repoRoot "docs\experiments\pipeline\.active_run.json"
$pythonExe = "C:\Users\cedri\miniconda3\envs\auto-sat\python.exe"

function Append-QueueBlock {
    param(
        [string]$Status,
        [string]$StatusParagraph,
        [string]$Artifacts,
        [string]$ActionTaken,
        [string]$ErrorsEncountered,
        [string]$FixesApplied,
        [string]$QuestionForUser = ""
    )

    $ts = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    $block = @"
---
timestamp_utc: $ts
agent: long-run-watch
profile: exp14-stage-a-b (ad-hoc)
status: $Status
---

## Status

$StatusParagraph

## Artifacts

$Artifacts

## Action taken

$ActionTaken

## Errors encountered

$ErrorsEncountered

## Fixes applied

$FixesApplied
"@

    if ($QuestionForUser.Trim().Length -gt 0) {
        $block += @"

## Question for user

$QuestionForUser
"@
    }

    Add-Content -Path $queuePath -Value $block -Encoding UTF8
}

function Get-ScreenProcess {
    if (Test-Path $activeRunPath) {
        try {
            $active = Get-Content $activeRunPath -Raw | ConvertFrom-Json
            if ($active.script -match "^screen:" -and $active.pid) {
                $proc = Get-CimInstance Win32_Process -Filter "ProcessId = $($active.pid)" -ErrorAction SilentlyContinue
                if ($proc -and $proc.Name -eq "python.exe") {
                    return $proc
                }
            }
        } catch {
        }
    }
    return Get-CimInstance Win32_Process | Where-Object {
        $_.Name -eq "python.exe" -and $_.CommandLine -match "run.py --screen"
    } | Select-Object -First 1
}

function Get-FullProcess {
    return Get-CimInstance Win32_Process | Where-Object {
        $_.Name -eq "python.exe" -and $_.CommandLine -match "run.py --full"
    } | Select-Object -First 1
}

function Get-ScreenArmsCount {
    if (-not (Test-Path $screenSummaryPath)) { return 0 }
    try {
        $json = Get-Content $screenSummaryPath -Raw | ConvertFrom-Json
        if ($null -eq $json.arms) { return 0 }
        return @($json.arms).Count
    } catch {
        return 0
    }
}

function Get-WinnerArm {
    if (-not (Test-Path $screenSummaryPath)) { return "unknown" }
    try {
        $json = Get-Content $screenSummaryPath -Raw | ConvertFrom-Json
        return [string]$json.winner_arm_id
    } catch {
        return "unknown"
    }
}

$stageAStartedByWatcher = $false
$stageBStartedByWatcher = $false

while ($true) {
    $screenProc = Get-ScreenProcess
    $fullProc = Get-FullProcess
    $armsCount = Get-ScreenArmsCount
    $winnerArm = Get-WinnerArm
    $stageBComplete = Test-Path $stageBSummaryPath
    $lockPresent = Test-Path $lockPath
    $activeRunPresent = Test-Path $activeRunPath

    if (-not $screenProc -and -not $fullProc -and $lockPresent) {
        Remove-Item $lockPath -Force -ErrorAction SilentlyContinue
        if (Test-Path $activeRunPath) {
            Remove-Item $activeRunPath -Force -ErrorAction SilentlyContinue
        }
        $lockPresent = Test-Path $lockPath
        $activeRunPresent = Test-Path $activeRunPath
    }

    if ($screenProc) {
        $statusParagraph = "Stage A is still running (`run.py --screen`) with pid $($screenProc.ProcessId); Stage B remains blocked until this process exits and Stage A artifacts are complete."
        $artifacts = "- lock file: $lockPresent`n- active_run.json: $activeRunPresent`n- stage A arms in summary: $armsCount`n- current winner_arm_id: $winnerArm`n- stage_b_summary.json exists: $stageBComplete"
        Append-QueueBlock -Status "running" -StatusParagraph $statusParagraph -Artifacts $artifacts -ActionTaken "none (passive monitor)" -ErrorsEncountered "none" -FixesApplied "none"
        Start-Sleep -Seconds 3600
        continue
    }

    if (-not $stageBStartedByWatcher -and -not $fullProc) {
        if ($stageBComplete) {
            $statusParagraph = "Stage B completion artifact already exists and no Stage A/Stage B process is active."
            $artifacts = "- stage B summary: yes ($stageBSummaryPath)`n- stage A arms in summary: $armsCount`n- winner_arm_id: $winnerArm"
            Append-QueueBlock -Status "completed" -StatusParagraph $statusParagraph -Artifacts $artifacts -ActionTaken "none" -ErrorsEncountered "none after resume" -FixesApplied "none"
            break
        }

        if ($armsCount -ge 5) {
            $proc = Start-Process -FilePath $pythonExe -ArgumentList @("run.py", "--full", "--show-progress", "--export-artifacts") -WorkingDirectory $expDir -PassThru
            $stageBStartedByWatcher = $true
            $statusParagraph = "Stage A appears complete (no screen process, screen summary has $armsCount arms). Stage B was auto-started with pid $($proc.Id) and --export-artifacts."
            $artifacts = "- stage A summary: yes ($screenSummaryPath)`n- winner_arm_id: $winnerArm`n- stage B summary present before launch: no"
            Append-QueueBlock -Status "running" -StatusParagraph $statusParagraph -Artifacts $artifacts -ActionTaken "auto-started: run.py --full --show-progress --export-artifacts" -ErrorsEncountered "none" -FixesApplied "none"
            Start-Sleep -Seconds 3600
            continue
        } else {
            if (-not $stageAStartedByWatcher) {
                $stageAProc = Start-Process -FilePath $pythonExe -ArgumentList @("run.py", "--screen", "--export-artifacts") -WorkingDirectory $expDir -PassThru
                $stageAStartedByWatcher = $true
                $statusParagraph = "No active Stage A process was detected and summary is incomplete ($armsCount arms), so Stage A was auto-resumed with a full screen rerun (pid $($stageAProc.Id)). Stage B will auto-start after Stage A completes."
                $artifacts = "- stage A summary path: $screenSummaryPath`n- arms found before resume: $armsCount`n- stage B summary exists: $stageBComplete`n- stale lock cleared: $(-not $lockPresent)"
                Append-QueueBlock -Status "running" -StatusParagraph $statusParagraph -Artifacts $artifacts -ActionTaken "auto-started: run.py --screen" -ErrorsEncountered "Stage A process exited before full 5-arm completion" -FixesApplied "removed stale pipeline lock mirror and relaunched Stage A (semantically correct resume)"
            } else {
                $statusParagraph = "Stage A auto-resume appears to have exited before producing a full 5-arm summary ($armsCount arms). Stage B remains blocked until Stage A completion."
                $artifacts = "- stage A summary path: $screenSummaryPath`n- arms found: $armsCount`n- stage B summary exists: $stageBComplete"
                Append-QueueBlock -Status "failed" -StatusParagraph $statusParagraph -Artifacts $artifacts -ActionTaken "none" -ErrorsEncountered "Stage A rerun ended without full arm set" -FixesApplied "none" -QuestionForUser "Approve another Stage A relaunch now, or proceed to Stage B with explicit arm override?"
            }
            Start-Sleep -Seconds 3600
            continue
        }
    }

    if ($fullProc) {
        $statusParagraph = "Stage B is running (`run.py --full`) with pid $($fullProc.ProcessId); monitoring until completion artifact is written."
        $artifacts = "- stage B summary exists: $stageBComplete`n- lock file present: $lockPresent`n- active_run.json present: $activeRunPresent"
        Append-QueueBlock -Status "running" -StatusParagraph $statusParagraph -Artifacts $artifacts -ActionTaken "none (passive monitor)" -ErrorsEncountered "none" -FixesApplied "none"
        Start-Sleep -Seconds 3600
        continue
    }

    if ($stageBStartedByWatcher -and -not $fullProc) {
        if (Test-Path $stageBSummaryPath) {
            $statusParagraph = "Stage B process is no longer running and completion artifact is present; A→B overnight chain finished."
            $artifacts = "- stage B summary: yes ($stageBSummaryPath)`n- stage A summary arms: $armsCount`n- winner_arm_id: $winnerArm"
            Append-QueueBlock -Status "completed" -StatusParagraph $statusParagraph -Artifacts $artifacts -ActionTaken "none" -ErrorsEncountered "none after resume" -FixesApplied "none"
            break
        } else {
            $statusParagraph = "Stage B process exited but completion artifact is missing."
            $artifacts = "- expected completion: $stageBSummaryPath`n- lock file present: $lockPresent`n- active_run.json present: $activeRunPresent"
            Append-QueueBlock -Status "failed" -StatusParagraph $statusParagraph -Artifacts $artifacts -ActionTaken "none" -ErrorsEncountered "Stage B ended without stage_b_summary.json" -FixesApplied "none" -QuestionForUser "Approve manual relaunch of Stage B now?"
            break
        }
    }

    Start-Sleep -Seconds 3600
}
