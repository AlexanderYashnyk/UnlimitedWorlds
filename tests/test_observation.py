import unlimitedworlds as uw


def test_observe_manhattan_radius_1_tiles_count_center():
    grid = uw.Grid(5, 5)
    world = uw.World(grid)

    a = uw.Agent(sensor=uw.SensorSpec(radius=1, shape=uw.SensorShape.MANHATTAN))
    world.spawn(a, at=(2, 2))

    obs = world.observe(a)
    positions = {tile.pos for tile in obs.tiles}

    assert positions == {(2, 2), (1, 2), (3, 2), (2, 1), (2, 3)}


def test_observe_respects_bounds():
    grid = uw.Grid(5, 5)
    world = uw.World(grid)

    a = uw.Agent(sensor=uw.SensorSpec(radius=2, shape=uw.SensorShape.MANHATTAN))
    world.spawn(a, at=(0, 0))

    obs = world.observe(a)

    assert (0, 0) in {tile.pos for tile in obs.tiles}
    assert all(grid.in_bounds(tile.pos) for tile in obs.tiles)


def test_two_agents_different_sensors_see_different():
    grid = uw.Grid(5, 5)
    world = uw.World(grid)

    small = uw.Agent(sensor=uw.SensorSpec(radius=1, shape=uw.SensorShape.MANHATTAN))
    big = uw.Agent(sensor=uw.SensorSpec(radius=3, shape=uw.SensorShape.MANHATTAN))
    world.spawn(small, at=(2, 2))
    world.spawn(big, at=(2, 2))

    obs_small = world.observe(small)
    obs_big = world.observe(big)

    assert len(obs_big.tiles) > len(obs_small.tiles)
