FROM 200ms/alpinenet_dev2

# How To build Alpine package:
# https://wiki.alpinelinux.org/wiki/Creating_an_Alpine_package

# required  openrc bash nftables jq
RUN dev2_addtools.sh openrc bash nftables jq \
                     py3-nftables \
                     ulogd alpine-sdk


# install network software to experiment with:
RUN dev2_addtools.sh openssh-client openssh-server scanssh \
                     lighttpd \
                     inetutils-telnet

# to launch services inside container:
RUN mkdir -p /run/openrc && touch /run/openrc/softlevel

COPY ./src/init.d/nftlist /etc/init.d/
COPY ./src/cron/nftlist.daily.sh /etc/periodic/daily/

COPY ./src/nftlist.sh /usr/local/bin/
COPY ./src/nftlist.py /usr/local/bin/

# NFT Examples:
# /usr/share/nftables/
