import pytest
import unlimitedworlds as uw


def test_spawn_and_move_east():
    """Spawned agent can move east and emits a moved event."""
    grid = uw.Grid(5, 5)
    world = uw.World(grid)

    a = uw.Agent()
    world.spawn(a, at=(1, 1))

    a.act(uw.move(uw.E))
    out = world.tick()

    assert out.state.tick == pytest.approx(1)
    assert out.state.positions[a.uid] == pytest.approx((2, 1))
    assert any(e.name == "moved" for e in out.events)


def test_blocked_by_wall():
    """Moving into a wall keeps position and emits a blocked event."""
    grid = uw.Grid(5, 5)
    grid.set((2, 1), uw.Wall())
    world = uw.World(grid)

    a = uw.Agent()
    world.spawn(a, at=(1, 1))

    a.act(uw.move(uw.E))
    out = world.tick()

    assert out.state.positions[a.uid] == pytest.approx((1, 1))
    assert any(e.name == "blocked" for e in out.events)


def test_wait_action_keeps_position():
    """Wait action keeps position and emits a waited event."""
    grid = uw.Grid(5, 5)
    world = uw.World(grid)

    a = uw.Agent()
    world.spawn(a, at=(1, 1))

    a.act(uw.wait())
    out = world.tick()

    assert out.state.positions[a.uid] == pytest.approx((1, 1))
    assert any(e.name == "waited" for e in out.events)


def test_spawn_rejects_non_walkable_tile():
    """Spawning on a non-walkable tile raises ValueError."""
    grid = uw.Grid(5, 5)
    grid.set((0, 0), uw.Wall())
    world = uw.World(grid)

    a = uw.Agent()
    with pytest.raises(ValueError):
        world.spawn(a, at=(0, 0))


def test_last_action_wins_per_tick():
    """Only the last queued action before tick is applied."""
    grid = uw.Grid(5, 5)
    world = uw.World(grid)

    a = uw.Agent()
    world.spawn(a, at=(2, 2))

    a.act(uw.move(uw.E))
    a.act(uw.move(uw.S))
    out = world.tick()

    assert out.state.positions[a.uid] == pytest.approx((2, 3))


def test_snapshot_does_not_advance_tick():
    """Snapshot returns state without advancing tick count."""
    grid = uw.Grid(5, 5)
    world = uw.World(grid)

    a = uw.Agent()
    world.spawn(a, at=(0, 0))

    snap = world.snapshot()

    assert snap.tick == pytest.approx(0)
    assert world.tick_count == pytest.approx(0)
    assert snap.positions[a.uid] == pytest.approx((0, 0))
