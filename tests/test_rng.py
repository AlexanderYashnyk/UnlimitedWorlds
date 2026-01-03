import unlimitedworlds as uw


def test_seed_reproducibility_and_difference():
    class RngSystem(uw.System):
        def post_tick(self, world: uw.World, ctx: uw.TickContext) -> None:
            x = ctx.rng.random()
            ctx.events.append(uw.Event("rng", {"x": x}))

    def tick_and_get_x(world: uw.World) -> float:
        out = world.tick()
        for e in out.events:
            if e.name == "rng":
                return e.data["x"]
        raise AssertionError("rng event missing")

    world_a = uw.World(uw.Grid(1, 1))
    world_b = uw.World(uw.Grid(1, 1))
    world_a.reset(seed=123)
    world_b.reset(seed=123)
    world_a.add_system(RngSystem())
    world_b.add_system(RngSystem())

    x1 = tick_and_get_x(world_a)
    x2 = tick_and_get_x(world_b)

    assert x1 == x2

    world_c = uw.World(uw.Grid(1, 1))
    world_c.reset(seed=124)
    world_c.add_system(RngSystem())

    y1 = tick_and_get_x(world_c)
    y2 = tick_and_get_x(world_c)

    assert (x1, x2) != (y1, y2)
