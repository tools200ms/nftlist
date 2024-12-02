
import nftables

class NFT:
    def __init__(self):
        self.__nft = nftables.Nftables()

    def fillSet(self):
        self.__nft.cmd("")



