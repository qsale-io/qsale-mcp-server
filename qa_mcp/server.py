"""MCP server entry: exposes qsale console REST API tools over stdio.

Launch:
  python -m qa_mcp.server

Required env:
  QSALE_API_TOKEN   employee token
  QSALE_COMPANY_ID  Company UUID (default: AIST)
"""
from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from . import tools as t
from .client import QsaleClient

srv = FastMCP('qa-catalog')

# Lazy singleton — only created when first tool is called.
_client: QsaleClient | None = None


def _c() -> QsaleClient:
    global _client
    if _client is None:
        _client = QsaleClient()
    return _client


@srv.tool()
def list_categories(
    parent_id: str | None = None,
    slug: str | None = None,
    limit: int = 500,
) -> list[dict[str, Any]]:
    """List ProductCategory rows from console.qsale.io.

    parent_id: filter by parent UUID. 'NULL' = root categories. None = no filter.
    slug: filter by exact slug.
    limit: max rows (default 500).
    """
    return t.list_categories(_c(), parent_id=parent_id, slug=slug, limit=limit)


@srv.tool()
def get_category(category_id: str) -> dict[str, Any]:
    """Get a single ProductCategory by UUID."""
    return t.get_category(_c(), category_id)


@srv.tool()
def update_category(category_id: str, fields: dict[str, Any]) -> dict[str, Any]:
    """PATCH a ProductCategory. Only whitelisted fields are accepted.

    Allowed fields: parent, slug, name, title, description, meta_title,
    meta_description, published, sort.

    To reparent to root: {"parent": null}.
    To move under another category: {"parent": "<uuid>"}.
    """
    return t.update_category(_c(), category_id, fields)


@srv.tool()
def list_redirect_sites() -> list[dict[str, Any]]:
    """List RedirectSite entries."""
    return t.list_redirect_sites(_c())


@srv.tool()
def list_redirects(
    site_id: str | None = None,
    url: str | None = None,
    limit: int = 500,
) -> list[dict[str, Any]]:
    """List UrlRedirect entries, optionally filtered by site/url."""
    return t.list_redirects(_c(), site_id=site_id, url=url, limit=limit)


@srv.tool()
def create_redirect(
    site_id: str,
    url: str,
    target_url: str,
    is_permanent: bool = True,
    priority: int = 0,
    is_template: bool = False,
    host: str | None = None,
    content_type: str | None = None,
) -> dict[str, Any]:
    """Create one UrlRedirect.

    site_id: RedirectSite UUID (get from list_redirect_sites).
    url:     source path with trailing slash, e.g. '/tours/europe/turkey/'.
    target_url: destination path with trailing slash.
    is_permanent: True → 301, False → 302.
    is_template: True → url uses {NAME}/{NAME*} placeholders (frontend
                 builds a regex and substitutes captured values in
                 target_url). False → exact-string match.
    host:        Restrict the rule to this hostname; None → applies to
                 all hosts registered for the company.
    content_type: Optional semantic hint (e.g. 'catalog.productcategory').
    """
    return t.create_redirect(
        _c(), site_id, url, target_url,
        is_permanent=is_permanent, priority=priority,
        is_template=is_template, host=host, content_type=content_type,
    )


@srv.tool()
def update_redirect(redirect_id: str, fields: dict[str, Any]) -> dict[str, Any]:
    """PATCH a UrlRedirect.

    Allowed fields: url, target_url, is_permanent, is_active, priority,
    is_template, host, content_type.
    """
    return t.update_redirect(_c(), redirect_id, fields)


@srv.tool()
def create_redirect_site(host: str, main_site: str | None = None, is_enabled: bool = True) -> dict[str, Any]:
    """Create one RedirectSite for the current tenant.

    host: fully-qualified hostname, no scheme/port (e.g. 'aist.travel').
    main_site: UUID of an existing root site to make this an alias of.
    is_enabled: defaults to True.
    """
    return t.create_redirect_site(_c(), host, main_site=main_site, is_enabled=is_enabled)


@srv.tool()
def update_redirect_site(site_id: str, fields: dict[str, Any]) -> dict[str, Any]:
    """PATCH a RedirectSite. Allowed fields: host, main_site, is_enabled."""
    return t.update_redirect_site(_c(), site_id, fields)


@srv.tool()
def list_pages(slug: str | None = None, limit: int = 500) -> list[dict[str, Any]]:
    """List Page rows (content pages like /mauritius/). Filter by `slug`."""
    return t.list_pages(_c(), slug=slug, limit=limit)


@srv.tool()
def get_page(page_id: str) -> dict[str, Any]:
    """Get full Page record by UUID, including body."""
    return t.get_page(_c(), page_id)


@srv.tool()
def propose_page_update(page_id: str, fields: dict[str, Any], reason: str = '') -> dict[str, Any]:
    """Stage a Page patch for explicit approval. Does NOT write.

    Returns proposal_id + per-field before/after diff. Show it to the user;
    after they OK, call apply_page_update(proposal_id).

    Allowed fields: meta_title, meta_description, meta_keywords,
    canonical_url, title, body.
    """
    return t.propose_page_update(_c(), page_id, fields, reason)


@srv.tool()
def apply_page_update(proposal_id: str) -> dict[str, Any]:
    """Apply a previously-staged page update. Use only after explicit user OK."""
    return t.apply_page_update(_c(), proposal_id)


@srv.tool()
def list_proposals(kind: str | None = None) -> list[dict[str, Any]]:
    """Inspect pending proposals in this MCP process. Lost on server restart."""
    return t.list_proposals(kind=kind)


def main() -> None:
    srv.run()


if __name__ == '__main__':
    main()
