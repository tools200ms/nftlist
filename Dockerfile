FROM 200ms/alpinenet_dev2

# How To build Alpine package:
# https://wiki.alpinelinux.org/wiki/Creating_an_Alpine_package

RUN dev2_addtools.sh openrc bash nftables alpine-sdk

COPY nft-helper /etc/init.d/
COPY nft-helper.sh /usr/local/bin/
COPY nft-helper.daily.sh /etc/periodic/daily/
