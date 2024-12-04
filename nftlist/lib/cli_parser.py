
import argparse
from ctypes import Union
from typing import Callable, Final, Tuple

from nftlist.core.modes import Mode
from nftlist.lib.about import About
from nftlist.lib.exceptions import CliSyntaxError
from nftlist.lib.validators import FileValidator


class CliParser:

    MAIN_CHAIN: Final = 'main'
    class Result:
        def __init__(self):
            self.__latest_ref = None

        def define(self, chain_name: str, prop_name: str, value: object = None) -> None:
            ref = chain_name + '_' + prop_name

            if hasattr(self, ref):
                raise CliSyntaxError(f"Re-defined property: {getattr(self, ref)} and {value}")

            setattr(self, ref, value)
            self.__latest_ref = ref

        @property
        def latest(self):
            return getattr(self, self.__latest_ref)

        def isEmpty(self):
            return self.__latest_ref == None

    class OptionArg:
        def __init__(self, validators: Tuple[Callable[[str], bool]]):
            self.__arg_cnt = len(validators)
            self.__oargs = (None,) * self.__arg_cnt
            self.__carg = 0
            self.__val = validators
        def add(self, arg: str):
            if self.__carg >= self.__arg_cnt:
                return False
            if self.__val(arg):
                self.__oargs[self.__carg] = arg
                self.__carg += 1
            return True

        @property
        def exploited(self):
            return self.__carg >= self.__arg_cnt

        @property
        def name(self):
            return self.__name

    @staticmethod
    def parse( argv: [str] ) -> Result:
        res = CliParser.Result()
        fun  = None
        obj = None

        for cnt, arg in enumerate(argv[1:]):

            if len(arg) > 2048 or '\n' in arg or '\r' in arg:
                raise CliSyntaxError(f"Incorrect argument no.: {cnt}")

            if isinstance(fun, CliParser.OptionArg):
                if fun.add(arg):
                    continue

            match arg:
                # check for options:
                case '--config_file'|'-c':
                    valid = FileValidator( FileValidator.Properties.IS_FILE )
                    obj = CliParser.OptionArg((valid))

                    res.define('conf', 'file', obj)
                case '--do_pretend'|'-d':
                    res.define('set', 'pret', True)
                case '--verbose'|'-V':
                    res.define('set', 'verb', True)
                case '--debug'|'-D':
                    res.define('set', 'debg', True)
                case '--quiet'|'-Q':
                    res.define('set', 'quiet', True)
                case '--help'|'-h'|'help':
                    res.define(CliParser.MAIN_CHAIN, 'msg', About.getHelpMsg)
                case '--version'|'-v':
                    res.define(CliParser.MAIN_CHAIN, 'msg', About.getVersionMsg)
                case _:
                    mode = Mode.findMode(arg)
                    if mode == None:
                        raise CliSyntaxError(f"Unknown command: {arg}")
                    res.define(CliParser.MAIN_CHAIN, 'mode', mode)

            fun = res.latest

        if fun == None:
            raise CliSyntaxError("No parameter provided.")
        elif isinstance(fun, CliParser.OptionArg) and not fun.exploited:
            raise CliSyntaxError(f"Missing parameters for option {fun.name}")

        if hasattr(res, 'main_mode') and hasattr(res, 'main_msg'):
            raise CliSyntaxError(f"Unbigous arguments provided, \n    use '--help' for help.")

        # finalise:
        if not hasattr(res, 'main_mode'):
            res.define(CliParser.MAIN_CHAIN, 'mode')

        if not hasattr(res, 'main_msg'):
            res.define(CliParser.MAIN_CHAIN, 'msg')

        if not hasattr(res, 'conf_file'):
            res.define('conf', 'file')

        if not hasattr(res, 'set_pret'):
            res.define('set', 'pret', False)

        if not hasattr(res, 'set_verb'):
            res.define('set', 'verb', False)

        if not hasattr(res, 'set_debg'):
            res.define('set', 'debg', False)

        if not hasattr(res, 'set_quiet'):
            res.define('set', 'quiet', False)

        return res

