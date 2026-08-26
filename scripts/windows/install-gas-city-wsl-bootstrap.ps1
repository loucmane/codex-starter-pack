[CmdletBinding()]
param(
    [ValidateSet('Check', 'Apply', 'Remove')]
    [string]$Mode = 'Check',

    [string]$SourceScript,

    [ValidatePattern('^[0-9a-fA-F]{64}$')]
    [string]$ExpectedSha256,

    [ValidatePattern('^[A-Za-z0-9._-]+$')]
    [string]$Distro = 'Ubuntu',

    [ValidatePattern('^[A-Za-z0-9._-]+$')]
    [string]$LinuxUser = 'loucmane',

    [string]$TaskName = 'GasCity-WSL-Bootstrap'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$InstallRoot = Join-Path $env:LOCALAPPDATA 'GasCity\bootstrap'
$InstalledScript = Join-Path $InstallRoot 'gas-city-wsl-bootstrap.ps1'
$PowerShellExe = Join-Path $env:WINDIR 'System32\WindowsPowerShell\v1.0\powershell.exe'
$CurrentIdentity = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name

function Get-TaskContract {
    $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($null -eq $task) {
        return $null
    }
    $actions = @($task.Actions)
    $triggers = @($task.Triggers)
    if ($actions.Count -ne 1 -or $triggers.Count -ne 1) {
        throw "scheduled task must have exactly one action and one trigger"
    }
    return [ordered]@{
        task_name = $TaskName
        state = $task.State.ToString()
        execute = [string]$actions[0].Execute
        arguments = [string]$actions[0].Arguments
        user_id = [string]$task.Principal.UserId
        run_level = $task.Principal.RunLevel.ToString()
        trigger_class = [string]$triggers[0].CimClass.CimClassName
        delay = [string]$triggers[0].Delay
        installed_script = $InstalledScript
        installed_sha256 = if (Test-Path -LiteralPath $InstalledScript -PathType Leaf) {
            (Get-FileHash -LiteralPath $InstalledScript -Algorithm SHA256).Hash.ToLowerInvariant()
        } else {
            $null
        }
    }
}

function Assert-TaskContract {
    param([Parameter(Mandatory)] $Contract)
    if ($Contract.state -notin @('Ready', 'Running')) { throw "task state is $($Contract.state)" }
    if ($Contract.execute -ne $PowerShellExe) { throw "task executable drifted" }
    if ($Contract.arguments -notmatch 'gas-city-wsl-bootstrap\.ps1') { throw "task script argument drifted" }
    if ($Contract.arguments -notmatch '-NoProfile') { throw "task NoProfile flag is missing" }
    if ($Contract.arguments -notmatch '-NonInteractive') { throw "task NonInteractive flag is missing" }
    if ($Contract.user_id -ne $CurrentIdentity) { throw "task principal drifted" }
    if ($Contract.run_level -ne 'Limited') { throw "task must run with limited privileges" }
    if ($Contract.trigger_class -ne 'MSFT_TaskLogonTrigger') { throw "task trigger is not logon" }
    if ($Contract.delay -ne 'PT30S') { throw "task delay must be PT30S" }
    if ($null -eq $Contract.installed_sha256) { throw "installed bootstrap script is missing" }
}

if ($Mode -eq 'Check') {
    $contract = Get-TaskContract
    if ($null -eq $contract) { throw "scheduled task $TaskName is absent" }
    Assert-TaskContract -Contract $contract
    $contract | ConvertTo-Json -Depth 20
    exit 0
}

if ($Mode -eq 'Remove') {
    $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($null -ne $task) {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    }
    if (Test-Path -LiteralPath $InstalledScript -PathType Leaf) {
        Remove-Item -LiteralPath $InstalledScript -Force
    }
    [ordered]@{ task_removed = $true; evidence_preserved = $true } | ConvertTo-Json
    exit 0
}

if ([string]::IsNullOrWhiteSpace($SourceScript) -or [string]::IsNullOrWhiteSpace($ExpectedSha256)) {
    throw 'Apply requires -SourceScript and -ExpectedSha256'
}
if (-not (Test-Path -LiteralPath $SourceScript -PathType Leaf)) {
    throw "source script is missing: $SourceScript"
}
$sourceHash = (Get-FileHash -LiteralPath $SourceScript -Algorithm SHA256).Hash.ToLowerInvariant()
if ($sourceHash -ne $ExpectedSha256.ToLowerInvariant()) {
    throw "source script digest mismatch: got $sourceHash"
}
if ($null -ne (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue)) {
    throw "scheduled task already exists: $TaskName"
}
if (Test-Path -LiteralPath $InstalledScript) {
    throw "installed bootstrap path already exists: $InstalledScript"
}

$taskCreated = $false
$scriptCreated = $false
try {
    New-Item -ItemType Directory -Path $InstallRoot -Force | Out-Null
    $temporary = Join-Path $InstallRoot ('gas-city-wsl-bootstrap.ps1.tmp.{0}' -f ([guid]::NewGuid().ToString('N')))
    Copy-Item -LiteralPath $SourceScript -Destination $temporary
    if ((Get-FileHash -LiteralPath $temporary -Algorithm SHA256).Hash.ToLowerInvariant() -ne $sourceHash) {
        throw 'staged bootstrap digest mismatch'
    }
    Move-Item -LiteralPath $temporary -Destination $InstalledScript
    $scriptCreated = $true

    $actionArguments = (
        '-NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass ' +
        '-File "{0}" -Distro "{1}" -LinuxUser "{2}"' -f $InstalledScript, $Distro, $LinuxUser
    )
    $action = New-ScheduledTaskAction -Execute $PowerShellExe -Argument $actionArguments
    $trigger = New-ScheduledTaskTrigger -AtLogOn -User $CurrentIdentity
    $trigger.Delay = 'PT30S'
    $principal = New-ScheduledTaskPrincipal -UserId $CurrentIdentity -LogonType Interactive -RunLevel Limited
    $settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Minutes 5) `
        -MultipleInstances IgnoreNew
    $task = New-ScheduledTask -Action $action -Trigger $trigger -Principal $principal `
        -Settings $settings -Description 'Start WSL and record read-only Gas City reboot readiness.'
    Register-ScheduledTask -TaskName $TaskName -InputObject $task | Out-Null
    $taskCreated = $true

    $contract = Get-TaskContract
    Assert-TaskContract -Contract $contract
    if ($contract.installed_sha256 -ne $sourceHash) { throw 'installed bootstrap digest mismatch' }
    $contract | ConvertTo-Json -Depth 20
}
catch {
    if ($taskCreated) {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
    }
    if ($scriptCreated -and (Test-Path -LiteralPath $InstalledScript -PathType Leaf)) {
        Remove-Item -LiteralPath $InstalledScript -Force
    }
    throw
}
