# Validation of the Codex port

Based on upstream commit `efb36182057f0bfd104f4e92af7c3a0b6005f523`; local branch `codex-port`.

Validation: `python -m unittest discover -s tests -v`: 23 tests, 22 passed,
1 skipped because this Windows account cannot create symlinks. No paid API requests.
All PowerShell scripts parse successfully with the Windows PowerShell parser.

Coverage includes a real temporary git worktree with scripted API responses,
owned-file editing, unchanged main checkout, host-side acceptance commands containing
quotes, and rejection of incomplete worker runs even when those commands pass.
The installer was exercised twice in a temporary folder with spaces, including
backup creation and the installed launcher dry run.

Live provider authentication, model access, throughput and billing remain unverified.
The archive excludes .git, caches, temporary projects and secrets. It includes the
source, tests, installer, original MIT license and historical design documents.
Port scope and missing upstream features are described in README.md.
