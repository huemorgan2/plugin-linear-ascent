# Phase4 quiver discovery correction

13 September2026. Reproduced in QA0.115.0/8b26030 before edits. P4-001: the exact first query “show me the arrows I can use with this bow” made zero tool calls and falsely denied ammunition. An explicit refresh returned100 Common Ordinary arrows in `weapon_collection.quiver.stock` but the response again denied a quiver. The collection renderer does not render that payload, and the sheet payload exposes stock and raw per-instance choices without definitions or resolved default selection. Shared coaching requires refreshed weapons but does not describe the new ammo surface. No production change or emergency mitigation.

## Changes

1. Make the authoritative quiver payload self-contained: finite capacity, one-per-accepted-shot/miss rule, six named payloads with actual effects/channel, per-grade owned counts/Forge quotes/access, and resolved selection for each carried bow. Keep the raw stock/choices for compatibility. Reads cannot spend or replenish arrows except the already receipted one-time enrollment.
2. Render that owned stock in a collection drawer using the existing font, icons and grade frames, including zero-stock options and the resolved selected payload. Explain Forge replenishment and free in-fight selection. Use valid current scene actions only; do not make a fake buying button that silently travels.
3. Update scene/character tool descriptions and shared coaching to refresh arrow questions and read this payload. In candidate rules Ordinary ammo is finite; legacy rules remain distinct. Do not let previous chat claims override a current response. Honor exact user action limits while doing authorized chains; a two-attempt request means at most two attempts, with separate authorized extraction/navigation only.
4. Test the payload/renderer against real engine ownership, default/explicit selection, grade gates and supply conservation. Restart only owned QA worldd/Luna with the same databases, tenant, credentials and conversations. Repeat the exact first query in the preserved conversation, then continue the frozen phase4 combat browser fixtures.

## Rollback and verification

Record implementation SHA and targeted/full suite results. Revert only the presentation/coaching/payload additions if needed, retaining0.115 arrows/group readers and owned stock. No database reset, time jump, natural-player grant or conversation deletion. Browser evidence lives outside the repo until allowlisted/sanitized. Phase4 is not complete until its real combat/site walkthrough and measurements pass.

Execution: reproduced; implementation pending.
