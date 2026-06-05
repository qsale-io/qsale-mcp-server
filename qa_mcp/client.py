"""HTTP client for the QSale REST API.

Authentication is token-based: requests carry the ``Authorization: Token …``
header together with the ``X-QA-Company`` tenant header. Configuration is
sourced exclusively from environment variables so the same module image can
be reused for any tenant / installation without code changes.

Required environment:
    QSALE_API_TOKEN     — employee API token issued in the QSale admin panel.
    QSALE_COMPANY_ID    — Company UUID to operate against (tenant scope).

Optional environment:
    QSALE_API_BASE      — Base URL of the QSale REST API.
                          Defaults to https://console.qsale.io (the managed
                          QSale instance). Self-hosted installations should
                          point this at their own console host.
    QSALE_CLIENT_TYPE   — Value of the ``X-QA-Client-Type`` header.
                          Defaults to ``WEB``.
"""

from __future__ import annotations

import os
from typing import Any

import httpx

DEFAULT_BASE = 'https://console.qsale.io'
DEFAULT_CLIENT_TYPE = 'WEB'


class QsaleClient:
    def __init__(
        self,
        token: str | None = None,
        company_id: str | None = None,
        base_url: str | None = None,
        client_type: str | None = None,
    ) -> None:
        self.token = token or os.environ.get('QSALE_API_TOKEN', '')
        self.company_id = company_id or os.environ.get('QSALE_COMPANY_ID', '')
        self.base_url = (base_url or os.environ.get('QSALE_API_BASE', DEFAULT_BASE)).rstrip('/')
        self.client_type = client_type or os.environ.get('QSALE_CLIENT_TYPE', DEFAULT_CLIENT_TYPE)
        if not self.token:
            raise RuntimeError('QSALE_API_TOKEN env var is required')
        if not self.company_id:
            raise RuntimeError('QSALE_COMPANY_ID env var is required')
        self._http = httpx.Client(
            base_url=self.base_url,
            headers={
                'Authorization': f'Token {self.token}',
                'X-QA-Company': self.company_id,
                'X-QA-Client-Type': self.client_type,
                'Accept': 'application/json',
            },
            timeout=30.0,
        )

    def request(self, method: str, path: str, **kwargs) -> Any:
        r = self._http.request(method, path, **kwargs)
        if r.status_code >= 400:
            raise QsaleError(r.status_code, r.text, method, path)
        if not r.content:
            return None
        try:
            return r.json()
        except ValueError:
            return r.text

    def get(self, path: str, **kwargs) -> Any:
        return self.request('GET', path, **kwargs)

    def post(self, path: str, json: Any = None, **kwargs) -> Any:
        return self.request('POST', path, json=json, **kwargs)

    def patch(self, path: str, json: Any = None, **kwargs) -> Any:
        return self.request('PATCH', path, json=json, **kwargs)

    def patch_file(self, path: str, field: str, file_path: str, content_type: str | None = None) -> Any:
        """PATCH a multipart file upload (single field). Used for file-typed frontend settings."""
        import mimetypes
        import pathlib

        p = pathlib.Path(file_path)
        ct = content_type or mimetypes.guess_type(str(p))[0] or 'application/octet-stream'
        with p.open('rb') as fh:
            r = self._http.patch(path, files={field: (p.name, fh, ct)})
        if r.status_code >= 400:
            raise QsaleError(r.status_code, r.text, 'PATCH', path)
        if not r.content:
            return None
        try:
            return r.json()
        except ValueError:
            return r.text

    def put(self, path: str, json: Any = None, **kwargs) -> Any:
        return self.request('PUT', path, json=json, **kwargs)

    def delete(self, path: str, **kwargs) -> Any:
        return self.request('DELETE', path, **kwargs)


class QsaleError(RuntimeError):
    def __init__(self, status: int, body: str, method: str, path: str) -> None:
        super().__init__(f'{method} {path} → HTTP {status}: {body[:300]}')
        self.status = status
        self.body = body
