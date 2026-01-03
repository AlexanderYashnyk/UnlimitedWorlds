from dataclasses import dataclass
from enum import Enum
from typing import Any

from .actions import Action, Dir
from .agent import Agent
from .grid import Grid, Pos


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


class CollisionPolicy(Enum):
    BLOCK = "block"


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
        self._tick = 0
        self._agents.clear()

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

    def tick(self) -> Tick:
        """
        Advance simulation by exactly one tick.

        Base rules:
        - "wait": no movement
        - "move": attempt to move by one tile if target is walkable
        """
        self._tick += 1
        events: list[Event] = []

        # Collect queued actions for this tick in deterministic uid order.
        sorted_agents = sorted(self._agents, key=lambda agent: agent.uid)
        pending_actions: list[tuple[Agent, Action]] = []
        for a in sorted_agents:
            act = a._take_queued_action()
            if act is None:
                act = Action("wait", {})
            pending_actions.append((a, act))

        positions: dict[int, Pos] = {
            a.uid: a.pos for a in sorted_agents if a.pos is not None
        }
        desired_moves: dict[int, Pos] = {}
        blocked_targets: dict[int, Pos] = {}

        for a, act in pending_actions:
            if a.pos is None:
                continue

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

        # Apply actions.
        for a, act in pending_actions:
            if a.pos is None:
                continue

            if act.name == "wait":
                events.append(Event("waited", {"agent": a.uid}))
                continue

            if act.name == "move":
                if a.uid in blocked_targets:
                    events.append(Event("blocked", {"agent": a.uid, "to": blocked_targets[a.uid]}))
                    continue
                if a.uid in collision_uids and self.collision_policy == CollisionPolicy.BLOCK:
                    events.append(Event("collision", {"agent": a.uid, "to": desired_moves[a.uid]}))
                    continue

                target = desired_moves.get(a.uid)
                if target is not None:
                    a.pos = target
                    events.append(Event("moved", {"agent": a.uid, "to": target}))
                continue

            events.append(Event("unknown_action", {"agent": a.uid, "name": act.name}))

        return Tick(state=self.snapshot(), events=tuple(events))
