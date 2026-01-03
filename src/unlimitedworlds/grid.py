from typing import Optional, TYPE_CHECKING


Pos = tuple[int, int]

if TYPE_CHECKING:
    from .agent import Agent


class Tile:
    """
    Base tile type.

    Users can subclass Tile to add custom data (e.g. terrain cost, triggers).
    The base engine contract uses only the `walkable` flag.
    """
    walkable: bool = True


class Floor(Tile):
    """Walkable base tile."""
    walkable = True


class Wall(Tile):
    """Non-walkable base tile."""
    walkable = False


class Grid:
    """
    Grid owns map topology and walkability queries.

    World asks Grid whether a given position can be occupied.
    More advanced rules can be added later without changing World API.
    """

    def __init__(self, width: int, height: int, default: Optional[Tile] = None) -> None:
        self.width = width
        self.height = height
        base = default if default is not None else Floor()
        self._tiles: list[Tile] = [base for _ in range(width * height)]

    def in_bounds(self, pos: Pos) -> bool:
        x, y = pos
        return 0 <= x < self.width and 0 <= y < self.height

    def _idx(self, pos: Pos) -> int:
        x, y = pos
        return y * self.width + x

    def get(self, pos: Pos) -> Tile:
        """Return the tile at pos. Raises IndexError if out of bounds."""
        if not self.in_bounds(pos):
            raise IndexError(f"Out of bounds: {pos}")
        return self._tiles[self._idx(pos)]

    def set(self, pos: Pos, tile: Tile) -> None:
        """Set the tile at pos. Raises IndexError if out of bounds."""
        if not self.in_bounds(pos):
            raise IndexError(f"Out of bounds: {pos}")
        self._tiles[self._idx(pos)] = tile

    def is_walkable(self, pos: Pos, *, agent: Optional["Agent"] = None) -> bool:
        """
        Return True if pos can be occupied.

        The `agent` keyword is reserved for future extensions (agent-specific traversal).
        It is not used by the base implementation.
        """
        if not self.in_bounds(pos):
            return False
        return self.get(pos).walkable
