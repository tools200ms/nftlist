#!/bin/bash

# Compile and locally install multiple Python versions
[ -n "$DEBUG" ] && [[ $(echo "$DEBUG" | tr '[:upper:]' '[:lower:]') =~ ^y|yes|1|on$ ]] && \
        set -xe || set -e

# also '--pretend' parameter can be used
[ -n "$PRETEND" ] && [[ $(echo "$PRETEND" | tr '[:upper:]' '[:lower:]') =~ ^y|yes|1|on$ ]] && \
        RUN='echo' || RUN=


VERSIONS='3.13 3.12 3.11 3.10 3.9'
LOCALBIN='~/bin'


$RUN git clone https://github.com/python/cpython.git
$RUN cd cpython/


for v in $VERSIONS; do

    $RUN git checkout ${v}

    $RUN ./configure --enable-optimizations --prefix=${LOCALBIN}/python-${v}

    $RUN make -j$(nproc)

    $RUN make test

    $RUN make altinstall

done

exit 0
