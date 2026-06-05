# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and this project adheres to [Semantic Versioning](https://semver.org).

## [Unreleased]

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
