"""WorldClient — the plugin as a thin client of worldd.

HMAC per request: signature = HMAC-SHA256(secret, f"{ts}.{body}").
Idempotency keys on every mutation. Server scenes render client-side.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
import uuid

import httpx

API_VERSION = "1"


class WorldError(RuntimeError):
    pass


class WorldClient:
    def __init__(self, base_url: str, tenant: str, secret: str,
                 timeout: float = 15.0):
        self._base = base_url.rstrip("/")
        self._tenant = tenant
        self._secret = secret.encode()
        self._timeout = timeout

    def _headers(self, body: bytes) -> dict[str, str]:
        ts = str(int(time.time()))
        sig = hmac.new(self._secret, f"{ts}.".encode() + body,
                       hashlib.sha256).hexdigest()
        return {
            "Content-Type": "application/json",
            "X-Ascent-Tenant": self._tenant,
            "X-Ascent-Ts": ts,
            "X-Ascent-Signature": sig,
            "X-Ascent-Api": API_VERSION,
        }

    async def _post(self, path: str, payload: dict) -> dict:
        body = json.dumps(payload, separators=(",", ":")).encode()
        async with httpx.AsyncClient(timeout=self._timeout) as c:
            r = await c.post(self._base + path, content=body,
                             headers=self._headers(body))
        if r.status_code >= 400:
            try:
                detail = r.json().get("detail", r.text)
            except Exception:
                detail = r.text
            raise WorldError(f"worldd {r.status_code}: {detail}")
        return r.json()

    async def scene(self, luna_user: str) -> dict:
        out = await self._post("/v1/scene", {"player": luna_user})
        return out["scene"]

    async def act(self, luna_user: str, option: str, text: str) -> dict:
        out = await self._post("/v1/act", {
            "player": luna_user, "option": option, "text": text,
            "idem": str(uuid.uuid4()),
        })
        return out["scene"]

    async def character(self, luna_user: str) -> dict:
        return await self._post("/v1/character", {"player": luna_user})
