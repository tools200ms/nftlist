
import argparse
from ctypes import Union
from typing import Callable, Final, Tuple

from nftlist.core.modes import Mode
from nftlist.lib.about import About
from nftlist.lib.exceptions import CliSyntaxError
from nftlist.lib.validators import FileValidator


class CliParser:

    MAIN_CHAIN: Final = '_'
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
    def parse( argv: [str] ):
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
                case 'verbose'|'-V':
                    res.define('set', 'verb', True)
                case '--help'|'-h'|'help':
                    res.define(CliParser.MAIN_CHAIN, 'msg', CliParser.printHelp)
                case '--version'|'-v':
                    res.define(CliParser.MAIN_CHAIN, 'msg', CliParser.printVersion)
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

        if hasattr(res, '__mode') and hasattr(res, '__msg'):
            raise CliSyntaxError(f"Unbigous arguments provided, \n    use '--help' for help.")

        # finalise:
        if not hasattr(res, '__mode'):
            res.define(CliParser.MAIN_CHAIN, 'mode')

        if not hasattr(res, '__msg'):
            res.define(CliParser.MAIN_CHAIN, 'msg')

        if not hasattr(res, 'conf_file'):
            res.define('conf', 'file')

        if not hasattr(res, 'set_pret'):
            res.define('set', 'pret')

        if not hasattr(res, 'set_verb'):
            res.define('set', 'verb')

        return res
    @staticmethod
    def printHelp():
        text = f"Command syntax: \n\
        {About.command} <refresh|clean|panic> [--config_file|-c <path>] --do_pretend|-d\n\
\n\
	refresh,r - Refresh Nftables sets according to settings in configuration.\n\
	clean,c   - Remove all elements loaded to Nftables sets referred in configuration.\n\
	panic,p,! - keep, or discard NFT sets that has been marked by directive @onpanic, \n\
                or determinated as\n\
\n\
	Optional: \n\
	--config_file|-c <path> - path to INI configuration file\n\
    --do_pretend|-d         - don't do any Nftables modifications, just display what would be done.\n\
\n\
{About.command} --help | -h\n\
	Print this help\n\
\n\
{About.command} --version | -v\n\
	Print version\n\
        "

        print(text)

    @staticmethod
    def printVersion():
        text = f"{About.name}, version: {About.version}\n    by: {About.authors}"

