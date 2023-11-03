FROM 200ms/alpinenet_dev2

RUN dev2_addtools.sh openrc bash nftables

COPY nft-helper /etc/init.d/
COPY nft-helper.sh /usr/local/bin/
COPY nft-helper.daily.sh /etc/periodic/daily/
