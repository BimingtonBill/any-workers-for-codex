---
name: deepseek-agents
description: Delegate bounded repository research, independent reviews and isolated coding tasks to paid DeepSeek workers while Codex plans, verifies and integrates the results. Use when the user asks for DeepSeek or Any Workers.
---

# Any Workers for Codex

Resolve runtime paths relative to this SKILL.md. The installer places ds-agent.ps1,
ds-spawn.ps1, tools/ and templates/ beside it. In the source repository they live
in launcher/, tools/ and templates/. Use PowerShell on Windows and Python 3.10+.

Before launching, read the project's delegation level with `python tools/ds_delegation.py`
using the installed tool's absolute path and `--project <project>`.
Workers send brief text and the project files they read to the configured paid API.
Never put keys in briefs or chat. Workers use DEEPSEEK_API_KEY from the environment
or the saved Windows user environment. Use the private key setup script if needed.

Write a self-contained brief with Goal, Context, Scope, Done when and Report sections.
Name tasks `<kind>-<nnn>-<slug>`, for example research-001-config.
For reading and review, run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "<skill>/ds-agent.ps1" -Dir "<project>" -TaskFile "<brief.md>" -Label research-001-config -Kind research -Mode read
```

Run long worker commands through Codex's available shell execution tool, retaining
the returned process/session identifier and polling it when useful. While workers
run, do independent work. For up to six independent readers use ds-spawn.ps1
with `-Dir <project> -Briefs "<brief1>,<brief2>" -NoCrosstalk`.
This is host-side process parallelism; workers cannot spawn or message each other.

For coding use `tools/ds_impl.ps1 -Brief <brief> -Name impl-002-parser
-Files "src/parser.py,tests/test_parser.py" -Accept "python -m unittest"` from
the project folder. It creates a git worktree, writes the exact owned-file list,
runs the worker, checks scope, and runs host-side acceptance commands. Use briefs
with `Owned files:` and `Acceptance:` lines. Workers have read/list/search/write
tools and no shell. Acceptance commands are supplied by the trusted lead, never
copied blindly from worker reports. Run independent review and inspect the whole
diff before integrating with `ds_impl.ps1 -Integrate <name>`. -Force is only for
deliberately resolving a checked conflict. The main checkout remains the lead's.

Worker outputs start with Status, Verdict when appropriate, Summary, Left and Next.
Read the opening first; read the full report and verify material evidence before
using it. Report paths, manifests, tool logs and token transcripts are kept on disk.
Exit codes: 0 finished, 1 worker failure/incomplete, 2 setup or unsupported option,
3 timeout, 4 held by spend controls. A held task can be handled by Codex or queued.
Never call a partial run accepted just because its tests happen to pass.

Spend tools: `python <skill>/ds_spend.py status --offline`,
`set 2 --per day`, `set 1.5 --per run`, `stretch 2w`, `off`.
State defaults to ~/.codex-workers, separate from upstream Claude state.
Cost checks happen between responses, so one in-flight response can exceed a cap.
For a model override, update price overrides in limits.json as well.

Supported: DeepSeek Chat Completions and the registry's OpenRouter sol entry
(OpenRouter not live-verified). Meta/MiMo Anthropic endpoints, subscription/training
tiers, worker web access, arbitrary shell, AddDir, resume, hierarchy, crosstalk,
Claude hooks and automatic Codex plan pacing are unavailable. Unsupported launcher
flags fail explicitly. Effort is compatibility-only and uses provider defaults.
Do web research and command-based reviews with Codex's own tools; don't ask a
file-only worker to perform them. Use denyRead/denyEdit lists in
.deepseek-agents.json for project file policy. No worker needs Codex login files.
