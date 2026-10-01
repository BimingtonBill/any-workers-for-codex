# Install Codex skills and runtime. No account, hook or config changes.
param([string]$Target, [switch]$DryRun)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$skillsRoot = if ($Target) { [IO.Path]::GetFullPath($Target) } else { Join-Path $HOME '.agents\skills' }
$destination = Join-Path $skillsRoot 'deepseek-agents'
$backupRoot = Join-Path (Split-Path -Parent $skillsRoot) 'any-workers-backups'
if ($DryRun) { "Codex skills: $skillsRoot"; "Runtime: $destination"; exit 0 }
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss-ffff'
foreach ($name in 'deepseek-agents', 'delegation', 'spend-limit', 'advisor-loop') {
    $to = Join-Path $skillsRoot $name
    if (Test-Path -LiteralPath $to) {
        New-Item -ItemType Directory -Force -Path $backupRoot | Out-Null
        Copy-Item -LiteralPath $to -Destination (Join-Path $backupRoot "$name-$stamp") -Recurse
    }
    New-Item -ItemType Directory -Force -Path $to | Out-Null
    Copy-Item -LiteralPath (Join-Path $root "skill\$name\SKILL.md") -Destination (Join-Path $to 'SKILL.md') -Force
}
Get-ChildItem (Join-Path $root 'launcher') -File | Where-Object {
    $_.Name -notin @('ds_claude.py', 'ds_mcp.py', 'ds-watch.ps1', 'ds-which.ps1')
} | ForEach-Object {
    Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $destination $_.Name) -Force
}
foreach ($folder in 'tools', 'templates') {
    $to = Join-Path $destination $folder
    New-Item -ItemType Directory -Force -Path $to | Out-Null
    Get-ChildItem (Join-Path $root $folder) -File | Where-Object { $_.Name -ne 'install-skill.ps1' } | ForEach-Object {
        Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $to $_.Name) -Force
    }
}
"Installed Any Workers for Codex into $skillsRoot. Existing skills backed up in $backupRoot."
