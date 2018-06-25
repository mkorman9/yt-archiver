#!/bin/bash

OPTIONS='-o /data'

if [[ ! -z "$CHANNELS" ]]; then
    OPTIONS="$OPTIONS -c $CHANNELS"
else
    echo "CHANNELS parameter is required"
    exit 1
fi

if [[ ! -z "$KEY" ]]; then
    OPTIONS="$OPTIONS -k $KEY"
else
    echo "KEY parameter is required"
    exit 1
fi

if [[ ! -z "$RECORD_LIVESTREAMS" ]]; then
    OPTIONS="$OPTIONS -s"
fi

if [[ !  -z "$ARCHIVE_ALL" ]]; then
    OPTIONS="$OPTIONS -a"
fi

if [[ ! -z "$LOAD_PLUGINS" ]]; then
    OPTIONS="$OPTIONS -p /opt/ytarchiver/plugins.yml"
fi

python -m ytarchiver.main $OPTIONS
