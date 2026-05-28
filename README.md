# qsale-mcp-server

MCP tool server bridging Claude Code / AI agents to the [qsale console REST API](https://console.qsale.io).

## Setup

```bash
pip install -e .
```

Required env vars:

| Variable | Description | Default |
|---|---|---|
| `QSALE_API_TOKEN` | Employee API token | — (required) |
| `QSALE_COMPANY_ID` | Company UUID | AIST (`6d6d8a2b-...`) |
| `QSALE_API_BASE` | qa-server base URL | `https://console.qsale.io` |
| `QSALE_CLIENT_TYPE` | Client type header | `WEB` |

## Launch

```bash
python -m qa_mcp.server
```

Or via `mcp` CLI in your Claude Desktop config:

```json
{
  "mcpServers": {
    "qa-catalog": {
      "command": "python",
      "args": ["-m", "qa_mcp.server"],
      "env": {
        "QSALE_API_TOKEN": "your-token",
        "QSALE_COMPANY_ID": "your-company-uuid"
      }
    }
  }
}
```

## Architecture

All writes go through an **in-memory propose/apply flow**:

1. `propose_*()` — validates input, fetches current state for diff, registers an in-memory `Proposal`, returns `proposal_id` + human-readable before/after.
2. Human reviews the diff and says OK.
3. `apply_*()` — consumes the proposal (single-use), executes the REST call.

Proposals are lost on server restart by design (short-lived, no persistence needed).

## Tool catalogue

### Categories & ProductCategory

| Tool | Description |
|---|---|
| `list_categories` | List ProductCategory rows. Filter by `parent_id` or `slug`. |
| `get_category` | Get a single category by UUID. |
| `update_category` | PATCH a category (whitelisted fields: parent, slug, name, title, description, meta_title, meta_description, published, sort). |
| `propose_category_create` | Stage a new category (name + slug required). |
| `apply_category_create` | Apply staged category creation. |

### Dictionaries

| Tool | Description |
|---|---|
| `list_dictionaries` | List Dictionary rows for the tenant. |
| `get_dictionary` | Get a single Dictionary by UUID (incl. `allowed_segment_models`). |
| `list_dictionary_items` | List DictionaryItems. Filter by `dictionary_id` and/or `search`. |
| `get_dictionary_item` | Get a single DictionaryItem by UUID. |
| `propose_dictionary_item_create` | Stage a new DictionaryItem (`dictionary`, `name` required; `data` for Sletat IDs etc.). |
| `apply_dictionary_item_create` | Apply staged DictionaryItem creation. |
| `propose_dictionary_item_delete` | Stage a DictionaryItem deletion (shows name + dictionary as before-state). |
| `apply_dictionary_item_delete` | Apply staged deletion. |

### Segments

| Tool | Description |
|---|---|
| `list_segments` | List Segments. Filter by `model_id` and/or `search`. |
| `get_segment` | Get a single Segment by UUID. |
| `propose_segment_create` | Stage a new Segment (`model_id`, `name`). |
| `apply_segment_create` | Apply staged Segment creation. |
| `propose_segment_delete` | Stage a Segment deletion (shows name + filter count warning). |
| `apply_segment_delete` | Apply staged deletion. |

### SegmentProperties & SegmentFilters

| Tool | Description |
|---|---|
| `list_segment_properties` | List SegmentProperties. Filter by `model_id`. Use to find valid property UUIDs and allowed operators. |
| `get_segment_property` | Get a single SegmentProperty by UUID. |
| `list_segment_filters` | List SegmentFilters. Filter by `segment_id`. |
| `get_segment_filter` | Get a single SegmentFilter by UUID. |
| `propose_segment_filter_create` | Stage a new filter (`segment`, `property`, `operator`, `value` required). |
| `apply_segment_filter_create` | Apply staged filter creation. |
| `propose_segment_filter_update` | Stage a filter `value` update (fetches current value for before/after diff). |
| `apply_segment_filter_update` | Apply staged filter update. |
| `propose_segment_filter_delete` | Stage a filter deletion (shows segment/property/operator/value as before-state). |
| `apply_segment_filter_delete` | Apply staged deletion. |

### M2M Links — DictionaryItem ↔ Segment

| Tool | Description |
|---|---|
| `list_di_segments` | List Segments linked to a DictionaryItem. |
| `propose_link_di_segment` | Stage a link (server validates model compatibility). |
| `apply_link_di_segment` | Apply: POST `.../segments/` → 201 linked / 200 already_linked. |
| `propose_unlink_di_segment` | Stage an unlink (shows current links as before-state). |
| `apply_unlink_di_segment` | Apply: DELETE `.../segments/{segment_id}/` → 204. |

### M2M Links — ProductCategory ↔ Segment

| Tool | Description |
|---|---|
| `list_pc_segments` | List Segments linked to a ProductCategory. |
| `propose_link_pc_segment` | Stage a link. |
| `apply_link_pc_segment` | Apply: POST `.../segments/` → 201 linked / 200 already_linked. |
| `propose_unlink_pc_segment` | Stage an unlink (shows current links as before-state). |
| `apply_unlink_pc_segment` | Apply: DELETE `.../segments/{segment_id}/` → 204. |

### Task Triggers (Celery)

| Tool | Description |
|---|---|
| `propose_run_update_all_dicts` | Stage an `update_all_dicts` task enqueue (Singleton — self-deduplicates). |
| `apply_run_update_all_dicts` | Apply: POST `/api/tasks/update-all-dicts/` → 202 queued. |
| `propose_run_set_category_for_products` | Stage a `set_category_for_products` task for a specific category. |
| `apply_run_set_category_for_products` | Apply: POST `/api/tasks/set-category-for-products/` → 202 queued. |

### Redirects

| Tool | Description |
|---|---|
| `list_redirect_sites` | List RedirectSite entries. |
| `create_redirect_site` | Create a RedirectSite. |
| `update_redirect_site` | PATCH a RedirectSite. |
| `list_redirects` | List UrlRedirects. Filter by `site_id` / `url`. |
| `create_redirect` | Create a UrlRedirect. |
| `update_redirect` | PATCH a UrlRedirect. |

### Pages

| Tool | Description |
|---|---|
| `list_pages` | List Pages (SEO landing pages). Filter by `slug`. |
| `get_page` | Get full Page record by UUID. |
| `propose_page_update` | Stage a Page PATCH (meta_title, meta_description, meta_keywords, canonical_url, title, body). |
| `apply_page_update` | Apply staged Page update. |

### Navigation

| Tool | Description |
|---|---|
| `list_navigation_groups` | List NavigationGroup containers (header, footer, …). |
| `list_navigation_items` | List NavigationItems. Filter by group, parent, type. |
| `get_navigation_item` | Get a single NavigationItem. |
| `propose_navigation_item_create` | Stage a new NavigationItem. |
| `apply_navigation_item_create` | Apply staged creation. |
| `propose_navigation_item_update` | Stage a NavigationItem PATCH. |
| `apply_navigation_item_update` | Apply staged update. |

### Mail Templates

| Tool | Description |
|---|---|
| `list_mail_templates` | List MailTemplates (compact; bodies shown as char counts). |
| `get_mail_template` | Get full MailTemplate by UUID. |
| `propose_mail_template_create` | Stage a new MailTemplate. |
| `apply_mail_template_create` | Apply staged creation. |
| `propose_mail_template_update` | Stage a MailTemplate PATCH. |
| `apply_mail_template_update` | Apply staged update. |
| `list_mail_template_images` | List MailTemplateImages. |
| `create_mail_template_image` | Attach an image to a MailTemplate (base64 or local file). |

### Promotion Triggers

| Tool | Description |
|---|---|
| `list_trigger_categories` | List promotion-trigger categories and their configurable field names. |
| `list_promotion_triggers` | List PromotionTriggers. Filter by promotion, category. |
| `get_promotion_trigger` | Get a single PromotionTrigger. |
| `propose_promotion_trigger_create` | Stage a new PromotionTrigger. |
| `apply_promotion_trigger_create` | Apply staged creation. |

### Frontend Settings

| Tool | Description |
|---|---|
| `list_frontend_settings` | List all frontend settings (group, key, type, value). |
| `get_frontend_setting` | Get one setting by key (incl. schema). |
| `update_frontend_setting_json` | Update a json-typed setting. Direct write — get user OK first. |
| `set_frontend_setting_file` | Upload a file-typed setting (logo, etc.). Direct write — get user OK first. |

### Proposal Management

| Tool | Description |
|---|---|
| `list_proposals` | Inspect pending proposals (lost on server restart). Filter by `kind`. |

## Turkey Resort Batch — worked example

Creating one resort entry (e.g. "Kemer") with full segment linkage:

```
1. get_dictionary(sletat_dict_id)
2. propose_dictionary_item_create({dictionary: ..., name: "Kemer", data: {sletat_id: 12345}}) → apply
3. propose_segment_create(product_model_id, "ResortId — Kemer A") → apply
4. propose_segment_filter_create({segment: seg_a_id, property: resortid_prop_id, operator: "IN", value: [12345]}) → apply
5. propose_link_di_segment(di_id, seg_a_id) → apply
6. propose_segment_create(product_model_id, "ResortId — Kemer B") → apply
7. propose_segment_filter_create({segment: seg_b_id, property: resortid_prop_id, operator: "IN", value: [12345]}) → apply
8. propose_category_create({parent: turkey_cat_id, name: "Кемер", slug: "kemer"}) → apply
9. propose_link_pc_segment(cat_id, seg_b_id) → apply

After all 58 resorts:
10. propose_run_update_all_dicts() → apply
11. propose_run_set_category_for_products(turkey_parent_id) → apply
```

## Notes

- **Multitenancy:** every REST call carries `X-QA-Company` header (from `QSALE_COMPANY_ID`). Cross-tenant access returns 404.
- **Errors:** HTTP 4xx/5xx from qa-server are returned as `"HTTP {status}: {body[:500]}"` — never swallowed.
- **New endpoints** (`list_segment_filters`, `get_segment_filter`, PC↔Segment m2m, DI↔Segment m2m, task triggers) require qa-server branch `feat/qsale-24-mcp-catalog-api` (MR !515) to be deployed.
- **No tests** in this repo (pure thin HTTP proxy; integration-tested via qa-server's 32-test suite in MR !515).
