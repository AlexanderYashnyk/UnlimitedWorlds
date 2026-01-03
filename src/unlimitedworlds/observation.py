from dataclasses import dataclass
from enum import Enum

from .grid import Pos


class SensorShape(Enum):
    MANHATTAN = "manhattan"
    SQUARE = "square"


@dataclass
class SensorSpec:
    radius: int = 2
    shape: SensorShape = SensorShape.MANHATTAN


@dataclass
class VisibleTile:
    pos: Pos
    tile: str


@dataclass
class VisibleEntity:
    uid: int
    kind: str
    pos: Pos


@dataclass
class Observation:
    tick: int
    self_uid: int
    self_pos: Pos
    tiles: tuple[VisibleTile, ...]
    entities: tuple[VisibleEntity, ...]
