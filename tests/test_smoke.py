import unlimitedworlds as uw


def test_spawn_and_move_east():
    grid = uw.Grid(5, 5)
    world = uw.World(grid)

    a = uw.Agent()
    world.spawn(a, at=(1, 1))

    a.act(uw.move(uw.E))
    out = world.tick()

    assert out.state.tick == 1
    assert out.state.positions[a.uid] == (2, 1)
    assert any(e.name == "moved" for e in out.events)


def test_blocked_by_wall():
    grid = uw.Grid(5, 5)
    grid.set((2, 1), uw.Wall())
    world = uw.World(grid)

    a = uw.Agent()
    world.spawn(a, at=(1, 1))

    a.act(uw.move(uw.E))
    out = world.tick()

    assert out.state.positions[a.uid] == (1, 1)
    assert any(e.name == "blocked" for e in out.events)
