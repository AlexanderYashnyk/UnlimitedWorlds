import unlimitedworlds as uw


def test_system_hook_order_is_deterministic():
    class SysA(uw.System):
        def pre_tick(self, world: uw.World, ctx: uw.TickContext) -> None:
            ctx.events.append(uw.Event("sysA.pre", {}))

        def resolve(self, world: uw.World, ctx: uw.TickContext) -> None:
            ctx.events.append(uw.Event("sysA.resolve", {}))

        def post_tick(self, world: uw.World, ctx: uw.TickContext) -> None:
            ctx.events.append(uw.Event("sysA.post", {}))

    class SysB(uw.System):
        def pre_tick(self, world: uw.World, ctx: uw.TickContext) -> None:
            ctx.events.append(uw.Event("sysB.pre", {}))

        def resolve(self, world: uw.World, ctx: uw.TickContext) -> None:
            ctx.events.append(uw.Event("sysB.resolve", {}))

        def post_tick(self, world: uw.World, ctx: uw.TickContext) -> None:
            ctx.events.append(uw.Event("sysB.post", {}))

    grid = uw.Grid(3, 3)
    world = uw.World(grid)
    world.add_system(SysA())
    world.add_system(SysB())

    a = uw.Agent()
    world.spawn(a, at=(1, 1))

    out = world.tick()

    names = [e.name for e in out.events]
    assert names == [
        "sysA.pre",
        "sysB.pre",
        "waited",
        "sysA.resolve",
        "sysB.resolve",
        "sysA.post",
        "sysB.post",
    ]


def test_system_can_inject_event():
    class HelloSystem(uw.System):
        def post_tick(self, world: uw.World, ctx: uw.TickContext) -> None:
            ctx.events.append(uw.Event("hello", {}))

    grid = uw.Grid(3, 3)
    world = uw.World(grid)
    world.add_system(HelloSystem())

    a = uw.Agent()
    world.spawn(a, at=(1, 1))

    out = world.tick()

    assert any(e.name == "hello" for e in out.events)
