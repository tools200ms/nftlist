import sys
from nftlist import Nftlist

ret_code = 0
if __name__ == "__main__":
    ret_code = Nftlist.main(sys.argv)

exit(ret_code)
