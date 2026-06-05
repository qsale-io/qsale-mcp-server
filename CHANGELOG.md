# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and this project adheres to [Semantic Versioning](https://semver.org).

## [Unreleased]

### Added

- `propose / apply_promotion_prolong` — extends an active promotion's
  `active_until` date. Backed by `POST /api/promotions/<id>/prolong/`.
  Backend rejects with 400 if the promotion is not in the ACTIVE state or
  has no finite end date; the validation message is proxied verbatim.

## [0.2.0] - 2026-06-05

### Added

- `list_promotions`, `get_promotion` — read access to Promotion entities
  with filters by state, type, published flag, name.
- `propose / apply_promotion_create`, `propose / apply_promotion_update`
  — two-phase write for Promotion. Whitelist validation on input
  fields and on the `type` value (BONUS_AMOUNT, BONUS_PERCENT, AMOUNT,
  PERCENT, GIFT, INFO).
- `list_promotion_codes`, `get_promotion_code` — read access to
  PromotionCode entries with filter by parent promotion, usage state,
  or exact code value.

## [0.1.0] - 2026-06-05

Initial public release.

### Added

- MCP server entry point at `qa_mcp.server` exposing the QSale REST API
  over stdio.
- Read tools for product categories, products, content pages, navigation,
  redirects, mail templates, promotion triggers, dictionaries, segments,
  segment properties, segment filters, segment property choices, and
  frontend settings.
- Propose / apply write tools (two-phase) for pages, navigation items,
  categories, mail templates, promotion triggers, dictionaries,
  dictionary items, segments, segment properties, segment property
  choices, segment filters, and dictionary-item / product-category
  segment links.
- Admin task triggers: `run_update_all_dicts`, `run_update_dict`,
  `run_set_category_for_products`.
- `bulk_apply` — single approval over N already-staged proposals.
- Configuration entirely via environment variables.
