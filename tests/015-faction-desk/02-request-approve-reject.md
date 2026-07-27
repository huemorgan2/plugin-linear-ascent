# 015 / 02 — Join requests: file, accept, reject

Needs two players: an admin of a faction (founder works) and an
unaffiliated requester (second tenant via the Layer-2 driver is fine).

## Steps

1. As the requester, open a faction page from COMMUNITY (click its name).
   Click ASK TO JOIN. The button must flip to a pending state with a
   WITHDRAW action — no gold leaves the requester yet.
2. As the admin, open the same faction page. The ADMIN DESK must show the
   request row (name + level) with ACCEPT and REJECT buttons.
3. Click ACCEPT: the requester becomes a member, the join fee moves
   requester → faction store exactly once (check the store ledger),
   and the request row disappears inline (no popup, no reload).
4. File a second request from another player and REJECT it: the row
   clears, no membership, no gold moved.

## Pass

- Request/withdraw/accept/reject all inline in the pane.
- Fee charged only on accept; refused (with the request kept) if the
  requester can't pay.

## Fail

- Join is immediate without approval, fee charged at request time,
  or any popup/confirm() dialog appears.
