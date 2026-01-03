from dataclasses import dataclass
from enum import Enum
from typing import Any


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


# Shorthand aliases for compact usage: move(E) instead of move(Dir.E).
N = Dir.N
E = Dir.E
S = Dir.S
W = Dir.W


@dataclass
class Action:
    """
    A typed action request applied by the world on tick().

    - name: action identifier ("move", "wait", ...)
    - data: action parameters (typed values, not stringly-typed protocols)
    """
    name: str
    data: dict[str, Any]


def move(direction: Dir) -> Action:
    """Request a one-tile move in the given direction."""
    return Action("move", {"dir": direction})


def wait() -> Action:
    """Request to do nothing this tick."""
    return Action("wait", {})
