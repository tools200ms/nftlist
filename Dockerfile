FROM 200ms/alpinenet_dev2

# How To build Alpine package:
# https://wiki.alpinelinux.org/wiki/Creating_an_Alpine_package

# required  openrc bash nftables jq
RUN dev2_addtools.sh openrc bash nftables jq \
                     ulogd alpine-sdk


# install network software to experiment with:
RUN dev2_addtools.sh openssh-client openssh-server scanssh \
                     lighttpd \
                     inetutils-telnet

# to launch services inside container:
RUN mkdir -p /run/openrc && touch /run/openrc/softlevel

COPY ./src/nft-helper /etc/init.d/
COPY ./src/nft-helper.sh /usr/local/bin/
COPY ./src/nft-helper.daily.sh /etc/periodic/daily/

# NFT Examples:
# /usr/share/nftables/
