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

USERNAME=$(cat /tmp/username)
PASSWORD=$(cat /tmp/password)

# Remove user "archie" from chroot
chroot /tmp/maloneyos userdel archie
chroot /tmp/maloneyos rm -rf /home/archie

# Add user with specified username
chroot /tmp/maloneyos useradd -m -G wheel -s /usr/bin/zsh "$USERNAME"
chroot /tmp/maloneyos useradd -m "$USERNAME"

# Set PASSWORD for the user
echo "$USERNAME:$PASSWORD" | chroot /tmp/maloneyos chpasswd <<< "$USERNAME:$PASSWORD"

# Remove sddm.conf autologin
chroot /tmp/maloneyos rm /etc/sddm.conf.d/autologin.conf

sudoers_dir="/tmp/maloneyos/etc/sudoers.d"
rm "$sudoers_dir/00_archie"

echo "$USERNAME ALL=(ALL) ALL" >> "$sudoers_dir/00_$USERNAME"
echo "$USERNAME ALL=(ALL) ALL" >> "$sudoers_dir/00_$USERNAME"