from enum import Enum

from nftlist.core.actions import Action


class Mode(Enum):
    class Elem:
        def __init__(self, name, action):
            self.__name = name
            self.__action = action

        def matches(self, str: str) -> bool:
            return self.__name.startswith(str)

        @property
        def action(self):
            return self.__action

    UPDATE  = Elem('update', Action.update)
    REFRESH = Elem('refresh', Action.refresh)
    CLEAN = Elem('clean', Action.clean)
    PANIC   = Elem('panic', Action.panic)

    @staticmethod
    def findMode(str: str):
        if len(str) == 0:
            return None

        for mode in Mode:
            if mode.value().matches(str):
                return mode
        return None

    def __str__(self):
        return self.value
