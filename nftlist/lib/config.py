from ctypes import Union
from typing import Final


class Config:

    CLOUDFLARE_IPv4_NS1: Final = "1.1.1.1"
    CLOUDFLARE_IPv4_NS2: Final = "1.0.0.1"
    CLOUDFLARE_IPv6_NS1: Final = "2606: 4700:4700::1111"
    CLOUDFLARE_IPv6_NS2: Final = "2606: 4700:4700::1001"


    def __init__(self, ini_conf_path: Union[str|None] = None):

        if ini_conf_path == None:
            self.__ini_conf_path = "/etc/nftlist/conf.ini"
        else:
            self.__ini_conf_path = ini_conf_path

        self.__ns1_ipv4 = Config.CLOUDFLARE_IPv4_NS1
        self.__ns2_ipv4 = Config.CLOUDFLARE_IPv4_NS2
        self.__ns1_ipv6 = Config.CLOUDFLARE_IPv6_NS1
        self.__ns2_ipv6 = Config.CLOUDFLARE_IPv6_NS2



