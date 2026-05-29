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
def propose_mail_template_update(template_id: str, fields: dict[str, Any], reason: str = '') -> dict[str, Any]:
    """Stage a MailTemplate PATCH for explicit approval. Does NOT write.

    Editable fields: name, category, promotion, subject, text, html, context.
    Partial — only the keys you pass are changed; omit the rest. Use this to fix
    CTA links, swap logo vars, etc. in existing templates without re-creating them.

    Returns proposal_id + a diff (html/text shown as char counts). After the user
    OKs, call apply_mail_template_update(proposal_id).
    """
    return t.propose_mail_template_update(_c(), template_id, fields, reason)


@srv.tool()
def apply_mail_template_update(proposal_id: str) -> dict[str, Any]:
    """Apply a previously-staged MailTemplate update. Use only after explicit user OK."""
    return t.apply_mail_template_update(_c(), proposal_id)


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
def list_trigger_categories() -> list[dict[str, Any]]:
    """List promotion-trigger categories and their configurable field names
    (from /api/triggers/). Use to discover valid `category` + `values` keys.
    """
    return t.list_trigger_categories(_c())


@srv.tool()
def list_promotion_triggers(
    promotion: str | None = None,
    promotion_isnull: bool | None = None,
    category: str | None = None,
    limit: int = 200,
) -> list[dict[str, Any]]:
    """List PromotionTrigger rows (compact). Filter by promotion UUID,
    promotion_isnull (True → triggers not bound to a promotion), or category.
    """
    return t.list_promotion_triggers(
        _c(), promotion=promotion, promotion_isnull=promotion_isnull, category=category, limit=limit
    )


@srv.tool()
def get_promotion_trigger(trigger_id: str) -> dict[str, Any]:
    """Get a single PromotionTrigger by UUID (full record incl. values + templates)."""
    return t.get_promotion_trigger(_c(), trigger_id)


@srv.tool()
def propose_promotion_trigger_create(fields: dict[str, Any], reason: str = '') -> dict[str, Any]:
    """Stage a PromotionTrigger creation for explicit approval. Does NOT write.

    Required: category, values (dict matching the category's fields — see
    list_trigger_categories; omitted keys fall back to server defaults).
    Optional: name, promotion (UUID), mail_template/sms_template/push_template
    (UUIDs). Pass values={'enabled': False, ...} to create dormant. The API
    rejects a duplicate (promotion, category). After the user OKs, call
    apply_promotion_trigger_create(proposal_id).
    """
    return t.propose_promotion_trigger_create(_c(), fields, reason)


@srv.tool()
def apply_promotion_trigger_create(proposal_id: str) -> dict[str, Any]:
    """Apply a previously-staged PromotionTrigger creation. Use only after explicit user OK."""
    return t.apply_promotion_trigger_create(_c(), proposal_id)


@srv.tool()
def list_frontend_settings() -> list[dict[str, Any]]:
    """List company frontend settings (flattened: group, key, type, name, value).
    Use the returned `key` with get_frontend_setting / update_frontend_setting_json /
    set_frontend_setting_file.
    """
    return t.list_frontend_settings(_c())


@srv.tool()
def get_frontend_setting(key: str) -> dict[str, Any]:
    """Get one frontend setting by key (incl. setting_type, schema, current value)."""
    return t.get_frontend_setting(_c(), key)


@srv.tool()
def update_frontend_setting_json(key: str, value: Any) -> dict[str, Any]:
    """Update a json-typed frontend setting. Server validates `value` against the
    setting's JSON schema. Use only after explicit user OK — writes immediately.
    """
    return t.update_frontend_setting_json(_c(), key, value)


@srv.tool()
def set_frontend_setting_file(key: str, file_path: str) -> dict[str, Any]:
    """Replace a file-typed frontend setting (e.g. logo_for_emails) by uploading a
    local file (multipart). Use only after explicit user OK — writes immediately.
    """
    return t.set_frontend_setting_file(_c(), key, file_path)


@srv.tool()
def list_proposals(kind: str | None = None) -> list[dict[str, Any]]:
    """Inspect pending proposals in this MCP process. Lost on server restart."""
    return t.list_proposals(kind=kind)


# ---------------------------------------------------------------------------
# §FR-1 Read tools — Dictionaries
# ---------------------------------------------------------------------------

@srv.tool()
def list_dictionaries(limit: int = 200) -> list[dict[str, Any]]:
    """List Dictionary rows for the current tenant."""
    return t.list_dictionaries(_c(), limit=limit)


@srv.tool()
def get_dictionary(dictionary_id: str) -> dict[str, Any]:
    """Get a single Dictionary by UUID (incl. allowed_segment_models)."""
    return t.get_dictionary(_c(), dictionary_id)


@srv.tool()
def list_dictionary_items(
    dictionary_id: str | None = None,
    search: str | None = None,
    limit: int = 200,
) -> list[dict[str, Any]]:
    """List DictionaryItem rows (compact). Filter by dictionary UUID and/or search.

    dictionary_id: restrict to items belonging to this dictionary.
    search: substring match on item name.
    """
    return t.list_dictionary_items(_c(), dictionary_id=dictionary_id, search=search, limit=limit)


@srv.tool()
def get_dictionary_item(item_id: str) -> dict[str, Any]:
    """Get a single DictionaryItem by UUID (full record incl. data, segments)."""
    return t.get_dictionary_item(_c(), item_id)


# ---------------------------------------------------------------------------
# §FR-1 Read tools — Segments
# ---------------------------------------------------------------------------

@srv.tool()
def list_segments(
    model_id: str | None = None,
    search: str | None = None,
    limit: int = 500,
) -> list[dict[str, Any]]:
    """List Segment rows (compact). Filter by model UUID and/or search string.

    model_id: SegmentModel UUID (get from list_segment_properties).
    search: substring match on segment name.
    """
    return t.list_segments(_c(), model_id=model_id, search=search, limit=limit)


@srv.tool()
def get_segment(segment_id: str) -> dict[str, Any]:
    """Get a single Segment by UUID (full record incl. filters, count)."""
    return t.get_segment(_c(), segment_id)


@srv.tool()
def list_segment_properties(model_id: str | None = None, limit: int = 500) -> list[dict[str, Any]]:
    """List SegmentProperty rows. Filter by model UUID.

    Use to discover valid property UUIDs and their allowed operator types
    before calling propose_segment_filter_create.
    """
    return t.list_segment_properties(_c(), model_id=model_id, limit=limit)


@srv.tool()
def get_segment_property(property_id: str) -> dict[str, Any]:
    """Get a single SegmentProperty by UUID (incl. allowed operators)."""
    return t.get_segment_property(_c(), property_id)


@srv.tool()
def list_segment_filters(segment_id: str | None = None) -> list[dict[str, Any]]:
    """List SegmentFilter rows. Filter by segment UUID.

    Uses the NEW GET /api/segment-filters/ endpoint on qa-server (branch
    feat/qsale-24-mcp-catalog-api). Each filter shows: id, segment, property,
    operator, value, count, data, exclude.
    """
    return t.list_segment_filters(_c(), segment_id=segment_id)


@srv.tool()
def get_segment_filter(filter_id: str) -> dict[str, Any]:
    """Get a single SegmentFilter by UUID.

    Uses the NEW GET /api/segment-filters/{id}/ endpoint on qa-server.
    """
    return t.get_segment_filter(_c(), filter_id)


# ---------------------------------------------------------------------------
# §FR-1 Read tools — M2M list views (NEW endpoints)
# ---------------------------------------------------------------------------

@srv.tool()
def list_pc_segments(category_id: str) -> list[dict[str, Any]]:
    """List Segments linked to a ProductCategory.

    Uses the NEW GET /api/product-categories/{id}/segments/ endpoint.
    Each row: {id, model, name, count}.
    """
    return t.list_pc_segments(_c(), category_id)


@srv.tool()
def list_di_segments(dictionary_item_id: str) -> list[dict[str, Any]]:
    """List Segments linked to a DictionaryItem.

    Uses the NEW GET /api/dictionary-items/{id}/segments/ endpoint.
    Each row: {id, model, name, count}.
    """
    return t.list_di_segments(_c(), dictionary_item_id)


# ---------------------------------------------------------------------------
# §FR-2 Category write tools (propose/apply)
# ---------------------------------------------------------------------------

@srv.tool()
def propose_category_create(fields: dict[str, Any], reason: str = '') -> dict[str, Any]:
    """Stage a ProductCategory creation for explicit approval. Does NOT write.

    Required fields: name, slug. Optional: parent (UUID — nest under an existing
    category; null for root), title, description, meta_title, meta_description,
    group (ProductCategoryGroup UUID). Company is set by the API from the auth
    header. Returns proposal_id + after-state summary. After the user OKs, call
    apply_category_create(proposal_id).
    """
    return t.propose_category_create(_c(), fields, reason)


@srv.tool()
def apply_category_create(proposal_id: str) -> dict[str, Any]:
    """Apply a previously-staged ProductCategory creation. Use only after explicit user OK."""
    return t.apply_category_create(_c(), proposal_id)


# ---------------------------------------------------------------------------
# §FR-2 DictionaryItem write tools (propose/apply)
# ---------------------------------------------------------------------------

@srv.tool()
def propose_dictionary_item_create(fields: dict[str, Any], reason: str = '') -> dict[str, Any]:
    """Stage a DictionaryItem creation for explicit approval. Does NOT write.

    Required fields: dictionary (UUID), name. Optional: data (dict — e.g.
    {\"sletat_id\": 12345}), description, sort (int, default 0). Company inherited
    from the dictionary. Returns proposal_id + after-state summary. After the
    user OKs, call apply_dictionary_item_create(proposal_id).
    """
    return t.propose_dictionary_item_create(_c(), fields, reason)


@srv.tool()
def apply_dictionary_item_create(proposal_id: str) -> dict[str, Any]:
    """Apply a previously-staged DictionaryItem creation. Use only after explicit user OK."""
    return t.apply_dictionary_item_create(_c(), proposal_id)


@srv.tool()
def propose_dictionary_item_delete(item_id: str, reason: str = '') -> dict[str, Any]:
    """Stage a DictionaryItem deletion for explicit approval. Does NOT write.

    Fetches current state (name + dictionary) for a before-state diff. API 400
    (item in use / protected FK) is proxied when apply is called. After the user
    OKs, call apply_dictionary_item_delete(proposal_id).
    """
    return t.propose_dictionary_item_delete(_c(), item_id, reason)


@srv.tool()
def apply_dictionary_item_delete(proposal_id: str) -> dict[str, Any] | None:
    """Apply a previously-staged DictionaryItem deletion. Use only after explicit user OK."""
    return t.apply_dictionary_item_delete(_c(), proposal_id)


# ---------------------------------------------------------------------------
# §FR-3 Segment write tools (propose/apply)
# ---------------------------------------------------------------------------

@srv.tool()
def propose_segment_create(
    model_id: str,
    name: str,
    filters: list[dict[str, Any]] | None = None,
    reason: str = '',
) -> dict[str, Any]:
    """Stage a Segment creation for explicit approval. Does NOT write.

    model_id: SegmentModel UUID (e.g. the product segment model — get from
    list_segment_properties). name: human-readable label.
    filters: inline SegmentFilter dicts (qa-server requires at least one).
    Each: {property: UUID, operator: 'in'|..., value: list|scalar, exclude?: bool}.
    After the user OKs, call apply_segment_create(proposal_id).
    """
    return t.propose_segment_create(_c(), model_id, name, filters, reason)


@srv.tool()
def apply_segment_create(proposal_id: str) -> dict[str, Any]:
    """Apply a previously-staged Segment creation. Use only after explicit user OK."""
    return t.apply_segment_create(_c(), proposal_id)


@srv.tool()
def propose_segment_delete(segment_id: str, reason: str = '') -> dict[str, Any]:
    """Stage a Segment deletion for explicit approval. Does NOT write.

    Fetches the segment (name + filter count) and shows a warning. API 400
    (segment not deletable) is proxied when apply is called. After the user OKs,
    call apply_segment_delete(proposal_id).
    """
    return t.propose_segment_delete(_c(), segment_id, reason)


@srv.tool()
def apply_segment_delete(proposal_id: str) -> dict[str, Any] | None:
    """Apply a previously-staged Segment deletion. Use only after explicit user OK."""
    return t.apply_segment_delete(_c(), proposal_id)


# ---------------------------------------------------------------------------
# §FR-3 SegmentFilter write tools (propose/apply)
# ---------------------------------------------------------------------------

@srv.tool()
def propose_segment_filter_create(fields: dict[str, Any], reason: str = '') -> dict[str, Any]:
    """Stage a SegmentFilter creation for explicit approval. Does NOT write.

    Required fields: segment (UUID), property (UUID), operator (IN/NOT_IN/EQ/
    GTE/LTE/…), value (list for IN/NOT_IN, scalar for others). Optional: exclude
    (bool, default False), data (dict). Use get_segment_property to check allowed
    operators for the property type. Server validates compatibility; 400 proxied.
    After the user OKs, call apply_segment_filter_create(proposal_id).
    """
    return t.propose_segment_filter_create(_c(), fields, reason)


@srv.tool()
def apply_segment_filter_create(proposal_id: str) -> dict[str, Any]:
    """Apply a previously-staged SegmentFilter creation. Use only after explicit user OK."""
    return t.apply_segment_filter_create(_c(), proposal_id)


@srv.tool()
def propose_segment_filter_update(filter_id: str, value: Any, reason: str = '') -> dict[str, Any]:
    """Stage a SegmentFilter value update for explicit approval. Does NOT write.

    Fetches the current filter (via NEW endpoint) to build a before/after diff.
    `value`: list for IN/NOT_IN operators (e.g. [12345, 67890] for Sletat resort
    IDs), scalar for EQ/GTE/LTE. After the user OKs, call
    apply_segment_filter_update(proposal_id).
    """
    return t.propose_segment_filter_update(_c(), filter_id, value, reason)


@srv.tool()
def apply_segment_filter_update(proposal_id: str) -> dict[str, Any]:
    """Apply a previously-staged SegmentFilter update. Use only after explicit user OK."""
    return t.apply_segment_filter_update(_c(), proposal_id)


@srv.tool()
def propose_segment_filter_delete(filter_id: str, reason: str = '') -> dict[str, Any]:
    """Stage a SegmentFilter deletion for explicit approval. Does NOT write.

    Fetches current filter state for the before-state diff. After the user OKs,
    call apply_segment_filter_delete(proposal_id).
    """
    return t.propose_segment_filter_delete(_c(), filter_id, reason)


@srv.tool()
def apply_segment_filter_delete(proposal_id: str) -> dict[str, Any] | None:
    """Apply a previously-staged SegmentFilter deletion. Use only after explicit user OK."""
    return t.apply_segment_filter_delete(_c(), proposal_id)


# ---------------------------------------------------------------------------
# §FR-4 M2M link/unlink tools — DictionaryItem ↔ Segment
# ---------------------------------------------------------------------------

@srv.tool()
def propose_link_di_segment(
    dictionary_item_id: str,
    segment_id: str,
    reason: str = '',
) -> dict[str, Any]:
    """Stage a DictionaryItem ↔ Segment link for explicit approval. Does NOT write.

    Server validates that segment.model is in dictionary.allowed_segment_models;
    400 proxied. After the user OKs, call apply_link_di_segment(proposal_id).
    """
    return t.propose_link_di_segment(_c(), dictionary_item_id, segment_id, reason)


@srv.tool()
def apply_link_di_segment(proposal_id: str) -> dict[str, Any]:
    """Apply a previously-staged DI↔Segment link. Use only after explicit user OK.

    Returns 201 {status: 'linked'} on success, 200 {status: 'already_linked'} if
    the link already exists (ADR-2).
    """
    return t.apply_link_di_segment(_c(), proposal_id)


@srv.tool()
def propose_unlink_di_segment(
    dictionary_item_id: str,
    segment_id: str,
    reason: str = '',
) -> dict[str, Any]:
    """Stage a DictionaryItem ↔ Segment unlink for explicit approval. Does NOT write.

    Fetches current linked segments to confirm the link exists (before-state diff).
    After the user OKs, call apply_unlink_di_segment(proposal_id).
    """
    return t.propose_unlink_di_segment(_c(), dictionary_item_id, segment_id, reason)


@srv.tool()
def apply_unlink_di_segment(proposal_id: str) -> dict[str, Any] | None:
    """Apply a previously-staged DI↔Segment unlink. Use only after explicit user OK. 204 on success."""
    return t.apply_unlink_di_segment(_c(), proposal_id)


# ---------------------------------------------------------------------------
# §FR-4 M2M link/unlink tools — ProductCategory ↔ Segment
# ---------------------------------------------------------------------------

@srv.tool()
def propose_link_pc_segment(
    category_id: str,
    segment_id: str,
    reason: str = '',
) -> dict[str, Any]:
    """Stage a ProductCategory ↔ Segment link for explicit approval. Does NOT write.

    qa-server calls category.set_cache() explicitly after the link (no m2m_changed
    signal for ProductCategory.products). After the user OKs, call
    apply_link_pc_segment(proposal_id).
    """
    return t.propose_link_pc_segment(_c(), category_id, segment_id, reason)


@srv.tool()
def apply_link_pc_segment(proposal_id: str) -> dict[str, Any]:
    """Apply a previously-staged PC↔Segment link. Use only after explicit user OK.

    Returns 201 {status: 'linked'} on success, 200 {status: 'already_linked'} if
    the link already exists (ADR-2).
    """
    return t.apply_link_pc_segment(_c(), proposal_id)


@srv.tool()
def propose_unlink_pc_segment(
    category_id: str,
    segment_id: str,
    reason: str = '',
) -> dict[str, Any]:
    """Stage a ProductCategory ↔ Segment unlink for explicit approval. Does NOT write.

    Fetches current linked segments for the before-state diff. After the user OKs,
    call apply_unlink_pc_segment(proposal_id).
    """
    return t.propose_unlink_pc_segment(_c(), category_id, segment_id, reason)


@srv.tool()
def apply_unlink_pc_segment(proposal_id: str) -> dict[str, Any] | None:
    """Apply a previously-staged PC↔Segment unlink. Use only after explicit user OK. 204 on success."""
    return t.apply_unlink_pc_segment(_c(), proposal_id)


# ---------------------------------------------------------------------------
# §FR-5 Task trigger tools (propose/apply)
# ---------------------------------------------------------------------------

@srv.tool()
def propose_run_update_all_dicts(reason: str = '') -> dict[str, Any]:
    """Stage an update_all_dicts Celery task trigger for explicit approval. Does NOT enqueue.

    Recalculates cache for all dictionaries belonging to the current company.
    The task is a Celery Singleton — self-deduplicates if already running. 202
    fire-and-forget (not a sync result). After the user OKs, call
    apply_run_update_all_dicts(proposal_id).
    """
    return t.propose_run_update_all_dicts(_c(), reason)


@srv.tool()
def apply_run_update_all_dicts(proposal_id: str) -> dict[str, Any]:
    """Apply a previously-staged update_all_dicts trigger. Use only after explicit user OK.

    Returns 202 {status: 'queued', task: 'update_all_dicts', company_id}.
    """
    return t.apply_run_update_all_dicts(_c(), proposal_id)


@srv.tool()
def propose_run_set_category_for_products(category_id: str, reason: str = '') -> dict[str, Any]:
    """Stage a set_category_for_products Celery task trigger for explicit approval. Does NOT enqueue.

    category_id: ProductCategory UUID — the category whose linked Segments define
    product membership. 202 fire-and-forget. After the user OKs, call
    apply_run_set_category_for_products(proposal_id).
    """
    return t.propose_run_set_category_for_products(_c(), category_id, reason)


@srv.tool()
def apply_run_set_category_for_products(proposal_id: str) -> dict[str, Any]:
    """Apply a previously-staged set_category_for_products trigger. Use only after explicit user OK.

    Returns 202 {status: 'queued', task: 'update_product_categories', category_id}.
    """
    return t.apply_run_set_category_for_products(_c(), proposal_id)


def main() -> None:
    srv.run()


if __name__ == '__main__':
    main()
