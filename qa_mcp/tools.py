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
    'group',           # ProductCategoryGroup UUID or None — admin tree placement
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


def propose_mail_template_update(
    client: QsaleClient,
    template_id: str,
    fields: dict[str, Any],
    reason: str = '',
) -> dict[str, Any]:
    """Stage a MailTemplate PATCH for explicit approval. Does NOT write.

    Editable fields: name, category, promotion, subject, text, html, context.
    `category`, if given, must be a valid MailTemplate category. Bodies (html/text)
    are shown as char-counts in the diff, not dumped. After the user OKs, call
    apply_mail_template_update(proposal_id).
    """
    bad = set(fields) - ALLOWED_MAIL_TEMPLATE_FIELDS
    if bad:
        raise ValueError(f'Field(s) not in whitelist: {sorted(bad)}. Allowed: {sorted(ALLOWED_MAIL_TEMPLATE_FIELDS)}')
    if not fields:
        raise ValueError('fields must not be empty')
    if 'category' in fields and fields['category'] not in MAIL_TEMPLATE_CATEGORIES:
        raise ValueError(f'category {fields["category"]!r} invalid. One of: {sorted(MAIL_TEMPLATE_CATEGORIES)}')

    current = get_mail_template(client, template_id)
    before = {k: current.get(k) for k in fields}

    p = proposals.register('mail_template_update', template_id, fields, before, reason)
    return {
        'proposal_id': p.id,
        'template_id': template_id,
        'reason': reason,
        'changes': [
            {
                'field': k,
                'before': _summarise_mail_fields({k: before[k]})[k],
                'after': _summarise_mail_fields({k: fields[k]})[k],
            }
            for k in fields
        ],
    }


def apply_mail_template_update(client: QsaleClient, proposal_id: str) -> dict[str, Any]:
    """Apply a previously-staged MailTemplate update. Single-use — proposal is consumed."""
    p = proposals.pop(proposal_id)
    if p.kind != 'mail_template_update':
        raise ValueError(f'Proposal {proposal_id} is kind={p.kind!r}, not mail_template_update')
    return client.patch(f'/api/mail-templates/{p.target_id}/', json=p.fields)


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


def list_frontend_settings(client: QsaleClient) -> list[dict[str, Any]]:
    """List company frontend settings (flattened: group, key, type, name, value).

    `value` is the current value (string/URL for file-typed, JSON for json-typed).
    Use the `key` with get/update tools.
    """
    res = client.get('/api/frontend-settings/')
    groups = res if isinstance(res, list) else (res.get('results', []) if isinstance(res, dict) else [])
    out: list[dict[str, Any]] = []
    for grp in groups:
        for s in grp.get('settings', []) or []:
            out.append(
                {
                    'group': grp.get('name'),
                    'key': s.get('key'),
                    'type': s.get('setting_type'),
                    'name': s.get('name'),
                    'value': s.get('value'),
                }
            )
    return out


def get_frontend_setting(client: QsaleClient, key: str) -> dict[str, Any]:
    """Get one frontend setting by key (id, key, setting_type, name, schema, value)."""
    return client.get(f'/api/frontend-settings/{key}/')


def update_frontend_setting_json(client: QsaleClient, key: str, value: Any) -> dict[str, Any]:
    """Update a json-typed frontend setting. Server validates `value` against the
    setting's JSON schema (use get_frontend_setting to see it). Narrate intent and
    get the user's OK before calling — this writes to the tenant immediately.
    """
    return client.patch(f'/api/frontend-settings/{key}/json/', json={'value': value})


def set_frontend_setting_file(client: QsaleClient, key: str, file_path: str) -> dict[str, Any]:
    """Replace a file-typed frontend setting (e.g. logo_for_emails) by uploading a
    local file. Direct write — narrate intent and get the user's OK before calling.
    """
    return client.patch_file(f'/api/frontend-settings/{key}/file/', 'value', file_path)


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


# ---------------------------------------------------------------------------
# Fields allowed in category create proposals.
# ---------------------------------------------------------------------------
ALLOWED_CATEGORY_CREATE_FIELDS = {
    'parent',
    'name',
    'slug',
    'title',
    'description',
    'meta_title',
    'meta_description',
    'group',
}

REQUIRED_CATEGORY_CREATE_FIELDS = {'name', 'slug'}

# Fields allowed in dictionary-item create proposals.
ALLOWED_DICTIONARY_ITEM_CREATE_FIELDS = {
    'dictionary',
    'name',
    'data',
    'description',
    'sort',
}

REQUIRED_DICTIONARY_ITEM_CREATE_FIELDS = {'dictionary', 'name'}

# Fields allowed in segment-filter create proposals.
ALLOWED_SEGMENT_FILTER_CREATE_FIELDS = {
    'segment',
    'property',
    'operator',
    'value',
    'exclude',
    'data',
}

REQUIRED_SEGMENT_FILTER_CREATE_FIELDS = {'segment', 'property', 'operator', 'value'}


# ---------------------------------------------------------------------------
# §FR-1 Read tools — Dictionaries
# ---------------------------------------------------------------------------

def list_dictionaries(client: QsaleClient, limit: int = 200) -> list[dict[str, Any]]:
    """List Dictionary rows for the current tenant."""
    res = client.get('/api/dictionaries/', params={'limit': limit})
    rows = res.get('results') if isinstance(res, dict) else res
    return rows or []


def get_dictionary(client: QsaleClient, dictionary_id: str) -> dict[str, Any]:
    """Get a single Dictionary by UUID."""
    return client.get(f'/api/dictionaries/{dictionary_id}/')


def list_dictionary_items(
    client: QsaleClient,
    dictionary_id: str | None = None,
    search: str | None = None,
    limit: int = 200,
) -> list[dict[str, Any]]:
    """List DictionaryItem rows. Filter by dictionary UUID and/or search string."""
    params: dict[str, Any] = {'limit': limit}
    if dictionary_id:
        params['dictionary'] = dictionary_id
    if search:
        params['search'] = search
    res = client.get('/api/dictionary-items/', params=params)
    rows = res.get('results') if isinstance(res, dict) else res
    return [_compact_dictionary_item(i) for i in (rows or [])]


def get_dictionary_item(client: QsaleClient, item_id: str) -> dict[str, Any]:
    """Get a single DictionaryItem by UUID."""
    return client.get(f'/api/dictionary-items/{item_id}/')


# ---------------------------------------------------------------------------
# §FR-1 Read tools — Segments
# ---------------------------------------------------------------------------

def list_segments(
    client: QsaleClient,
    model_id: str | None = None,
    search: str | None = None,
    limit: int = 500,
) -> list[dict[str, Any]]:
    """List Segment rows. Filter by model UUID and/or search string."""
    params: dict[str, Any] = {'limit': limit}
    if model_id:
        params['model'] = model_id
    if search:
        params['search'] = search
    res = client.get('/api/segments/', params=params)
    rows = res.get('results') if isinstance(res, dict) else res
    return [_compact_segment(s) for s in (rows or [])]


def get_segment(client: QsaleClient, segment_id: str) -> dict[str, Any]:
    """Get a single Segment by UUID."""
    return client.get(f'/api/segments/{segment_id}/')


def list_segment_properties(
    client: QsaleClient,
    model_id: str | None = None,
    limit: int = 500,
) -> list[dict[str, Any]]:
    """List SegmentProperty rows. Filter by model UUID."""
    params: dict[str, Any] = {'limit': limit}
    if model_id:
        params['model'] = model_id
    res = client.get('/api/segment-properties/', params=params)
    rows = res.get('results') if isinstance(res, dict) else res
    return rows or []


def get_segment_property(client: QsaleClient, property_id: str) -> dict[str, Any]:
    """Get a single SegmentProperty by UUID."""
    return client.get(f'/api/segment-properties/{property_id}/')


def list_segment_filters(
    client: QsaleClient,
    segment_id: str | None = None,
) -> list[dict[str, Any]]:
    """List SegmentFilter rows. Filter by segment UUID (NEW endpoint on qa-server)."""
    params: dict[str, Any] = {}
    if segment_id:
        params['segment'] = segment_id
    res = client.get('/api/segment-filters/', params=params)
    rows = res.get('results') if isinstance(res, dict) else res
    return rows or []


def get_segment_filter(client: QsaleClient, filter_id: str) -> dict[str, Any]:
    """Get a single SegmentFilter by UUID (NEW endpoint on qa-server)."""
    return client.get(f'/api/segment-filters/{filter_id}/')


# ---------------------------------------------------------------------------
# §FR-1 Read tools — M2M list views (NEW endpoints)
# ---------------------------------------------------------------------------

def list_pc_segments(client: QsaleClient, category_id: str) -> list[dict[str, Any]]:
    """List Segments linked to a ProductCategory (NEW endpoint on qa-server)."""
    res = client.get(f'/api/product-categories/{category_id}/segments/')
    rows = res.get('results') if isinstance(res, dict) else res
    return rows or []


def list_di_segments(client: QsaleClient, dictionary_item_id: str) -> list[dict[str, Any]]:
    """List Segments linked to a DictionaryItem (NEW endpoint on qa-server)."""
    res = client.get(f'/api/dictionary-items/{dictionary_item_id}/segments/')
    rows = res.get('results') if isinstance(res, dict) else res
    return rows or []


# ---------------------------------------------------------------------------
# §FR-2 Category write tools
# ---------------------------------------------------------------------------

def propose_category_create(
    client: QsaleClient,
    fields: dict[str, Any],
    reason: str = '',
) -> dict[str, Any]:
    """Stage a ProductCategory creation for explicit approval. Does NOT write.

    Required fields: name, slug. Optional: parent (UUID or null for root),
    title, description, meta_title, meta_description, group (UUID). Company
    is set by the API from the auth header. After the user OKs, call
    apply_category_create(proposal_id).
    """
    bad = set(fields) - ALLOWED_CATEGORY_CREATE_FIELDS
    if bad:
        raise ValueError(
            f'Field(s) not in whitelist: {sorted(bad)}. Allowed: {sorted(ALLOWED_CATEGORY_CREATE_FIELDS)}'
        )
    missing = REQUIRED_CATEGORY_CREATE_FIELDS - set(fields)
    if missing:
        raise ValueError(f'Missing required field(s) for create: {sorted(missing)}')

    p = proposals.register('category_create', '', fields, {}, reason)
    return {
        'proposal_id': p.id,
        'reason': reason,
        'summary': {
            'action': 'CREATE ProductCategory',
            'after': fields,
        },
    }


def apply_category_create(client: QsaleClient, proposal_id: str) -> dict[str, Any]:
    """Apply a previously-staged ProductCategory creation. Single-use."""
    p = proposals.pop(proposal_id)
    if p.kind != 'category_create':
        raise ValueError(f'Proposal {proposal_id} is kind={p.kind!r}, not category_create')
    return client.post('/api/product-categories/', json=p.fields)


def propose_category_delete(
    client: QsaleClient,
    category_id: str,
    reason: str = '',
) -> dict[str, Any]:
    """Stage a ProductCategory deletion for explicit approval. Does NOT write.

    Fetches current category (name, slug, parent, published) and shows it as a
    warning. API 400/409 (category has children or other constraints) will be
    proxied when apply is called. After the user OKs, call
    apply_category_delete(proposal_id).
    """
    current = get_category(client, category_id)
    before = {
        'name': current.get('name'),
        'slug': current.get('slug'),
        'parent': current.get('parent'),
        'published': current.get('published'),
    }
    p = proposals.register('category_delete', category_id, {}, before, reason)
    return {
        'proposal_id': p.id,
        'category_id': category_id,
        'reason': reason,
        'warning': (
            f'ProductCategory "{before["name"]}" (slug={before["slug"]!r}) will be deleted. '
            'Children, linked segments, and product memberships are detached per qa-server rules.'
        ),
        'summary': {
            'action': 'DELETE ProductCategory',
            'before': before,
        },
    }


def apply_category_delete(client: QsaleClient, proposal_id: str) -> dict[str, Any] | None:
    """Apply a previously-staged ProductCategory deletion. Single-use."""
    p = proposals.pop(proposal_id)
    if p.kind != 'category_delete':
        raise ValueError(f'Proposal {proposal_id} is kind={p.kind!r}, not category_delete')
    return client.delete(f'/api/product-categories/{p.target_id}/')


# ---------------------------------------------------------------------------
# §FR-2 DictionaryItem write tools
# ---------------------------------------------------------------------------

def propose_dictionary_item_create(
    client: QsaleClient,
    fields: dict[str, Any],
    reason: str = '',
) -> dict[str, Any]:
    """Stage a DictionaryItem creation for explicit approval. Does NOT write.

    Required fields: dictionary (UUID), name. Optional: data (dict), description,
    sort (int, default 0). After the user OKs, call
    apply_dictionary_item_create(proposal_id).
    """
    bad = set(fields) - ALLOWED_DICTIONARY_ITEM_CREATE_FIELDS
    if bad:
        raise ValueError(
            f'Field(s) not in whitelist: {sorted(bad)}. Allowed: {sorted(ALLOWED_DICTIONARY_ITEM_CREATE_FIELDS)}'
        )
    missing = REQUIRED_DICTIONARY_ITEM_CREATE_FIELDS - set(fields)
    if missing:
        raise ValueError(f'Missing required field(s) for create: {sorted(missing)}')

    p = proposals.register('dictionary_item_create', '', fields, {}, reason)
    return {
        'proposal_id': p.id,
        'reason': reason,
        'summary': {
            'action': 'CREATE DictionaryItem',
            'after': fields,
        },
    }


def apply_dictionary_item_create(client: QsaleClient, proposal_id: str) -> dict[str, Any]:
    """Apply a previously-staged DictionaryItem creation. Single-use."""
    p = proposals.pop(proposal_id)
    if p.kind != 'dictionary_item_create':
        raise ValueError(f'Proposal {proposal_id} is kind={p.kind!r}, not dictionary_item_create')
    return client.post('/api/dictionary-items/', json=p.fields)


def propose_dictionary_item_delete(
    client: QsaleClient,
    item_id: str,
    reason: str = '',
) -> dict[str, Any]:
    """Stage a DictionaryItem deletion for explicit approval. Does NOT write.

    Fetches current state (name + dictionary) for the before-state diff. API 400
    (item in use) will be proxied when apply is called. After the user OKs, call
    apply_dictionary_item_delete(proposal_id).
    """
    current = get_dictionary_item(client, item_id)
    before = {
        'name': current.get('name'),
        'dictionary': current.get('dictionary'),
    }
    p = proposals.register('dictionary_item_delete', item_id, {}, before, reason)
    return {
        'proposal_id': p.id,
        'item_id': item_id,
        'reason': reason,
        'summary': {
            'action': 'DELETE DictionaryItem',
            'before': before,
        },
    }


def apply_dictionary_item_delete(client: QsaleClient, proposal_id: str) -> dict[str, Any] | None:
    """Apply a previously-staged DictionaryItem deletion. Single-use."""
    p = proposals.pop(proposal_id)
    if p.kind != 'dictionary_item_delete':
        raise ValueError(f'Proposal {proposal_id} is kind={p.kind!r}, not dictionary_item_delete')
    return client.delete(f'/api/dictionary-items/{p.target_id}/')


# ---------------------------------------------------------------------------
# §FR-3 Segment write tools
# ---------------------------------------------------------------------------

def propose_segment_create(
    client: QsaleClient,
    model_id: str,
    name: str,
    filters: list[dict[str, Any]] | None = None,
    reason: str = '',
) -> dict[str, Any]:
    """Stage a Segment creation for explicit approval. Does NOT write.

    model_id: SegmentModel UUID (use list_segment_properties to discover models).
    name: human-readable label (e.g. 'ResortId — Kemer A').
    filters: list of inline SegmentFilter dicts (qa-server requires at least one
        per POST /api/segments/). Each dict: {property, operator, value, exclude?}.
        Example: [{'property': '<uuid>', 'operator': 'in', 'value': ['6805']}].
    After the user OKs, call apply_segment_create(proposal_id).
    """
    fields: dict[str, Any] = {'model': model_id, 'name': name, 'filters': filters or []}
    p = proposals.register('segment_create', '', fields, {}, reason)
    return {
        'proposal_id': p.id,
        'reason': reason,
        'summary': {
            'action': 'CREATE Segment',
            'after': fields,
        },
    }


def apply_segment_create(client: QsaleClient, proposal_id: str) -> dict[str, Any]:
    """Apply a previously-staged Segment creation. Single-use."""
    p = proposals.pop(proposal_id)
    if p.kind != 'segment_create':
        raise ValueError(f'Proposal {proposal_id} is kind={p.kind!r}, not segment_create')
    return client.post('/api/segments/', json=p.fields)


def propose_segment_delete(
    client: QsaleClient,
    segment_id: str,
    reason: str = '',
) -> dict[str, Any]:
    """Stage a Segment deletion for explicit approval. Does NOT write.

    Fetches current segment (name + filter count) and shows it as a warning.
    API 400 (segment not deletable) will be proxied when apply is called.
    After the user OKs, call apply_segment_delete(proposal_id).
    """
    current = get_segment(client, segment_id)
    filters = list_segment_filters(client, segment_id=segment_id)
    before = {
        'name': current.get('name'),
        'model': current.get('model'),
        'filter_count': len(filters),
    }
    p = proposals.register('segment_delete', segment_id, {}, before, reason)
    return {
        'proposal_id': p.id,
        'segment_id': segment_id,
        'reason': reason,
        'warning': f'Segment "{before["name"]}" has {before["filter_count"]} filter(s). Deleting removes them all.',
        'summary': {
            'action': 'DELETE Segment',
            'before': before,
        },
    }


def apply_segment_delete(client: QsaleClient, proposal_id: str) -> dict[str, Any] | None:
    """Apply a previously-staged Segment deletion. Single-use."""
    p = proposals.pop(proposal_id)
    if p.kind != 'segment_delete':
        raise ValueError(f'Proposal {proposal_id} is kind={p.kind!r}, not segment_delete')
    return client.delete(f'/api/segments/{p.target_id}/')


# ---------------------------------------------------------------------------
# §FR-3 SegmentFilter write tools
# ---------------------------------------------------------------------------

def propose_segment_filter_create(
    client: QsaleClient,
    fields: dict[str, Any],
    reason: str = '',
) -> dict[str, Any]:
    """Stage a SegmentFilter creation for explicit approval. Does NOT write.

    Required fields: segment (UUID), property (UUID), operator (e.g. IN/NOT_IN/
    EQ/GTE/LTE), value (JSON — list for IN/NOT_IN, scalar for others). Optional:
    exclude (bool, default False), data (dict). Use get_segment_property first to
    check allowed operators for the property type. Server validates operator/value
    compatibility (400 proxied). After the user OKs, call
    apply_segment_filter_create(proposal_id).
    """
    bad = set(fields) - ALLOWED_SEGMENT_FILTER_CREATE_FIELDS
    if bad:
        raise ValueError(
            f'Field(s) not in whitelist: {sorted(bad)}. Allowed: {sorted(ALLOWED_SEGMENT_FILTER_CREATE_FIELDS)}'
        )
    missing = REQUIRED_SEGMENT_FILTER_CREATE_FIELDS - set(fields)
    if missing:
        raise ValueError(f'Missing required field(s) for create: {sorted(missing)}')

    p = proposals.register('segment_filter_create', '', fields, {}, reason)
    return {
        'proposal_id': p.id,
        'reason': reason,
        'summary': {
            'action': 'CREATE SegmentFilter',
            'after': fields,
        },
    }


def apply_segment_filter_create(client: QsaleClient, proposal_id: str) -> dict[str, Any]:
    """Apply a previously-staged SegmentFilter creation. Single-use."""
    p = proposals.pop(proposal_id)
    if p.kind != 'segment_filter_create':
        raise ValueError(f'Proposal {proposal_id} is kind={p.kind!r}, not segment_filter_create')
    return client.post('/api/segment-filters/', json=p.fields)


def propose_segment_filter_update(
    client: QsaleClient,
    filter_id: str,
    value: Any,
    reason: str = '',
) -> dict[str, Any]:
    """Stage a SegmentFilter value update for explicit approval. Does NOT write.

    Fetches current filter (NEW endpoint) to build before/after diff. `value` is
    a JSON array for IN/NOT_IN operators (list of Sletat resort IDs etc.) or a
    scalar for EQ/GTE/LTE. After the user OKs, call
    apply_segment_filter_update(proposal_id).
    """
    current = get_segment_filter(client, filter_id)
    before_value = current.get('value')
    fields = {'value': value}

    p = proposals.register('segment_filter_update', filter_id, fields, {'value': before_value}, reason)
    return {
        'proposal_id': p.id,
        'filter_id': filter_id,
        'reason': reason,
        'changes': [
            {'field': 'value', 'before': before_value, 'after': value},
        ],
    }


def apply_segment_filter_update(client: QsaleClient, proposal_id: str) -> dict[str, Any]:
    """Apply a previously-staged SegmentFilter value update. Single-use."""
    p = proposals.pop(proposal_id)
    if p.kind != 'segment_filter_update':
        raise ValueError(f'Proposal {proposal_id} is kind={p.kind!r}, not segment_filter_update')
    return client.patch(f'/api/segment-filters/{p.target_id}/', json=p.fields)


def propose_segment_filter_delete(
    client: QsaleClient,
    filter_id: str,
    reason: str = '',
) -> dict[str, Any]:
    """Stage a SegmentFilter deletion for explicit approval. Does NOT write.

    Fetches current state for the before-state diff. After the user OKs, call
    apply_segment_filter_delete(proposal_id).
    """
    current = get_segment_filter(client, filter_id)
    before = {
        'segment': current.get('segment'),
        'property': current.get('property'),
        'operator': current.get('operator'),
        'value': current.get('value'),
    }
    p = proposals.register('segment_filter_delete', filter_id, {}, before, reason)
    return {
        'proposal_id': p.id,
        'filter_id': filter_id,
        'reason': reason,
        'summary': {
            'action': 'DELETE SegmentFilter',
            'before': before,
        },
    }


def apply_segment_filter_delete(client: QsaleClient, proposal_id: str) -> dict[str, Any] | None:
    """Apply a previously-staged SegmentFilter deletion. Single-use."""
    p = proposals.pop(proposal_id)
    if p.kind != 'segment_filter_delete':
        raise ValueError(f'Proposal {proposal_id} is kind={p.kind!r}, not segment_filter_delete')
    return client.delete(f'/api/segment-filters/{p.target_id}/')


# ---------------------------------------------------------------------------
# §FR-4 M2M link/unlink tools — DictionaryItem ↔ Segment
# ---------------------------------------------------------------------------

def propose_link_di_segment(
    client: QsaleClient,
    dictionary_item_id: str,
    segment_id: str,
    reason: str = '',
) -> dict[str, Any]:
    """Stage a DictionaryItem ↔ Segment link for explicit approval. Does NOT write.

    Validation (model compatibility) is enforced server-side; 400 proxied.
    After the user OKs, call apply_link_di_segment(proposal_id).
    """
    fields = {'segment_id': segment_id}
    p = proposals.register('link_di_segment', dictionary_item_id, fields, {}, reason)
    return {
        'proposal_id': p.id,
        'reason': reason,
        'summary': {
            'action': 'LINK DictionaryItem → Segment',
            'dictionary_item_id': dictionary_item_id,
            'segment_id': segment_id,
        },
    }


def apply_link_di_segment(client: QsaleClient, proposal_id: str) -> dict[str, Any]:
    """Apply a previously-staged DI↔Segment link. Single-use."""
    p = proposals.pop(proposal_id)
    if p.kind != 'link_di_segment':
        raise ValueError(f'Proposal {proposal_id} is kind={p.kind!r}, not link_di_segment')
    return client.post(
        f'/api/dictionary-items/{p.target_id}/segments/',
        json={'segment_id': p.fields['segment_id']},
    )


def propose_unlink_di_segment(
    client: QsaleClient,
    dictionary_item_id: str,
    segment_id: str,
    reason: str = '',
) -> dict[str, Any]:
    """Stage a DictionaryItem ↔ Segment unlink for explicit approval. Does NOT write.

    Fetches current linked segments to confirm the link exists (before-state).
    After the user OKs, call apply_unlink_di_segment(proposal_id).
    """
    current_links = list_di_segments(client, dictionary_item_id)
    before = {'linked_segments': [s.get('id') for s in current_links]}
    fields = {'segment_id': segment_id}
    p = proposals.register('unlink_di_segment', dictionary_item_id, fields, before, reason)
    return {
        'proposal_id': p.id,
        'reason': reason,
        'summary': {
            'action': 'UNLINK DictionaryItem ← Segment',
            'dictionary_item_id': dictionary_item_id,
            'segment_id': segment_id,
            'currently_linked_segment_ids': before['linked_segments'],
        },
    }


def apply_unlink_di_segment(client: QsaleClient, proposal_id: str) -> dict[str, Any] | None:
    """Apply a previously-staged DI↔Segment unlink. Single-use."""
    p = proposals.pop(proposal_id)
    if p.kind != 'unlink_di_segment':
        raise ValueError(f'Proposal {proposal_id} is kind={p.kind!r}, not unlink_di_segment')
    return client.delete(
        f'/api/dictionary-items/{p.target_id}/segments/{p.fields["segment_id"]}/'
    )


# ---------------------------------------------------------------------------
# §FR-4 M2M link/unlink tools — ProductCategory ↔ Segment
# ---------------------------------------------------------------------------

def propose_link_pc_segment(
    client: QsaleClient,
    category_id: str,
    segment_id: str,
    reason: str = '',
) -> dict[str, Any]:
    """Stage a ProductCategory ↔ Segment link for explicit approval. Does NOT write.

    After link, qa-server calls category.set_cache() explicitly (no m2m_changed
    signal). 400/404 proxied. After the user OKs, call apply_link_pc_segment(proposal_id).
    """
    fields = {'segment_id': segment_id}
    p = proposals.register('link_pc_segment', category_id, fields, {}, reason)
    return {
        'proposal_id': p.id,
        'reason': reason,
        'summary': {
            'action': 'LINK ProductCategory → Segment',
            'category_id': category_id,
            'segment_id': segment_id,
        },
    }


def apply_link_pc_segment(client: QsaleClient, proposal_id: str) -> dict[str, Any]:
    """Apply a previously-staged PC↔Segment link. Single-use."""
    p = proposals.pop(proposal_id)
    if p.kind != 'link_pc_segment':
        raise ValueError(f'Proposal {proposal_id} is kind={p.kind!r}, not link_pc_segment')
    return client.post(
        f'/api/product-categories/{p.target_id}/segments/',
        json={'segment_id': p.fields['segment_id']},
    )


def propose_unlink_pc_segment(
    client: QsaleClient,
    category_id: str,
    segment_id: str,
    reason: str = '',
) -> dict[str, Any]:
    """Stage a ProductCategory ↔ Segment unlink for explicit approval. Does NOT write.

    Fetches current linked segments to confirm the link exists (before-state).
    After the user OKs, call apply_unlink_pc_segment(proposal_id).
    """
    current_links = list_pc_segments(client, category_id)
    before = {'linked_segments': [s.get('id') for s in current_links]}
    fields = {'segment_id': segment_id}
    p = proposals.register('unlink_pc_segment', category_id, fields, before, reason)
    return {
        'proposal_id': p.id,
        'reason': reason,
        'summary': {
            'action': 'UNLINK ProductCategory ← Segment',
            'category_id': category_id,
            'segment_id': segment_id,
            'currently_linked_segment_ids': before['linked_segments'],
        },
    }


def apply_unlink_pc_segment(client: QsaleClient, proposal_id: str) -> dict[str, Any] | None:
    """Apply a previously-staged PC↔Segment unlink. Single-use."""
    p = proposals.pop(proposal_id)
    if p.kind != 'unlink_pc_segment':
        raise ValueError(f'Proposal {proposal_id} is kind={p.kind!r}, not unlink_pc_segment')
    return client.delete(
        f'/api/product-categories/{p.target_id}/segments/{p.fields["segment_id"]}/'
    )


# ---------------------------------------------------------------------------
# §FR-5 Task trigger tools
# ---------------------------------------------------------------------------

def propose_run_update_all_dicts(
    client: QsaleClient,
    reason: str = '',
) -> dict[str, Any]:
    """Stage an update_all_dicts task trigger for explicit approval. Does NOT enqueue.

    The task is a Celery Singleton — self-deduplicates if already running.
    Response is 202 (fire-and-forget; not a sync result). After the user OKs,
    call apply_run_update_all_dicts(proposal_id).
    """
    fields: dict[str, Any] = {}
    p = proposals.register('run_update_all_dicts', '', fields, {}, reason)
    return {
        'proposal_id': p.id,
        'reason': reason,
        'warning': (
            f'Will trigger update_all_dicts_actual_task for company {client.company_id}. '
            'Async — dictionary caches recalculated in background.'
        ),
    }


def apply_run_update_all_dicts(client: QsaleClient, proposal_id: str) -> dict[str, Any]:
    """Apply a previously-staged update_all_dicts task trigger. Single-use."""
    p = proposals.pop(proposal_id)
    if p.kind != 'run_update_all_dicts':
        raise ValueError(f'Proposal {proposal_id} is kind={p.kind!r}, not run_update_all_dicts')
    return client.post('/api/tasks/update-all-dicts/')


def propose_run_set_category_for_products(
    client: QsaleClient,
    category_id: str,
    reason: str = '',
) -> dict[str, Any]:
    """Stage a set_category_for_products task trigger for explicit approval. Does NOT enqueue.

    category_id: ProductCategory UUID — the category whose linked Segments will
    define product membership. Response is 202 (fire-and-forget). After the user
    OKs, call apply_run_set_category_for_products(proposal_id).
    """
    fields = {'category_id': category_id}
    p = proposals.register('run_set_category_for_products', '', fields, {}, reason)
    return {
        'proposal_id': p.id,
        'reason': reason,
        'warning': (
            f'Will trigger update_product_categories for category {category_id}. '
            'Async — products recategorized in background.'
        ),
    }


def apply_run_set_category_for_products(client: QsaleClient, proposal_id: str) -> dict[str, Any]:
    """Apply a previously-staged set_category_for_products task trigger. Single-use."""
    p = proposals.pop(proposal_id)
    if p.kind != 'run_set_category_for_products':
        raise ValueError(
            f'Proposal {proposal_id} is kind={p.kind!r}, not run_set_category_for_products'
        )
    return client.post(
        '/api/tasks/set-category-for-products/',
        json={'category_id': p.fields['category_id']},
    )


# ---------------------------------------------------------------------------
# Compact helpers for new types
# ---------------------------------------------------------------------------

def _compact_dictionary_item(i: dict[str, Any]) -> dict[str, Any]:
    """Trim DictionaryItem to list-view essentials."""
    return {
        'id': i.get('id'),
        'name': i.get('name'),
        'dictionary': i.get('dictionary'),
        'description': i.get('description'),
        'sort': i.get('sort'),
        'data': i.get('data'),
    }


def _compact_segment(s: dict[str, Any]) -> dict[str, Any]:
    """Trim Segment to list-view essentials."""
    return {
        'id': s.get('id'),
        'name': s.get('name'),
        'model': s.get('model'),
        'count': s.get('count'),
        'system': s.get('system'),
    }


# ---------------------------------------------------------------------------
# Bulk apply: one approval covers N already-staged proposals of any kind.
# Stops on first failure, returns per-proposal results.
# ---------------------------------------------------------------------------

_BULK_APPLY_REGISTRY: dict[str, Any] = {
    'page_update': apply_page_update,
    'navigation_item_update': apply_navigation_item_update,
    'navigation_item_create': apply_navigation_item_create,
    'mail_template_create': apply_mail_template_create,
    'mail_template_update': apply_mail_template_update,
    'promotion_trigger_create': apply_promotion_trigger_create,
    'category_create': apply_category_create,
    'category_delete': apply_category_delete,
    'dictionary_item_create': apply_dictionary_item_create,
    'dictionary_item_delete': apply_dictionary_item_delete,
    'segment_create': apply_segment_create,
    'segment_delete': apply_segment_delete,
    'segment_filter_create': apply_segment_filter_create,
    'segment_filter_update': apply_segment_filter_update,
    'segment_filter_delete': apply_segment_filter_delete,
    'link_di_segment': apply_link_di_segment,
    'unlink_di_segment': apply_unlink_di_segment,
    'link_pc_segment': apply_link_pc_segment,
    'unlink_pc_segment': apply_unlink_pc_segment,
    'run_update_all_dicts': apply_run_update_all_dicts,
    'run_set_category_for_products': apply_run_set_category_for_products,
}


def bulk_apply(client: QsaleClient, proposal_ids: list[str]) -> dict[str, Any]:
    """Apply N already-staged proposals of any kind in order. One approval.

    Each proposal is dispatched to its kind-specific apply function. Stops on
    first failure, returns per-proposal results with success/error per item.
    No rollback — manual cleanup via delete tools if needed.

    Use case: any workflow that stages many proposals (e.g. programmatic SEO
    rolling out N category trees, each needing DI + Segment + PC + links).
    """
    if not proposal_ids:
        raise ValueError('proposal_ids must be non-empty')
    results: list[dict[str, Any]] = []
    for pid in proposal_ids:
        p = proposals.get(pid)
        if p is None:
            results.append({'proposal_id': pid, 'status': 'not_found'})
            return {'completed': len(results) - 1, 'total': len(proposal_ids), 'results': results}
        apply_fn = _BULK_APPLY_REGISTRY.get(p.kind)
        if apply_fn is None:
            results.append({'proposal_id': pid, 'status': 'unsupported_kind', 'kind': p.kind})
            return {'completed': len(results) - 1, 'total': len(proposal_ids), 'results': results}
        try:
            result = apply_fn(client, pid)
            results.append({'proposal_id': pid, 'status': 'ok', 'kind': p.kind, 'result': result})
        except Exception as e:
            results.append({'proposal_id': pid, 'status': 'failed', 'kind': p.kind, 'error': str(e)})
            return {'completed': len(results) - 1, 'total': len(proposal_ids), 'results': results}
    return {'completed': len(proposal_ids), 'total': len(proposal_ids), 'results': results}


# ---------------------------------------------------------------------------
# Products (read-only) — for spot-checks and pipeline verification.
# ---------------------------------------------------------------------------


def _compact_product(p: dict[str, Any]) -> dict[str, Any]:
    """Trim Product API response — keep fields useful for spot-checks."""
    return {
        'id': p.get('id'),
        'ext_id': p.get('ext_id'),
        'name': p.get('name'),
        'slug': p.get('slug'),
        'category': p.get('category'),
        'published': p.get('published'),
        'sort': p.get('sort'),
        'price': p.get('price'),
        'share_path': p.get('share_path'),
    }


def list_products(
    client: QsaleClient,
    name: str | None = None,
    published: bool | None = None,
    segment_filters: dict[str, str] | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict[str, Any]:
    """List products from /api/products/ (paginated).

    name: icontains match on Product.name.
    published: filter by published flag.
    segment_filters: dict of {SegmentProperty.id.hex: Segment.id.hex} — filter
        products matching the given segment. Use UUID strings (with or without
        hyphens). Multiple entries AND together. Only SegmentProperties with
        is_filter=True and at least one system_segment are accepted — others
        are silently ignored by the API. Check `GET /api/products/filters/`
        to see what is filterable.
    page, page_size: pagination (default page_size=20).

    Returns: {count, page, results: [<compact product>, ...]}.
    """
    params: dict[str, Any] = {'page': page, 'page_size': page_size}
    if name:
        params['name'] = name
    if published is not None:
        params['published'] = 'true' if published else 'false'
    for prop_id, seg_id in (segment_filters or {}).items():
        params[prop_id.replace('-', '')] = seg_id.replace('-', '')
    raw = client.get('/api/products/', params=params) or {}
    if isinstance(raw, list):
        return {'count': len(raw), 'page': 1, 'results': [_compact_product(p) for p in raw]}
    return {
        'count': raw.get('count'),
        'page': raw.get('page'),
        'next_page': raw.get('next_page'),
        'results': [_compact_product(p) for p in (raw.get('results') or [])],
    }


def get_product(client: QsaleClient, product_id: str) -> dict[str, Any]:
    """Get a single product by UUID. Returns full detail incl. data, images, attachments."""
    return client.get(f'/api/products/{product_id}/')


# ---------------------------------------------------------------------------
# §FR-4 Dictionary write tools
# ---------------------------------------------------------------------------

ALLOWED_DICTIONARY_CREATE_FIELDS = {
    'name',
    'description',
    'data',
    'allowed_segment_models',
}

REQUIRED_DICTIONARY_CREATE_FIELDS = {'name'}


def propose_dictionary_create(
    client: QsaleClient,
    fields: dict[str, Any],
    reason: str = '',
) -> dict[str, Any]:
    """Stage a Dictionary creation for explicit approval. Does NOT write.

    Required fields: name. Optional: description, data (dict),
    allowed_segment_models (list of SegmentModel UUIDs — controls which segment
    types can link this dictionary's items). After the user OKs, call
    apply_dictionary_create(proposal_id).
    """
    bad = set(fields) - ALLOWED_DICTIONARY_CREATE_FIELDS
    if bad:
        raise ValueError(
            f'Field(s) not in whitelist: {sorted(bad)}. Allowed: {sorted(ALLOWED_DICTIONARY_CREATE_FIELDS)}'
        )
    missing = REQUIRED_DICTIONARY_CREATE_FIELDS - set(fields)
    if missing:
        raise ValueError(f'Missing required field(s) for create: {sorted(missing)}')

    p = proposals.register('dictionary_create', '', fields, {}, reason)
    return {
        'proposal_id': p.id,
        'reason': reason,
        'summary': {
            'action': 'CREATE Dictionary',
            'after': fields,
        },
    }


def apply_dictionary_create(client: QsaleClient, proposal_id: str) -> dict[str, Any]:
    """Apply a previously-staged Dictionary creation. Single-use."""
    p = proposals.pop(proposal_id)
    if p.kind != 'dictionary_create':
        raise ValueError(f'Proposal {proposal_id} is kind={p.kind!r}, not dictionary_create')
    return client.post('/api/dictionaries/', json=p.fields)


def propose_dictionary_delete(
    client: QsaleClient,
    dictionary_id: str,
    reason: str = '',
) -> dict[str, Any]:
    """Stage a Dictionary deletion for explicit approval. Does NOT write.

    Fetches current state for diff. API will 400 if items are still in use; that
    error is proxied at apply time. After the user OKs, call
    apply_dictionary_delete(proposal_id).
    """
    current = get_dictionary(client, dictionary_id)
    before = {
        'name': current.get('name'),
        'description': current.get('description'),
        'allowed_segment_models': current.get('allowed_segment_models'),
    }
    p = proposals.register('dictionary_delete', dictionary_id, {}, before, reason)
    return {
        'proposal_id': p.id,
        'dictionary_id': dictionary_id,
        'reason': reason,
        'summary': {
            'action': 'DELETE Dictionary',
            'before': before,
        },
    }


def apply_dictionary_delete(client: QsaleClient, proposal_id: str) -> dict[str, Any] | None:
    """Apply a previously-staged Dictionary deletion. Single-use."""
    p = proposals.pop(proposal_id)
    if p.kind != 'dictionary_delete':
        raise ValueError(f'Proposal {proposal_id} is kind={p.kind!r}, not dictionary_delete')
    return client.delete(f'/api/dictionaries/{p.target_id}/')


# ---------------------------------------------------------------------------
# §FR-5 SegmentProperty write tools
# ---------------------------------------------------------------------------

ALLOWED_SEGMENT_PROPERTY_CREATE_FIELDS = {
    'model',
    'name',
    'slug',
    'group',
    'field',
    'path',
    'type',
    'widget',
    'parent',
    'remote_model',
    'dictionary',
    'search_weight',
    'is_editable',
    'is_enum',
    'is_filter',
    'is_many',
    'is_required',
    'is_segment_filter',
    'is_visible',
    'is_readable',
    'is_batch_upload',
    'is_selector',
    'data',
    'sort',
}

REQUIRED_SEGMENT_PROPERTY_CREATE_FIELDS = {'model', 'name', 'type'}

ALLOWED_SEGMENT_PROPERTY_UPDATE_FIELDS = ALLOWED_SEGMENT_PROPERTY_CREATE_FIELDS - {'model'}


def propose_segment_property_create(
    client: QsaleClient,
    fields: dict[str, Any],
    reason: str = '',
) -> dict[str, Any]:
    """Stage a SegmentProperty creation for explicit approval. Does NOT write.

    Required fields: model (SegmentModel UUID), name, type. Optional: slug, group,
    field (default 'data'), path, widget, parent (UUID for child property),
    remote_model, dictionary (UUID linking enum choices to a Dictionary),
    is_* flags, data, sort. After the user OKs, call
    apply_segment_property_create(proposal_id).
    """
    bad = set(fields) - ALLOWED_SEGMENT_PROPERTY_CREATE_FIELDS
    if bad:
        raise ValueError(
            f'Field(s) not in whitelist: {sorted(bad)}. Allowed: {sorted(ALLOWED_SEGMENT_PROPERTY_CREATE_FIELDS)}'
        )
    missing = REQUIRED_SEGMENT_PROPERTY_CREATE_FIELDS - set(fields)
    if missing:
        raise ValueError(f'Missing required field(s) for create: {sorted(missing)}')

    p = proposals.register('segment_property_create', '', fields, {}, reason)
    return {
        'proposal_id': p.id,
        'reason': reason,
        'summary': {
            'action': 'CREATE SegmentProperty',
            'after': fields,
        },
    }


def apply_segment_property_create(client: QsaleClient, proposal_id: str) -> dict[str, Any]:
    """Apply a previously-staged SegmentProperty creation. Single-use."""
    p = proposals.pop(proposal_id)
    if p.kind != 'segment_property_create':
        raise ValueError(f'Proposal {proposal_id} is kind={p.kind!r}, not segment_property_create')
    return client.post('/api/segment-properties/', json=p.fields)


def propose_segment_property_update(
    client: QsaleClient,
    property_id: str,
    fields: dict[str, Any],
    reason: str = '',
) -> dict[str, Any]:
    """Stage a SegmentProperty update for explicit approval. Does NOT write.

    Sends only the keys in `fields` as a PATCH. Use this to retype a property
    (e.g. flip widget=enum / type=str → widget='' / type=dict when introducing
    a dictionary-backed brand). `model` cannot be changed via this path.
    """
    bad = set(fields) - ALLOWED_SEGMENT_PROPERTY_UPDATE_FIELDS
    if bad:
        raise ValueError(
            f'Field(s) not in whitelist: {sorted(bad)}. Allowed: {sorted(ALLOWED_SEGMENT_PROPERTY_UPDATE_FIELDS)}'
        )
    current = get_segment_property(client, property_id)
    before = {k: current.get(k) for k in fields}
    p = proposals.register('segment_property_update', property_id, fields, before, reason)
    return {
        'proposal_id': p.id,
        'property_id': property_id,
        'reason': reason,
        'summary': {
            'action': 'UPDATE SegmentProperty',
            'before': before,
            'after': fields,
        },
    }


def apply_segment_property_update(client: QsaleClient, proposal_id: str) -> dict[str, Any]:
    """Apply a previously-staged SegmentProperty update. Single-use."""
    p = proposals.pop(proposal_id)
    if p.kind != 'segment_property_update':
        raise ValueError(f'Proposal {proposal_id} is kind={p.kind!r}, not segment_property_update')
    return client.patch(f'/api/segment-properties/{p.target_id}/', json=p.fields)


def propose_segment_property_delete(
    client: QsaleClient,
    property_id: str,
    reason: str = '',
) -> dict[str, Any]:
    """Stage a SegmentProperty deletion for explicit approval. Does NOT write."""
    current = get_segment_property(client, property_id)
    before = {
        'name': current.get('name'),
        'slug': current.get('slug'),
        'model': current.get('model'),
        'type': current.get('type'),
        'widget': current.get('widget'),
    }
    p = proposals.register('segment_property_delete', property_id, {}, before, reason)
    return {
        'proposal_id': p.id,
        'property_id': property_id,
        'reason': reason,
        'summary': {
            'action': 'DELETE SegmentProperty',
            'before': before,
        },
    }


def apply_segment_property_delete(client: QsaleClient, proposal_id: str) -> dict[str, Any] | None:
    """Apply a previously-staged SegmentProperty deletion. Single-use."""
    p = proposals.pop(proposal_id)
    if p.kind != 'segment_property_delete':
        raise ValueError(f'Proposal {proposal_id} is kind={p.kind!r}, not segment_property_delete')
    return client.delete(f'/api/segment-properties/{p.target_id}/')


# ---------------------------------------------------------------------------
# §FR-6 SegmentPropertyChoice tools
# ---------------------------------------------------------------------------

ALLOWED_SEGMENT_PROPERTY_CHOICE_CREATE_FIELDS = {
    'segment_property',
    'label',
    'value',
    'is_published',
    'sort',
}

REQUIRED_SEGMENT_PROPERTY_CHOICE_CREATE_FIELDS = {'segment_property', 'value'}


def list_segment_property_choices(
    client: QsaleClient,
    segment_property_id: str | None = None,
    limit: int = 200,
) -> list[dict[str, Any]]:
    """List SegmentPropertyChoice rows. Filter by parent property UUID."""
    params: dict[str, Any] = {'limit': limit}
    if segment_property_id:
        params['segment_property'] = segment_property_id
    res = client.get('/api/segment-property-choices/', params=params)
    rows = res.get('results') if isinstance(res, dict) else res
    return rows or []


def propose_segment_property_choice_create(
    client: QsaleClient,
    fields: dict[str, Any],
    reason: str = '',
) -> dict[str, Any]:
    """Stage a SegmentPropertyChoice creation for explicit approval. Does NOT write.

    Required fields: segment_property (UUID of parent property), value.
    Optional: label (display text, defaults to value), is_published, sort.
    After the user OKs, call apply_segment_property_choice_create(proposal_id).
    """
    bad = set(fields) - ALLOWED_SEGMENT_PROPERTY_CHOICE_CREATE_FIELDS
    if bad:
        raise ValueError(
            f'Field(s) not in whitelist: {sorted(bad)}. '
            f'Allowed: {sorted(ALLOWED_SEGMENT_PROPERTY_CHOICE_CREATE_FIELDS)}'
        )
    missing = REQUIRED_SEGMENT_PROPERTY_CHOICE_CREATE_FIELDS - set(fields)
    if missing:
        raise ValueError(f'Missing required field(s) for create: {sorted(missing)}')

    p = proposals.register('segment_property_choice_create', '', fields, {}, reason)
    return {
        'proposal_id': p.id,
        'reason': reason,
        'summary': {
            'action': 'CREATE SegmentPropertyChoice',
            'after': fields,
        },
    }


def apply_segment_property_choice_create(client: QsaleClient, proposal_id: str) -> dict[str, Any]:
    """Apply a previously-staged SegmentPropertyChoice creation. Single-use."""
    p = proposals.pop(proposal_id)
    if p.kind != 'segment_property_choice_create':
        raise ValueError(
            f'Proposal {proposal_id} is kind={p.kind!r}, not segment_property_choice_create'
        )
    return client.post('/api/segment-property-choices/', json=p.fields)


def propose_segment_property_choice_delete(
    client: QsaleClient,
    choice_id: str,
    reason: str = '',
) -> dict[str, Any]:
    """Stage a SegmentPropertyChoice deletion for explicit approval. Does NOT write."""
    current = client.get(f'/api/segment-property-choices/{choice_id}/')
    before = {
        'segment_property': current.get('segment_property'),
        'value': current.get('value'),
        'label': current.get('label'),
    }
    p = proposals.register('segment_property_choice_delete', choice_id, {}, before, reason)
    return {
        'proposal_id': p.id,
        'choice_id': choice_id,
        'reason': reason,
        'summary': {
            'action': 'DELETE SegmentPropertyChoice',
            'before': before,
        },
    }


def apply_segment_property_choice_delete(client: QsaleClient, proposal_id: str) -> dict[str, Any] | None:
    """Apply a previously-staged SegmentPropertyChoice deletion. Single-use."""
    p = proposals.pop(proposal_id)
    if p.kind != 'segment_property_choice_delete':
        raise ValueError(
            f'Proposal {proposal_id} is kind={p.kind!r}, not segment_property_choice_delete'
        )
    return client.delete(f'/api/segment-property-choices/{p.target_id}/')
