# Codex worker entry point, compatible with ds-spawn and ds_impl. No Claude dependency.
[CmdletBinding(PositionalBinding = $false)]
param(
    [string]$Task, [string]$TaskFile, [string]$Extra,
    [string]$Dir = (Get-Location).Path,
    [ValidateSet('read', 'edit')][string]$Mode,
    [string]$Label, [string]$Model, [string]$Provider, [string]$Tier,
    [string]$Kind, [string]$Title, [string]$Parent, [string]$Schema,
    [int]$MaxTurns = 60, [double]$TimeoutMinutes = 30, [double]$MaxCost = 0,
    [ValidateSet('low', 'medium', 'high', 'xhigh', 'max')][string]$Effort = 'high',
    [switch]$FullReport, [switch]$DryRun, [switch]$NoCrosstalk,
    [switch]$Crosstalk, [switch]$CanSpawn, [switch]$SubAgents,
    [string]$WebDomains, [string]$Resume, [string]$AddDir, [string]$AllowTools, [string]$DenyEdit
)
$ErrorActionPreference = 'Stop'
if ($Crosstalk -or $CanSpawn -or $SubAgents -or $WebDomains -or $Resume -or $AddDir -or $AllowTools -or $DenyEdit) {
    [Console]::Error.WriteLine('[ds-agent] Unsupported in this port: crosstalk, worker leads, web, resume, extra roots and Claude permission rules. Use denyRead/denyEdit in project configuration; run tests through the host.')
    exit 2
}
$workerArgs = @((Join-Path $PSScriptRoot 'ds_worker.py'), '--dir', $Dir,
    '--max-turns', $MaxTurns, '--timeout-minutes', $TimeoutMinutes, '--max-cost', $MaxCost)
$values = @{ 'task'=$Task; 'task-file'=$TaskFile; 'extra'=$Extra; 'mode'=$Mode;
    'label'=$Label; 'model'=$Model; 'provider'=$Provider; 'tier'=$Tier; 'kind'=$Kind;
    'title'=$Title; 'parent'=$Parent; 'schema'=$Schema }
foreach ($entry in $values.GetEnumerator()) {
    if ($entry.Value) { $workerArgs += @("--$($entry.Key)", [string]$entry.Value) }
}
if ($FullReport) { $workerArgs += '--full-report' }
if ($DryRun) { $workerArgs += '--dry-run' }
if ($PSBoundParameters.ContainsKey('Effort')) {
    [Console]::Error.WriteLine('[ds-agent] Effort is accepted for compatibility; the provider default is used.')
}
$ErrorActionPreference = 'Continue'
& python @workerArgs
exit $LASTEXITCODE
