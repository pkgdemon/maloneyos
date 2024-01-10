#!/usr/bin/env python3
        
import os
import subprocess

# Define variables
WORKDIR="/tmp/maloneyos"
ISO=f"{WORKDIR}/archiso-tmp"
RELENG=f"{WORKDIR}/archlive"

# Build the image
subprocess.run(["mkarchiso", "-v", "-w", ISO, "-o", WORKDIR, RELENG])
