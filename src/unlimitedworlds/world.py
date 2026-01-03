from dataclasses import dataclass
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


class World:
    """
    Minimal step-based world runtime.

    Responsibilities:
    - owns runtime state (agents + their positions)
    - uses Grid for movement validity
    - applies queued agent actions on tick()
    - returns a state snapshot and structured events
    """

    def __init__(self, grid: Grid) -> None:
        self.grid = grid
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

        Collision rules are intentionally not defined yet.
        """
        self._tick += 1
        events: list[Event] = []

        # Collect queued actions for this tick.
        pending_actions: list[tuple[Agent, Action]] = []
        for a in self._agents:
            act = a._take_queued_action()
            if act is not None:
                pending_actions.append((a, act))

        # Apply actions.
        for a, act in pending_actions:
            if a.pos is None:
                continue

            if act.name == "wait":
                events.append(Event("waited", {"agent": a.uid}))
                continue

            if act.name == "move":
                d: Dir = act.data["dir"]
                nxt = (a.pos[0] + d.dx, a.pos[1] + d.dy)

                if self.grid.is_walkable(nxt, agent=a):
                    a.pos = nxt
                    events.append(Event("moved", {"agent": a.uid, "to": nxt}))
                else:
                    events.append(Event("blocked", {"agent": a.uid, "to": nxt}))
                continue

            events.append(Event("unknown_action", {"agent": a.uid, "name": act.name}))

        return Tick(state=self.snapshot(), events=tuple(events))
