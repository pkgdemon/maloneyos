#!/usr/bin/env python3

import os
import shutil
import sys

if os.geteuid() != 0:
    print("Error: This script requires root privileges. Please run with 'sudo'.")
    sys.exit(1)

# Define variables
WORKDIR="/tmp/maloneyos"

# Remove the working directory if it exists
if os.path.isdir(WORKDIR):
    shutil.rmtree(WORKDIR)