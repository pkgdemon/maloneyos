#!/usr/bin/env python3
'''
Script to build the after customizations.
'''
import subprocess

# Define variables
WORKDIR="/tmp/maloneyos"
ISO=f"{WORKDIR}/archiso-tmp"
RELENG=f"{WORKDIR}/archlive"

# Build the image
subprocess.run(["mkarchiso", "-v", "-w", ISO, "-o", WORKDIR, RELENG], check=True)

# End-of-file (EOF)
