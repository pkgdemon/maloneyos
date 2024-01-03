#!/bin/bash

# Check for root privileges
if [ "$EUID" -ne 0 ]; then
    echo "Error: This script requires root privileges. Please run with 'sudo'."
    exit 1
fi

# Source the build configuration file
source ../config/build.conf

# Remove the working directory if it exists
if [ -d "${WORKDIR}" ]; then
    rm -rf "${WORKDIR}"
fi