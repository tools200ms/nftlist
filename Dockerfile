FROM 200ms/alpinenet_dev2

# How To build Alpine package:
# https://wiki.alpinelinux.org/wiki/Creating_an_Alpine_package

ENV FEATURES=""

# required  openrc bash nftables jq
RUN dev2_addtools.sh openrc bash nftables jq \
                     py3-nftables \
                     ulogd alpine-sdk


# install network software to experiment with:
RUN dev2_addtools.sh conntrack-tools tcpdump \
                     openssh-client openssh-server scanssh \
                     lighttpd \
                     inetutils-telnet

RUN dev2_addtools.sh docs

# to launch services inside container:
RUN mkdir -p /run/openrc && touch /run/openrc/softlevel

COPY ./src/init.d/nftlist /etc/init.d/
COPY ./src/cron/nftlist.daily.sh /etc/periodic/daily/

COPY ./src/nftlist-little.sh /usr/local/bin/
COPY ./src/nftlist.py /usr/local/bin/

RUN nftlist-little.sh init

COPY ./lists /etc/nftlists/included/predef
COPY ./examples /usr/share/nftlist

# overwrite:
COPY ./entry.sh /entry2.sh
RUN chmod +x /entry2.sh

CMD ["/entry2.sh"]
