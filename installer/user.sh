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

# Prompt for username, password, and confirm password using kdialog
prompt_credentials() {
    username=$(kdialog --title "Enter Username" --inputbox "Please enter your username:")
    password=$(kdialog --title "Enter Password" --password "Please enter your password:")
    confirm_password=$(kdialog --title "Confirm Password" --password "Please confirm your password:")

    # Check if passwords match
    while [ "$password" != "$confirm_password" ]; do
        kdialog --title "Password Mismatch" --error "Passwords do not match. Please try again."
        password=$(kdialog --title "Enter Password" --password "Please enter your password:")
        confirm_password=$(kdialog --title "Confirm Password" --password "Please confirm your password:")
    done
}

check_path
prompt_credentials

# Remove user "archie" from chroot
chroot /tmp/maloneyos userdel archie
chroot /tmp/maloneyos rm -rf /home/archie

# Add user with specified username
chroot /tmp/maloneyos useradd -m -G wheel -s /usr/bin/zsh "$username"
chroot /tmp/maloneyos useradd -m "$username"

# Set password for the user
echo "$username:$password" | chroot /tmp/maloneyos chpasswd <<< "$username:$password"

# Remove sddm.conf autologin
chroot /tmp/maloneyos rm /etc/sddm.conf.d/autologin.conf

sudoers_dir="/tmp/maloneyos/etc/sudoers.d"
rm "$sudoers_dir/00_archie"

echo "$username ALL=(ALL) ALL" >> "$sudoers_dir/00_$username"
echo "$username ALL=(ALL) ALL" >> "$sudoers_dir/00_$username"