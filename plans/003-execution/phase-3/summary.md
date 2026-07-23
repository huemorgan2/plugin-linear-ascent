# Plugin Phase 3 — execution summary (worldd client)

Status: **complete**, browser-verified end-to-end on localhost.

## Built

- `backend/remote.py` — `WorldClient`: HMAC-SHA256 signed requests (`X-Ascent-Tenant/Ts/Signature/Api`), UUID idempotency key per act, honest error mapping (`WorldError` on 4xx/5xx with server detail).
- `plugin.py` backend selection: remote when `LUNA_ASCENT_WORLDD_URL` + `LUNA_ASCENT_SHARED_SECRET` are set (tenant via `LUNA_ASCENT_TENANT`), local SQL otherwise. Same scenes, same renderer either way.
- **Fix found in live testing:** Luna's `ctx.get_env` only resolves env vars declared in Luna's own config schema (`EnvConfig` is `extra="ignore"`), so plugin-custom `LUNA_ASCENT_*` vars silently came back `None` and the plugin stayed in local mode. Added an `os.environ` fallback (`luna serve` loads `.env` into the process via `load_dotenv`).
- **Hardening found in live testing:** one invalid floor YAML bricked every scene (`load_floors` was all-or-nothing). Runtime loader now skips bad files; the strict gate moved to `lint_floors()` + `test_every_floor_file_lints_clean`.

## Verified in browser (Luna chat on :8777 → worldd on :8600)

Fresh chat with the worldd env configured: character creation ran against worldd (`POST /v1/scene` / `/v1/act` in server logs; the old local-mode character was absent, proving the backend switch). Torvald (human warrior) created; the Roothollow town card listed the world-mode-only locations — Relay Office, the Fields (PvP), the Guildhall — confirming `_world` injection made it through the full plugin → HMAC → worldd → engine → renderer loop.
