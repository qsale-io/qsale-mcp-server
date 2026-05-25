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
def list_navigation_groups(slug: str | None = None, limit: int = 500) -> list[dict[str, Any]]:
    """List NavigationGroup menu containers (header, footer, bottom-bar, …).

    Filter by `slug`. Returns id, slug, name, client_types, sort, employee_roles.
    """
    return t.list_navigation_groups(_c(), slug=slug, limit=limit)


@srv.tool()
def list_navigation_items(
    group: str | None = None,
    parent: str | None = None,
    parent_isnull: bool | None = None,
    type: str | None = None,
    limit: int = 500,
) -> list[dict[str, Any]]:
    """List NavigationItem menu entries (compact view).

    Filters:
      group:        NavigationGroup UUID (get from list_navigation_groups).
      parent:       parent NavigationItem UUID (children of a submenu).
      parent_isnull: True → only top-level items; False → only nested.
      type:         one of LINK, PAGE, PRODUCT, PRODUCT_CATEGORY, PROMOTION,
                    LANDING, OUTLET, BANNER_GROUP, SCREEN, SEPARATOR, WEBVIEW.

    `value` semantics: for content types (PAGE/PRODUCT/PRODUCT_CATEGORY/
    PROMOTION/SCREEN/OUTLET) it is the UUID of the referenced object. LINK is
    only for external URLs; SEPARATOR has no value.
    """
    return t.list_navigation_items(
        _c(), group=group, parent=parent, parent_isnull=parent_isnull, type=type, limit=limit
    )


@srv.tool()
def get_navigation_item(item_id: str) -> dict[str, Any]:
    """Get a single NavigationItem by UUID (full record incl. display_settings)."""
    return t.get_navigation_item(_c(), item_id)


@srv.tool()
def propose_navigation_item_update(item_id: str, fields: dict[str, Any], reason: str = '') -> dict[str, Any]:
    """Stage a NavigationItem patch for explicit approval. Does NOT write.

    Returns proposal_id + per-field before/after diff. After the user OKs,
    call apply_navigation_item_update(proposal_id).

    Allowed fields: name, group, parent, type, value, published, sort,
    is_template, display_settings. To turn a broken LINK section-header into a
    non-clickable separator: {"type": "SEPARATOR", "value": ""}.
    """
    return t.propose_navigation_item_update(_c(), item_id, fields, reason)


@srv.tool()
def apply_navigation_item_update(proposal_id: str) -> dict[str, Any]:
    """Apply a previously-staged NavigationItem update. Use only after explicit user OK."""
    return t.apply_navigation_item_update(_c(), proposal_id)


@srv.tool()
def propose_navigation_item_create(fields: dict[str, Any], reason: str = '') -> dict[str, Any]:
    """Stage a NavigationItem creation for explicit approval. Does NOT write.

    Required fields: name, group (NavigationGroup UUID), type. For content
    types (PAGE/PRODUCT/PRODUCT_CATEGORY/PROMOTION/SCREEN/OUTLET) pass
    value=<target object UUID>; for LINK pass value=<external URL>. Optional:
    parent (UUID to nest), published, sort, is_template, display_settings.

    After the user OKs, call apply_navigation_item_create(proposal_id).
    """
    return t.propose_navigation_item_create(_c(), fields, reason)


@srv.tool()
def apply_navigation_item_create(proposal_id: str) -> dict[str, Any]:
    """Apply a previously-staged NavigationItem creation. Use only after explicit user OK."""
    return t.apply_navigation_item_create(_c(), proposal_id)


@srv.tool()
def list_mail_templates(
    category: str | None = None,
    promotion: str | None = None,
    promotion_isnull: bool | None = None,
    limit: int = 200,
) -> list[dict[str, Any]]:
    """List MailTemplate rows (compact: bodies shown as lengths, not content).

    Filters:
      category:        SYSTEM / TRANSACTIONAL / PROMOTIONAL / PERSONAL / CUSTOM.
      promotion:       Promotion UUID — templates bound to that promotion.
      promotion_isnull: True → only templates NOT bound to any promotion.
    """
    return t.list_mail_templates(
        _c(), category=category, promotion=promotion, promotion_isnull=promotion_isnull, limit=limit
    )


@srv.tool()
def get_mail_template(template_id: str) -> dict[str, Any]:
    """Get a full MailTemplate by UUID (subject, text, html, context, images)."""
    return t.get_mail_template(_c(), template_id)


@srv.tool()
def propose_mail_template_create(fields: dict[str, Any], reason: str = '') -> dict[str, Any]:
    """Stage a MailTemplate creation for explicit approval. Does NOT write.

    Required fields: name, category, subject, text. Optional: html, context
    (dict of template-level overrides), promotion (UUID — enables PROMOTION_NAME/
    PROMOTION_SINCE/PROMOTION_UNTIL and the trigger-supplied promo_code var).
    Categories: SYSTEM, TRANSACTIONAL, PROMOTIONAL, PERSONAL, CUSTOM.

    Returns proposal_id + a summary (html/text shown as char counts). After the
    user OKs, call apply_mail_template_create(proposal_id). Company is set by the
    API from the auth header.
    """
    return t.propose_mail_template_create(_c(), fields, reason)


@srv.tool()
def apply_mail_template_create(proposal_id: str) -> dict[str, Any]:
    """Apply a previously-staged MailTemplate creation. Use only after explicit user OK."""
    return t.apply_mail_template_create(_c(), proposal_id)


@srv.tool()
def list_mail_template_images(template: str | None = None, limit: int = 200) -> list[dict[str, Any]]:
    """List MailTemplateImage rows. Filter by template UUID. Server-side
    template-less rows are company-wide shared images (exposed as IMAGES_COMMON).
    """
    return t.list_mail_template_images(_c(), template=template, limit=limit)


@srv.tool()
def create_mail_template_image(
    template: str,
    slug: str,
    image_path: str | None = None,
    base64_data: str | None = None,
) -> dict[str, Any]:
    """Attach an image to a MailTemplate. Reference it in the body via {{ IMAGES.<slug> }}.

    template: MailTemplate UUID. slug: short identifier, unique per template.
    Provide exactly one of:
      image_path:  path to a local file (read + base64-encoded here), or
      base64_data: raw base64 or a full 'data:image/...;base64,...' URI.
    Accepted types: JPEG, PNG, GIF, WEBP. Direct create (no propose/apply) —
    narrate intent and get the user's OK before calling.
    """
    return t.create_mail_template_image(_c(), template, slug, image_path=image_path, base64_data=base64_data)


@srv.tool()
def list_proposals(kind: str | None = None) -> list[dict[str, Any]]:
    """Inspect pending proposals in this MCP process. Lost on server restart."""
    return t.list_proposals(kind=kind)


def main() -> None:
    srv.run()


if __name__ == '__main__':
    main()
