#!/bin/bash
set -xe

if [[ "$MYROLE" =~ ^[a-zA-Z0-9]+$ ]]; then
  if [ ! -e /tmp/pipes/$MYROLE ]; then
    mkfifo /tmp/pipes/$MYROLE
    chown 1000:1000 /tmp/pipes/$MYROLE
  elif [ ! -p /tmp/pipes/$MYROLE ]; then
    echo "Ensure file: '/tmp/pipes/$MYROLE' is a pipe"
    exit 2
  fi
fi

tcpdump -s 0 -U -n -w - -i any > /tmp/pipes/$MYROLE

exit 0
