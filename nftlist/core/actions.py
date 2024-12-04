from abc import ABC


class Action(ABC):
    def registerName(self, name: str):
        self._name = name

    def __str__(self):
        return self._name


class ActionUpdate(Action):
    pass

class ActionRefresh(Action):
    pass

class ActionClean(Action):
    pass

class ActionPanic(Action):
    pass

