import configparser

from nftlist.lib.exceptions import IniFileFormatError


class IniParser():
    def __init__(self, path):
        self.__ini_parser = configparser.ConfigParser()

        with open(path) as f:
            self.__ini_parser.read_file(f)

        if not self.__ini_parser.has_section('nftlist'):
            raise IniFileFormatError(f"File '{path}' is missing [nftlist] section")

        nftlist = self.__ini_parser['nftlist2']

        # Extract values
#        flag_timeout = nftlist.get('flag_timeout')
#        conf_dir = nftlist.get('conf_dir')
#        incl_dir = nftlist.get('incl_dir')

        # Print parsed values
#        print("Parsed INI file:")
#        print(f"flag_timeout = {flag_timeout}")
#        print(f"conf_dir = {conf_dir}")
#        print(f"incl_dir = {incl_dir}")
