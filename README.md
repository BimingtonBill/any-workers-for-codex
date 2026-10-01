# Any Workers for Codex

An independent Windows worker toolkit for Codex.
Codex leads the work, delegates bounded tasks to cheaper API workers, checks their
reports and diffs, and integrates accepted changes. **Claude Code is not required.**

The paid workers run in a Python tool loop against Chat Completions, rather than
through Claude Code or your Codex subscription. Your Codex app/CLI remains the
orchestrator. This avoids assuming Anthropic-compatible providers support the
Responses API used by Codex. Python's standard library is the only runtime dependency.

## Install

Requirements: Windows, Codex app or CLI, Python 3.10+, Git for coding workers,
and a funded DeepSeek account.

Download [the preview installer ZIP](https://github.com/BimingtonBill/any-workers-for-codex/releases/download/v0.1.0/any-workers-for-codex.zip),
unzip it, double-click **install.cmd**, and restart Codex.
Preview releases are listed on the [releases page](https://github.com/BimingtonBill/any-workers-for-codex/releases).
To install from source instead:

```powershell
git clone https://github.com/BimingtonBill/any-workers-for-codex.git
cd any-workers-for-codex
```

Then run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File setup.ps1
```

Setup installs four skills in `%USERPROFILE%\.agents\skills`, backing up existing
copies outside the skills directory. If needed, it opens a private window for
your DeepSeek API key. Never paste keys into chat. Restart Codex after installing.
To preview installation, run `tools/install-skill.ps1 -DryRun`.
For a reversible test install use `setup.ps1 -Target <test-skills> -NoKeyWindow`.
Uninstall by removing the four installed skill directories; restore any previous
versions from `any-workers-backups` beside the skills directory. The installer
does not edit Codex config.toml, account files, hooks or Claude settings.

## Use

In Codex, invoke `$deepseek-agents`, or ask:

- "Use DeepSeek workers to trace where this project loads settings."
- "Have an Any Workers coder add a median function with tests, then review it."
- "Use a worker to review the diff for edge cases."
- "Limit DeepSeek workers to $2 a day."

`$delegation` controls levels 1–5; `$spend-limit` manages budgets;
`$advisor-loop` gets a bounded second opinion. Codex still makes design decisions,
checks evidence, runs commands and reviews changes before integrating them.

Direct reader launch (from this source folder):

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File launcher/ds-agent.ps1 -TaskFile brief.md -Dir C:\code\app -Kind research -Label research-001-settings
```

Readers get read/list/search tools. Coding workers get write_file only for exact
owned paths in a separate git worktree created by `tools/ds_impl.ps1`:

```powershell
# Run from your project. Use an absolute path to this kit's tool.
powershell -NoProfile -ExecutionPolicy Bypass -File <kit>/tools/ds_impl.ps1 -Brief brief.md -Name impl-002-median -Files "stats.py,test_stats.py" -Accept "python -m unittest"
```

The host runs acceptance commands and checks changed-file scope. Inspect the
worktree diff, run an independent review, then explicitly integrate:
`<kit>/tools/ds_impl.ps1 -Integrate impl-002-median`.
The worker has no shell and cannot run its own acceptance tests.

Up to six read tasks run in parallel with `launcher/ds-spawn.ps1 -Dir <project>
-Briefs "a.md,b.md" -NoCrosstalk`. Codex's shell tool can keep a long command
running and retain its process/session id. There is no Claude Background tasks hook.

Reports preserve the compact Status / Verdict / Summary / Left / Next opening.
Each run saves report.md, transcript.jsonl, tools.jsonl and manifest.json, with
start/end events in the shared manifest.jsonl. Default state and budgets live in
`~/.codex-workers`; DS_STATE_DIR and DS_SPEND_DIR override their locations.
An optional `.deepseek-agents.json` keeps the upstream project configuration name.
Supported policy: denyRead, denyEdit, stateDir and defaults.mode. Reads reject
traversal, links, .git, .env and harness configuration. Coding writes require an
exact owned-file entry. These are bounded tools, not a general OS sandbox.

## Budgets and providers

```powershell
python launcher/ds_spend.py status --offline
python launcher/ds_spend.py set 2 --per day
python launcher/ds_spend.py set 1.5 --per run
```

The port reuses upstream daily/weekly pacing, admission checks, per-run caps and
cost accounting. Checks occur between API responses, so an in-flight response can
overshoot a cap. API errors and incomplete runs retain a partial report and ledger
entry. Usage must be supplied by the provider; omission stops further work.
Prices inherited from upstream are estimates, not a verified current bill. Adjust
the `prices` override in limits.json when using a different DeepSeek model.

DeepSeek uses `https://api.deepseek.com/chat/completions` and `deepseek-flash` by
default; pass -Model to override it. The OpenRouter `sol` registry entry has a
Chat Completions endpoint and uses OPENROUTER_API_KEY; its live behavior is unverified.
Meta and MiMo entries remain as upstream metadata but fail at launch because their
Anthropic endpoints cannot be treated as verified Chat Completions endpoints.
Training/contributor and subscription tiers fail explicitly.

## Port differences

This port supports repository research, file-based reviews, isolated coding,
host-side parallel workers, delegation levels, reports and spend controls.
It does **not** port Claude hooks, automatic Codex plan pacing, worker web search,
worker shell, additional read roots, resume, worker leads, subagents or crosstalk.
Unsupported options return setup error 2; -Effort is accepted for compatibility
with upstream runners and uses the provider's default. Codex handles web and shell
work using its own tools. Historical design documents describe the upstream
project and should not be read as parity promises; see docs/upstream-README.md.

Exit codes: 0 finished, 1 worker failed/incomplete, 2 invalid setup/unsupported
option, 3 timeout, 4 held/stopped by spending. A failed worker cannot pass the
implementation runner's acceptance gate just because its tests happen to pass.

## Validation

```powershell
python -m unittest discover -s tests -v
```

Tests use scripted responses and temporary projects, without API calls or paid
usage. They cover tool restrictions, coding ownership, report/schema validation,
tool-call continuation, budget stops, API failure accounting and installation.
Real paid-provider execution still needs a live smoke test with your own key.

Codex skill format and discovery follow the
[official skill documentation](https://developers.openai.com/codex/skills/).
The default model and request format follow DeepSeek's
[Chat Completions reference](https://api-docs.deepseek.com/api/create-chat-completion/).

## Attribution

Created by BimingtonBill, based on
[Any Workers for Claude Code](https://github.com/BimingtonBill/any-workers-for-claude-code).
This repository is independently distributed and maintained for Codex.
MIT; original attribution and LICENSE preserved. An independent community project,
not made or endorsed by OpenAI or the worker model providers.
