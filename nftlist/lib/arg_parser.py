
import argparse

from nftlist.core.modes import Mode
from nftlist.lib.about import About


class ArgParser:

    class OptionArg:
        def __init__(self, name: str, min_arg_cnt: int, max_arg_cnt: int):
            self.__oargs = (None,) * max_arg_cnt
            self.__obligatory_arg_cnt = min_arg_cnt
            self.__carg = 0
            self.__name = name
        def add(self, arg):
            if self.__carg >= len(self.__oargs):
                return False
            self.__oargs[self.__carg] = arg
            return True

        @property
        def exploited(self):
            return self.__carg >= self.__obligatory_arg_cnt

        @property
        def name(self):
            return self.__name

    @staticmethod
    def parse( argv: [] ):
        mode = None
        new_mode = None
        fun  = None
        fun_chain = {'msg': None, 'conf': None, 'set': {}}
        fun_chain_ref = None

        for cnt, arg in enumerate(argv[1:]):

            if len(arg) > 2048 or '\n' in arg or '\r' in arg:
                raise Exception(f"Incorrect argument no.: {cnt}")

            if fun != None and isinstance(fun, ArgParser.OptionArg):
                if fun.add(arg) == False:
                    raise Exception(f"Excess option parameters: {fun.name} ... {arg}")
                continue

            match arg:
                # check for options:
                case '--config_file|-c':
                    fun_chain_ref = fun_chain['conf']
                    fun = ArgParser.OptionArg(arg, 1, 1)
                case '--pretend|-p':
                    fun_chain_ref = fun_chain['set']['p']
                    fun = ArgParser.OptionArg(arg, 0, 0)
                case 'verbose|-V':
                    fun_chain_ref = fun_chain['set']['V']
                    fun = ArgParser.OptionArg(arg, 0, 0)
                case '--help|-h|help':
                    fun_chain_ref = fun_chain['msg']
                    fun = ArgParser.printHelp
                case '--version|-v':
                    fun_chain_ref = fun_chain['msg']
                    fun = ArgParser.printVersion
                case _:
                    new_mode = Mode.findMode(arg)
                    if new_mode == None:
                        raise Exception(f"Unknown mode: {arg}")

            if mode == None:
                mode = new_mode
            else:
                raise Exception(f"Redefined modes: {mode} and {new_mode}")

            if fun != None:
                if fun_chain_ref != None:
                    fun_chain_ref = fun
                else:
                    raise Exception(f"Conflicting options: {fun.name} and {fun_chain_ref.name}")
                fun = None


        if fun != None and isinstance(fun, ArgParser.OptionArg) and not fun.exploited:
            raise Exception(f"Missing parameters for option {fun.name}")

        return mode, fun
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

