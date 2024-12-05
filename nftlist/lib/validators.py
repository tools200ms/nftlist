from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from types import MethodType

from nftlist.lib.exceptions import ValidationFail


class Validator(ABC):
    @staticmethod
    @abstractmethod
    def validate(str: str) -> bool:
        pass
    @abstractmethod
    def validate(self, str: str) -> bool:
        pass

class FileValidator(Validator):
    class Property(Enum):
        IS_FILE = Path.is_file
        IS_DIR = Path.is_dir

    #def __init__(self, property: Property):
    #    self.__prop = property

    @staticmethod
    def get(property: Property, is_obligatory: bool = True):

        if is_obligatory:
            return lambda str: FileValidator.validateRaiseIfFailed(property, str)

        return lambda str: FileValidator.validate(property, str)

    @staticmethod
    def validate(prop, str: str) -> bool:
        str = str.strip()
        if str == "":
            raise ValidationFail(f"An empty string has been provided.")

        return MethodType(prop, Path(str))()

    @staticmethod
    def validateRaiseIfFailed(prop, str: str) -> bool:
        if FileValidator.validate(prop, str):
            return True

        if not Path(str).exists():
            raise ValidationFail(f"File '{str}' does not exists.")

        match prop:
            case FileValidator.Property.IS_FILE:
                expected = "file"
            case FileValidator.Property.IS_FILE:
                expected = "directory"

        raise ValidationFail(f"Path is not a {expected} path as expected")

