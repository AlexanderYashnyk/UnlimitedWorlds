from abc import ABC
import random
from dataclasses import dataclass
from enum import Enum
from typing import Any

from .actions import Action, Dir
from .agent import Agent
from .grid import Grid, Pos
from .observation import Observation, SensorShape, VisibleEntity, VisibleTile


@dataclass
class Event:
    """
    Structured event emitted by the world.

    Events support external UI/logging/replay without embedding those concerns into the core.
    """
    name: str
    data: dict[str, Any]


@dataclass
class WorldState:
    """Compact snapshot of observable world state after a tick."""
    tick: int
    positions: dict[int, Pos]  # agent.uid -> (x, y)


@dataclass
class Tick:
    """Return value of World.tick()."""
    state: WorldState
    events: tuple[Event, ...]


@dataclass
class TickContext:
    tick: int
    actions: dict[int, Action]
    events: list[Event]
    rng: random.Random


class CollisionPolicy(Enum):
    BLOCK = "block"


class System(ABC):
    def pre_tick(self, world: "World", ctx: TickContext) -> None:
        return None

    def resolve(self, world: "World", ctx: TickContext) -> None:
        return None

    def post_tick(self, world: "World", ctx: TickContext) -> None:
        return None


class World:
    """
    Minimal step-based world runtime.

    Responsibilities:
    - owns runtime state (agents + their positions)
    - uses Grid for movement validity
    - applies queued agent actions on tick()
    - returns a state snapshot and structured events
    """

    def __init__(self, grid: Grid, collision_policy: CollisionPolicy = CollisionPolicy.BLOCK) -> None:
        self.grid = grid
        self.collision_policy = collision_policy
        self.systems: list[System] = []
        self.seed: int | None = None
        self.rng = random.Random()
        self._tick = 0
        self._agents: list[Agent] = []

    @property
    def tick_count(self) -> int:
        """Number of ticks elapsed since reset()."""
        return self._tick

    def reset(self, *, seed: int | None = None) -> None:
        """
        Reset world runtime state.

        `seed` is reserved for future deterministic generation and randomized rules.
        """
        self.seed = seed
        self.rng = random.Random(seed) if seed is not None else random.Random()
        self._tick = 0
        self._agents.clear()

    def add_system(self, system: System) -> None:
        self.systems.append(system)

    def spawn(self, agent: Agent, *, at: Pos) -> Agent:
        """
        Attach an agent to this world and place it at the given position.

        Raises:
            ValueError: if agent is already attached or tile is not walkable.
        """
        if agent.world is not None:
            raise ValueError("Agent is already spawned in a world.")
        if not self.grid.is_walkable(at, agent=agent):
            raise ValueError(f"Cannot spawn at non-walkable tile: {at}")

        agent.world = self
        agent.pos = at
        self._agents.append(agent)
        return agent

    def snapshot(self) -> WorldState:
        """Return a compact snapshot of current world state."""
        return WorldState(
            tick=self._tick,
            positions={a.uid: a.pos for a in self._agents if a.pos is not None},
        )

    def observe(self, agent: Agent) -> Observation:
        if agent.world is not self:
            raise ValueError("Agent is not spawned in this world.")
        if agent.pos is None:
            raise ValueError("Agent position is not set.")

        center = agent.pos
        radius = agent.sensor.radius
        shape = agent.sensor.shape

        tiles: list[VisibleTile] = []
        visible_positions: set[Pos] = set()

        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                if shape == SensorShape.MANHATTAN:
                    if abs(dx) + abs(dy) > radius:
                        continue
                elif shape == SensorShape.SQUARE:
                    if max(abs(dx), abs(dy)) > radius:
                        continue
                else:
                    continue

                pos = (center[0] + dx, center[1] + dy)
                if not self.grid.in_bounds(pos):
                    continue

                walkable = self.grid.is_walkable(pos, agent=agent)
                tile_name = "floor" if walkable else "wall"
                tiles.append(VisibleTile(pos=pos, tile=tile_name))
                visible_positions.add(pos)

        entities: list[VisibleEntity] = []
        for a in sorted(self._agents, key=lambda entry: entry.uid):
            if a.pos is None:
                continue
            if a.pos in visible_positions:
                entities.append(VisibleEntity(uid=a.uid, kind="agent", pos=a.pos))

        return Observation(
            tick=self._tick,
            self_uid=agent.uid,
            self_pos=center,
            tiles=tuple(tiles),
            entities=tuple(entities),
        )

    def tick(self) -> Tick:
        """
        Advance simulation by exactly one tick.

        Base rules:
        - "wait": no movement
        - "move": attempt to move by one tile if target is walkable
        """
        self._tick += 1

        # Collect queued actions for this tick in deterministic uid order.
        sorted_agents = sorted(self._agents, key=lambda agent: agent.uid)
        actions: dict[int, Action] = {}
        for a in sorted_agents:
            act = a._take_queued_action()
            if act is None:
                act = Action("wait", {})
            actions[a.uid] = act

        ctx = TickContext(tick=self._tick, actions=actions, events=[], rng=self.rng)

        for system in self.systems:
            system.pre_tick(self, ctx)

        positions: dict[int, Pos] = {
            a.uid: a.pos for a in sorted_agents if a.pos is not None
        }
        desired_moves: dict[int, Pos] = {}
        blocked_targets: dict[int, Pos] = {}

        for a in sorted_agents:
            if a.pos is None:
                continue
            act = ctx.actions[a.uid]

            if act.name == "move":
                d: Dir = act.data["dir"]
                nxt = (a.pos[0] + d.dx, a.pos[1] + d.dy)

                if self.grid.is_walkable(nxt, agent=a):
                    desired_moves[a.uid] = nxt
                else:
                    blocked_targets[a.uid] = nxt

        collision_uids: set[int] = set()
        if self.collision_policy == CollisionPolicy.BLOCK:
            targets: dict[Pos, list[int]] = {}
            for uid, target in desired_moves.items():
                targets.setdefault(target, []).append(uid)
            for uids in targets.values():
                if len(uids) > 1:
                    collision_uids.update(uids)

            pos_to_uid = {pos: uid for uid, pos in positions.items()}
            for uid, target in desired_moves.items():
                other_uid = pos_to_uid.get(target)
                if other_uid is None or other_uid == uid:
                    continue
                other_target = desired_moves.get(other_uid)
                if other_target == positions.get(uid):
                    collision_uids.add(uid)
                    collision_uids.add(other_uid)

        # System order: pre_tick -> core resolve/apply -> resolve -> post_tick.
        for a in sorted_agents:
            if a.pos is None:
                continue
            act = ctx.actions[a.uid]

            if act.name == "wait":
                ctx.events.append(Event("waited", {"agent": a.uid}))
                continue

            if act.name == "move":
                if a.uid in blocked_targets:
                    ctx.events.append(Event("blocked", {"agent": a.uid, "to": blocked_targets[a.uid]}))
                    continue
                if a.uid in collision_uids and self.collision_policy == CollisionPolicy.BLOCK:
                    ctx.events.append(Event("collision", {"agent": a.uid, "to": desired_moves[a.uid]}))
                    continue

                target = desired_moves.get(a.uid)
                if target is not None:
                    a.pos = target
                    ctx.events.append(Event("moved", {"agent": a.uid, "to": target}))
                continue

            ctx.events.append(Event("unknown_action", {"agent": a.uid, "name": act.name}))

        for system in self.systems:
            system.resolve(self, ctx)

        for system in self.systems:
            system.post_tick(self, ctx)

        return Tick(state=self.snapshot(), events=tuple(ctx.events))
