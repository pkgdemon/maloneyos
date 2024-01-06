#!/bin/bash

# Check for root privileges
if [ "$EUID" -ne 0 ]; then
    echo "Error: This script requires root privileges. Please run with 'sudo'."
    exit 1
fi

# Function to check for path to make sure we are running in arch linux livecd
check_path() {
    if [ ! -d "/run/archiso/cowspace" ]; then
        echo "Error: This installer can only be run in the Arch Linux LiveCD environment."
        exit 1
    fi
}

check_path

MNT="/tmp/maloneyos"
DISK=$(cat /tmp/selected-disk)

# Unmount file  systems
umount "${MNT}"/dev >/dev/null 2>&1
umount "${MNT}"/proc >/dev/null 2>&1
umount "${MNT}"/sys/firmware/efi/efivars >/dev/null 2>&1
umount "${MNT}"/sys >/dev/null 2>&1
umount "${MNT}"/efi >/dev/null 2>&1

# Export active zpools
zpool export -a