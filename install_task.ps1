# Registers the LotClock daily collection task.
# Run in PowerShell AS ADMINISTRATOR (admin is needed only for -WakeToRun).
#
# Paths below are examples — the script resolves run_daily.cmd from its own
# location ($PSScriptRoot), so it works from wherever the repo is cloned.
#
#   powershell -ExecutionPolicy Bypass -File E:\Portfolio\LotClock\install_task.ps1
#
# On a second machine, add -Backup. That host runs later in the day and skips
# entirely if the primary already collected, so two collectors close the gaps
# left by a machine being off without doubling the load on the source.
#
#   powershell -ExecutionPolicy Bypass -File E:\Portfolio\LotClock\install_task.ps1 -Backup

param(
    [switch]$Backup
)

$ErrorActionPreference = "Stop"

$TaskName = if ($Backup) { "LotClock daily scrape (backup)" } else { "LotClock daily scrape" }
$Script   = Join-Path $PSScriptRoot "run_daily.cmd"
$RunAt    = if ($Backup) { "8pm" } else { "10am" }

if (-not (Test-Path $Script)) {
    Write-Error "Cannot find $Script"
    exit 1
}

# Remove any previous version so re-running this is safe
$existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "Removing existing task..."
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

$Action = if ($Backup) {
    New-ScheduledTaskAction -Execute $Script -Argument "--skip-if-collected"
} else {
    New-ScheduledTaskAction -Execute $Script
}

$Trigger = New-ScheduledTaskTrigger -Daily -At $RunAt

# WakeToRun            : wake the PC from sleep to collect
# StartWhenAvailable   : catch up a missed run when the PC comes back
# AllowStartIfOnBatteries / DontStopIfGoingOnBatteries : run unplugged too
$Settings = New-ScheduledTaskSettingsSet `
    -WakeToRun `
    -StartWhenAvailable `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -ExecutionTimeLimit (New-TimeSpan -Hours 2)

Register-ScheduledTask `
    -TaskName    $TaskName `
    -Action      $Action `
    -Trigger     $Trigger `
    -Settings    $Settings `
    -Description "LotClock: daily used-car listing collection" | Out-Null

Write-Host ""
Write-Host "Registered: $TaskName" -ForegroundColor Green
Get-ScheduledTask -TaskName $TaskName |
    Select-Object TaskName, State |
    Format-Table -AutoSize

Write-Host "Next run:" -ForegroundColor Cyan
Get-ScheduledTaskInfo -TaskName $TaskName |
    Select-Object NextRunTime, LastRunTime, LastTaskResult |
    Format-Table -AutoSize
