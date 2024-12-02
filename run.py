import sys

from nftlist.lib.arg_parser import ArgParser

if __name__ == "__main__":
    mode, fun = ArgParser.parse(sys.argv)

    if mode == None and fun == None:
        raise Exception("No parameter provided.")

exit(0)
