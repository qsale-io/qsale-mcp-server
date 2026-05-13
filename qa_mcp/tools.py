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
}

# Fields allowed in page proposals — SEO + content. `slug` excluded (renames URL).
ALLOWED_PAGE_FIELDS = {
    'meta_title',
    'meta_description',
    'meta_keywords',
    'canonical_url',
    'title',
    'body',
}


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


def list_redirect_sites(client: QsaleClient) -> list[dict[str, Any]]:
    rows = client.get('/api/redirect-sites/')
    return rows or []


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
) -> dict[str, Any]:
    body = {
        'site': site_id,
        'url': url,
        'target_url': target_url,
        'is_permanent': is_permanent,
        'priority': priority,
        'is_active': True,
    }
    return client.post('/api/url-redirects/', json=body)


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
