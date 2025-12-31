from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional


__version__ = "0.1.0"

Pos = tuple[int, int]


# -------------------------
# Directions
# -------------------------

class Dir(Enum):
    """
    Cardinal directions for grid movement.

    Values are (dx, dy) offsets.
    """
    N = (0, -1)
    E = (1, 0)
    S = (0, 1)
    W = (-1, 0)

    @property
    def dx(self) -> int:
        return self.value[0]

    @property
    def dy(self) -> int:
        return self.value[1]


# Shorthand aliases for a compact "DSL-like" usage: move(E) instead of move(Dir.E).
N = Dir.N
E = Dir.E
S = Dir.S
W = Dir.W


# -------------------------
# Actions
# -------------------------

@dataclass
class Action:
    """
    A typed action request issued by an agent and applied by the world on tick().

    This is intentionally minimal:
    - name: action identifier, e.g. "move", "wait"
    - data: action parameters (typed values, not stringly-typed dicts)
    """
    name: str
    data: dict[str, Any]


def move(direction: Dir) -> Action:
    """Request a one-cell move in the given direction."""
    return Action("move", {"dir": direction})


def wait() -> Action:
    """Request to do nothing this tick."""
    return Action("wait", {})


# -------------------------
# Grid and cells
# -------------------------

class Cell:
    """
    Base cell type.

    Users can subclass Cell to add custom fields (e.g. terrain cost, triggers).
    The engine-level contract is defined by the 'walkable' flag for now.
    """
    walkable: bool = True


class Floor(Cell):
    """Walkable base cell."""
    walkable = True


class Wall(Cell):
    """Non-walkable base cell."""
    walkable = False


class Grid:
    """
    Grid is responsible for map topology and walkability.

    World queries Grid to validate movement. More advanced rules (costs, one-way
    doors, per-agent constraints) can be added later without changing World API.
    """

    def __init__(self, width: int, height: int, default: Optional[Cell] = None) -> None:
        self.width = width
        self.height = height
        base = default if default is not None else Floor()
        self._cells: list[Cell] = [base for _ in range(width * height)]

    def in_bounds(self, pos: Pos) -> bool:
        x, y = pos
        return 0 <= x < self.width and 0 <= y < self.height

    def _idx(self, pos: Pos) -> int:
        x, y = pos
        return y * self.width + x

    def get(self, pos: Pos) -> Cell:
        """Return cell object at pos. Raises IndexError if out of bounds."""
        if not self.in_bounds(pos):
            raise IndexError(f"Out of bounds: {pos}")
        return self._cells[self._idx(pos)]

    def set(self, pos: Pos, cell: Cell) -> None:
        """Set cell object at pos. Raises IndexError if out of bounds."""
        if not self.in_bounds(pos):
            raise IndexError(f"Out of bounds: {pos}")
        self._cells[self._idx(pos)] = cell

    def is_walkable(self, pos: Pos, *, agent: Optional["Agent"] = None) -> bool:
        """
        Return True if 'pos' can be occupied.

        The 'agent' parameter is reserved for future extensions (e.g., different
        traversal rules per agent type). It is not used in the base implementation.
        """
        if not self.in_bounds(pos):
            return False
        return self.get(pos).walkable


# -------------------------
# Agent
# -------------------------

class Agent:
    """
    Agent is an entity that can be placed into a world.

    The agent may exist independently (not attached to any world).
    An agent can enqueue a single action for the next tick via act().
    """

    _next_uid = 1

    def __init__(self) -> None:
        self.uid = Agent._next_uid
        Agent._next_uid += 1

        self.world: Optional["World"] = None
        self.pos: Optional[Pos] = None

        self._queued_action: Optional[Action] = None

    def act(self, action: Action) -> None:
        """
        Enqueue an action for the next world tick.

        If called multiple times before tick(), the last action wins.
        """
        self._queued_action = action

    def _take_queued_action(self) -> Optional[Action]:
        """Internal: consume queued action for this tick."""
        a = self._queued_action
        self._queued_action = None
        return a


# -------------------------
# World runtime
# -------------------------

@dataclass
class Event:
    """
    Structured event emitted by the world.

    Events are useful for:
    - debugging
    - UI rendering (external)
    - replay recording (later)
    """
    name: str
    data: dict[str, Any]


@dataclass
class WorldState:
    """
    Snapshot of observable world state after a tick.

    This is intentionally compact and stable; richer state can be added later.
    """
    tick: int
    positions: dict[int, Pos]  # agent.uid -> (x, y)


@dataclass
class TickResult:
    """Return value of World.tick()."""
    state: WorldState
    events: tuple[Event, ...]


class World:
    """
    Minimal step-based world.

    Responsibilities:
    - owns grid reference and entity placement
    - applies queued agent actions on tick()
    - emits events and returns a state snapshot
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

        The seed parameter is reserved for future deterministic generation and
        randomized rules. It is not used by the base implementation.
        """
        self._tick = 0
        self._agents.clear()

    def spawn(self, agent: Agent, *, at: Pos) -> Agent:
        """
        Attach an agent to this world and place it at the given position.

        Raises:
            ValueError: if agent is already attached to a world or cell is not walkable.
        """
        if agent.world is not None:
            raise ValueError("Agent is already spawned in a world.")
        if not self.grid.is_walkable(at, agent=agent):
            raise ValueError(f"Cannot spawn at non-walkable cell: {at}")

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

    def tick(self) -> TickResult:
        """
        Advance simulation by exactly one tick.

        Current base rules:
        - "wait": no movement
        - "move": attempt to move by one cell if target is walkable

        Collision rules (two agents to the same cell) are intentionally not defined yet.
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

        return TickResult(state=self.snapshot(), events=tuple(events))
