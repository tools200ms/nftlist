import logging
from pprint import pprint

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

            print(res.main_mode)
            print(res.main_msg())
        except CliSyntaxError as syntax_err:
            Log.error(f"CLI Syntax Error: {syntax_err}")

        return 0
