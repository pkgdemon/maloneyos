#!/bin/bash

# Check for root privileges
if [ "$EUID" -ne 0 ]; then
    echo "Error: This script requires root privileges. Please run with 'sudo'."
    exit 1
fi

# Load configuration
source ../config/build.conf

# Build the image
mkarchiso -v \
          -w "${ISO}" \
          -o "${WORKDIR}" \
          "${RELENG}"