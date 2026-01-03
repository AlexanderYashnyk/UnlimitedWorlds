import unlimitedworlds as uw


def test_send_delivered_next_tick():
    grid = uw.Grid(3, 3)
    world = uw.World(grid)

    a = uw.Agent()
    b = uw.Agent()
    world.spawn(a, at=(1, 1))
    world.spawn(b, at=(2, 1))

    a.act(uw.send(b.uid, "hi"))
    world.tick()

    obs_b = world.observe(b)

    assert any(m.payload == "hi" and m.src_uid == a.uid for m in obs_b.messages)


def test_message_order_is_deterministic():
    grid = uw.Grid(3, 3)
    world = uw.World(grid)

    sender1 = uw.Agent()
    sender2 = uw.Agent()
    receiver = uw.Agent()
    world.spawn(sender1, at=(0, 1))
    world.spawn(sender2, at=(1, 1))
    world.spawn(receiver, at=(2, 1))

    sender1.act(uw.send(receiver.uid, "one"))
    sender2.act(uw.send(receiver.uid, "two"))
    world.tick()

    obs = world.observe(receiver)
    src_order = [m.src_uid for m in obs.messages]

    assert src_order == sorted(src_order)


def test_payload_truncated_to_max_len():
    grid = uw.Grid(3, 3)
    world = uw.World(grid)

    sender = uw.Agent()
    receiver = uw.Agent()
    world.spawn(sender, at=(0, 0))
    world.spawn(receiver, at=(1, 0))

    payload = "x" * (uw.MAX_MESSAGE_LEN + 10)
    sender.act(uw.send(receiver.uid, payload))
    world.tick()

    obs = world.observe(receiver)

    assert len(obs.messages[0].payload) == uw.MAX_MESSAGE_LEN
