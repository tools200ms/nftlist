
import sys
from enum import Enum

import nftables
import json

from os import listdir
from os.path import isfile, isdir, exists, join

class ConfError(Exception):
    pass

class DataError(Exception):
    pass


class Program:
    class Action (Enum):
        UPDATE = 'update'
        PURGE = 'purge'
        PANIC = 'panic'

        def __init__(self, manual = False):
            self.manual = manual

        def isManual(self):
            return self.manual

        @staticmethod
        def validate(arg):
            res = None
            match(arg):
                case 'update' | 'u':
                    res = Program.Action.UPDATE()
                case 'purge':
                    res = Program.Action.PURGE()
                case 'panic':
                    res = Program.Action.PANIC()
            return res

    class ConfPath:
        DEFAULT='/etc/nftlists/enabled'
        def __init__(self, path = DEFAULT):
            self.path = path
        @staticmethod
        def validate(arg):
            res = None
            if isfile(arg) or isdir(arg):
                res = Program.ConfPath(arg)

            return res
    class SetDArg:
        def __init__(self):
            self.arg_feed_cnt = 0
            self.family = None
            self.table = None
            self.set = None

        @staticmethod
        def validate(arg):
            if arg == 'set' or arg == 's':
                return Program.SetArg()
            return None
        def feed(self, arg):
            match(self.arg_feed_cnt):
                case 0:
                    self.family = arg
                case 1:
                    self.table = arg
                case 2:
                    self.set = arg

            self.arg_feed_cnt += 1

    class inclDArg:
        pass

    class InclDirArg:
        DEFAULT = '/etc/nftlists/included'

        def __init__(self):
            self.path = Program.InclDirArg.DEFAULT
        def feed(self, arg):
            if isdir(arg):
                self.path = arg
            elif exists(arg):
                raise ConfError('--includedir should be a directory path')
            else:
                raise ConfError('--includedir does not point to existing directory')

    class HelpArg:

        @staticmethod
        def validate(arg):
            return arg == '--help' or '-h'

        def feed(self, arg):
            return False

        @staticmethod
        def print(self):
            print(f"Command syntax: \
{} <update|purge|panic> [conf. path] [--set <address family> <table> <set>] [--includedir <path>]\
\
	update,u - updates NFT sets according to settings from configuration\
	purge    - delete all elements of NFT sets referred in configuration\
	panic    - keep, or discard NFT sets that has been marked by directive @onpanic\
\
	Optional:\
	<conf path> - path to file or directory configuration, if path is a directory\
	              all '*.list' files under this location are loaded (no recurcive search)\
\
	--set,-s - define set, replaces '@set' directive from file\
	--includedir,-D - indicates search directory for files included with '@include' directive\
\
	If settings are not provided, default values are:\
		'$_DEFAULT_CONF' as configuration directory and\
		'$_DEFAULT_INCL' as include directory is used\
\
$(basename $0) --help | -h\
	Print this help\
\
$(basename $0) --version | -v\
	Print version")

    class VersionArg:

        @staticmethod
        def validate(arg):
            return arg == '--version' or '-v'
        def feed(self, arg):
            return False

        def print(self):
            pass



print (sys.argv[1])

action = Program.Action(True)
config = Program.ConfPath()
include = Program.InclDirArg()
set = None
feed = None

# for arg in sys.argv:
    argv = sys.argv;
    arg_idx = 0

    if argv[arg_idx].startswith('-'):
        if feed != '-':
            raise ConfError('Incorrect syntax')

        if Program.HelpArg.validate(argv[arg_idx]):
            Program.HelpArg.print()
            exit(0)
        elif Program.VersionArg.validate(argv[arg_idx]):
            Program.VersionArg.print()
            exit(0)
        elif set == None:
            set = Program.SetDArg(argv[arg_idx])
            if set != None:
                feed = set
                arg_idx += 1

    passed_action = Program.Action.validate(argv[arg_idx])
    if passed_action != None:
        action = passed_action
        arg_idx += 1

    passed_config = Program.ConfPath(argv[arg_idx])
    if passed_config ~= None:
        config = passed_config
        arg_idx += 1



#LIST_INPUT
#for file in listdir()


#nft = nftables.Nftables()
#nft.set_json_output(True)

#rc, output, error = nft.cmd("list ruleset")
#print(json.loads(output))

