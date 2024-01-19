FROM 200ms/alpinenet_dev2

# How To build Alpine package:
# https://wiki.alpinelinux.org/wiki/Creating_an_Alpine_package

RUN dev2_addtools.sh openrc bash nftables jq \ # required
                        ulogd alpine-sdk

COPY src/nft-helper /etc/init.d/
COPY src/nft-helper.sh /usr/local/bin/
COPY src/nft-helper.daily.sh /etc/periodic/daily/


