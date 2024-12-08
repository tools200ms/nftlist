FROM 200ms/alpinenet_dev2

# How To build Alpine package:
# https://wiki.alpinelinux.org/wiki/Creating_an_Alpine_package

ENV FEATURES="python"

# required  openrc bash nftables jq
RUN dev2_addtools.sh openrc bash nftables jq \
                     py3-nftables \
                     ulogd alpine-sdk


COPY ./setup/nftlist.init /etc/init.d/nftlist
COPY ./setup/refresh-nftlist.sh /etc/periodic/daily/nftlist.daily.sh

#COPY ./src/nftlist-little.sh /usr/local/bin/
COPY ./nftlist/ /usr/local/bin/nftlist/


COPY ./examples /usr/share/nftlist/

COPY ../setup.py /root/
