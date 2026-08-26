[CmdletBinding()]
param(
    [ValidatePattern('^[A-Za-z0-9._-]+$')]
    [string]$Distro = 'Ubuntu',

    [ValidatePattern('^[A-Za-z0-9._-]+$')]
    [string]$LinuxUser = 'loucmane',

    [ValidatePattern('^/[A-Za-z0-9._/-]+$')]
    [string]$DoctorPath = '/home/loucmane/.local/bin/codex-wsl-readiness',

    [string]$EvidenceRoot = (Join-Path $env:LOCALAPPDATA 'GasCity\reboot-readiness'),

    [ValidateRange(1, 12)]
    [int]$MaxAttempts = 12,

    [ValidateRange(1, 30)]
    [int]$RetryDelaySeconds = 5
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$Utf8NoBom = [System.Text.UTF8Encoding]::new($false)
$WslExe = Join-Path $env:WINDIR 'System32\wsl.exe'

function Write-AtomicUtf8 {
    param(
        [Parameter(Mandatory)] [string]$Path,
        [Parameter(Mandatory)] [string]$Content
    )
    $temporary = '{0}.tmp.{1}.{2}' -f $Path, $PID, ([guid]::NewGuid().ToString('N'))
    [System.IO.File]::WriteAllText($temporary, $Content, $Utf8NoBom)
    Move-Item -LiteralPath $temporary -Destination $Path -Force
}

if (-not (Test-Path -LiteralPath $WslExe -PathType Leaf)) {
    throw "wsl.exe is unavailable at $WslExe"
}
New-Item -ItemType Directory -Path $EvidenceRoot -Force | Out-Null

$attempts = [System.Collections.Generic.List[object]]::new()
$acceptedReport = $null
$acceptedExit = $null
for ($attempt = 1; $attempt -le $MaxAttempts; $attempt++) {
    $stderrPath = Join-Path $env:TEMP ('gas-city-wsl-bootstrap-{0}-{1}.stderr' -f $PID, $attempt)
    $lines = @(
        & $WslExe -d $Distro --user $LinuxUser --exec $DoctorPath --observer host-wsl --json 2> $stderrPath
    )
    $doctorExit = $LASTEXITCODE
    $stdoutText = $lines -join "`n"
    $stderrText = ''
    if (Test-Path -LiteralPath $stderrPath -PathType Leaf) {
        $stderrText = [System.IO.File]::ReadAllText($stderrPath)
        Remove-Item -LiteralPath $stderrPath -Force
    }
    if ($stderrText.Length -gt 8192) {
        $stderrText = $stderrText.Substring(0, 8192)
    }

    $report = $null
    $parseError = $null
    try {
        $report = $stdoutText | ConvertFrom-Json -Depth 100
    }
    catch {
        $parseError = $_.Exception.Message
    }
    $validReport = (
        $null -ne $report -and
        [string]$report.schema_version -eq '1' -and
        @('ready', 'degraded', 'failed') -contains [string]$report.overall -and
        [string]$report.observer -eq 'host-wsl'
    )
    $accepted = (
        $validReport -and
        @('ready', 'degraded') -contains [string]$report.overall -and
        @(0, 1) -contains $doctorExit
    )
    $attempts.Add([ordered]@{
        attempt = $attempt
        exit_code = $doctorExit
        valid_report = $validReport
        accepted = $accepted
        overall = if ($validReport) { [string]$report.overall } else { $null }
        parse_error = $parseError
        stderr = $stderrText
    })
    if ($accepted) {
        $acceptedReport = $report
        $acceptedExit = $doctorExit
        break
    }
    if ($attempt -lt $MaxAttempts) {
        Start-Sleep -Seconds $RetryDelaySeconds
    }
}

$observedAt = [DateTimeOffset]::UtcNow
$record = [ordered]@{
    schema_version = '1'
    bootstrap_status = if ($null -ne $acceptedReport) { 'pass' } else { 'fail' }
    observed_at = $observedAt.ToString('o')
    distro = $Distro
    linux_user = $LinuxUser
    doctor_path = $DoctorPath
    doctor_exit_code = $acceptedExit
    attempts = $attempts
    report = $acceptedReport
}
$recordJson = $record | ConvertTo-Json -Depth 100
$historyName = 'readiness-{0}.json' -f $observedAt.ToString('yyyyMMddTHHmmss.fffffffZ')
Write-AtomicUtf8 -Path (Join-Path $EvidenceRoot $historyName) -Content $recordJson
Write-AtomicUtf8 -Path (Join-Path $EvidenceRoot 'latest.json') -Content $recordJson

if ($null -eq $acceptedReport) {
    exit 2
}
exit 0
