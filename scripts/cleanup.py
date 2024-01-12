#!/usr/bin/env python3

import os
import shutil

# Define variables
WORKDIR="/tmp/maloneyos"

# Remove the working directory if it exists
if os.path.isdir(WORKDIR):
    shutil.rmtree(WORKDIR)

# End-of-file (EOF)
