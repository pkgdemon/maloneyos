#!/bin/bash

# Check for root privileges
if [ "$EUID" -ne 0 ]; then
    echo "Error: This script requires root privileges. Please run with 'sudo'."
    exit 1
fi

# Source the build configuration
source ../config/build.conf

# Create the working directory if it doesn't exist
if [ ! -d "${WORKDIR}" ]; then
    mkdir ${WORKDIR}
fi

# Copy the releng configuration
cp -r /usr/share/archiso/configs/releng/ ${RELENG}