#!/bin/bash
set -xe

if [ -z "${MYROLE}" ]; then
  echo "'MYROLE' env. variable not set while required."
fi

if [[ "${MYROLE}" =~ ^[a-zA-Z0-9]+$ ]]; then
  if [ ! -e ${MYPIPES_DIR}/${MYROLE} ]; then
    mkfifo ${MYPIPES_DIR}/${MYROLE}
    #chown 1000:1000 /tmp/pipes/$MYROLE
  elif [ ! -p ${MYPIPES_DIR}/${MYROLE} ]; then
    echo "File '/tmp/pipes/${MYROLE}' is not a pipe as required"
    exit 2
  fi
fi

tcpdump -s 0 -U -n -w - -i any > ${MYPIPES_DIR}/${MYROLE}

exit 0
