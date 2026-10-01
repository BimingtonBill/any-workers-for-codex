---
name: delegation
description: Show or set how much Codex delegates to Any Workers, from 1 (only when asked) to 5 (orchestrate).
---

Use the ds_delegation.py tool in the installed deepseek-agents skill's tools directory.
Resolve ~/.agents/skills/deepseek-agents/tools/ds_delegation.py, or the local repo tool.
Run it with --project <project> to show the current level; --table shows all levels.
A requested level uses --set N --agents-md for this project; an explicitly requested
global default uses --set N --global. Summarize the effective setting and its scope.
Preserve unrelated project instructions. Supported delegation is bounded file
research, review and worktree coding; web and shell work remain with Codex.
