"""HTTPX client for console.qsale.io API.

Auth: Token (qa-console "@nuxtjs/auth-next" Local scheme, type: 'Token').
Required env:
  QSALE_API_TOKEN     — employee API token
  QSALE_COMPANY_ID    — Company UUID (default: AIST)
Optional env:
  QSALE_API_BASE      — defaults to https://console.qsale.io
  QSALE_CLIENT_TYPE   — defaults to 'WEB'
"""
from __future__ import annotations

import os
from typing import Any

import httpx

DEFAULT_BASE = 'https://console.qsale.io'
AIST_COMPANY = '6d6d8a2b-34ac-4073-bd6d-bcc82e83ba86'


class QsaleClient:
    def __init__(
        self,
        token: str | None = None,
        company_id: str | None = None,
        base_url: str | None = None,
        client_type: str | None = None,
    ) -> None:
        self.token = token or os.environ.get('QSALE_API_TOKEN', '')
        self.company_id = company_id or os.environ.get('QSALE_COMPANY_ID', AIST_COMPANY)
        self.base_url = (base_url or os.environ.get('QSALE_API_BASE', DEFAULT_BASE)).rstrip('/')
        self.client_type = client_type or os.environ.get('QSALE_CLIENT_TYPE', 'WEB')
        if not self.token:
            raise RuntimeError('QSALE_API_TOKEN env var is required')
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

    def put(self, path: str, json: Any = None, **kwargs) -> Any:
        return self.request('PUT', path, json=json, **kwargs)

    def delete(self, path: str, **kwargs) -> Any:
        return self.request('DELETE', path, **kwargs)


class QsaleError(RuntimeError):
    def __init__(self, status: int, body: str, method: str, path: str) -> None:
        super().__init__(f'{method} {path} → HTTP {status}: {body[:300]}')
        self.status = status
        self.body = body
