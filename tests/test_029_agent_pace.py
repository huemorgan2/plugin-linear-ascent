"""0.29.5 — the player watches the agent play: every agent-rendered
screen holds for AGENT_MOVE_GAP_S before the next move replaces it.
Only the agent tool path is paced; the pane's own clicks never are."""

import asyncio
import time

from plugin_linear_ascent import runtime


def test_the_next_move_waits_out_the_previous_screen(monkeypatch):
    runtime.state["agent_pace"].clear()
    sleeps = []

    async def fake_sleep(s):
        sleeps.append(s)

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)
    runtime.pace_mark("u1")
    asyncio.run(runtime.pace_wait("u1"))
    assert len(sleeps) == 1
    assert 0 < sleeps[0] <= runtime.AGENT_MOVE_GAP_S


def test_the_first_move_is_never_paced(monkeypatch):
    runtime.state["agent_pace"].clear()
    sleeps = []

    async def fake_sleep(s):
        sleeps.append(s)

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)
    asyncio.run(runtime.pace_wait("fresh"))
    assert sleeps == []


def test_a_screen_already_watched_costs_nothing(monkeypatch):
    runtime.state["agent_pace"]["idle"] = (
        time.monotonic() - runtime.AGENT_MOVE_GAP_S - 5)
    sleeps = []

    async def fake_sleep(s):
        sleeps.append(s)

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)
    asyncio.run(runtime.pace_wait("idle"))
    assert sleeps == []


def test_pacing_is_per_player():
    runtime.state["agent_pace"].clear()
    runtime.pace_mark("a")
    assert "b" not in runtime.state["agent_pace"]
    t0 = time.monotonic()
    asyncio.run(runtime.pace_wait("b"))       # someone else's screen
    assert time.monotonic() - t0 < 0.5
