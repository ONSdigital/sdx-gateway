#!/bin/bash
if [ -z ${PORT+x} ];
then
    export PORT=5000;
fi

python3 -m app.main
