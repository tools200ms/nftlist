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

    def context(self, name: str, value=None):
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
    def __init__(self, arg, sarg):
        self._arg = arg
        self._sarg = sarg
        self._assocobj = None

    def getArg(self) -> str:
        return self._arg

    def getSArg(self) -> str:
        return self._sarg

    def validate(self, arg):
        if self._assocobj != None:
            raise ConfError('Illegal argument re-declaration: ' + self._arg)

        return arg == self._arg or arg == self._sarg

    def getAssocObj(self):
        if self._assocobj == None:
            raise Exception('Missing argument(s) for: ' + self._arg)

        return self._assocobj

    @abstractmethod
    def feed(self):
        pass


class StrArgWCnt(StrArg):
    def __init__(self, arg, sarg):
        super().__init__(arg, sarg)
        self.__arg_feed_cnt = -1

    def postincr(self, skip=False):
        self.__arg_feed_cnt += 1
        return self.__arg_feed_cnt

    def decr(self):
        self.__arg_feed_cnt -= 1


class ConfError(Exception):
    pass


class DataError(Exception):
    pass


class InclDirPath:
    __DEFAULT = '/etc/nftlists/included'

    def __init__(self, path=__DEFAULT):
        self.__path = normpath(path)
        self.__verified = False

    def verifyPath(self):
        if self.__verified:
            return

        if not isdir(self.__path) and exists(self.__path):
            raise ConfError('--includedir should be a directory path')
        else:
            raise ConfError('--includedir does not point to existing directory')

        # rewrite to realpath
        self.__path = realpath(self.__path)
        self.__verified = True

    def getFilePath(self, file_name):
        self.verifyPath()
        return os.path.join(self.__path, file_name)


class NFTListDirective:
    def update(self):
        pass


class SetDirective(NFTListDirective):
    def __init__(self, family, tablen, setn):
        errors = []

        match family:
            case 'ip' | 'ip6' | 'inet' | 'arp' | 'bridge' | 'netdev':
                self.__family = family
            case '-':
                self.__family = None
            case _:
                errors.append('Incorrect family name or no \'-\' qualifier provided')

        if re.fullmatch('([a-zA-Z0-9_\.\-]){1,64}', tablen) != None:
            self.__tablen = tablen
        elif tablen == '-':
            self.__tablen = None
        else:
            errors.append('Illegal table name or no \'-\' qualifier provided')

        if re.fullmatch('([a-zA-Z0-9_\.\-]){1,64}', setn) != None:
            self.__setn = setn
        elif setn == '-':
            self.__setn = None
        else:
            errors.append('Illegal set name or no \'-\' qualifier provided')

        if len(errors) != 0:
            errors.insert(0, 'Cannot load set, following errors has been encounted: ')
            raise ConfError('\n * '.join(errors))

    def isCompleate(self):
        pass

    def merge(self, perv_set):
        pass


class InclDirective(NFTListDirective):
    def __init__(self, file_name):
        self.__file_name = normpath(file_name)


class OnPanicDirective(NFTListDirective):
    def __init__(self):
        pass


class Program:
    @staticmethod
    def name() -> str:
        return "NFT List"

    @staticmethod
    def command() -> str:
        return "nftlist"

    @staticmethod
    def Author() -> str:
        return "Mateusz Piwek"

    @staticmethod
    def Version() -> str:
        return "1.2.9 - alpha"

    @staticmethod
    def License() -> str:
        return "MIT License"

    class Action(CmdOption, Enum):
        UPDATE = 'update'
        PURGE = 'purge'
        PANIC = 'panic'

        def __init__(self, value):
            self.context('wizzard', False)
            self.__value = value

        @staticmethod
        def validate(arg):
            res = None
            match (arg):
                case 'update' | 'u':
                    res = Program.Action.UPDATE
                case 'purge':
                    res = Program.Action.PURGE
                case 'panic':
                    res = Program.Action.PANIC
            return res

    class ConfPath(CmdOption):
        __DEFAULT = '/etc/nftlists/enabled'

        def getPath(self):
            return self.__path

        def __init__(self, path: str = __DEFAULT):
            if isdir(path):
                self.__isdir = True
            elif isfile(path):
                self.__isdir = False
            else:
                raise Exception('Configuration file or direcotry not found')

            self.__path = realpath(path)

        def isDir(self):
            return self.__isdir

        @staticmethod
        def validate(arg):
            return Program.ConfPath(arg)

    class SetArg(StrArgWCnt):
        def __init__(self):
            super().__init__('--set', '-s')
            self._family = None
            self._table = None

        def feed(self, arg):
            if arg.startswith('--'):
                raise ConfError('Incorrect syntax')

            match (self.postincr()):
                case 0:
                    self._family = arg
                case 1:
                    self._table = arg
                case 2:
                    # end of data list
                    self._assocobj = SetDirective(self._family, self._table, arg)
                    return None
                case _:
                    raise Exception('Something wrong went with a code flow')

            return self

    class InclDirArg(StrArg):
        def __init__(self, path: str = None):
            super().__init__('--includedir', '-D')

        def feed(self, arg):
            self._assocobj = InclDirPath(arg)
            self._assocobj.verifyPath()
            return None

    class HelpArg(BinaryArg):

        @staticmethod
        def validate(arg):
            return arg == '--help' or arg == '-h'

        @staticmethod
        def print():
            )

    class VersionArg(BinaryArg):
        @staticmethod
        def validate(arg):
            return arg == '--version' or arg == '-v'

        @staticmethod
        def print():
            print(f"NFT List, version: {Program.Version()}\
Created by {Program.License()}, released with {Program.License()}")


Program.HelpArg.print()

exit(0)


# Meaningfull (not empty) line:
def parse_line(mean_line: str) -> None:
    # index of a comment mark '#'
    c_idx = mean_line.find('#')
    if c_idx != -1:
        # cut end comment
        mean_line = mean_line[0: c_idx].strip()

    if line[0] == '@':
        # directive has been encounted
        direct = line.split()
        match direct[0]:
            case '@set':
                if len(direct) != 4:
                    raise ConfError('@set directive requiers 4 arguments')
                return SetDirective(direct[1], direct[2], direct[3])

            case '@include':
                if len(direct) != 2:
                    raise ConfError('@ include directive requiers 1 argument')
                return InclDirective(direct[1])
            case '@query':
                raise Exception('Not implemented')
            case '@onpanic':
                if len(direct) != 2:
                    raise ConfError('@onpanic directive requiers 1 argument')
                return OnPanicDirective(direct[1])

    # clasify to what data set resource belongs to


action = None
config = None

set_arg = Program.SetArg()
incl_arg = Program.InclDirArg()

in_feed = None

for arg in sys.argv[1:]:
    if in_feed != None:
        in_feed = in_feed.feed(arg)
        continue

    if arg.startswith('-'):
        if Program.HelpArg.validate(arg):
            Program.HelpArg.print()
            exit(0)
        elif Program.VersionArg.validate(arg):
            Program.VersionArg.print()
            exit(0)
        else:
            if set_arg.validate(arg):
                in_feed = set_arg
                continue

            if incl_arg.validate(arg):
                in_feed = incl_arg
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

# if feed != None:


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
LINE_LEN_LIMIT = 2048
LINE_CNT_LIMIT = 1024 * 1024

# NFTListDirective
context = None

set_direct = set_arg.getAssocObj()
# parse files
for cf in conf_files:
    cf_path = join(conf_path, cf)
    print('Reading \'' + cf_path + '\'')

    try:
        with open(cf_path, 'r') as cf:
            line_no = 0
            while line_no < LINE_CNT_LIMIT:
                line_no += 1
                line = cf.readline(LINE_LEN_LIMIT).strip()
                lines = cf.readlines(4096)

                for line in lines:
                    pass

                map(None, lines)

                if not line:
                    break

                parse_line(line)

            if line_no == LINE_CNT_LIMIT:
                raise DataError(
                    f"Max line number count been excceded\n MAX_CNT_LIMIT: {LINE_CNT_LIMIT}, file:{cf_path}")
    except Exception as ex:
        print(f"Error in file: '{cf_path}' at line: {line_no}\n" + ' * \n'.join(ex.args))

if set_arg == None:
    print('No set has been encouned, exiting')
    exit(1)

# LIST_INPUT
# for file in listdir()


# nft = nftables.Nftables()
# nft.set_json_output(True)

# rc, output, error = nft.cmd("list ruleset")
# print(json.loads(output))

