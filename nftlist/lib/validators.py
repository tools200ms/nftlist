from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from types import MethodType


class Validator(ABC):
    @staticmethod
    @abstractmethod
    def validate(str: str) -> bool:
        pass
    @abstractmethod
    def validate(self, str: str) -> bool:
        pass

class FileValidator(Validator):
    class Properties(Enum):
        IS_FILE = Path.is_file
        IS_DIR = Path.is_dir

    def __init__(self, property: Properties):
        self.__prop = property

    def validate(self, str: str) -> bool:
        v = MethodType(self.__prop, str)
        return v()


