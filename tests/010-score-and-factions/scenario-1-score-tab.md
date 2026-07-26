# 010 · Scenario 1 — the Score tab is the world's muster roll

Goal: SCORE lists every playing climber with level and gold, monospace
grammar, own row highlighted.

## Steps

1. Open the Linear Ascent pane, click SCORE.
2. **Expect:** a mono table — rank, name (race/class dim), level, floor,
   carried ◈, banked ◈, faction — sorted by level then wealth. Your own
   tenant's row reads in aether blue.
3. Cross-check server truth: the top row's level/gold must match the
   worldd DB (`SELECT doc->>'name', doc->>'level', doc->>'gold' ...`).
4. Screenshot and read it — no raw JSON, no broken grid columns, gold
   formatted with thousands separators.

## Pass criteria

- Every playing character appears; values match the DB.
- Own row highlighted; layout clean at 760px and at mobile width.
