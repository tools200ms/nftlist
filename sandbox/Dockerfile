FROM 200ms/alpinenet_dev2

# How To build Alpine package:
# https://wiki.alpinelinux.org/wiki/Creating_an_Alpine_package

ENV FEATURES="dev2fs python"

ENV MYROLE="solo"
# this is to plug WireShark:
ENV MYPIPES_DIR="/tmp/pipes.my"
ENV PIPES_DIR="/tmp/pipes"

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

RUN mkdir $MYPIPES_DIR

RUN feat setup --all
RUN bash -l -c "pip install nftlist"

# overwrite:
COPY files/entry.sh /entry2.sh
RUN chmod +x /entry2.sh

ENTRYPOINT ["/entry2.sh"]
