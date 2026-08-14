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

    async def import_doc(self, luna_user: str, doc: dict) -> dict:
        """One-time local→world character migration (007 Phase 1)."""
        return await self._post("/v1/import", {"player": luna_user,
                                               "doc": doc})

    # ── 010: score & community ───────────────────────────────────────────

    async def leaderboard(self, luna_user: str) -> dict:
        return await self._post("/v1/leaderboard", {"player": luna_user})

    # ── 022/003: presence ────────────────────────────────────────────────

    async def presence(self, luna_user: str) -> dict:
        """{"floor", "hot", "camped"} for the player's floor — served
        from worldd's 30s cache, cheap by construction."""
        return await self._post("/v1/presence", {"player": luna_user})

    async def room_more(self, luna_user: str) -> dict:
        """The presence grid's unfold — the rest of the room, ≤200."""
        return await self._post("/v1/room_more", {"player": luna_user})

    async def faction_list(self, luna_user: str, q: str = "") -> dict:
        """The ledger: top 10 by members; q searches server-side (015)."""
        return await self._post("/v1/faction/list",
                                {"player": luna_user, "q": q})

    async def faction_status(self, luna_user: str) -> dict:
        return await self._post("/v1/faction/status", {"player": luna_user})

    async def faction_create(self, luna_user: str, name: str, banner: str,
                             join_fee: int = 0,
                             weekly_dues: int = 5) -> dict:
        return await self._post("/v1/faction/create", {
            "player": luna_user, "name": name, "banner": banner,
            "join_fee": join_fee, "weekly_dues": weekly_dues})

    async def faction_join(self, luna_user: str, faction: str) -> dict:
        return await self._post("/v1/faction/join", {
            "player": luna_user, "faction": faction})

    async def faction_leave(self, luna_user: str) -> dict:
        return await self._post("/v1/faction/leave", {"player": luna_user})

    async def faction_kick(self, luna_user: str, target_tenant: str,
                           target_player: str) -> dict:
        return await self._post("/v1/faction/kick", {
            "player": luna_user, "target_tenant": target_tenant,
            "target_player": target_player})

    async def faction_donate(self, luna_user: str, amount: int) -> dict:
        return await self._post("/v1/faction/donate", {
            "player": luna_user, "amount": amount})

    async def faction_enter(self, luna_user: str) -> dict:
        return await self._post("/v1/faction/enter", {"player": luna_user})

    async def faction_board(self, luna_user: str) -> dict:
        """The COMMUNITY news board — read-only faction rankings + news."""
        return await self._post("/v1/faction/board", {"player": luna_user})

    # ── 015: the faction desk ────────────────────────────────────────────

    async def faction_detail(self, luna_user: str, name: str) -> dict:
        return await self._post("/v1/faction/detail",
                                {"player": luna_user, "name": name})

    async def faction_request(self, luna_user: str, name: str) -> dict:
        return await self._post("/v1/faction/request",
                                {"player": luna_user, "name": name})

    async def faction_cancel_request(self, luna_user: str) -> dict:
        return await self._post("/v1/faction/cancel_request",
                                {"player": luna_user})

    async def faction_approve(self, luna_user: str, target_tenant: str,
                              target_player: str) -> dict:
        return await self._post("/v1/faction/approve", {
            "player": luna_user, "target_tenant": target_tenant,
            "target_player": target_player})

    async def faction_reject(self, luna_user: str, target_tenant: str,
                             target_player: str) -> dict:
        return await self._post("/v1/faction/reject", {
            "player": luna_user, "target_tenant": target_tenant,
            "target_player": target_player})

    async def faction_rename(self, luna_user: str, name: str) -> dict:
        return await self._post("/v1/faction/rename",
                                {"player": luna_user, "name": name})

    async def faction_promote(self, luna_user: str, target_tenant: str,
                              target_player: str) -> dict:
        return await self._post("/v1/faction/promote", {
            "player": luna_user, "target_tenant": target_tenant,
            "target_player": target_player})

    # ── 051: the postbox ─────────────────────────────────────────────────

    async def feedback_create(self, luna_user: str, subject: str, body: str,
                              attachments: list) -> dict:
        return await self._post("/v1/feedback/create", {
            "player": luna_user, "subject": subject, "body": body,
            "attachments": attachments})

    async def feedback_mine(self, luna_user: str) -> dict:
        return await self._post("/v1/feedback/mine", {"player": luna_user})

    async def feedback_thread(self, luna_user: str, fid: int,
                              as_admin: bool = False) -> dict:
        return await self._post("/v1/feedback/thread", {
            "player": luna_user, "id": fid, "as_admin": as_admin})

    async def feedback_reply(self, luna_user: str, fid: int, body: str,
                             attachments: list,
                             as_admin: bool = False) -> dict:
        return await self._post("/v1/feedback/reply", {
            "player": luna_user, "id": fid, "body": body,
            "attachments": attachments, "as_admin": as_admin})

    async def feedback_unread(self, luna_user: str) -> dict:
        return await self._post("/v1/feedback/unread", {"player": luna_user})

    async def feedback_admin(self, luna_user: str) -> dict:
        return await self._post("/v1/feedback/admin", {"player": luna_user})

    async def feedback_att(self, luna_user: str, att_id: int) -> dict:
        """{"mime", "data" (base64)} — the route decodes it back to bytes."""
        return await self._post("/v1/feedback/att", {
            "player": luna_user, "id": att_id})
