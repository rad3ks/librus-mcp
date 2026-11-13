# Rules for AI assistants in this fork

1. Read [AGENTS.md](AGENTS.md) (upstream project rules) and [FORK.md](FORK.md) (what this fork changes and why).
2. Work on branch `grok-remarks`. `main` mirrors upstream; do not commit fork changes there.
3. Run the checks with `uv run --frozen ...` (FORK.md "Develop"). Without `--frozen`, the local
   `uv` rewrites `uv.lock`. Never commit a `uv.lock` change you did not intend.
4. Do not call live Librus from tests or scripts unless the user explicitly authorizes that run.
5. When you add, remove or rename a tool: update the counts in `tests_native/test_catalog_schema.py`,
   `test_native_stdio.py` and `test_http_transport.py`, add the tool to `CHECKS`, `CATALOG_TOOLS` or
   `REFUSED` in `check_tools.py`, bump `FORK_REVISION` in `server.py`, and tell the user that Grok
   needs a new connector URL and name (FORK.md "Grok caveat").
6. Deployment lives in the private repo rad3ks/mikrus-infrastructure (`scripts/deploy.sh librus-mcp`).
   Never `docker build` on the Mikrus host.
7. Keep fork changes small and clearly marked with a `# Fork:` comment, so rebasing on upstream stays easy.
