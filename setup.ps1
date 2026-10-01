# One-step setup for Any Workers for Codex.
param([string]$Target, [switch]$NoKeyWindow)
$ErrorActionPreference = 'Stop'
$installArgs = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', (Join-Path $PSScriptRoot 'tools\install-skill.ps1'))
if ($Target) { $installArgs += @('-Target', $Target) }
& powershell @installArgs
if ($LASTEXITCODE) { exit $LASTEXITCODE }
if (-not (Get-Command python -ErrorAction SilentlyContinue)) { Write-Warning 'Python 3.10+ is required.' }
if (-not (Get-Command git -ErrorAction SilentlyContinue)) { Write-Warning 'Git is required for isolated coding workers.' }
$keyPresent = $env:DEEPSEEK_API_KEY -or [Environment]::GetEnvironmentVariable('DEEPSEEK_API_KEY', 'User')
if (-not $keyPresent -and -not $NoKeyWindow) {
    # An explicitly interactive key-entry window; the key never enters chat.
    $keyScript = Join-Path $PSScriptRoot 'tools\set-deepseek-key.ps1'
    Start-Process powershell -ArgumentList @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-NoExit', '-File', "`"$keyScript`"")
} elseif (-not $keyPresent) { Write-Warning 'No DeepSeek key saved; key window skipped.' }
Write-Host 'Restart Codex, then invoke $deepseek-agents in a project.'
