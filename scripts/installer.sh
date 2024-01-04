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

MNT=$(mktemp -d)
SWAPSIZE=4
RESERVE=1

# Get a list of disk names excluding loop and sr0 devices
disk_names=$(lsblk -o NAME -n -p -r | grep -vE "loop|sr0|[0-9]")

# Create an array of menu items
menu_items=()
while read -r disk_name; do
    menu_items+=("$disk_name" "$disk_name")
done <<< "$disk_names"

# Use kdialog to present the menu
selected_disk=$(kdialog --menu "Select a disk:" "${menu_items[@]}" 2>/dev/null)

# Check if a disk is selected
if [ -z "$selected_disk" ] || [ "$selected_disk" == "cancel" ]; then
    kdialog --error "Error: No disk selected. Please choose a disk." 2>/dev/null
    selected_disk=""
    exit 1
fi

# Store the selected disk in the DISK variable
DISK="$selected_disk"

# Display the selected disk
kdialog --msgbox "You selected: $DISK" 2>/dev/null

# Export active zpools
zpool export -a
zpool labelclear bpool -f
zpool labelclear rpool -f

# Ensure disk has been erased properly with wipefs
wipefs -aq "$DISK"

# Partition the disk
partition_disk () {
 local disk="${1}"

 parted --script --align=optimal  "${disk}" -- \
 mklabel gpt \
 mkpart EFI 2MiB 1GiB \
 mkpart bpool 1GiB 5GiB \
 mkpart rpool 5GiB -$((SWAPSIZE + RESERVE))GiB \
 mkpart swap  -$((SWAPSIZE + RESERVE))GiB -"${RESERVE}"GiB \
 mkpart BIOS 1MiB 2MiB \
 set 1 esp on \
 set 5 bios_grub on \
 set 5 legacy_boot on

 partprobe "${disk}"
}

for i in ${DISK}; do
   partition_disk "${i}"
done

# Create the boot pool
# shellcheck disable=SC2046
zpool create -o compatibility=legacy  \
    -o ashift=12 \
    -o autotrim=on \
    -O acltype=posixacl \
    -O canmount=off \
    -O devices=off \
    -O normalization=formD \
    -O relatime=on \
    -O xattr=sa \
    -O mountpoint=/boot \
    -R "${MNT}" \
    bpool \
    $(for i in ${DISK}; do
       printf '%s ' "${i}2";
      done)

# Create the root pool
zpool create \
    -o ashift=12 \
    -o autotrim=on \
    -R "${MNT}" \
    -O acltype=posixacl \
    -O canmount=off \
    -O compression=zstd \
    -O dnodesize=auto \
    -O normalization=formD \
    -O relatime=on \
    -O xattr=sa \
    -O mountpoint=/ \
    rpool \
   $(for i in ${DISK}; do
      printf '%s ' "${i}3";
     done)