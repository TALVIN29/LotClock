# Registers the LotClock daily collection task.
# Run in PowerShell AS ADMINISTRATOR (admin is needed only for -WakeToRun).
#
#   powershell -ExecutionPolicy Bypass -File E:\Portfolio\price-story\install_task.ps1

$ErrorActionPreference = "Stop"

$TaskName = "LotClock daily scrape"
$Script   = Join-Path $PSScriptRoot "run_daily.cmd"

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

$Action = New-ScheduledTaskAction -Execute $Script

$Trigger = New-ScheduledTaskTrigger -Daily -At 10am

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
