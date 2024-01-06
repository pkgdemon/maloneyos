#!/usr/bin/env python3
        
import os
import subprocess

# Check for root privileges
if os.geteuid() != 0:
    print("Error: This script requires root privileges. Please run with 'sudo'.")
    exit(1)

WORKDIR="/tmp/maloneyos"
ISO=f"{WORKDIR}/archiso-tmp"
RELENG=f"{WORKDIR}/archlive"

# Build the image
subprocess.run(["mkarchiso", "-v", "-w", ISO, "-o", WORKDIR, RELENG])
