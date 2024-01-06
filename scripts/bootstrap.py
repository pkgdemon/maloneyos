#!/usr/bin/env python3

import os
import shutil

# Check for root privileges
if os.geteuid() != 0:
    print("Error: This script requires root privileges. Please run with 'sudo'.")
    exit(1)

WORKDIR="/tmp/maloneyos"
ISO=f"{WORKDIR}/archiso-tmp"
RELENG=f"{WORKDIR}/archlive"

# Create the working directory if it doesn't exist
if not os.path.exists(WORKDIR):
    os.mkdir(WORKDIR)

# Copy the releng configuration
shutil.copytree('/usr/share/archiso/configs/releng/', RELENG, symlinks=True)