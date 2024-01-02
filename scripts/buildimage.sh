#!/bin/bash

# Check for root privileges
if [ "$EUID" -ne 0 ]; then
    echo "Error: This script requires root privileges. Please run with 'sudo'."
    exit 1
fi

source ../config/build.conf

mkarchiso -v -w ${ISO} -o ${WORKDIR} ${RELENG}