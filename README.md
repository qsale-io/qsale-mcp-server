# qsale-mcp

[Model Context Protocol](https://modelcontextprotocol.io) server for the
[QSale](https://qsale.io) headless commerce platform.

Lets an LLM (Claude Code, Claude Desktop, Cursor, any MCP-compatible client)
operate a QSale tenant through the same REST API the admin panel uses:
catalog, content pages, navigation, segments, dictionaries, mailings,
promotion triggers, redirects, and admin task triggers.

All write operations follow a **propose → review → apply** pattern: the
model first stages the change and returns a before/after diff for you to
read; nothing hits the backend until you say so.

---

## Installation

Requires Python 3.11+.

```bash
pip install git+https://github.com/qsale-io/qsale-mcp-server.git
```

Or with [uv](https://github.com/astral-sh/uv):

```bash
uvx --from git+https://github.com/qsale-io/qsale-mcp-server.git qsale-mcp
```

## Configuration

The server reads its configuration from environment variables — no flags,
no config files.

| Variable             | Required | Default                       | Purpose                                |
| -------------------- | -------- | ----------------------------- | -------------------------------------- |
| `QSALE_API_TOKEN`    | yes      | —                             | Employee API token                     |
| `QSALE_COMPANY_ID`   | yes      | —                             | Company UUID (tenant scope)            |
| `QSALE_API_BASE`     | no       | `https://console.qsale.io`    | Base URL of the QSale REST API         |
| `QSALE_CLIENT_TYPE`  | no       | `WEB`                         | Value of the `X-QA-Client-Type` header |

### Obtaining a token and a company id

1. Sign in to your QSale admin panel.
2. Open *Settings → API tokens* and create a new employee token. Save it
   somewhere safe — it is shown only once.
3. The company UUID is visible in the admin URL or under
   *Settings → Company*.

Self-hosted installations override `QSALE_API_BASE` to point at their own
console host (e.g. `https://console.example.com`).

### Wiring into Claude Code

Add to your `.mcp.json` (or the global Claude Code MCP config):

```json
{
  "mcpServers": {
    "qsale": {
      "command": "qsale-mcp",
      "env": {
        "QSALE_API_TOKEN": "your-token-here",
        "QSALE_COMPANY_ID": "00000000-0000-0000-0000-000000000000"
      }
    }
  }
}
```

For Claude Desktop, the configuration file lives at
`~/Library/Application Support/Claude/claude_desktop_config.json` (macOS)
or `%APPDATA%\Claude\claude_desktop_config.json` (Windows) with the same
`mcpServers` shape.

## Available tools

The server registers ~100 tools, grouped by domain. See the source files
or the model's `tools/list` output for the full list; below is the high
level shape.

### Read

Listing and detail tools for:

- Product categories, products
- Content pages
- Navigation groups and items
- URL redirects and redirect sites
- Mail templates and template images
- Promotion triggers and trigger categories
- Dictionaries and dictionary items
- Segments, segment properties, segment filters, segment property choices
- Frontend settings

### Write — propose / apply

Two-phase writes that stage the change in memory, return a diff, and only
hit the backend when `apply_*` is called. Cover:

- `propose/apply_page_update`
- `propose/apply_navigation_item_create + update`
- `propose/apply_category_create + delete`
- `propose/apply_mail_template_create + update`
- `propose/apply_promotion_trigger_create`
- `propose/apply_dictionary_create + delete`
- `propose/apply_dictionary_item_create + delete`
- `propose/apply_segment_create + delete`
- `propose/apply_segment_property_create + update + delete`
- `propose/apply_segment_property_choice_create + delete`
- `propose/apply_segment_filter_create + update + delete`
- `propose/apply_link_di_segment + unlink_di_segment`
- `propose/apply_link_pc_segment + unlink_pc_segment`

### Admin task triggers

Schedule asynchronous backend tasks via the admin task endpoints:

- `propose/apply_run_update_all_dicts`
- `propose/apply_run_update_dict`
- `propose/apply_run_set_category_for_products`

### Direct writes (no two-phase)

Idempotent or low-impact operations are exposed as single calls:

- `create_redirect`, `update_redirect`, `create_redirect_site`, `update_redirect_site`
- `update_category`
- `update_frontend_setting_json`, `set_frontend_setting_file`
- `create_mail_template_image`

### Batch

- `bulk_apply([proposal_ids])` — one approval covers N already-staged
  proposals of any kind. Stops on the first failure and returns
  per-proposal results.

## How writes work

```
propose_* ──► in-memory Proposal{ id, kind, fields, before }  (no HTTP write)
                       │
                       ▼
            you read the diff in chat
                       │
                       ▼
apply_*  ──► REST POST/PATCH/DELETE on console.qsale.io
```

Proposals live only in process memory — restarting the MCP server discards
them. This is intentional: a stale proposal should never be reused after
a code reload.

## Development

```bash
git clone https://github.com/qsale-io/qsale-mcp-server.git
cd qsale-mcp-server
python -m venv .venv && source .venv/bin/activate
pip install -e '.[dev]'
ruff check .
pytest
```

## Versioning

This project follows [Semantic Versioning](https://semver.org). See
[CHANGELOG.md](./CHANGELOG.md) for release notes.

## Security

Found a vulnerability? See [SECURITY.md](./SECURITY.md). Do not open a
public issue for security reports.

## License

Apache License 2.0 — see [LICENSE](./LICENSE).
