---
name: advisor-loop
description: Get a bounded independent second opinion from an Any Workers reader on a concrete repository decision or change.
---

Use the installed deepseek-agents runtime. Write a standalone brief explaining the
decision, candidate options, relevant paths and the question to answer, then call
ds-agent.ps1 -Kind advisor -Mode read -TaskFile <brief> -Dir <project>.
Check its evidence yourself and give the user the conclusion. A second opinion
does not authorize edits, external actions or repeated paid runs without a purpose.
Workers have no shell or web tools; use Codex to verify command-dependent claims.
