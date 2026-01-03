from typing import Optional

from .actions import Action
from .entity import Entity


class Agent(Entity):
    """
    An actor entity.

    The agent may exist independently (not attached to any world).
    External code enqueues actions via act(); the world consumes them on tick().
    """

    def __init__(self) -> None:
        super().__init__()
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
