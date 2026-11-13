# rad3ks/librus-mcp: fork for Grok (Tesla)

This fork of [krzysztofbury/librus-mcp](https://github.com/krzysztofbury/librus-mcp) makes the
server usable from Grok's custom connectors, including the in-car Grok on Tesla.
Branch **`grok-remarks`** is deployed; `main` tracks upstream.

## Changes from upstream 2.7.0

| Change | Where | Why |
|---|---|---|
| New tool `get_remarks` (behaviour remarks, *uwagi*) | `src/librus_mcp/remarks_tools.py` | Upstream has no remarks read. Reads Synergia's `/uwagi` page via the library's internal `behaviour_notes_probe` endpoint and its private `_page`/`_read` helpers. Against upstream's AGENTS.md rule (scraping belongs in `librus-python-api`), so it cannot go upstream as is. |
| `get_message_content` opens messages even when `allow_mark_read=false`, unless the operator set `mark_read_consent: true` | `src/librus_mcp/message_tools.py` | Grok always passes `false`, then gives up on `CONSENT_REQUIRED`. |
| `LIBRUS_MCP_HIDE_RECIPIENT_TOOLS=1` hides the three recipient lookups while sending is disabled | `src/librus_mcp/server.py`, `message_tools.py` | Keeps the catalog small for Grok. Default behaviour unchanged. |
| serverInfo version `2.7.0+fork.<FORK_REVISION>` | `src/librus_mcp/server.py` | Lets clients tell fork versions apart. Bump `FORK_REVISION` when tools change. |

Tests are adjusted for these changes, and `tests_native/test_remarks.py` covers the remarks parser.

## Run it

Production runs on a Mikrus VPS. Deployment, URLs, secrets and runbooks are in the private repo
**rad3ks/mikrus-infrastructure** (`docs/librus-mcp.md`). In short: the upstream image
`ghcr.io/krzysztofbury/librus-mcp:2.7.0` runs with this repo's `src/librus_mcp` mounted over the
packaged module:

```yaml
services:
  librus-mcp:
    image: ghcr.io/krzysztofbury/librus-mcp:2.7.0
    command: ["--transport", "http", "--allowed-host", "<public-host>:*"]
    environment:
      LIBRUS_CONFIG: /config/config.json
      LIBRUS_MCP_TOKEN_FILE: /config/token
      LIBRUS_MCP_HIDE_RECIPIENT_TOOLS: "1"
    volumes:
      - ./config.json:/config/config.json:ro      # {"accounts":[{"alias":..,"username":..,"password":..}]}
      - ./token:/config/token:ro                  # docker run --rm ghcr.io/krzysztofbury/librus-mcp:2.7.0 --generate-token
      - ./data:/data
      - ./librus-mcp/src/librus_mcp:/opt/librus-mcp/lib/python3.14/site-packages/librus_mcp:ro
    ports: ["127.0.0.1:8000:8000"]                # put TLS in front (reverse proxy)
    restart: unless-stopped
```

`config.json` and `token` must belong to uid 10001 with mode 600. This works only while the fork
keeps upstream 2.7.0's dependencies. If `pyproject.toml` or `uv.lock` change, build the image from
this repo's `Dockerfile` instead.

Locally: `uv run --frozen librus-mcp --config /path/to/config.json` (stdio) or add
`--transport http` with `LIBRUS_MCP_TOKEN` set.

## Develop

```bash
uv run --frozen ruff check src/librus_mcp tests_native && uv run --frozen ruff format --check src/librus_mcp tests_native
uv run --frozen mypy
uv run --frozen pytest -q          # ~3 min, offline; never calls live Librus
```

Use `--frozen`: an older local `uv` rewrites `uv.lock` (it cannot parse `exclude-newer = "7 days"`).

## Grok caveat

Grok caches a connector's tool list by URL and connector name, even across Disconnect and
re-adding it. After changing tools, serve the server under a new URL and add the connector under a
new name.

## Sync with upstream

```bash
git fetch upstream && git switch grok-remarks && git rebase upstream/main   # or the new release tag
uv run --frozen pytest -q && git push --force-with-lease origin grok-remarks
```
