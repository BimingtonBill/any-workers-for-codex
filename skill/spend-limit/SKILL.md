---
name: spend-limit
description: Show or set the paid API budgets for Any Workers, including daily, weekly and per-worker limits.
---

Use ds_spend.py beside the installed deepseek-agents SKILL.md (launcher/ in the repo).
Show `status --offline` by default. Set only the budget the user requested:
`set 2 --per day`, `set 10 --per week`, `set 1.5 --per run` or `stretch 2w`.
Use `off --per day|week|run|stretch` to remove that limit. Global state is
~/.codex-workers/spend or DS_SPEND_DIR. Never touch upstream Claude state.
Dollar figures are estimates at configured prices; dashboards hold actual billing.
Limits are checked between API responses, so one response may overshoot.
Codex account plan usage is separate and is not automatically paced by this port.
