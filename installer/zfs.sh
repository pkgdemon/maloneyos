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
SWAPSIZE=4
RESERVE=1
DISK=$(cat /tmp/selected-disk)

# Check if the boot menu entry already exists
entries=("MaloneyOS")
for entry in "${entries[@]}"; do
    existing_entry=$(efibootmgr | grep "$entry")
    if [[ -n "$existing_entry" ]]; then
        # Remove the existing entries before creating a new one
        entry_number=$(echo "$existing_entry" | awk '{print $1}' | sed 's/Boot//' | sed 's/^00//' | tr -d '*')
        efibootmgr -Bb "$entry_number"
    fi
done

# Make MNT directory if it does not exist
if [ ! -d "${MNT}" ]; then
    mkdir "${MNT}"
fi

# Unmount file  systems
umount "${MNT}"/dev >/dev/null 2>&1
umount "${MNT}"/proc >/dev/null 2>&1
umount "${MNT}"/sys/firmware/efi/efivars >/dev/null 2>&1
umount "${MNT}"/sys >/dev/null 2>&1
umount ${MNT}/efi >/dev/null 2>&1

# Export active zpools
zpool export -a
zpool labelclear zroot -f 2>/dev/null

# Remove MNT directory and recreate it
rm -rf "${MNT}" >/dev/null 2>&1
mkdir "${MNT}" >/dev/null 2>&1

# Ensure disk has been erased properly with wipefs
wipefs -aq "$DISK"

# Generate hostid
zgenhostid

# Partition the disk
sgdisk --zap-all $DISK
sgdisk -n1:1M:+512M -t1:EF00 $DISK
sgdisk -n2:0:0 -t2:BF00 $DISK

# Create zroot
zpool create -f \
 -o ashift=12 \
 -o autotrim=on \
 -O acltype=posixacl \
 -O compression=zstd \
 -O dnodesize=auto \
 -O normalization=formD \
 -O relatime=on \
 -O xattr=sa \
 -m none zroot "${DISK}"2

# Create datasets
zfs create -o mountpoint=none zroot/ROOT
zfs create -o mountpoint=/ -o canmount=noauto zroot/ROOT/arch
zfs create -o mountpoint=/home zroot/home

# Test the pool by importing and exporting
zpool export zroot
zpool import -N -R "${MNT}" zroot
zfs mount zroot/ROOT/arch
zfs mount zroot/home

# Create and mount the EFI partition
mkfs.vfat -F 32 -n EFI ${DISK}1
mkdir "${MNT}"/efi
mount "${DISK}"1 "${MNT}"/efi