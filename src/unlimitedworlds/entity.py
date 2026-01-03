from typing import Optional, TYPE_CHECKING

from .grid import Pos

if TYPE_CHECKING:
    from .world import World


class Entity:
    """
    Base world entity.

    Any object that exists in a world can be modeled as an Entity (agents, doors,
    items, traps). For now, the base engine only needs:
    - uid: stable identifier within a process
    - world/pos: placement data (optional until spawned)
    """

    _next_uid = 1

    def __init__(self) -> None:
        self.uid = Entity._next_uid
        Entity._next_uid += 1

        self.world: Optional["World"] = None
        self.pos: Optional[Pos] = None
