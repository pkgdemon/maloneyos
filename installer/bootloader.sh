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

# Set a cachefile for ZFS
chroot "${MNT}" zpool set cachefile=/etc/zfs/zpool.cache zroot

# Set the bootfs
chroot "${MNT}" zpool set bootfs=zroot/ROOT/arch zroot

# Enable all needed daemons
chroot "${MNT}" systemctl enable zfs-import-cache zfs-import.target zfs-mount zfs-zed zfs.target

# Create EFI subfolder
chroot "${MNT}" mkdir -p /efi/EFI/zbm

# Get the latest zfsbootmenu
wget https://get.zfsbootmenu.org/latest.EFI -O "${MNT}"/efi/EFI/zbm/zfsbootmenu.EFI

# Add an entry to your boot menu
chroot "${MNT}" efibootmgr --disk "${DISK}" --part 1 --create --label "ZFSBootMenu" --loader '\EFI\zbm\zfsbootmenu.EFI' --unicode "spl_hostid=$(hostid) zbm.timeout=3 zbm.prefer=zroot zbm.import_policy=hostid" --verbose

# Set the kernel parameters
chroot "${MNT}" zfs set org.zfsbootmenu:commandline="noresume init_on_alloc=0 rw spl.spl_hostid=$(hostid)" zroot/ROOT