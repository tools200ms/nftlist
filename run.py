import sys

from nftlist.lib.cli_parser import CliParser
from nftlist.lib.exceptions import CliSyntaxError

if __name__ == "__main__":

    try:
        res = CliParser.parse(sys.argv)

        print( res.__mode )
    except CliSyntaxError as syntax_err:
        print(f"CLI Syntax Error: {syntax_err}")



exit(0)
