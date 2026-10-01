# The launcher's state-dir rule, in one place: where run records (manifest.jsonl, runs.csv, pilot.csv,
# runs\<run id>\) are kept. Every PowerShell tool calls this script instead of repeating the rule, and
# tools/ds_state.py runs it for the Python ones.
#
#   powershell -NoProfile -ExecutionPolicy Bypass -File launcher/ds-state.ps1 -Dir C:\code\app
#
# First match wins:
#   1. DS_STATE_DIR, when it is set and not empty;
#   2. "stateDir" in <Dir>\.deepseek-agents.json - absolute used as-is, otherwise joined onto <Dir>. A
#      missing or unreadable file, bad JSON, or a missing or empty key falls through;
#   3. <Dir>\local\agents, when <Dir>\local is an existing folder;
#   4. $HOME\.codex-workers\agents.
#
# Prints one line - that folder, absolute, with no trailing separator - and nothing else. It creates
# nothing, never fails on a missing or malformed config, and always exits 0.
param(
    # The project folder. Defaults to the current folder.
    [string]$Dir = (Get-Location).Path
)
$ErrorActionPreference = 'Continue'
# The Python caller reads this output as UTF-8, whatever the console's own code page is.
try { [Console]::OutputEncoding = (New-Object System.Text.UTF8Encoding $false) } catch { }

$stateDir = $null
try {
    $project = $Dir
    if (-not $project) { $project = (Get-Location).Path }

    # 1. The environment variable. A lead sets it for its workers, so they write to the lead's manifest.
    if ($env:DS_STATE_DIR) { $stateDir = $env:DS_STATE_DIR }

    # 2. The project's own setting. Anything wrong with the file means this step does not apply.
    if (-not $stateDir) {
        $configured = $null
        try {
            $configPath = Join-Path $project '.deepseek-agents.json'
            if (Test-Path -LiteralPath $configPath) {
                # UTF-8, as tools/ds_state.py reads it: PowerShell 5.1 would otherwise use the ANSI code page for a
                # file without a BOM (audit finding SDR-20260924-06).
                $config = Get-Content -LiteralPath $configPath -Raw -Encoding UTF8 -ErrorAction Stop | ConvertFrom-Json -ErrorAction Stop
                $configured = [string]$config.stateDir
            }
        } catch { $configured = $null }
        if ($configured) {
            $stateDir = if ([IO.Path]::IsPathRooted($configured)) { $configured } else { Join-Path $project $configured }
        }
    }

    # 3. The project's own agents folder, 4. or the shared one.
    if (-not $stateDir) {
        # A folder, not any item named local (audit finding SDR-20260924-02; tools/ds_state.py uses is_dir()).
        if (Test-Path -LiteralPath (Join-Path $project 'local') -PathType Container) { $stateDir = Join-Path $project 'local\agents' }
        else { $stateDir = Join-Path $HOME '.codex-workers\agents' }
    }
} catch {
    # Nothing here may stop a caller: treat an unexpected failure as if nothing were configured.
    $stateDir = Join-Path $HOME '.codex-workers\agents'
}

$full = $stateDir
if ($full) {
    try { $full = [IO.Path]::GetFullPath($full) } catch { $full = $stateDir }
    # No trailing separator, so a caller can Join-Path onto it; a bare drive root ("C:\") keeps its own.
    if ($full.Length -gt 3) { $full = $full.TrimEnd('\', '/') }
}
$full
exit 0
