from enum import Enum


class Mode(Enum):
    UPDATE  = 'update'
    REFRESH = 'refresh'
    PANIC   = 'panic'

    @staticmethod
    def findMode(str: str):
        if len(str) == 0:
            return None

        for mode in Mode:
            if mode.value.startswith(str):
                return mode
        return None
