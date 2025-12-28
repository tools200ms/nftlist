FROM 200ms/alpinenet_dev2

# How To build Alpine package:
# https://wiki.alpinelinux.org/wiki/Creating_an_Alpine_package

ENV FEATURES="dev2fs python"

ENV MYROLE="solo"
# this is to plug WireShark:
ENV DEV2FS_TARGET="/run/pipes"

# required  openrc bash nftables jq
RUN dev2_addtools.sh openrc bash nftables jq \
                     py3-nftables \
                     ulogd util-linux-misc

# No need for the below package:
#alpine-sdk

# install network software to experiment with:
RUN dev2_addtools.sh conntrack-tools tcpdump \
                     openssh-client openssh-server scanssh \
                     lighttpd \
                     inetutils-telnet

RUN dev2_addtools.sh docs

# Copy project (for development purposes belo paths are overwriten by 'sandbox/compose.yaml'):
COPY setup/openrc/nftlist /etc/init.d/nftlist
COPY setup/openrc/nftlist-refresh.sh /etc/periodic/daily/nftlist.daily.sh
COPY ./nftlist/ /root/nftlist/
COPY setup/nftlist /usr/local/bin/nftlist
RUN chmod +x /usr/local/bin/nftlist
#RUN ln -s /usr/local/bin/nftlist ~/nftlist
COPY ./examples /usr/share/nftlist/
# =============

RUN mkdir $DEV2FS_TARGET

RUN feat setup --all
#RUN bash -l -c "pip install nftlist"

# overwrite:
COPY sandbox/entry-withtcpdump.sh /entry-withtcpdump.sh
RUN chmod +x /entry-withtcpdump.sh

ENTRYPOINT ["/entry-withtcpdump.sh"]
