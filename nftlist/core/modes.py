from enum import Enum

from nftlist.lib.logger import Log
from nftlist.core.actions import Action, ActionUpdate, ActionRefresh, ActionClean, ActionPanic


class Mode(Enum):

    UPDATE  = ActionUpdate()
    REFRESH = ActionRefresh()
    CLEAN   = ActionClean()
    PANIC   = ActionPanic()

    def __init__(self, act: Action):
        act.registerName(self.name)

    def __str__(self):
        return self.name

    def run(self):
        Log.info(f"Runing in {self.name} mode")

    @staticmethod
    def findMode(str: str):
        if len(str) == 0:
            return None

        str = str.upper()
        for mode in Mode:
            if mode.name.startswith(str):
                return mode
        return None


