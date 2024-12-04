import logging
from pprint import pprint

from nftlist.core.modes import Mode
from nftlist.lib.cli_parser import CliParser
from nftlist.lib.exceptions import CliSyntaxError
from nftlist.lib.logger import Log


class Nftlist():
    @staticmethod
    def main( argv: [str] ) -> int:
        try:
            res = CliParser.parse(argv)
            if res.set_quiet:
                if not res.set_debg and not res.set_verb:
                    Log.init(logging.NOTSET)
                else:
                    raise CliSyntaxError(f"Flags conflicting with '--quiet'")

            elif res.set_debg:
                Log.init(logging.DEBUG)
                if __debug__:
                    Log.info("DEBUG mode ON")
                else:
                    Log.warn("No debug level messages available.\n '--debug' flag is ignored.")
            elif res.set_verb:
                Log.init(logging.WARN)
            # else - default logging for 'logging' is: WARNING
            # no need to do anything

            if res.main_msg != None:
                print(res.main_msg())
                if res.main_mode != None:
                    # return error code if excess parameters has been found
                    return 2
                else:
                    return 0

            if res.main_mode == None:
                raise CliSyntaxError("Mode has not been defined, nothing to do")

        except CliSyntaxError as syntax_err:
            Log.error(f"CLI Syntax Error: {syntax_err}")
            return 1

        res.main_mode.run()

        return 0
