"""In-memory proposal store for write operations requiring explicit approval.

Lives in the MCP server process. Lost on restart by design — proposals are
short-lived (propose → user reviews diff → apply). No persistence layer.

Flow:
  1. `propose_page_update(...)` registers a pending change, returns proposal_id + diff.
  2. User reviews diff in chat, says OK.
  3. `apply_page_update(proposal_id)` reads from this store and writes via API.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class Proposal:
    id: str
    kind: str                       # 'page_update', etc.
    target_id: str                  # row UUID being modified
    fields: dict[str, Any]          # patch payload
    before: dict[str, Any]          # current values of the same keys (for diff display)
    reason: str
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


_STORE: dict[str, Proposal] = {}


def register(kind: str, target_id: str, fields: dict[str, Any], before: dict[str, Any], reason: str) -> Proposal:
    p = Proposal(
        id=str(uuid.uuid4()),
        kind=kind,
        target_id=target_id,
        fields=fields,
        before=before,
        reason=reason,
    )
    _STORE[p.id] = p
    return p


def get(proposal_id: str) -> Proposal:
    if proposal_id not in _STORE:
        raise KeyError(f'proposal_id {proposal_id!r} not found (or expired with server restart)')
    return _STORE[proposal_id]


def pop(proposal_id: str) -> Proposal:
    """Read + remove. Called by apply_*; proposals are single-use."""
    p = get(proposal_id)
    del _STORE[proposal_id]
    return p


def list_pending(kind: str | None = None) -> list[Proposal]:
    if kind is None:
        return list(_STORE.values())
    return [p for p in _STORE.values() if p.kind == kind]
