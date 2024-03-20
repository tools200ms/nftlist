import os
import sys
from abc import abstractmethod
from dataclasses import dataclass
from enum import Enum
import re

import nftables
import json

from os import listdir
from os.path import isfile, isdir, exists, join, normpath, realpath


class CmdOption:
    __context_pattern = re.compile("[a-z0-9]{1,32}")
    __context = {}

    @staticmethod
    @abstractmethod
    def validate(arg):
        pass

    def context(self, name: str, value = None):
        if self.__context_pattern.fullmatch(name) == None:
            raise Exception('Internal error, not allowed context name')

        if value == None:
            return self.__context[name]

        self.__context[name] = value
        return None

class BinaryArg:
    @staticmethod
    @abstractmethod
    def validate(arg) -> bool:
        pass

    @staticmethod
    @abstractmethod
    def print(self) -> None:
        pass


class StrArg:
    @staticmethod
    @abstractmethod
    def validate(arg):
        pass

    @abstractmethod
    def feed(self):
        pass

class StrArgWCnt(StrArg):
    def __init__(self):
        self.__arg_feed_cnt = -1

    def postincr(self, skip = False):
        self.__arg_feed_cnt += 1
        return self.__arg_feed_cnt

    def decr(self):
        self.__arg_feed_cnt -= 1

class ConfError(Exception):
    pass

class DataError(Exception):
    pass


class Program:
    @staticmethod
    def name() -> str: return "NFT List"
    @staticmethod
    def command() -> str: return "nftlist"
    @staticmethod
    def Author() -> str: return "Mateusz Piwek"

    @staticmethod
    def Version() -> str: return "1.2.9 - alpha"

    @staticmethod
    def License() -> str: return "MIT License"

    class Action (CmdOption, Enum):
        UPDATE = 'update'
        PURGE = 'purge'
        PANIC = 'panic'

        def __init__(self, value):
            self.context('wizzard', False)
            self.__value = value

        @staticmethod
        def validate(arg):
            res = None
            match(arg):
                case 'update' | 'u':
                    res = Program.Action.UPDATE
                case 'purge':
                    res = Program.Action.PURGE
                case 'panic':
                    res = Program.Action.PANIC
            return res

    class ConfPath(CmdOption):
        @staticmethod
        def DEFAULT() -> str: return '/etc/nftlists/enabled'

        def getPath(self):
            return self.__path

        def __init__(self, path : str = None):
            if path == None:
                self.__path = Program.ConfPath.DEFAULT()
            else:
                self.__path = path

            if isdir(self.__path):
                self.__isdir = True
            elif isfile(self.__path):
                self.__isdir = False
            else:
                raise Exception('Configuration file or direcotry not found')

            self.__path = realpath(self.__path)
        def isDir(self):
            return self.__isdir
        @staticmethod
        def validate(arg):
            return Program.ConfPath(arg)

    class SetArg(StrArgWCnt):
        def __init__(self):
            super().__init__()
            self._family = None
            self._table = None
            self._set = None

        @staticmethod
        def validate(arg):
            if arg == '--set' or arg == '-s':
                return Program.SetArg()
            return None

        def feed(self, arg):
            if arg.startswith('--'):
                raise ConfError('Incorrect syntax')

            match(self.postincr()):
                case 0:
                    self._family = arg
                case 1:
                    self._table = arg
                case 2:
                    self._set = arg
                    # end of data list
                    return None
                case _:
                    raise Exception('Something wrong went with a code flow')

            return self

    class SetDirect(SetArg):
        def validate(self, arg):
            if arg == '@set':
                return Program.SetDirect()
            return None

    class InclDirArg(StrArg):
        DEFAULT = '/etc/nftlists/included'

        def __init__(self, path : str = None):
            if path == None:
                path = Program.InclDirArg.DEFAULT

            self.setPath(path)
        def setPath(self, path : str):
            if isdir(arg):
                self.__path = path
            # specifig error msg.
            elif exists(path):
                raise ConfError('--includedir should be a directory path')
            else:
                raise ConfError('--includedir does not point to existing directory')

            self.__path = realpath(self.__path)

        def getPath(self) -> str:
            return self.__path
        def validate(arg):
            if arg == '--includedir' or arg == '-D':
                return Program.InclDirArg(None)
            return None

        def feed(self, arg):
            self.setPath(arg)
            return None

    class HelpArg (BinaryArg):

        @staticmethod
        def validate(arg):
            return arg == '--help' or '-h'

        @staticmethod
        def print(self):
            print(f"Command syntax: \
{Program.command()} <update|purge|panic> [conf. path] [--set <address family> <table> <set>] [--includedir <path>]\
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

    class VersionArg(BinaryArg):
        @staticmethod
        def validate(arg):
            return arg == '--version' or '-v'

        @staticmethod
        def print():
            print(f"NFT List, version: {Program.Version()}\
Created by {Program.License()}, released with {Program.License()}")

action = None
config = None

incl_arg = None
set_arg = None

feed = None

for arg in sys.argv[1:]:
    if feed != None:
        feed = feed.feed(arg)
        continue

    if arg.startswith('-'):
        if Program.HelpArg.validate(arg):
            Program.HelpArg.print()
            exit(0)
        elif Program.VersionArg.validate(arg):
            Program.VersionArg.print()
            exit(0)
        else:
            feed = Program.SetArg.validate(arg)

            if feed != None:
                if set != None:
                    raise ConfError('Illegal argument re-declaration: ' + arg)
                set = feed
                continue

            feed = Program.InclDirArg.validate(arg)
            if feed != None:
                if incl_arg != None:
                    raise ConfError('Illegal argument re-declaration: ' + arg)

                incl_arg = feed
                continue

            raise ConfError('Unsupported argument: ' + arg)
    else:
        if action == None:
            action = Program.Action.validate(arg)
            if action != None:
                continue

        if config == None:
            config = Program.ConfPath(arg)
            if config != None:
                continue

        raise ConfError('Unidentified operation: ' + arg)

# Get default values if not passed with command arguments
if action == None:
    action = Program.Action.UPDATE
    action.context('wizzard', True)

if config == None:
    config = Program.ConfPath()

if incl_arg == None:
    incl_arg = Program.InclDirArg()


conf_path = config.getPath()

conf_files = []
if config.isDir():
    with os.scandir(conf_path) as dir_it:
        for entry in dir_it:
            if entry.name.endswith('.list') and entry.is_file():
                conf_files.append(entry.name)
else:
    conf_files.append(conf_path)

# ensure files are in alpha-numeric order:
conf_files.sort()

# parse files

for cf in conf_files:
    cf_path = join(conf_path, cf)
    print('Reading \'' + cf_path + '\'')

if set_arg == None:
    print('No set has been encouned, exiting')
    exit(1)


#LIST_INPUT
#for file in listdir()


#nft = nftables.Nftables()
#nft.set_json_output(True)

#rc, output, error = nft.cmd("list ruleset")
#print(json.loads(output))

