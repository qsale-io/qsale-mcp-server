"""Tool implementations — thin layer over QsaleClient.

Fields whitelisted for update_category are limited to SEO-relevant ones
to minimise blast radius of accidental writes.
"""
from __future__ import annotations

from typing import Any

from . import proposals
from .client import QsaleClient

# Fields allowed in update_category — anything else is rejected.
ALLOWED_CATEGORY_FIELDS = {
    'parent',          # UUID string or None — reparent
    'slug',
    'name',
    'title',
    'description',
    'meta_title',
    'meta_description',
    'published',
    'sort',
}

# Fields allowed in update_redirect.
ALLOWED_REDIRECT_FIELDS = {
    'url',
    'target_url',
    'is_permanent',
    'is_active',
    'priority',
    'is_template',
    'host',
    'content_type',
}

# Fields allowed in update_redirect_site.
ALLOWED_REDIRECT_SITE_FIELDS = {
    'host',
    'main_site',
    'is_enabled',
}

# Fields allowed in navigation-item create/update proposals.
ALLOWED_NAVIGATION_ITEM_FIELDS = {
    'name',
    'group',            # NavigationGroup UUID
    'parent',           # parent NavigationItem UUID or None
    'type',             # ContentItemType: LINK / PAGE / PRODUCT_CATEGORY / ...
    'value',            # object UUID for content types, external URL for LINK
    'published',
    'sort',
    'is_template',
    'display_settings',
}

# Minimum fields required to create a NavigationItem.
REQUIRED_NAVIGATION_CREATE_FIELDS = {'name', 'group', 'type'}

# Fields allowed in page proposals — SEO + content. `slug` excluded (renames URL).
ALLOWED_PAGE_FIELDS = {
    'meta_title',
    'meta_description',
    'meta_keywords',
    'canonical_url',
    'title',
    'body',
}

# Fields allowed in mail-template create proposals. `images` excluded — images
# are attached separately via create_mail_template_image (own file upload + FK).
ALLOWED_MAIL_TEMPLATE_FIELDS = {
    'name',
    'category',
    'promotion',   # Promotion UUID or None — binds PROMOTION_* template vars
    'subject',
    'text',        # plain-text body (required by the model)
    'html',        # optional HTML body
    'context',     # dict of template-level context overrides
}

# Minimum fields required to create a MailTemplate.
REQUIRED_MAIL_TEMPLATE_CREATE_FIELDS = {'name', 'category', 'subject', 'text'}

# Valid MailTemplate.category values (mail.models.MailTemplate.CATEGORIES).
MAIL_TEMPLATE_CATEGORIES = {'SYSTEM', 'TRANSACTIONAL', 'PROMOTIONAL', 'PERSONAL', 'CUSTOM'}

# Fields allowed in promotion-trigger create proposals.
ALLOWED_PROMOTION_TRIGGER_FIELDS = {
    'name',
    'promotion',       # Promotion UUID (required for code generation / PROMOTION_* vars)
    'category',        # e.g. REGISTRATION / BIRTHDAY / PURCHASE / ORDER_DONE / ...
    'mail_template',   # MailTemplate UUID (nullable)
    'sms_template',    # ShortMessageTemplate UUID (nullable)
    'push_template',   # PushTemplate UUID (nullable)
    'values',          # dict matching the category's field definitions
}

# Minimum fields required to create a PromotionTrigger (per WritePromotionTriggerSerializer).
REQUIRED_PROMOTION_TRIGGER_CREATE_FIELDS = {'category', 'values'}


def list_categories(
    client: QsaleClient,
    parent_id: str | None = None,
    slug: str | None = None,
    limit: int = 500,
) -> list[dict[str, Any]]:
    """List ProductCategory rows.

    parent_id: filter by parent UUID. Use 'NULL' to get root categories.
    slug: filter by slug.
    """
    params: dict[str, Any] = {'limit': limit}
    if parent_id is not None:
        if parent_id.upper() == 'NULL':
            params['parent__isnull'] = 'true'
        else:
            params['parent'] = parent_id
    if slug:
        params['slug'] = slug
    rows = client.get('/api/product-categories/', params=params)
    return [_compact_category(c) for c in (rows or [])]


def get_category(client: QsaleClient, category_id: str) -> dict[str, Any]:
    return client.get(f'/api/product-categories/{category_id}/')


def update_category(
    client: QsaleClient,
    category_id: str,
    fields: dict[str, Any],
) -> dict[str, Any]:
    """PATCH a single category. Only whitelisted fields are accepted.

    Example: update_category('uuid', {'parent': None}) → reparent to root.
    """
    bad = set(fields) - ALLOWED_CATEGORY_FIELDS
    if bad:
        raise ValueError(f'Field(s) not in whitelist: {sorted(bad)}. Allowed: {sorted(ALLOWED_CATEGORY_FIELDS)}')
    if not fields:
        raise ValueError('fields must not be empty')
    return client.patch(f'/api/product-categories/{category_id}/', json=fields)


def list_redirects(
    client: QsaleClient,
    site_id: str | None = None,
    url: str | None = None,
    limit: int = 500,
) -> list[dict[str, Any]]:
    params: dict[str, Any] = {'limit': limit}
    if site_id:
        params['site'] = site_id
    if url:
        params['url'] = url
    return client.get('/api/url-redirects/', params=params) or []


def create_redirect(
    client: QsaleClient,
    site_id: str,
    url: str,
    target_url: str,
    is_permanent: bool = True,
    priority: int = 0,
    is_template: bool = False,
    host: str | None = None,
    content_type: str | None = None,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        'site': site_id,
        'url': url,
        'target_url': target_url,
        'is_permanent': is_permanent,
        'priority': priority,
        'is_active': True,
        'is_template': is_template,
    }
    if host is not None:
        body['host'] = host
    if content_type is not None:
        body['content_type'] = content_type
    return client.post('/api/url-redirects/', json=body)


def list_redirect_sites(client: QsaleClient) -> list[dict[str, Any]]:
    rows = client.get('/api/redirect-sites/')
    return rows or []


def create_redirect_site(
    client: QsaleClient,
    host: str,
    main_site: str | None = None,
    is_enabled: bool = True,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        'host': host,
        'main_site': main_site,
        'is_enabled': is_enabled,
    }
    return client.post('/api/redirect-sites/', json=body)


def update_redirect_site(
    client: QsaleClient,
    site_id: str,
    fields: dict[str, Any],
) -> dict[str, Any]:
    bad = set(fields) - ALLOWED_REDIRECT_SITE_FIELDS
    if bad:
        raise ValueError(f'Field(s) not in whitelist: {sorted(bad)}. Allowed: {sorted(ALLOWED_REDIRECT_SITE_FIELDS)}')
    if not fields:
        raise ValueError('fields must not be empty')
    return client.patch(f'/api/redirect-sites/{site_id}/', json=fields)


def update_redirect(
    client: QsaleClient,
    redirect_id: str,
    fields: dict[str, Any],
) -> dict[str, Any]:
    bad = set(fields) - ALLOWED_REDIRECT_FIELDS
    if bad:
        raise ValueError(f'Field(s) not in whitelist: {sorted(bad)}. Allowed: {sorted(ALLOWED_REDIRECT_FIELDS)}')
    if not fields:
        raise ValueError('fields must not be empty')
    return client.patch(f'/api/url-redirects/{redirect_id}/', json=fields)


def list_pages(
    client: QsaleClient,
    slug: str | None = None,
    limit: int = 500,
) -> list[dict[str, Any]]:
    """List Page rows. `slug` filter matches exactly when provided."""
    params: dict[str, Any] = {'limit': limit}
    if slug:
        params['slug'] = slug
    res = client.get('/api/pages/', params=params)
    rows = res.get('results') if isinstance(res, dict) else res
    return [_compact_page(p) for p in (rows or [])]


def get_page(client: QsaleClient, page_id: str) -> dict[str, Any]:
    return client.get(f'/api/pages/{page_id}/')


def propose_page_update(
    client: QsaleClient,
    page_id: str,
    fields: dict[str, Any],
    reason: str = '',
) -> dict[str, Any]:
    """Stage a Page patch for explicit approval. Returns proposal_id + before/after.

    No API write happens here. Use `apply_page_update(proposal_id)` after the
    user reviews the diff and approves.
    """
    bad = set(fields) - ALLOWED_PAGE_FIELDS
    if bad:
        raise ValueError(f'Field(s) not in whitelist: {sorted(bad)}. Allowed: {sorted(ALLOWED_PAGE_FIELDS)}')
    if not fields:
        raise ValueError('fields must not be empty')

    current = get_page(client, page_id)
    before = {k: current.get(k) for k in fields}

    p = proposals.register('page_update', page_id, fields, before, reason)
    return {
        'proposal_id': p.id,
        'page_id': page_id,
        'reason': reason,
        'changes': [
            {'field': k, 'before': before[k], 'after': fields[k]}
            for k in fields
        ],
    }


def apply_page_update(client: QsaleClient, proposal_id: str) -> dict[str, Any]:
    """Apply a previously-staged page update. Single-use — proposal is consumed."""
    p = proposals.pop(proposal_id)
    if p.kind != 'page_update':
        raise ValueError(f'Proposal {proposal_id} is kind={p.kind!r}, not page_update')
    return client.patch(f'/api/pages/{p.target_id}/', json=p.fields)


def list_navigation_groups(
    client: QsaleClient,
    slug: str | None = None,
    limit: int = 500,
) -> list[dict[str, Any]]:
    """List NavigationGroup rows (menu containers: header, footer, etc.)."""
    params: dict[str, Any] = {'limit': limit}
    if slug:
        params['slug'] = slug
    res = client.get('/api/navigation-groups/', params=params)
    rows = res.get('results') if isinstance(res, dict) else res
    return rows or []


def list_navigation_items(
    client: QsaleClient,
    group: str | None = None,
    parent: str | None = None,
    parent_isnull: bool | None = None,
    type: str | None = None,
    limit: int = 500,
) -> list[dict[str, Any]]:
    """List NavigationItem rows. Filter by group UUID, parent UUID, top-level
    (parent_isnull=True), or content type.
    """
    params: dict[str, Any] = {'limit': limit}
    if group:
        params['group'] = group
    if parent:
        params['parent'] = parent
    if parent_isnull is not None:
        params['parent__isnull'] = 'true' if parent_isnull else 'false'
    if type:
        params['type'] = type
    res = client.get('/api/navigation-items/', params=params)
    rows = res.get('results') if isinstance(res, dict) else res
    return [_compact_navigation_item(i) for i in (rows or [])]


def get_navigation_item(client: QsaleClient, item_id: str) -> dict[str, Any]:
    return client.get(f'/api/navigation-items/{item_id}/')


def propose_navigation_item_update(
    client: QsaleClient,
    item_id: str,
    fields: dict[str, Any],
    reason: str = '',
) -> dict[str, Any]:
    """Stage a NavigationItem PATCH for explicit approval. Does NOT write.

    Use `apply_navigation_item_update(proposal_id)` after the user reviews the
    diff and approves. `value` semantics depend on `type` (see ALLOWED list /
    list_navigation_items docstring).
    """
    bad = set(fields) - ALLOWED_NAVIGATION_ITEM_FIELDS
    if bad:
        raise ValueError(f'Field(s) not in whitelist: {sorted(bad)}. Allowed: {sorted(ALLOWED_NAVIGATION_ITEM_FIELDS)}')
    if not fields:
        raise ValueError('fields must not be empty')

    current = get_navigation_item(client, item_id)
    before = {k: current.get(k) for k in fields}
    p = proposals.register('navigation_item_update', item_id, fields, before, reason)
    return {
        'proposal_id': p.id,
        'item_id': item_id,
        'reason': reason,
        'changes': [{'field': k, 'before': before[k], 'after': fields[k]} for k in fields],
    }


def apply_navigation_item_update(client: QsaleClient, proposal_id: str) -> dict[str, Any]:
    """Apply a previously-staged NavigationItem update. Single-use."""
    p = proposals.pop(proposal_id)
    if p.kind != 'navigation_item_update':
        raise ValueError(f'Proposal {proposal_id} is kind={p.kind!r}, not navigation_item_update')
    return client.patch(f'/api/navigation-items/{p.target_id}/', json=p.fields)


def propose_navigation_item_create(
    client: QsaleClient,
    fields: dict[str, Any],
    reason: str = '',
) -> dict[str, Any]:
    """Stage a NavigationItem creation for explicit approval. Does NOT write.

    Required: name, group (NavigationGroup UUID), type. For content types
    (PAGE/PRODUCT/PRODUCT_CATEGORY/PROMOTION/SCREEN/OUTLET) pass `value` = the
    target object UUID. For LINK pass `value` = external URL. `parent` (UUID)
    nests under an existing item. Company is set by the API from the auth header.
    """
    bad = set(fields) - ALLOWED_NAVIGATION_ITEM_FIELDS
    if bad:
        raise ValueError(f'Field(s) not in whitelist: {sorted(bad)}. Allowed: {sorted(ALLOWED_NAVIGATION_ITEM_FIELDS)}')
    missing = REQUIRED_NAVIGATION_CREATE_FIELDS - set(fields)
    if missing:
        raise ValueError(f'Missing required field(s) for create: {sorted(missing)}')

    p = proposals.register('navigation_item_create', '', fields, {}, reason)
    return {'proposal_id': p.id, 'reason': reason, 'fields': fields}


def apply_navigation_item_create(client: QsaleClient, proposal_id: str) -> dict[str, Any]:
    """Apply a previously-staged NavigationItem creation. Single-use."""
    p = proposals.pop(proposal_id)
    if p.kind != 'navigation_item_create':
        raise ValueError(f'Proposal {proposal_id} is kind={p.kind!r}, not navigation_item_create')
    return client.post('/api/navigation-items/', json=p.fields)


def list_mail_templates(
    client: QsaleClient,
    category: str | None = None,
    promotion: str | None = None,
    promotion_isnull: bool | None = None,
    limit: int = 200,
) -> list[dict[str, Any]]:
    """List MailTemplate rows (compact). Filter by category, promotion UUID, or
    promotion_isnull (True → only templates not bound to a promotion).
    """
    params: dict[str, Any] = {'limit': limit}
    if category:
        params['category'] = category
    if promotion:
        params['promotion'] = promotion
    if promotion_isnull is not None:
        params['promotion__isnull'] = 'true' if promotion_isnull else 'false'
    res = client.get('/api/mail-templates/', params=params)
    rows = res.get('results') if isinstance(res, dict) else res
    return [_compact_mail_template(t) for t in (rows or [])]


def get_mail_template(client: QsaleClient, template_id: str) -> dict[str, Any]:
    """Get a full MailTemplate by UUID (incl. subject/text/html/context/images)."""
    return client.get(f'/api/mail-templates/{template_id}/')


def propose_mail_template_create(
    client: QsaleClient,
    fields: dict[str, Any],
    reason: str = '',
) -> dict[str, Any]:
    """Stage a MailTemplate creation for explicit approval. Does NOT write.

    Required: name, category, subject, text. Optional: html, context (dict),
    promotion (UUID — enables PROMOTION_NAME/PROMOTION_SINCE/PROMOTION_UNTIL and
    the trigger-supplied promo_code var). Company is set by the API from the
    auth header. After the user OKs, call apply_mail_template_create(proposal_id).
    """
    bad = set(fields) - ALLOWED_MAIL_TEMPLATE_FIELDS
    if bad:
        raise ValueError(f'Field(s) not in whitelist: {sorted(bad)}. Allowed: {sorted(ALLOWED_MAIL_TEMPLATE_FIELDS)}')
    missing = REQUIRED_MAIL_TEMPLATE_CREATE_FIELDS - set(fields)
    if missing:
        raise ValueError(f'Missing required field(s) for create: {sorted(missing)}')
    category = fields.get('category')
    if category not in MAIL_TEMPLATE_CATEGORIES:
        raise ValueError(f'category {category!r} invalid. One of: {sorted(MAIL_TEMPLATE_CATEGORIES)}')

    p = proposals.register('mail_template_create', '', fields, {}, reason)
    return {'proposal_id': p.id, 'reason': reason, 'summary': _summarise_mail_fields(fields)}


def apply_mail_template_create(client: QsaleClient, proposal_id: str) -> dict[str, Any]:
    """Apply a previously-staged MailTemplate creation. Single-use."""
    p = proposals.pop(proposal_id)
    if p.kind != 'mail_template_create':
        raise ValueError(f'Proposal {proposal_id} is kind={p.kind!r}, not mail_template_create')
    return client.post('/api/mail-templates/', json=p.fields)


def list_mail_template_images(
    client: QsaleClient,
    template: str | None = None,
    limit: int = 200,
) -> list[dict[str, Any]]:
    """List MailTemplateImage rows. Filter by template UUID. Template-less rows
    (template=None on the server) are company-wide shared images (IMAGES_COMMON).
    """
    params: dict[str, Any] = {'limit': limit}
    if template:
        params['template'] = template
    res = client.get('/api/mail-template-images/', params=params)
    rows = res.get('results') if isinstance(res, dict) else res
    return rows or []


def create_mail_template_image(
    client: QsaleClient,
    template: str,
    slug: str,
    image_path: str | None = None,
    base64_data: str | None = None,
) -> dict[str, Any]:
    """Attach an image to a MailTemplate. Reference it in the body as {{ IMAGES.<slug> }}.

    Provide exactly one of image_path (local file, read + base64-encoded here) or
    base64_data (raw base64 or a full data: URI). Server accepts JPEG/PNG/GIF/WEBP
    via Base64ImageField. (slug, template, company) is unique — re-using a slug
    for the same template will be rejected by the API.
    """
    if bool(image_path) == bool(base64_data):
        raise ValueError('provide exactly one of image_path or base64_data')
    if image_path:
        import base64
        import mimetypes
        import pathlib

        path = pathlib.Path(image_path)
        raw = path.read_bytes()
        mime = mimetypes.guess_type(str(path))[0] or 'image/png'
        file_value = f'data:{mime};base64,{base64.b64encode(raw).decode()}'
    else:
        file_value = base64_data
    body = {'template': template, 'slug': slug, 'file': file_value}
    return client.post('/api/mail-template-images/', json=body)


def list_trigger_categories(client: QsaleClient) -> list[dict[str, Any]]:
    """List all promotion-trigger categories and their configurable fields
    (metadata from /api/triggers/). Use to discover valid `category` + `values`
    keys before create.
    """
    res = client.get('/api/triggers/')
    rows = res.get('promotion', []) if isinstance(res, dict) else (res or [])
    return [{'category': r.get('category'), 'fields': sorted((r.get('fields') or {}).keys())} for r in rows]


def list_promotion_triggers(
    client: QsaleClient,
    promotion: str | None = None,
    promotion_isnull: bool | None = None,
    category: str | None = None,
    limit: int = 200,
) -> list[dict[str, Any]]:
    """List PromotionTrigger rows (compact). Filter by promotion UUID,
    promotion_isnull, and/or category (category filtered client-side).
    """
    params: dict[str, Any] = {'limit': limit}
    if promotion:
        params['promotion'] = promotion
    if promotion_isnull is not None:
        params['promotion__isnull'] = 'true' if promotion_isnull else 'false'
    res = client.get('/api/promotions-triggers/', params=params)
    rows = res.get('results') if isinstance(res, dict) else res
    rows = rows or []
    if category:
        rows = [r for r in rows if r.get('category') == category]
    return [_compact_promotion_trigger(t) for t in rows]


def get_promotion_trigger(client: QsaleClient, trigger_id: str) -> dict[str, Any]:
    """Get a single PromotionTrigger by UUID (full record incl. values + templates)."""
    return client.get(f'/api/promotions-triggers/{trigger_id}/')


def propose_promotion_trigger_create(
    client: QsaleClient,
    fields: dict[str, Any],
    reason: str = '',
) -> dict[str, Any]:
    """Stage a PromotionTrigger creation for explicit approval. Does NOT write.

    Required: category, values (dict matching the category's field definitions —
    see list_trigger_categories; missing keys fall back to per-field defaults
    server-side). Optional: name, promotion (UUID), mail_template/sms_template/
    push_template (UUIDs). To create dormant, pass values={'enabled': False, ...}.
    The API rejects a duplicate (promotion, category) pair. After the user OKs,
    call apply_promotion_trigger_create(proposal_id).
    """
    bad = set(fields) - ALLOWED_PROMOTION_TRIGGER_FIELDS
    if bad:
        raise ValueError(
            f'Field(s) not in whitelist: {sorted(bad)}. Allowed: {sorted(ALLOWED_PROMOTION_TRIGGER_FIELDS)}'
        )
    missing = REQUIRED_PROMOTION_TRIGGER_CREATE_FIELDS - set(fields)
    if missing:
        raise ValueError(f'Missing required field(s) for create: {sorted(missing)}')
    if not isinstance(fields.get('values'), dict):
        raise ValueError("'values' must be a dict matching the category's field definitions")

    p = proposals.register('promotion_trigger_create', '', fields, {}, reason)
    return {'proposal_id': p.id, 'reason': reason, 'fields': fields}


def apply_promotion_trigger_create(client: QsaleClient, proposal_id: str) -> dict[str, Any]:
    """Apply a previously-staged PromotionTrigger creation. Single-use."""
    p = proposals.pop(proposal_id)
    if p.kind != 'promotion_trigger_create':
        raise ValueError(f'Proposal {proposal_id} is kind={p.kind!r}, not promotion_trigger_create')
    return client.post('/api/promotions-triggers/', json=p.fields)


def list_proposals(kind: str | None = None) -> list[dict[str, Any]]:
    """Inspect pending proposals (in-memory, lost on server restart)."""
    return [
        {
            'id': p.id, 'kind': p.kind, 'target_id': p.target_id,
            'fields': list(p.fields.keys()), 'reason': p.reason,
            'created_at': p.created_at,
        }
        for p in proposals.list_pending(kind)
    ]


def _compact_page(p: dict[str, Any]) -> dict[str, Any]:
    return {
        'id': p.get('id'),
        'slug': p.get('slug'),
        'title': p.get('title'),
        'meta_title': p.get('meta_title'),
        'meta_description': p.get('meta_description'),
        'meta_keywords': p.get('meta_keywords'),
        'canonical_url': p.get('canonical_url'),
    }


def _compact_navigation_item(i: dict[str, Any]) -> dict[str, Any]:
    """Trim NavigationItem to the fields that matter for menu editing.

    For non-LINK types `value` is the UUID of the referenced object
    (PRODUCT_CATEGORY, PRODUCT, PAGE, PROMOTION, SCREEN, OUTLET). LINK is
    reserved for external URLs; SEPARATOR carries no value.
    """
    return {
        'id': i.get('id'),
        'name': i.get('name'),
        'group': i.get('group'),
        'parent': i.get('parent'),
        'type': i.get('type'),
        'value': i.get('value'),
        'published': i.get('published'),
        'sort': i.get('sort'),
        'is_template': i.get('is_template'),
        'has_children': i.get('has_children'),
        'share_path': i.get('share_path'),
    }


def _compact_mail_template(t: dict[str, Any]) -> dict[str, Any]:
    """Trim MailTemplate to list-view essentials; bodies shown as lengths only."""
    return {
        'id': t.get('id'),
        'name': t.get('name'),
        'category': t.get('category'),
        'promotion': t.get('promotion'),
        'subject': t.get('subject'),
        'text_len': len(t.get('text') or ''),
        'html_len': len(t.get('html') or ''),
        'image_slugs': [i.get('slug') for i in (t.get('images') or [])],
    }


def _compact_promotion_trigger(t: dict[str, Any]) -> dict[str, Any]:
    """Trim PromotionTrigger to list-view essentials."""
    trig = t.get('trigger') or {}
    return {
        'id': t.get('id'),
        'name': t.get('name'),
        'category': t.get('category') or trig.get('category'),
        'promotion': t.get('promotion'),
        'mail_template': t.get('mail_template', {}).get('id') if isinstance(t.get('mail_template'), dict) else t.get('mail_template'),
        'sms_template': t.get('sms_template', {}).get('id') if isinstance(t.get('sms_template'), dict) else t.get('sms_template'),
        'values': t.get('values'),
    }


def _summarise_mail_fields(fields: dict[str, Any]) -> dict[str, Any]:
    """Render a create-proposal preview without dumping multi-KB html/text bodies."""
    out: dict[str, Any] = {}
    for k, v in fields.items():
        if k in ('html', 'text') and isinstance(v, str):
            out[k] = f'<{len(v)} chars>'
        else:
            out[k] = v
    return out


def _compact_category(c: dict[str, Any]) -> dict[str, Any]:
    """Trim API category response to relevant fields (cuts noise in tool output)."""
    return {
        'id': c.get('id'),
        'slug': c.get('slug'),
        'name': c.get('name'),
        'parent': c.get('parent'),
        'group': c.get('group'),
        'published': c.get('published'),
        'share_path': c.get('share_path'),
    }
